# 18 — Matched Baseline Comparison

The same two harbor conversations, 15 turns each, were run through `/api/chat` with the gate off and then with the gate on. Initial NPC topics and player strings match. Provider sampling does not: both runs called `gpt-4.1-mini` live, temperature 0 for semantic plans, and the legacy run used the existing interpreter instead of the semantic planner.

Legacy relevance 24/30. Semantic relevance 28/30.
Legacy sufficiency 1/30. Semantic sufficiency 25/30.

The legacy ferry-manager question in the gap scene delivered the harbor-bell sentence. The semantic run's smoke and labeled path are scored from `live_turns.jsonl` against the same forbidden string.

Baseline status: `completed`. Baseline provider calls in that summary: 31.
