#!/usr/bin/env python3
"""
FitFindr over HTTP. ← UNIT 9

    python serve.py                       run it on your machine
    gunicorn serve:app                    run it the way a host runs it

Everything else in this repo exits after one command. A host has nothing to
keep running, so a command line cannot be deployed. This file is the smallest
thing that can: it starts a web server, waits, and hands each request to the
same `run_agent()` your CLI calls. **No new agent logic lives here.** If your
loop works from `python app.py ask`, it works from here; if it doesn't, fix it
there, not in this file.

Two routes:

    POST /ask       {"query": "vintage graphic tee under $30",
                     "wardrobe": {...}}     ← wardrobe is optional
    GET  /health    is it awake?

`/ask` returns the session dict from `run_agent()` as JSON, unchanged — the
same keys you print from the command line, including `error`. Read
`session["error"]` first, exactly as you do everywhere else.

It runs **one request at a time**, and one route is deliberately slower than a
web server has to be. The reason is worth reading before you deploy: see the
note above `_one_at_a_time` below — it also decides which gunicorn worker you
can use.

Instrumented (unit 9): every /ask writes one JSON line through
request_log.py — timing split into queue wait and agent time, the outcome,
model calls, tokens and memory. Two more routes read it back:

    GET  /stats     aggregates since this instance booted (p50/p95, outcomes)
    GET  /logs      the last requests' log lines, as JSON — so they can be
                    copied out before a free instance sleeps and loses them
"""

import os
import sys
import threading
import time

# config first, and before anything that talks to the model: it loads your .env
# and fixes the Windows console encoding for every module that imports it.
import config  # noqa: F401

from flask import Flask, jsonify, request

import generate
import request_log
from agent import run_agent
from utils.data_loader import get_example_wardrobe

app = Flask(__name__)
# Keep log lines in the order they were written (ts first), not alphabetical.
app.json.sort_keys = False


# ── one request at a time ─────────────────────────────────────────────────────
# Here's why this exists.
#
# A web server will happily run two requests at once. Two things in this repo
# assume otherwise:
#
#   • If you moved a tool onto MCP in unit 4, `mcp_client.call_tool` starts
#     `mcp_server.py` as a separate process over stdio, one per call. Two
#     overlapping requests means two extra Python interpreters, and the free
#     tier you're deploying to has 512 MB for all of it. That is the reason
#     that would still be here even if everything else were perfect.
#   • `generate.py`'s pacing window and its call counter are plain module
#     globals — deliberately, because that file is teaching pacing and quota,
#     not locking. Two threads sharing them means the per-minute limiter is
#     counting something that isn't true.
#
# What the lock covers is exactly the agent run: the part that spawns
# processes and calls the model. Reading the request, rejecting a bad one, and
# turning the answer into JSON all happen outside it — so a request with a
# malformed body comes straight back with a 400 instead of queueing behind
# somebody else's agent.
#
# Serialising the runs costs you nothing here — this is one user asking one
# question — and it keeps the deployed behaviour identical to the CLI's. When
# that stops being an acceptable trade, the fix is a real queue, not a bigger
# lock.
#
# The same constraint decides your start command, and this is the part that
# bites in deployment rather than on your machine. `mcp_client.call_tool`
# wraps `asyncio.run()`, and `asyncio.run()` refuses to start when an event
# loop is already running. An async worker always has one running. So under
# `gunicorn -k gevent` (or `-k eventlet`, or `serve:app` wrapped for an ASGI
# server like uvicorn) EVERY MCP call fails with "asyncio.run() cannot be
# called from a running event loop" — not some of them under load, all of
# them, every time, in a place your laptop never showed you.
#
#     gunicorn serve:app              ← works: the DEFAULT sync worker
#     gunicorn serve:app --threads 4  ← what render.yaml runs: threads, no
#                                       event loop, so MCP works, and /health
#                                       answers while an /ask runs (unit 9)
#     gunicorn -k gevent serve:app    ← breaks every MCP call you make

_one_at_a_time = threading.Lock()


@app.get("/health")
def health():
    """Is the server awake? A host pings something like this to find out."""
    return jsonify({"status": "ok"})


@app.post("/ask")
def ask():
    """
    Run the agent on one query.

    In:   {"query": "...", "wardrobe": {...}}   wardrobe optional — leave it
                                                out and you get the same
                                                example wardrobe the CLI uses.
    Out:  the session dict from run_agent(), as JSON.
    """
    started = time.perf_counter()
    request_id = request_log.new_request_id()

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    query = payload.get("query")
    query = query.strip() if isinstance(query, str) else ""
    if not query:
        # 400 rather than a stack trace: the caller can act on this one.
        request_log.record({
            "request_id": request_id, "route": "/ask", "status": 400,
            "outcome": "bad_request", "total_ms": _ms_since(started),
        })
        response = jsonify({"error": "Send JSON with a 'query' field, e.g. "
                                     '{"query": "vintage graphic tee under $30"}'})
        response.headers["X-Request-Id"] = request_id
        return response, 400

    wardrobe = payload.get("wardrobe")
    if not isinstance(wardrobe, dict):
        wardrobe = get_example_wardrobe()

    # A queued request should look like a queued request. Without this the
    # second caller just sits there, and "slow" and "waiting its turn" are
    # indistinguishable from the outside — which is how people conclude the
    # deployment is broken when it is behaving exactly as designed.
    #
    # This is NOT the logging you add in the follow-along. It prints nothing
    # on the normal path, carries no timing and counts nothing; it says only
    # that this request had to wait. `locked()` can be a moment out of date,
    # so the note is occasionally missed — which costs nothing, because
    # nothing depends on it.
    if _one_at_a_time.locked():
        print(
            "  [serve] another request is still running. This one is waiting "
            "its turn — serve.py handles one at a time, on purpose.",
            file=sys.stderr,
            flush=True,
        )

    failure = None
    session = None
    waited_from = time.perf_counter()
    with _one_at_a_time:
        queue_ms = _ms_since(waited_from)
        # Snapshot generate.py's running totals INSIDE the lock, so the delta
        # below belongs to this request and nobody else's.
        calls0, hits0 = generate.call_count(), generate._cache_hits
        tokens0 = generate.token_counts()
        paced0 = generate.pacing_wait_ms()
        agent_started = time.perf_counter()
        try:
            session = run_agent(query, wardrobe)
        except Exception as exc:  # noqa: BLE001 — a 500 with a sentence beats a hang
            failure = f"{type(exc).__name__}: {exc}"
        agent_ms = _ms_since(agent_started)
        calls1, hits1 = generate.call_count(), generate._cache_hits
        tokens1 = generate.token_counts()
        paced1 = generate.pacing_wait_ms()

    # Outside the lock: building a response and writing the log are not work
    # the next caller should be waiting on.
    status = 500 if failure is not None else 200
    item = (session or {}).get("selected_item") or {}
    request_log.record({
        "request_id": request_id,
        "route": "/ask",
        "status": status,
        "outcome": _outcome(session, failure),
        "query": query,
        "parsed": (session or {}).get("parsed"),
        "item_id": item.get("id"),
        "steps": (session or {}).get("steps"),
        "wardrobe_items": len(wardrobe.get("items") or []),
        "queue_ms": queue_ms,
        "agent_ms": agent_ms,
        "total_ms": _ms_since(started),
        "model_calls": calls1 - calls0,
        "cache_hits": hits1 - hits0,
        "prompt_tokens": tokens1["prompt"] - tokens0["prompt"],
        "output_tokens": tokens1["output"] - tokens0["output"],
        "model_calls_since_boot": calls1,
        "stage_ms": (session or {}).get("timings_ms"),
        "pacing_ms": round(paced1 - paced0, 1),
        "error": failure or (session or {}).get("error"),
    })

    response = jsonify({"error": failure} if failure is not None else session)
    response.headers["X-Request-Id"] = request_id
    response.headers["Server-Timing"] = (
        f"queue;dur={queue_ms}, agent;dur={agent_ms}"
    )
    return response, status


@app.get("/stats")
def stats():
    """Aggregates over the requests this instance remembers. Resets on sleep."""
    return jsonify(request_log.stats())


@app.get("/logs")
def logs():
    """
    The last N structured log lines (default 50, ?n= for more, up to 200).

    The point: on a free host the log disappears when the instance sleeps.
    This hands it back over HTTP so it can be committed while it still exists.
    Wardrobe contents are never logged, so nothing here is more private than
    the queries themselves.
    """
    try:
        n = max(1, min(int(request.args.get("n", 50)), request_log.LOG_MEMORY))
    except ValueError:
        n = 50
    return jsonify(request_log.recent(n))


# ── instrumentation helpers ───────────────────────────────────────────────────

def _ms_since(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


def _outcome(session: dict | None, failure: str | None) -> str:
    """The run's result in one countable word. Mirrors run_agent()'s exits."""
    if failure is not None:
        return "server_error"
    if not session.get("error"):
        return "complete"
    steps = session.get("steps") or []
    if "search_listings" not in steps:
        return "mcp_error"
    if not session.get("search_results"):
        return "no_match"
    return "model_unavailable"


if __name__ == "__main__":
    # PORT and 0.0.0.0 are not decoration. A host tells you which port to
    # listen on through PORT, and it reaches your process from outside the
    # container — bind 127.0.0.1 and nothing but the container itself can
    # connect, which looks exactly like a broken app from the browser.
    port = int(os.getenv("PORT", "5000"))

    # Never on by default. Flask's debugger executes code typed into a browser,
    # and a deployed app with it on is a stranger's shell. Set AI201_DEBUG=1 in
    # your own terminal when you want the reloader.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"\nFitFindr is listening on http://localhost:{port}")
    print("It runs one request at a time — a second one waits for the first.")
    print("Ask it something (single quotes, as always):\n")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"query\": \"vintage graphic tee under $30\"}}'\n"
    )
    print("Ctrl-C to stop.\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
