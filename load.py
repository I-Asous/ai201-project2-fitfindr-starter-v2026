#!/usr/bin/env python3
"""
Load observation — ten times the normal rate (unit 9 stretch).

    python load.py --url https://fitfindr-ha9z.onrender.com

"Normal" for this system is one client with one request in flight
(measure.py). This sends from --clients clients AT ONCE (default 10), each
making --per-client requests one after another (default 3: match, no-match,
match). Meanwhile a probe hits /health every --probe seconds, so we can see
whether the server still answers its health check under load.

It records the client's view of every request, matches it to the server's
log line by X-Request-Id (queue_ms, agent_ms, stage_ms), checks whether the
instance restarted (boot_id before vs after), and writes
results/load_<timestamp>.md plus a .json twin.

Standard library only.
"""

import argparse
import json
import statistics
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from measure import call, client_outcome

RESULTS = Path(__file__).parent / "results"
PLAN = [
    ("match", {"query": "vintage graphic tee under $30"}),
    ("no_match", {"query": "designer ballgown size XXS under $5"}),
    ("match_size", {"query": "90s track jacket in size M"}),
]


def pct(values, p):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(1, round(p / 100 * len(ordered))) - 1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--url", required=True)
    ap.add_argument("--clients", type=int, default=10)
    ap.add_argument("--per-client", type=int, default=3)
    ap.add_argument("--probe", type=float, default=2.0, help="seconds between /health probes")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    started = datetime.now(timezone.utc)

    # Warm it up first: this is a load test, not a cold-start test.
    status, _, ms, _ = call("GET", f"{base}/health", timeout=180)
    print(f"warm-up /health: {status} in {ms:.0f} ms")
    _, before, _, _ = call("GET", f"{base}/stats")
    boot_before = before.get("boot_id") if isinstance(before, dict) else None

    t0 = time.perf_counter()
    asks: list[dict] = []
    probes: list[dict] = []
    lock = threading.Lock()
    stop = threading.Event()
    gate = threading.Barrier(args.clients)

    def probe():
        while not stop.is_set():
            at = time.perf_counter() - t0
            st, _, pms, _ = call("GET", f"{base}/health", timeout=60)
            with lock:
                probes.append({"at_s": round(at, 1), "status": st, "ms": pms})
            stop.wait(args.probe)

    def client(n: int):
        gate.wait()  # all clients start together
        for i in range(args.per_client):
            name, body = PLAN[i % len(PLAN)]
            sent = time.perf_counter() - t0
            st, resp, cms, headers = call("POST", f"{base}/ask", body, timeout=900)
            with lock:
                asks.append({
                    "client": n, "seq": i + 1, "name": name, "status": st,
                    "sent_s": round(sent, 1), "client_ms": cms,
                    "client_outcome": client_outcome(st, resp),
                    "request_id": headers.get("x-request-id"),
                    "error": (resp.get("error") if isinstance(resp, dict) else str(resp))
                             if client_outcome(st, resp) != "complete" else None,
                })
            print(f"  client {n:>2} #{i + 1} {name:<10} {st}  {cms / 1000:6.1f} s  "
                  f"{client_outcome(st, resp)}", flush=True)

    prober = threading.Thread(target=probe, daemon=True)
    prober.start()
    threads = [threading.Thread(target=client, args=(n,)) for n in range(1, args.clients + 1)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    stop.set()
    prober.join(timeout=70)
    wall_s = time.perf_counter() - t0

    _, after, _, _ = call("GET", f"{base}/stats")
    _, logs, _, _ = call("GET", f"{base}/logs?n=200")
    logs = logs if isinstance(logs, list) else []
    boot_after = after.get("boot_id") if isinstance(after, dict) else None
    by_id = {l.get("request_id"): l for l in logs}
    for a in asks:
        line = by_id.get(a["request_id"]) or {}
        a["queue_ms"] = line.get("queue_ms")
        a["agent_ms"] = line.get("agent_ms")
        a["logged"] = bool(line)

    # ── summary ──
    full = [a for a in asks if a["client_outcome"] == "complete"]
    client_ms = [a["client_ms"] for a in asks if a["status"] == 200]
    queue = [a["queue_ms"] for a in asks if a["queue_ms"] is not None]
    probe_ms = [p["ms"] for p in probes]
    summary = {
        "clients": args.clients, "per_client": args.per_client,
        "requests": len(asks), "wall_s": round(wall_s, 1),
        "outcomes": {o: sum(1 for a in asks if a["client_outcome"] == o)
                     for o in sorted({a["client_outcome"] for a in asks})},
        "5xx_or_no_response": sum(1 for a in asks if a["status"] is None or a["status"] >= 500),
        "full_runs_per_min": round(len(full) / (wall_s / 60), 2),
        "client_ms": {"p50": pct(client_ms, 50), "p95": pct(client_ms, 95),
                      "max": max(client_ms) if client_ms else None},
        "queue_ms": {"p50": pct(queue, 50), "max": max(queue) if queue else None},
        "health_probe_ms": {"n": len(probe_ms), "p50": pct(probe_ms, 50),
                            "max": max(probe_ms) if probe_ms else None,
                            "over_5s": sum(1 for m in probe_ms if m > 5000),
                            "non_200": sum(1 for p in probes if p["status"] != 200)},
        "logged": f"{sum(a['logged'] for a in asks)} of {len(asks)}",
        "restarted": boot_before != boot_after,
        "boot_id": {"before": boot_before, "after": boot_after},
        "peak_rss_mb": after.get("peak_rss_mb") if isinstance(after, dict) else None,
        "children_peak_rss_mb": after.get("children_peak_rss_mb") if isinstance(after, dict) else None,
        "model_calls": after.get("model_calls") if isinstance(after, dict) else None,
    }

    RESULTS.mkdir(exist_ok=True)
    stem = RESULTS / f"load_{started.strftime('%Y-%m-%d_%H%M%S')}"
    record = {"url": base, "started": started.isoformat(timespec="seconds"),
              "summary": summary, "asks": asks, "probes": probes,
              "stats_before": before, "stats_after": after, "logs": logs}
    stem.with_suffix(".json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
    with stem.with_suffix(".md").open("w", encoding="utf-8") as f:
        f.write(f"# Load observation — {args.clients} clients × {args.per_client}\n\n")
        f.write(f"- URL: {base}\n- Started: {record['started']}\n- Raw data: `{stem.name}.json`\n\n")
        f.write("## Summary\n\n```json\n" + json.dumps(summary, indent=2) + "\n```\n\n")
        f.write("## Requests, in order sent\n\n| client | # | request | sent at s | status | "
                "client s | queue s | agent s | outcome | logged |\n|---|---|---|---|---|---|---|---|---|---|\n")
        for a in sorted(asks, key=lambda a: a["sent_s"]):
            q = f"{a['queue_ms'] / 1000:.1f}" if a["queue_ms"] is not None else ""
            g = f"{a['agent_ms'] / 1000:.1f}" if a["agent_ms"] is not None else ""
            f.write(f"| {a['client']} | {a['seq']} | {a['name']} | {a['sent_s']} | {a['status']} | "
                    f"{a['client_ms'] / 1000:.1f} | {q} | {g} | {a['client_outcome']} | {a['logged']} |\n")
        f.write("\n## /health probes during the load\n\n| at s | status | ms |\n|---|---|---|\n")
        for p in probes:
            f.write(f"| {p['at_s']} | {p['status']} | {p['ms']} |\n")
        f.write("\n## Server log lines (`/logs`)\n\n```jsonl\n")
        for line in logs:
            if line.get("request_id") in {a["request_id"] for a in asks}:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
        f.write("```\n")

    print("\n" + json.dumps(summary, indent=2))
    print(f"\nWrote {stem.with_suffix('.md').relative_to(Path(__file__).parent)} and its .json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
