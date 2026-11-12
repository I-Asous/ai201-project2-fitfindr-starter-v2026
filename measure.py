#!/usr/bin/env python3
"""
Measure a running FitFindr server from the outside. ← UNIT 9

    python measure.py --url https://fitfindr-xxxx.onrender.com --rounds 3
    python measure.py --url http://localhost:5000 --label local
    python measure.py --score results/deploy_hosted_*.json

What one session does, in order:

  1. GET /health once and time it. If the instance was asleep, THIS is the
     request that pays for waking it up — the server's own log can't see that
     time, because the server didn't exist yet. So it's measured here.
  2. POST /ask for each query in QUERIES, --rounds times over.
  3. GET /stats and GET /logs, so the server's own record comes back with it.
  4. Scores the session against criteria D1–D5 (criteria.md) and writes
     results/deploy_<label>_<timestamp>.md, plus a .json twin with the raw
     data so several sessions can be scored together with --score.

Commit both files the same session you make them. On a free host the server's
log is wiped when the instance sleeps; the files in the repo are the record
that lasts.

Standard library only — nothing to install to run it against a deployed app.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RESULTS = Path(__file__).parent / "results"

# (name, body). Each one exercises a different exit from run_agent().
QUERIES = [
    ("match", {"query": "vintage graphic tee under $30"}),
    ("match_size", {"query": "90s track jacket in size M"}),
    ("no_match", {"query": "designer ballgown size XXS under $5"}),
    ("empty_wardrobe", {"query": "vintage graphic tee under $30",
                        "wardrobe": {"items": []}}),
    ("bad_request", {"not_query": "oops"}),
]

# ── the targets from criteria.md, unit 9. Written before any hosted result. ──
COLD_HEALTH_MAX_MS = 60_000      # D1
WARM_P50_MAX_MS = 8_000          # D2
WARM_P95_MAX_MS = 75_000         # D2
PEAK_MEMORY_MAX_MB = 256         # D4
MEAN_TOKENS_PER_RUN_MAX = 1_000  # D5
# D5 was written after some sessions had already run (see criteria.md), so it
# is scored only on sessions that started after it existed.
D5_WRITTEN_AT = "2026-11-12T03:56:02+00:00"
EXPECTED_CALLS = {"complete": 2, "no_match": 0, "bad_request": 0}  # D5


# ── HTTP ─────────────────────────────────────────────────────────────────────

def call(method: str, url: str, body: dict | None = None, timeout: float = 360):
    """One HTTP call. Returns (status, parsed_json_or_text, client_ms, headers)."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, raw, headers = resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        status, raw, headers = exc.code, exc.read(), dict(exc.headers)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, f"{type(exc).__name__}: {exc}", _ms(t0), {}
    ms = _ms(t0)
    # HTTP/2 (Render, behind Cloudflare) sends header names in lowercase;
    # HTTP/1.1 locally keeps Flask's capitals. Lowercase them all so the
    # lookups below work either way.
    headers = {k.lower(): v for k, v in headers.items()}
    try:
        return status, json.loads(raw), ms, headers
    except ValueError:
        return status, raw.decode(errors="replace")[:300], ms, headers


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


def client_outcome(status, body) -> str:
    """
    The outcome as the CLIENT sees it — the same rules as serve._outcome(),
    applied to what came back over the wire. D3 compares this against the
    outcome the server logged.
    """
    if status is None:
        return "no_response"
    if status == 400:
        return "bad_request"
    if status >= 500 or not isinstance(body, dict):
        return "server_error"
    if not body.get("error"):
        return "complete"
    if "search_listings" not in (body.get("steps") or []):
        return "mcp_error"
    if not body.get("search_results"):
        return "no_match"
    return "model_unavailable"


# ── one session ──────────────────────────────────────────────────────────────

def run_session(base: str, rounds: int) -> dict:
    session_t0 = time.perf_counter()
    first_ask_elapsed_s = None
    print(f"GET {base}/health  (may take ~a minute if the instance is asleep)")
    status, body, ms, _ = call("GET", f"{base}/health", timeout=180)
    health = {"status": status, "client_ms": ms}
    print(f"  {status}  {ms:.0f} ms")

    asks = []
    for r in range(1, rounds + 1):
        for name, payload in QUERIES:
            status, body, ms, headers = call("POST", f"{base}/ask", payload)
            if first_ask_elapsed_s is None:
                # D1's cold proof: if the server's uptime at this request is
                # shorter than this, its process didn't exist when we started.
                first_ask_elapsed_s = round(time.perf_counter() - session_t0, 1)
            agent = None
            for part in headers.get("server-timing", "").split(","):
                if part.strip().startswith("agent;dur="):
                    agent = float(part.split("=")[1])
            outcome = client_outcome(status, body)
            item = (body.get("selected_item") or {}) if isinstance(body, dict) else {}
            detail = (f"fit card for {item.get('id')}" if outcome == "complete"
                      else str(body.get("error") if isinstance(body, dict) else body)[:70])
            asks.append({
                "round": r, "name": name, "status": status, "client_ms": ms,
                "server_agent_ms": agent, "client_outcome": outcome,
                "detail": detail, "request_id": headers.get("x-request-id"),
            })
            print(f"  [{r}] {name:<15} {status}  client {ms:>8.0f} ms   "
                  f"agent {agent if agent is not None else '-':>8} ms   {outcome}")

    _, stats, _, _ = call("GET", f"{base}/stats")
    _, logs, _, _ = call("GET", f"{base}/logs?n=200")
    return {
        "url": base,
        "rounds": rounds,
        "health": health,
        "first_ask_elapsed_s": first_ask_elapsed_s,
        "asks": asks,
        "stats": stats if isinstance(stats, dict) else {"unavailable": str(stats)},
        "logs": logs if isinstance(logs, list) else [],
    }


# ── scoring against criteria.md D1–D5 ────────────────────────────────────────

def _pct(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile, the same definition request_log.py uses."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(1, round(p / 100 * len(ordered))) - 1]


def _join(session: dict) -> list[tuple[dict, list[dict]]]:
    """Each /ask paired with every server log line carrying its request_id."""
    by_id: dict[str, list[dict]] = {}
    for line in session["logs"]:
        by_id.setdefault(line.get("request_id"), []).append(line)
    return [(a, by_id.get(a["request_id"], []) if a["request_id"] else [])
            for a in session["asks"]]


def score(sessions: list[dict]) -> list[dict]:
    """One result per criterion, over however many sessions are passed in."""
    results = []

    # D1 — cold start. Revised before any hosted result (see criteria.md D1):
    # a session counts as cold only when the server process is younger than
    # the session — its uptime at the first /ask is shorter than the time
    # since this session began. nth_since_boot == 1 alone can't tell a woken
    # instance from an awake one that simply hasn't served an /ask yet.
    cold_rows, d1_pass, not_cold = [], 0, 0
    for s in sessions:
        pairs = _join(s)
        first = pairs[0][1][0] if pairs and pairs[0][1] else {}
        uptime, elapsed = first.get("uptime_s"), s.get("first_ask_elapsed_s")
        cold = uptime is not None and elapsed is not None and uptime <= elapsed
        fast = (s["health"]["status"] == 200
                and s["health"]["client_ms"] <= COLD_HEALTH_MAX_MS)
        if not cold:
            not_cold += 1
            mark = "NOT COLD — doesn't count, re-run after 15 min idle"
        else:
            d1_pass += fast
            mark = "PASS" if fast else "FAIL"
        cold_rows.append(f"/health {s['health']['status']} in "
                         f"{s['health']['client_ms'] / 1000:.1f} s, server uptime "
                         f"{uptime} s at first /ask vs {elapsed} s since session "
                         f"start → {mark}")
    n_cold = len(sessions) - not_cold
    results.append({
        "id": "D1", "name": "cold start answers within 60 s",
        "measured": f"{d1_pass} of {n_cold} cold sessions"
                    + (f" ({not_cold} not cold)" if not_cold else ""),
        "verdict": ("FAIL" if d1_pass < n_cold
                    else "INCOMPLETE" if not_cold else "PASS"),
        "detail": cold_rows,
    })

    # D2 — warm full-run latency
    warm, any_5xx = [], 0
    for s in sessions:
        for ask, lines in _join(s):
            if ask["status"] is not None and ask["status"] >= 500:
                any_5xx += 1
            if ask["client_outcome"] != "complete" or not lines:
                continue
            if lines[0].get("nth_since_boot", 1) > 1:
                warm.append(ask["client_ms"])
    p50, p95 = _pct(warm, 50), _pct(warm, 95)
    d2_ok = (p50 is not None and p50 <= WARM_P50_MAX_MS
             and p95 <= WARM_P95_MAX_MS and any_5xx == 0)
    results.append({
        "id": "D2", "name": "warm full runs: p50 ≤ 8 s, p95 ≤ 75 s, no 5xx",
        "measured": (f"n={len(warm)}, p50={p50 / 1000:.1f} s, p95={p95 / 1000:.1f} s, "
                     f"5xx={any_5xx}") if warm else f"no warm full runs, 5xx={any_5xx}",
        "verdict": "PASS" if d2_ok else "FAIL",
        "detail": [f"warm full-run client ms, sorted: {sorted(warm)}"],
    })

    # D3 — exactly one truthful log line per request
    total, good, misses = 0, 0, []
    for s in sessions:
        for ask, lines in _join(s):
            total += 1
            if len(lines) != 1:
                misses.append(f"{ask['name']} r{ask['round']} {ask['request_id']}: "
                              f"{len(lines)} log lines")
            elif lines[0].get("outcome") != ask["client_outcome"]:
                misses.append(f"{ask['name']} r{ask['round']} {ask['request_id']}: "
                              f"logged {lines[0].get('outcome')!r}, client saw "
                              f"{ask['client_outcome']!r}")
            else:
                good += 1
    results.append({
        "id": "D3", "name": "one truthful log line per /ask",
        "measured": f"{good} of {total}",
        "verdict": "PASS" if total and good == total else "FAIL",
        "detail": misses or ["every request matched"],
    })

    # D4 — peak memory
    mem_rows, d4_pass = [], 0
    for s in sessions:
        peaks = [(l.get("peak_rss_mb") or 0) + (l.get("children_peak_rss_mb") or 0)
                 for _, lines in _join(s) for l in lines]
        peak = max(peaks) if peaks else None
        ok = peak is not None and peak <= PEAK_MEMORY_MAX_MB
        d4_pass += ok
        mem_rows.append(f"peak server + MCP child = {peak} MB → {'PASS' if ok else 'FAIL'}")
    results.append({
        "id": "D4", "name": "peak memory ≤ 256 MB",
        "measured": f"{d4_pass} of {len(sessions)} sessions",
        "verdict": "PASS" if d4_pass == len(sessions) else "FAIL",
        "detail": mem_rows,
    })
    # D5 — cost: tokens per full run and model calls per request
    eligible = [s for s in sessions
                if datetime.fromisoformat(s.get("started", "1970-01-01T00:00:00+00:00"))
                > datetime.fromisoformat(D5_WRITTEN_AT)]
    tokens, agent_ms, call_total, call_ok, call_misses = [], [], 0, 0, []
    for s in eligible:
        for ask, lines in _join(s):
            call_total += 1
            if len(lines) != 1:
                call_misses.append(f"{ask['name']} r{ask['round']}: no log line")
                continue
            line = lines[0]
            expected = EXPECTED_CALLS.get(ask["client_outcome"])
            if expected is not None and line.get("model_calls") == expected:
                call_ok += 1
            else:
                call_misses.append(f"{ask['name']} r{ask['round']}: "
                                   f"{line.get('model_calls')} calls, outcome "
                                   f"{ask['client_outcome']}")
            if ask["client_outcome"] == "complete":
                tokens.append((line.get("prompt_tokens") or 0)
                              + (line.get("output_tokens") or 0))
                if line.get("agent_ms") is not None:
                    agent_ms.append(line["agent_ms"])
    mean_tok = round(sum(tokens) / len(tokens), 1) if tokens else None
    d5_ok = (len(eligible) >= 1 and mean_tok is not None
             and mean_tok <= MEAN_TOKENS_PER_RUN_MAX and call_ok == call_total)
    results.append({
        "id": "D5", "name": "full run: mean ≤ 1,000 tokens; calls exactly 2 / 0",
        "measured": (f"{len(eligible)} eligible session(s); mean {mean_tok} tokens "
                     f"over {len(tokens)} full runs; calls as expected {call_ok} of "
                     f"{call_total}") if eligible
                    else "no sessions started after D5 was written",
        "verdict": ("INCOMPLETE" if not eligible else "PASS" if d5_ok else "FAIL"),
        "detail": ([f"tokens per full run: {sorted(tokens)}",
                    f"mean agent_ms per full run: "
                    f"{round(sum(agent_ms) / len(agent_ms)) if agent_ms else None}"]
                   + (call_misses or ["every request had the expected call count"]))
                  if eligible else [f"D5 counts sessions started after {D5_WRITTEN_AT}"],
    })
    return results


def _write_scores(f, results: list[dict]) -> None:
    f.write("| criterion | target | measured | verdict |\n|---|---|---|---|\n")
    for r in results:
        f.write(f"| {r['id']} | {r['name']} | {r['measured']} | **{r['verdict']}** |\n")
    f.write("\n")
    for r in results:
        f.write(f"- **{r['id']}**: " + "; ".join(r["detail"]) + "\n")
    f.write("\n")


# ── writing it down ──────────────────────────────────────────────────────────

def write_record(session: dict, label: str, started: datetime) -> Path:
    RESULTS.mkdir(exist_ok=True)
    stem = RESULTS / f"deploy_{label}_{started.strftime('%Y-%m-%d_%H%M%S')}"
    md, js = stem.with_suffix(".md"), stem.with_suffix(".json")

    session["label"], session["started"] = label, started.isoformat(timespec="seconds")
    js.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")

    with md.open("w", encoding="utf-8") as f:
        f.write(f"# Deploy run — {label}\n\n")
        f.write(f"- URL: {session['url']}\n- Started: {session['started']}\n")
        f.write(f"- Rounds: {session['rounds']}\n- Server commit: "
                f"{session['stats'].get('commit')}\n- Raw data: `{js.name}`\n\n")

        f.write("## Criteria D1–D5, this session alone\n\n")
        f.write("The criteria are defined over 3 sessions. Score them together with "
                "`python measure.py --score results/deploy_hosted_*.json`.\n\n")
        _write_scores(f, score([session]))

        f.write("## Client view\n\n")
        f.write(f"`GET /health` (wake-up): status {session['health']['status']}, "
                f"{session['health']['client_ms']} ms\n\n")
        f.write("`client_ms` is the full round trip seen from here, including network "
                "time. `server_agent_ms` is time inside `run_agent()`, from the "
                "`Server-Timing` header.\n\n")
        f.write("| round | request | status | client_ms | server_agent_ms | outcome | detail | request_id |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for a in session["asks"]:
            detail = str(a["detail"]).replace("|", "\\|")
            f.write(f"| {a['round']} | {a['name']} | {a['status']} | {a['client_ms']} | "
                    f"{a['server_agent_ms'] if a['server_agent_ms'] is not None else ''} | "
                    f"{a['client_outcome']} | {detail} | {a['request_id'] or ''} |\n")

        f.write("\n## Server `/stats`\n\n```json\n")
        f.write(json.dumps(session["stats"], indent=2, ensure_ascii=False))
        f.write("\n```\n\n## Server structured log (`/logs`)\n\nOne JSON object per "
                "request, as written by `request_log.py`.\n\n```jsonl\n")
        for line in session["logs"]:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
        f.write("```\n")
    return md


def score_files(paths: list[str]) -> int:
    sessions = [json.loads(Path(p).read_text(encoding="utf-8")) for p in paths]
    print(f"Scoring {len(sessions)} session(s) against criteria.md D1–D5:\n")
    for s in sessions:
        print(f"  {s.get('started')}  {s.get('url')}")
    print()
    results = score(sessions)
    for r in results:
        print(f"  {r['id']}  {r['verdict']:<4}  {r['measured']:<40}  {r['name']}")
        for d in r["detail"]:
            print(f"          {d}")
    print("\nPaste this into the README as text — or redirect it into a file "
          "and commit it.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", help="base URL, no trailing /ask")
    ap.add_argument("--rounds", type=int, default=3, help="times through QUERIES")
    ap.add_argument("--label", default="hosted")
    ap.add_argument("--score", nargs="+", metavar="JSON",
                    help="score saved sessions together instead of running one")
    args = ap.parse_args()

    if args.score:
        return score_files(args.score)
    if not args.url:
        ap.error("--url is required unless you pass --score")

    started = datetime.now(timezone.utc)
    session = run_session(args.url.rstrip("/"), args.rounds)
    out = write_record(session, args.label, started)

    print()
    for r in score([session]):
        print(f"  {r['id']}  {r['verdict']:<4}  {r['measured']}")
    print(f"\nWrote {out.relative_to(Path(__file__).parent)} and its .json — commit both now.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
