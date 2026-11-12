"""
The structured request log for serve.py. ← UNIT 9, the instrumentation.

One JSON object per request, one line each, written to two places:

  • stdout — that's what Render's log viewer shows. It is also gone the moment
    the free instance sleeps, so it is the place you READ, not the place you
    keep.
  • logs/requests.jsonl — a file on the instance's disk. Survives as long as
    the instance does (on Render: until it sleeps or redeploys; on your machine:
    until you delete it).

The last LOG_MEMORY requests are also kept in memory, so `GET /logs` and
`GET /stats` can hand them back over HTTP before the instance goes to sleep.
`measure.py` pulls them into a committed file under results/ — that file is the
record that counts.

What goes in a line, and why each field is there:

  ts, request_id         when, and a handle to match a client's view to ours
  boot_id, nth_since_boot, uptime_s
                         which life of the instance served it. nth_since_boot
                         == 1 is the first request after a cold start
  route, status          what was asked and what HTTP said back
  outcome                complete | no_match | model_unavailable | mcp_error |
                         server_error | bad_request — the run's result in one
                         word, so you can count them without reading text
  query, parsed, item_id what was asked, how the parser read it, what it found
  steps                  the tools that actually ran, in order
  wardrobe_items         size of the wardrobe used (the contents are NOT logged)
  queue_ms               time spent waiting for the one-at-a-time lock
  agent_ms               time inside run_agent() — the agent's own work
  total_ms               the whole request as the server saw it
  model_calls, cache_hits, prompt_tokens, output_tokens
                         what THIS request spent (a delta, not a running total)
  model_calls_since_boot generate.py's session budget is per process, so on a
                         long-lived server this creeps toward
                         SESSION_REQUEST_BUDGET. Logging it says how close
  peak_rss_mb, children_peak_rss_mb
                         the server's and the MCP subprocesses' peak memory.
                         The free tier has 512 MB for all of it
  error                  session["error"] or the exception, shortened

What the server can NOT see: the time Render spends waking a sleeping instance
before this process even exists. Only the client sees that — which is why
measure.py records its own timing alongside this.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import threading
import time
import uuid
from collections import Counter, deque
from datetime import datetime, timezone

import config
import generate

LOG_DIR = config.ROOT / "logs"
LOG_PATH = LOG_DIR / "requests.jsonl"
LOG_MEMORY = 200

BOOT_ID = uuid.uuid4().hex[:8]
BOOT_TS = datetime.now(timezone.utc).isoformat(timespec="seconds")
_BOOT_MONO = time.monotonic()

_recent: deque[dict] = deque(maxlen=LOG_MEMORY)
_write_lock = threading.Lock()
_count = 0


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _peak_rss_mb() -> tuple[float | None, float | None]:
    """Peak resident memory of this process and of its finished children, in MB."""
    try:
        import resource
    except ImportError:  # Windows has no `resource`; memory just goes unlogged
        return None, None
    # ru_maxrss is kilobytes on Linux (Render) and bytes on macOS.
    scale = 1024 * 1024 if sys.platform == "darwin" else 1024
    me = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / scale
    kids = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / scale
    return round(me, 1), round(kids, 1)


def _short(text, limit: int = 300):
    if text is None:
        return None
    text = str(text).splitlines()[0] if str(text) else ""
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def record(entry: dict) -> dict:
    """
    Finish a log entry with the fields every line carries, then write it.

    Never raises. A request that already succeeded must not turn into a 500
    because the log file couldn't be written.
    """
    global _count
    with _write_lock:
        _count += 1
        nth = _count

    rss, kids = _peak_rss_mb()
    line = {
        "ts": _now(),
        "request_id": entry.pop("request_id", None) or new_request_id(),
        "boot_id": BOOT_ID,
        "nth_since_boot": nth,
        "uptime_s": round(time.monotonic() - _BOOT_MONO, 1),
        **entry,
        "peak_rss_mb": rss,
        "children_peak_rss_mb": kids,
    }
    if "error" in line:
        line["error"] = _short(line["error"])

    text = json.dumps(line, ensure_ascii=False, default=str)
    print(text, flush=True)

    with _write_lock:
        _recent.append(line)
        try:
            LOG_DIR.mkdir(exist_ok=True)
            with LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(text + "\n")
        except OSError as exc:
            print(f"  [log] couldn't write {LOG_PATH}: {exc}", file=sys.stderr, flush=True)
    return line


def recent(limit: int = LOG_MEMORY) -> list[dict]:
    with _write_lock:
        return list(_recent)[-limit:]


def _pct(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile. None when there is nothing to measure."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, round(p / 100 * len(ordered)))
    return round(ordered[rank - 1], 1)


def stats() -> dict:
    """Aggregates over the requests this instance still remembers."""
    lines = [l for l in recent() if l.get("route") == "/ask"]
    timed = [l for l in lines if l.get("status") == 200]
    total = [l["total_ms"] for l in timed if l.get("total_ms") is not None]
    agent = [l["agent_ms"] for l in timed if l.get("agent_ms") is not None]
    complete = [l["agent_ms"] for l in timed if l.get("outcome") == "complete"]

    return {
        "boot_id": BOOT_ID,
        "booted_at": BOOT_TS,
        "uptime_s": round(time.monotonic() - _BOOT_MONO, 1),
        "requests_seen": len(lines),
        "outcomes": dict(Counter(l.get("outcome") for l in lines)),
        "status_codes": dict(Counter(str(l.get("status")) for l in lines)),
        "total_ms": {"p50": _pct(total, 50), "p95": _pct(total, 95),
                     "max": max(total) if total else None},
        "agent_ms": {"p50": _pct(agent, 50), "p95": _pct(agent, 95)},
        "agent_ms_complete_runs": {
            "n": len(complete),
            "mean": round(statistics.mean(complete), 1) if complete else None,
        },
        "model_calls": sum(l.get("model_calls") or 0 for l in lines),
        "cache_hits": sum(l.get("cache_hits") or 0 for l in lines),
        "tokens": {
            "prompt": sum(l.get("prompt_tokens") or 0 for l in lines),
            "output": sum(l.get("output_tokens") or 0 for l in lines),
        },
        "session_budget": {
            "used": generate.call_count(),
            "limit": config.SESSION_REQUEST_BUDGET,
        },
        "peak_rss_mb": _peak_rss_mb()[0],
        "children_peak_rss_mb": _peak_rss_mb()[1],
        "commit": os.getenv("RENDER_GIT_COMMIT", "")[:7] or None,
    }
