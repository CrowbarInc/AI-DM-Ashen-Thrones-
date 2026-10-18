# 04 — Historical Failure Inventory

Inspected 56 raw predecessor JSONL files across R6-R2, R2-R1, R2-R2, R3 and R3-R1. Preserved 30 full records in `historical_raw_examples.jsonl`, with original path/line and whole-file SHA-256 in `historical_inventory.json`. Counts are diagnostic records across overlapping runs, not independent failures.

- R2-R1 final/live_turns.jsonl:28: Oren is asked the north road name. Delivered source says Crown Way, but the source proposition leaves the requested subject blank. Earliest E03 (lost answer argument), downstream E08 (complete sentence classified partial).
- R3-R1 fresh/live_turns.jsonl:1: Cala/Brin/cistern source contains the cracked message. Both question and source use requested_role=value, and source omits message content. Earliest E03 on the source, with E01 role-vocabulary ambiguity also possible; downstream E08. Structurally accepted JSON is semantically incomplete.
- R3-R1 fresh/live_turns.jsonl:2: reverse_must_be_empty is an operation failure before correspondence. E01; exclude it from correspondence performance claims.
- R2-R1 baseline/live_turns.jsonl:1: amber reliquary is UNKNOWN; visible authored topics do not include amber. This is not automatically an evidence-recovery failure. Treating every UNKNOWN as a failure is E17.
- R2 matched_r2/live_turns.jsonl:10 and R3-R1 fresh:43 refuse restricted material. These are boundary successes, not answer failures.

The automatic `earliest_causal_hypothesis` is triage only. It does not establish an error from the selected source alone. Raw selected rows and author fixture definitions are included for external review; do not sum hypotheses as proven failures.
