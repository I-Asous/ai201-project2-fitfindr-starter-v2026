#!/usr/bin/env python3
"""
Where the time goes in one run — the unit 9 latency breakdown (stretch).

    python latency.py results/deploy_latency_*.json

Reads sessions saved by measure.py and splits each request's time, end to end:

    client round trip (measure.py)
      └ network + Render's proxy        = client_ms − total_ms
      └ server, total_ms
          └ queue_ms                    waiting for serve.py's lock
          └ agent_ms = run_agent()
              └ parse_query
              └ search_listings
                  └ .mcp_startup        spawn mcp_server.py + handshake
                  └ .tool_call          the search itself
                  └ .mcp_teardown       shutting the subprocess down
              └ select_item
              └ suggest_outfit          model call 1 (incl. any pacing wait)
              └ create_fit_card         model call 2 (incl. any pacing wait)
          └ the rest of total_ms        Flask, JSON, logging

Every number comes from the deployed system's own log (stage_ms, pacing_ms)
plus the client's clock. Nothing is estimated. Standard library only.
"""

import json
import statistics
import sys
from pathlib import Path

ORDER = [
    ("network + proxy", None),
    ("queue (lock wait)", None),
    ("parse_query", "parse_query"),
    ("search_listings", "search_listings"),
    ("  ├ MCP startup (spawn + handshake)", "search_listings.mcp_startup"),
    ("  ├ tool call (the search)", "search_listings.tool_call"),
    ("  └ MCP teardown", "search_listings.mcp_teardown"),
    ("select_item", "select_item"),
    ("suggest_outfit (model call 1)", "suggest_outfit"),
    ("create_fit_card (model call 2)", "create_fit_card"),
    ("server overhead (Flask, JSON, log)", None),
]


def rows_for(sessions: list[dict], outcome: str) -> list[dict]:
    """One dict of component → ms per request with this outcome."""
    rows = []
    for s in sessions:
        by_id = {l.get("request_id"): l for l in s["logs"]}
        for ask in s["asks"]:
            line = by_id.get(ask["request_id"])
            if not line or line.get("outcome") != outcome or not line.get("stage_ms"):
                continue
            st = line["stage_ms"]
            top = sum(v for k, v in st.items() if "." not in k)
            row = dict(st)
            row["network + proxy"] = ask["client_ms"] - line["total_ms"]
            row["queue (lock wait)"] = line.get("queue_ms") or 0.0
            row["server overhead (Flask, JSON, log)"] = (
                line["total_ms"] - (line.get("queue_ms") or 0.0) - top)
            row["_client"] = ask["client_ms"]
            row["_pacing"] = line.get("pacing_ms") or 0.0
            row["_cold"] = line.get("nth_since_boot") == 1
            rows.append(row)
    return rows


def table(rows: list[dict], title: str) -> str:
    if not rows:
        return f"### {title}\n\n(no requests)\n"
    client = [r["_client"] for r in rows]
    mean_client = statistics.mean(client)
    out = [f"### {title} — n = {len(rows)}\n",
           "| component | mean ms | median ms | max ms | share of mean round trip |",
           "|---|---|---|---|---|"]
    for label, key in ORDER:
        key = key or label
        vals = [r.get(key, 0.0) for r in rows]
        if not any(vals) and key not in ("queue (lock wait)",):
            continue
        mean = statistics.mean(vals)
        share = "" if label.startswith("  ") else f"{mean / mean_client:.1%}"
        out.append(f"| {label} | {mean:,.1f} | {statistics.median(vals):,.1f} | "
                   f"{max(vals):,.1f} | {share} |")
    out.append(f"| **client round trip** | **{mean_client:,.1f}** | "
               f"{statistics.median(client):,.1f} | {max(client):,.1f} | 100% |")
    paced = [r["_pacing"] for r in rows]
    out.append(f"\nOf the model stages, time spent waiting on `generate.py`'s pacer "
               f"or backoff: mean {statistics.mean(paced):,.1f} ms, max {max(paced):,.1f} ms. "
               f"Cold-start requests included: {sum(r['_cold'] for r in rows)}.\n")
    return "\n".join(out)


def main() -> int:
    paths = sys.argv[1:]
    if not paths:
        print(__doc__)
        return 2
    sessions = [json.loads(Path(p).read_text(encoding="utf-8")) for p in paths]
    print(f"Latency breakdown over {len(sessions)} session(s): "
          + ", ".join(Path(p).name for p in paths) + "\n")
    print(table(rows_for(sessions, "complete"), "Full runs (`complete`)"))
    print(table(rows_for(sessions, "no_match"), "No-match runs (no model call)"))
    print(table(rows_for(sessions, "model_unavailable"), "Runs that hit a model 503"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
