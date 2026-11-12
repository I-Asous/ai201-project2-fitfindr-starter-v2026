# Deploy run — after

- URL: https://fitfindr-ha9z.onrender.com
- Started: 2026-11-12T17:54:54+00:00
- Rounds: 3
- Server commit: None
- Raw data: `deploy_after_2026-11-12_175454.json`

## Criteria D1–D5, this session alone

The criteria are defined over 3 sessions. Score them together with `python measure.py --score results/deploy_hosted_*.json`.

| criterion | target | measured | verdict |
|---|---|---|---|
| D1 | cold start answers within 60 s | 0 of 0 cold sessions (1 not cold) | **INCOMPLETE** |
| D2 | warm full runs: p50 ≤ 8 s, p95 ≤ 75 s, no 5xx | no warm full runs, 5xx=0 | **FAIL** |
| D3 | one truthful log line per /ask | 0 of 15 | **FAIL** |
| D4 | peak memory ≤ 256 MB | 0 of 1 sessions | **FAIL** |
| D5 | full run: mean ≤ 1,000 tokens; calls exactly 2 / 0 | 1 eligible session(s); mean None tokens over 0 full runs; calls as expected 0 of 15 | **FAIL** |

- **D1**: /health None in 0.0 s, server uptime None s at first /ask vs 0.0 s since session start → NOT COLD — doesn't count, re-run after 15 min idle
- **D2**: warm full-run client ms, sorted: []
- **D3**: match r1 None: 0 log lines; match_size r1 None: 0 log lines; no_match r1 None: 0 log lines; empty_wardrobe r1 None: 0 log lines; bad_request r1 None: 0 log lines; match r2 None: 0 log lines; match_size r2 None: 0 log lines; no_match r2 None: 0 log lines; empty_wardrobe r2 None: 0 log lines; bad_request r2 None: 0 log lines; match r3 None: 0 log lines; match_size r3 None: 0 log lines; no_match r3 None: 0 log lines; empty_wardrobe r3 None: 0 log lines; bad_request r3 None: 0 log lines
- **D4**: peak server + MCP child = None MB → FAIL
- **D5**: tokens per full run: []; mean agent_ms per full run: None; match r1: no log line; match_size r1: no log line; no_match r1: no log line; empty_wardrobe r1: no log line; bad_request r1: no log line; match r2: no log line; match_size r2: no log line; no_match r2: no log line; empty_wardrobe r2: no log line; bad_request r2: no log line; match r3: no log line; match_size r3: no log line; no_match r3: no log line; empty_wardrobe r3: no log line; bad_request r3: no log line

## Client view

`GET /health` (wake-up): status None, 15.9 ms

`client_ms` is the full round trip seen from here, including network time. `server_agent_ms` is time inside `run_agent()`, from the `Server-Timing` header.

| round | request | status | client_ms | server_agent_ms | outcome | detail | request_id |
|---|---|---|---|---|---|---|---|
| 1 | match | None | 0.9 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 1 | match_size | None | 0.8 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 1 | no_match | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 1 | empty_wardrobe | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 1 | bad_request | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 2 | match | None | 0.7 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 2 | match_size | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 2 | no_match | None | 0.7 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 2 | empty_wardrobe | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 2 | bad_request | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 3 | match | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 3 | match_size | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 3 | no_match | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 3 | empty_wardrobe | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |
| 3 | bad_request | None | 0.6 |  | no_response | URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known> |  |

## Server `/stats`

```json
{
  "unavailable": "URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>"
}
```

## Server structured log (`/logs`)

One JSON object per request, as written by `request_log.py`.

```jsonl
```
