# Deploy run — hosted

- URL: https://fitfindr-ha9z.onrender.com
- Started: 2026-11-12T02:35:39+00:00
- Rounds: 3
- Server commit: 584bff4
- Raw data: `deploy_hosted_2026-11-12_023539.json`

## Criteria D1–D4, this session alone

The criteria are defined over 3 sessions. Score them together with `python measure.py --score results/deploy_hosted_*.json`.

| criterion | target | measured | verdict |
|---|---|---|---|
| D1 | cold start answers within 60 s | 0 of 0 cold sessions (1 not cold) | **INCOMPLETE** |
| D2 | warm full runs: p50 ≤ 8 s, p95 ≤ 75 s, no 5xx | no warm full runs, 5xx=0 | **FAIL** |
| D3 | one truthful log line per /ask | 0 of 15 | **FAIL** |
| D4 | peak memory ≤ 256 MB | 0 of 1 sessions | **FAIL** |

- **D1**: /health 200 in 0.4 s, server uptime None s at first /ask vs 16.6 s since session start → NOT COLD — doesn't count, re-run after 15 min idle
- **D2**: warm full-run client ms, sorted: []
- **D3**: match r1 None: 0 log lines; match_size r1 None: 0 log lines; no_match r1 None: 0 log lines; empty_wardrobe r1 None: 0 log lines; bad_request r1 None: 0 log lines; match r2 None: 0 log lines; match_size r2 None: 0 log lines; no_match r2 None: 0 log lines; empty_wardrobe r2 None: 0 log lines; bad_request r2 None: 0 log lines; match r3 None: 0 log lines; match_size r3 None: 0 log lines; no_match r3 None: 0 log lines; empty_wardrobe r3 None: 0 log lines; bad_request r3 None: 0 log lines
- **D4**: peak server + MCP child = None MB → FAIL

## Client view

`GET /health` (wake-up): status 200, 408.9 ms

`client_ms` is the full round trip seen from here, including network time. `server_agent_ms` is time inside `run_agent()`, from the `Server-Timing` header.

| round | request | status | client_ms | server_agent_ms | outcome | detail | request_id |
|---|---|---|---|---|---|---|---|
| 1 | match | 200 | 16195.2 |  | complete | fit card for lst_006 |  |
| 1 | match_size | 200 | 5570.2 |  | complete | fit card for lst_004 |  |
| 1 | no_match | 200 | 3925.1 |  | no_match | No listings matched 'designer ballgown' in size XXS under $5. Try drop |  |
| 1 | empty_wardrobe | 200 | 5709.8 |  | complete | fit card for lst_006 |  |
| 1 | bad_request | 400 | 171.3 |  | bad_request | Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee un |  |
| 2 | match | 200 | 6116.6 |  | complete | fit card for lst_006 |  |
| 2 | match_size | 200 | 5863.3 |  | complete | fit card for lst_004 |  |
| 2 | no_match | 200 | 3945.1 |  | no_match | No listings matched 'designer ballgown' in size XXS under $5. Try drop |  |
| 2 | empty_wardrobe | 200 | 5724.2 |  | complete | fit card for lst_006 |  |
| 2 | bad_request | 400 | 196.3 |  | bad_request | Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee un |  |
| 3 | match | 200 | 5419.4 |  | complete | fit card for lst_006 |  |
| 3 | match_size | 200 | 16599.1 |  | complete | fit card for lst_004 |  |
| 3 | no_match | 200 | 3751.0 |  | no_match | No listings matched 'designer ballgown' in size XXS under $5. Try drop |  |
| 3 | empty_wardrobe | 200 | 5853.1 |  | complete | fit card for lst_006 |  |
| 3 | bad_request | 400 | 161.7 |  | bad_request | Send JSON with a 'query' field, e.g. {"query": "vintage graphic tee un |  |

## Server `/stats`

```json
{
  "boot_id": "108522a1",
  "booted_at": "2026-11-12T02:35:19+00:00",
  "uptime_s": 105.5,
  "requests_seen": 15,
  "outcomes": {
    "complete": 9,
    "no_match": 3,
    "bad_request": 3
  },
  "status_codes": {
    "200": 12,
    "400": 3
  },
  "total_ms": {
    "p50": 5324.1,
    "p95": 15851.2,
    "max": 16423.7
  },
  "agent_ms": {
    "p50": 5324.0,
    "p95": 15850.5
  },
  "agent_ms_complete_runs": {
    "n": 9,
    "mean": 7869.6
  },
  "model_calls": 18,
  "cache_hits": 0,
  "tokens": {
    "prompt": 6091,
    "output": 1499
  },
  "session_budget": {
    "used": 18,
    "limit": 300
  },
  "peak_rss_mb": 98.4,
  "children_peak_rss_mb": 98.4,
  "commit": "584bff4"
}
```

## Server structured log (`/logs`)

One JSON object per request, as written by `request_log.py`.

```jsonl
{"ts": "2026-11-12T02:35:55.784+00:00", "request_id": "595cdc829a41", "boot_id": "108522a1", "nth_since_boot": 1, "uptime_s": 36.3, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 15850.5, "total_ms": 15851.2, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 778, "output_tokens": 182, "model_calls_since_boot": 2, "error": null, "peak_rss_mb": 98.3, "children_peak_rss_mb": 58.1}
{"ts": "2026-11-12T02:36:01.279+00:00", "request_id": "0485a9f20c72", "boot_id": "108522a1", "nth_since_boot": 2, "uptime_s": 41.8, "route": "/ask", "status": 200, "outcome": "complete", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "item_id": "lst_004", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 5308.3, "total_ms": 5308.6, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 763, "output_tokens": 172, "model_calls_since_boot": 4, "error": null, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.3}
{"ts": "2026-11-12T02:36:05.286+00:00", "request_id": "13c7c538eefc", "boot_id": "108522a1", "nth_since_boot": 3, "uptime_s": 45.8, "route": "/ask", "status": 200, "outcome": "no_match", "query": "designer ballgown size XXS under $5", "parsed": {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}, "item_id": null, "steps": ["parse_query", "search_listings"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 3748.7, "total_ms": 3749.0, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 4, "error": "No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.", "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:10.973+00:00", "request_id": "80f425c33384", "boot_id": "108522a1", "nth_since_boot": 4, "uptime_s": 51.5, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 0, "queue_ms": 0.0, "agent_ms": 5324.0, "total_ms": 5324.1, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 496, "output_tokens": 146, "model_calls_since_boot": 6, "error": null, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:11.172+00:00", "request_id": "103309a58eb2", "boot_id": "108522a1", "nth_since_boot": 5, "uptime_s": 51.7, "route": "/ask", "status": 400, "outcome": "bad_request", "total_ms": 0.1, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:17.285+00:00", "request_id": "141a33640d29", "boot_id": "108522a1", "nth_since_boot": 6, "uptime_s": 57.8, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 5941.2, "total_ms": 5941.5, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 770, "output_tokens": 188, "model_calls_since_boot": 8, "error": null, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:23.129+00:00", "request_id": "67ee0e1ef5e7", "boot_id": "108522a1", "nth_since_boot": 7, "uptime_s": 63.6, "route": "/ask", "status": 200, "outcome": "complete", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "item_id": "lst_004", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 5682.3, "total_ms": 5682.6, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 761, "output_tokens": 175, "model_calls_since_boot": 10, "error": null, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:27.092+00:00", "request_id": "fdc3736810af", "boot_id": "108522a1", "nth_since_boot": 8, "uptime_s": 67.6, "route": "/ask", "status": 200, "outcome": "no_match", "query": "designer ballgown size XXS under $5", "parsed": {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}, "item_id": null, "steps": ["parse_query", "search_listings"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 3785.3, "total_ms": 3785.6, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 10, "error": "No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.", "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:32.745+00:00", "request_id": "b59ea9638626", "boot_id": "108522a1", "nth_since_boot": 9, "uptime_s": 73.3, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 0, "queue_ms": 0.0, "agent_ms": 5502.0, "total_ms": 5502.1, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 510, "output_tokens": 151, "model_calls_since_boot": 12, "error": null, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:32.995+00:00", "request_id": "be9cfd2d56c9", "boot_id": "108522a1", "nth_since_boot": 10, "uptime_s": 73.5, "route": "/ask", "status": 400, "outcome": "bad_request", "total_ms": 0.1, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:38.435+00:00", "request_id": "ea5cbcc3ea82", "boot_id": "108522a1", "nth_since_boot": 11, "uptime_s": 78.9, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 5267.7, "total_ms": 5267.9, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 750, "output_tokens": 163, "model_calls_since_boot": 14, "error": null, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:55.015+00:00", "request_id": "b8694db1ebb8", "boot_id": "108522a1", "nth_since_boot": 12, "uptime_s": 95.5, "route": "/ask", "status": 200, "outcome": "complete", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "item_id": "lst_004", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 16423.5, "total_ms": 16423.7, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 744, "output_tokens": 157, "model_calls_since_boot": 16, "error": null, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:36:58.787+00:00", "request_id": "121ac52a584a", "boot_id": "108522a1", "nth_since_boot": 13, "uptime_s": 99.3, "route": "/ask", "status": 200, "outcome": "no_match", "query": "designer ballgown size XXS under $5", "parsed": {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}, "item_id": null, "steps": ["parse_query", "search_listings"], "wardrobe_items": 10, "queue_ms": 0.0, "agent_ms": 3560.8, "total_ms": 3561.0, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model_calls_since_boot": 16, "error": "No listings matched 'designer ballgown' in size XXS under $5. Try dropping the size (XXS), raising the $5 price ceiling, or using fewer or more general words, like 'jacket' or 'tee'.", "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:37:04.636+00:00", "request_id": "601df4ea02d0", "boot_id": "108522a1", "nth_since_boot": 14, "uptime_s": 105.2, "route": "/ask", "status": 200, "outcome": "complete", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "item_id": "lst_006", "steps": ["parse_query", "search_listings", "select_item", "suggest_outfit", "create_fit_card"], "wardrobe_items": 0, "queue_ms": 0.0, "agent_ms": 5526.9, "total_ms": 5527.1, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 519, "output_tokens": 165, "model_calls_since_boot": 18, "error": null, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
{"ts": "2026-11-12T02:37:04.804+00:00", "request_id": "b9cf22f04692", "boot_id": "108522a1", "nth_since_boot": 15, "uptime_s": 105.3, "route": "/ask", "status": 400, "outcome": "bad_request", "total_ms": 0.1, "peak_rss_mb": 98.4, "children_peak_rss_mb": 98.4}
```
