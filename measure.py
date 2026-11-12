#!/usr/bin/env python3
"""
Measure a running FitFindr server from the outside. ← UNIT 9

    python measure.py --url https://fitfindr-xxxx.onrender.com
    python measure.py --url http://localhost:5000 --label local

What it does, in order:

  1. GET /health once and time it. If the instance was asleep, THIS is the
     request that pays for waking it up — the server's own log can't see that
     time, because the server didn't exist yet. So it's measured here.
  2. POST /ask for each query in QUERIES (a matching one, an impossible one,
     an empty-wardrobe one, and a bad request), --rounds times over.
  3. GET /stats and GET /logs, so the server's own record comes back with it.
  4. Writes all of it to results/deploy_<label>_<timestamp>.md.

Commit that file the same session you make it. On a free host the server's
log is wiped when the instance sleeps; the file in the repo is the record that
lasts.

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
        return None, f"{type(exc).__name__}: {exc}", round((time.perf_counter() - t0) * 1000, 1), {}
    ms = round((time.perf_counter() - t0) * 1000, 1)
    try:
        return status, json.loads(raw), ms, headers
    except ValueError:
        return status, raw.decode(errors="replace")[:300], ms, headers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", required=True, help="base URL, no trailing /ask")
    ap.add_argument("--rounds", type=int, default=1, help="times through QUERIES")
    ap.add_argument("--label", default="hosted")
    args = ap.parse_args()
    base = args.url.rstrip("/")

    started = datetime.now(timezone.utc)
    rows = []

    print(f"GET {base}/health  (may take ~a minute if the instance is asleep)")
    status, body, ms, _ = call("GET", f"{base}/health", timeout=180)
    rows.append({"round": 0, "name": "health (wake)", "status": status, "client_ms": ms,
                 "server_total_ms": None, "outcome": body.get("status") if isinstance(body, dict) else body,
                 "request_id": None})
    print(f"  {status}  {ms:.0f} ms")

    for r in range(1, args.rounds + 1):
        for name, payload in QUERIES:
            status, body, ms, headers = call("POST", f"{base}/ask", payload)
            rid = headers.get("X-Request-Id")
            timing = headers.get("Server-Timing", "")
            agent = None
            for part in timing.split(","):
                if part.strip().startswith("agent;dur="):
                    agent = float(part.split("=")[1])
            if isinstance(body, dict):
                if body.get("error"):
                    outcome = "error: " + str(body["error"])[:70]
                else:
                    item = body.get("selected_item") or {}
                    outcome = f"fit card for {item.get('id')}"
            else:
                outcome = str(body)[:80]
            rows.append({"round": r, "name": name, "status": status, "client_ms": ms,
                         "server_agent_ms": agent, "outcome": outcome, "request_id": rid})
            print(f"  [{r}] {name:<15} {status}  client {ms:>8.0f} ms   agent {agent or '-':>8} ms   {outcome}")

    _, stats, _, _ = call("GET", f"{base}/stats")
    _, logs, _, _ = call("GET", f"{base}/logs?n=200")

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"deploy_{args.label}_{started.strftime('%Y-%m-%d_%H%M')}.md"
    with out.open("w", encoding="utf-8") as f:
        f.write(f"# Deploy run — {args.label}\n\n")
        f.write(f"- URL: {base}\n- Started: {started.isoformat(timespec='seconds')}\n")
        f.write(f"- Rounds: {args.rounds}\n- Python: {sys.version.split()[0]} (client)\n\n")
        f.write("## Client view\n\n")
        f.write("`client_ms` is the full round trip seen from here, including any wake-up "
                "and network time. `server_agent_ms` is time inside `run_agent()` from the "
                "`Server-Timing` header.\n\n")
        f.write("| round | request | status | client_ms | server_agent_ms | outcome | request_id |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for row in rows:
            f.write(f"| {row['round']} | {row['name']} | {row['status']} | {row['client_ms']} | "
                    f"{row.get('server_agent_ms') or ''} | {row['outcome']} | {row['request_id'] or ''} |\n")
        f.write("\n## Server `/stats`\n\n```json\n")
        f.write(json.dumps(stats, indent=2, ensure_ascii=False) if not isinstance(stats, str) else stats)
        f.write("\n```\n\n## Server structured log (`/logs`)\n\nOne JSON object per request, "
                "as written by `request_log.py`.\n\n```jsonl\n")
        if isinstance(logs, list):
            for line in logs:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
        else:
            f.write(str(logs) + "\n")
        f.write("```\n")

    print(f"\nWrote {out.relative_to(Path(__file__).parent)} — commit it now.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
