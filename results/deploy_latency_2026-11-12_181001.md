# Deploy run — latency

- URL: https://fitfindr-ha9z.onrender.com
- Started: 2026-11-12T18:10:01+00:00
- Rounds: 3
- Server commit: 9a0cf92
- Raw data: `deploy_latency_2026-11-12_181001.json`

## Criteria D1–D5, this session alone

The criteria are defined over 3 sessions. Score them together with `python measure.py --score results/deploy_hosted_*.json`.

| criterion | target | measured | verdict |
|---|---|---|---|
| D1 | cold start answers within 60 s | 0 of 0 cold sessions (1 not cold) | **INCOMPLETE** |
| D2 | warm full runs: p50 ≤ 8 s, p95 ≤ 75 s, no 5xx | n=4, p50=18.3 s, p95=31.4 s, 5xx=1 | **FAIL** |
| D3 | one truthful log line per /ask | 11 of 15 | **FAIL** |
| D4 | peak memory ≤ 256 MB | 1 of 1 sessions | **PASS** |
| D5 | full run: mean ≤ 1,000 tokens; calls exactly 2 / 0 | 1 eligible session(s); mean 863.8 tokens over 4 full runs; calls as expected 9 of 15 | **FAIL** |

- **D1**: /health 200 in 0.3 s, server uptime None s at first /ask vs 52.7 s since session start → NOT COLD — doesn't count, re-run after 15 min idle
- **D2**: warm full-run client ms, sorted: [10439.2, 18306.3, 19146.4, 31447.5]
- **D3**: match r1 91a84e5b5929: 0 log lines; match_size r1 8e1c8e19526f: 0 log lines; no_match r1 73512acc9079: 0 log lines; empty_wardrobe r1 None: 0 log lines
- **D4**: peak server + MCP child = 203.6 MB → PASS
- **D5**: tokens per full run: [675, 906, 913, 961]; mean agent_ms per full run: 19538; match r1: no log line; match_size r1: no log line; no_match r1: no log line; empty_wardrobe r1: no log line; match r2: 1 calls, outcome model_unavailable; empty_wardrobe r2: 1 calls, outcome model_unavailable

## Client view

`GET /health` (wake-up): status 200, 265.4 ms

`client_ms` is the full round trip seen from here, including network time. `server_agent_ms` is time inside `run_agent()`, from the `Server-Timing` header.

| round | request | status | client_ms | server_agent_ms | outcome | detail | request_id |
|---|---|---|---|---|---|---|---|
| 1 | match | 200 | 52413.0 | 52199.1 | complete | fit card for lst_006 | 91a84e5b5929 |
| 1 | match_size | 200 | 20859.6 | 20542.4 | complete | fit card for lst_004 | 8e1c8e19526f |
| 1 | no_match | 200 | 4256.8 | 4109.7 | no_match | No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'. | 73512acc9079 |
| 1 | empty_wardrobe | 502 | 2125.8 |  | server_error | <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-family: "Roobert";
  font-weight: 500;
  font-style: normal;
  font-stretch: normal;
  src: url("data:fo |  |
| 1 | bad_request | 400 | 173.1 |  | bad_request | Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee under $30"} | e5a9d84b3a37 |
| 2 | match | 200 | 24060.1 | 23854.6 | model_unavailable | Found Graphic Tee — 2003 Tour Bootleg Style ($24 on depop), but it couldn't be styled. Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'stat… Wait a minute and try again. | aaf0a7b0d941 |
| 2 | match_size | 200 | 31447.5 | 31264.3 | complete | fit card for lst_004 | c1012f3fc30d |
| 2 | no_match | 200 | 4967.2 | 3925.5 | no_match | No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'. | 558ae4a5790d |
| 2 | empty_wardrobe | 200 | 12410.7 | 12233.6 | model_unavailable | Found Graphic Tee — 2003 Tour Bootleg Style ($24 on depop), but it couldn't be styled. Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'stat… Wait a minute and try again. | 8ea3f2d0b532 |
| 2 | bad_request | 400 | 171.4 |  | bad_request | Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee under $30"} | 2d8fc099c8ee |
| 3 | match | 200 | 19146.4 | 18816.5 | complete | fit card for lst_006 | 7ea9a6badbc4 |
| 3 | match_size | 200 | 18306.3 | 17851.8 | complete | fit card for lst_004 | 8d1a0cbe62a2 |
| 3 | no_match | 200 | 4545.9 | 4184.2 | no_match | No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'. | 5b1f3541f30c |
| 3 | empty_wardrobe | 200 | 10439.2 | 10219.6 | complete | fit card for lst_006 | 8158452c9b53 |
| 3 | bad_request | 400 | 176.2 |  | bad_request | Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee under $30"} | 246751746a9a |

## Server `/stats`

```json
{
  "boot_id": "c3a28fa7",
  "booted_at": "2026-11-12T18:11:13+00:00",
  "uptime_s": 135.2,
  "requests_seen": 11,
  "outcomes": {
    "bad_request": 3,
    "model_unavailable": 2,
    "complete": 4,
    "no_match": 2
  },
  "status_codes": {
    "400": 3,
    "200": 8
  },
  "total_ms": {
    "p50": 12233.8,
    "p95": 31264.6,
    "max": 31264.6
  },
  "agent_ms": {
    "p50": 12233.6,
    "p95": 31264.3
  },
  "agent_ms_complete_runs": {
    "n": 4,
    "mean": 19538.0
  },
  "model_calls": 10,
  "cache_hits": 0,
  "tokens": {
    "prompt": 2791,
    "output": 664
  },
  "session_budget": {
    "used": 10,
    "limit": 300
  },
  "peak_rss_mb": 101.8,
  "children_peak_rss_mb": 101.8,
  "commit": "9a0cf92"
}
```

## Server structured log (`/logs`)

One JSON object per request, as written by `request_log.py`.

```jsonl
{"ts": "2026-11-12T18:11:21.856+00:00", "request_id": "e5a9d84b3a37", "boot_id": "c3a28fa7", "nth_since_boot": 1, "uptime_s": 8.7, "route": "/ask", "status": 400, "outcome": "bad_request", "total_ms": 0.4, "peak_rss_mb": 37.4, "children_peak_rss_mb": 0.0}
{"ts": "2026-11-12T18:11:45.861+00:00", "request_id": "aaf0a7b0d941", "boot_id": "c3a28fa7", "nth_since_boot": 2, "uptime_s": 32.7, "route": "/ask", "status": 200, "outcome": "model_unavailable", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 23854.6, "total_ms": 23855.1, "model_calls": 1, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 1, "stage_ms": {"parse_query": 0.2, "search_listings": 9788.8, "search_listings.mcp_startup": 3993.3, "search_listings.tool_call": 93.5, "search_listings.mcp_teardown": 5701.9, "select_item": 0.0, "suggest_outfit": 14065.3}, "pacing_ms": 0.0, "error": "Found Graphic Tee — 2003 Tour Bootleg Style ($24 on depop), but it couldn't be styled. Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'stat… Wait a minu…", "peak_rss_mb": 101.1, "children_peak_rss_mb": 62.6}
{"ts": "2026-11-12T18:12:17.360+00:00", "request_id": "c1012f3fc30d", "boot_id": "c3a28fa7", "nth_since_boot": 3, "uptime_s": 64.2, "route": "/ask", "status": 200, "outcome": "complete", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "item_id": "lst_004", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 31264.3, "total_ms": 31264.6, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 753, "output_tokens": 160, "model_calls_since_boot": 3, "stage_ms": {"parse_query": 0.0, "search_listings": 4800.9, "search_listings.mcp_startup": 3788.1, "search_listings.tool_call": 12.2, "search_listings.mcp_teardown": 1000.5, "select_item": 0.0, "suggest_outfit": 5427.9, "create_fit_card": 21035.3}, "pacing_ms": 0.0, "error": null, "peak_rss_mb": 101.5, "children_peak_rss_mb": 101.1}
{"ts": "2026-11-12T18:12:21.976+00:00", "request_id": "558ae4a5790d", "boot_id": "c3a28fa7", "nth_since_boot": 4, "uptime_s": 68.8, "route": "/ask", "status": 200, "outcome": "no_match", "query": "designer ballgown size XXS under $5", "parsed": {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}, "item_id": null, "steps": ["parse_query", "search_listings"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 3925.5, "total_ms": 3925.8, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 3, "stage_ms": {"parse_query": 0.0, "search_listings": 3925.4, "search_listings.mcp_startup": 3207.8, "search_listings.tool_call": 5.3, "search_listings.mcp_teardown": 712.3}, "pacing_ms": 0.0, "error": "No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.", "peak_rss_mb": 101.5, "children_peak_rss_mb": 101.5}
{"ts": "2026-11-12T18:12:34.738+00:00", "request_id": "8ea3f2d0b532", "boot_id": "c3a28fa7", "nth_since_boot": 5, "uptime_s": 81.6, "route": "/ask", "status": 200, "outcome": "model_unavailable", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item"], "wardrobe_items": 0, "queue_ms": 0.0, "agent_ms": 12233.6, "total_ms": 12233.8, "model_calls": 1, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 4, "stage_ms": {"parse_query": 0.0, "search_listings": 4090.2, "search_listings.mcp_startup": 3372.6, "search_listings.tool_call": 6.7, "search_listings.mcp_teardown": 710.9, "select_item": 0.0, "suggest_outfit": 8143.2}, "pacing_ms": 0.0, "error": "Found Graphic Tee — 2003 Tour Bootleg Style ($24 on depop), but it couldn't be styled. Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'stat… Wait a minu…", "peak_rss_mb": 101.6, "children_peak_rss_mb": 101.5}
{"ts": "2026-11-12T18:12:34.888+00:00", "request_id": "2d8fc099c8ee", "boot_id": "c3a28fa7", "nth_since_boot": 6, "uptime_s": 81.7, "route": "/ask", "status": 400, "outcome": "bad_request", "total_ms": 0.1, "peak_rss_mb": 101.6, "children_peak_rss_mb": 101.5}
{"ts": "2026-11-12T18:12:53.987+00:00", "request_id": "7ea9a6badbc4", "boot_id": "c3a28fa7", "nth_since_boot": 7, "uptime_s": 100.8, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 18816.5, "total_ms": 18816.8, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 772, "output_tokens": 189, "model_calls_since_boot": 6, "stage_ms": {"parse_query": 0.0, "search_listings": 3914.4, "search_listings.mcp_startup": 3210.6, "search_listings.tool_call": 5.6, "search_listings.mcp_teardown": 698.2, "select_item": 0.0, "suggest_outfit": 4735.4, "create_fit_card": 10166.5}, "pacing_ms": 0.0, "error": null, "peak_rss_mb": 101.6, "children_peak_rss_mb": 101.6}
{"ts": "2026-11-12T18:13:12.293+00:00", "request_id": "8d1a0cbe62a2", "boot_id": "c3a28fa7", "nth_since_boot": 8, "uptime_s": 119.1, "route": "/ask", "status": 200, "outcome": "complete", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "item_id": "lst_004", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 17851.8, "total_ms": 17852.2, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 751, "output_tokens": 155, "model_calls_since_boot": 8, "stage_ms": {"parse_query": 0.0, "search_listings": 4746.7, "search_listings.mcp_startup": 3937.4, "search_listings.tool_call": 6.9, "search_listings.mcp_teardown": 802.4, "select_item": 0.0, "suggest_outfit": 4802.1, "create_fit_card": 8302.7}, "pacing_ms": 0.0, "error": null, "peak_rss_mb": 101.6, "children_peak_rss_mb": 101.6}
{"ts": "2026-11-12T18:13:16.886+00:00", "request_id": "5b1f3541f30c", "boot_id": "c3a28fa7", "nth_since_boot": 9, "uptime_s": 123.7, "route": "/ask", "status": 200, "outcome": "no_match", "query": "designer ballgown size XXS under $5", "parsed": {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}, "item_id": null, "steps": ["parse_query", "search_listings"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 4184.2, "total_ms": 4184.5, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 8, "stage_ms": {"parse_query": 0.0, "search_listings": 4184.1, "search_listings.mcp_startup": 3476.0, "search_listings.tool_call": 5.4, "search_listings.mcp_teardown": 702.7}, "pacing_ms": 0.0, "error": "No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.", "peak_rss_mb": 101.8, "children_peak_rss_mb": 101.6}
{"ts": "2026-11-12T18:13:27.298+00:00", "request_id": "8158452c9b53", "boot_id": "c3a28fa7", "nth_since_boot": 10, "uptime_s": 134.1, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 0, "queue_ms": 0.0, "agent_ms": 10219.6, "total_ms": 10219.7, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 515, "output_tokens": 160, "model_calls_since_boot": 10, "stage_ms": {"parse_query": 0.0, "search_listings": 4607.4, "search_listings.mcp_startup": 3511.6, "search_listings.tool_call": 94.5, "search_listings.mcp_teardown": 1001.3, "select_item": 0.0, "suggest_outfit": 4942.0, "create_fit_card": 669.9}, "pacing_ms": 0.0, "error": null, "peak_rss_mb": 101.8, "children_peak_rss_mb": 101.8}
{"ts": "2026-11-12T18:13:27.518+00:00", "request_id": "246751746a9a", "boot_id": "c3a28fa7", "nth_since_boot": 11, "uptime_s": 134.3, "route": "/ask", "status": 400, "outcome": "bad_request", "total_ms": 0.1, "peak_rss_mb": 101.8, "children_peak_rss_mb": 101.8}
```
