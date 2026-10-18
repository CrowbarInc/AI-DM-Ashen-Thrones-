# 28 Turn-Level Qualification

live_turns.jsonl records player input, expectations, locked plans, raw proposal where available, selected/authorized facts, API speech, sealed accepted response, delivered history, resolution, changed session keys, provider usage and latency. semantic_traces.jsonl preserves actual model input/output. Full campaign state remains in disposable state/ and is excluded from the portable bundle. Canonical equality checks use the predecessor selected-state projection, not a full arbitrary-state diff.
