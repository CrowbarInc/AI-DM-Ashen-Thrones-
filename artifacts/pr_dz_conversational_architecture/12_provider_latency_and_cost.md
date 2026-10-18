# Provider Latency and Cost

No live provider calls were made by PR-DZ.

Known orchestration costs:

- Live interpretation: one structured response call, no retry (`game/live_chat_interpretation.py:118`, `game/live_chat_interpretation.py:207`).
- Narration: one primary call through `game/gm.py:4997` when provider calls are enabled.
- Narration retry: targeted retries can occur; manual safety cap is six GPT calls per turn (`game/api.py:2269`, `game/api.py:3285`).
- Provider budget can suppress calls and return deterministic fallback (`game/gm.py:5037-5079`).

Telemetry: `artifacts/pr_dy_live_gameplay/raw_live_responses.json` records interpretation calls around 2.45s to 3.23s and 887-1029 total tokens in sampled turns. The current session log records the failed movement turn with one interpretation call and zero narration calls.

Target: use one orchestration pass for understanding and response decision. Only call narration after an executable/answerable decision needs natural prose. Deterministic clarification should not need narration.
