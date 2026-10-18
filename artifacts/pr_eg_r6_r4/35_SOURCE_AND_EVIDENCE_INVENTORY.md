# 35 — Source and Evidence Inventory

`source_inventory.json` hashes this cycle's raw evidence, frozen labels, metrics and reports. `historical_inventory.json` lists the 56 inspected predecessor raw files and their hashes; `historical_raw_examples.jsonl` preserves complete selected rows with original path/line. The review bundle includes source code required to reproduce the experiment and relevant production boundaries, plus author fixture tools for historical verification.

Official: primary.jsonl, secondary.jsonl, supplemental_results.jsonl. Independent labels: development.json, validation.json, holdout.json, supplemental.json. Freeze manifests and adapter amendment record exact input lineage. Invalid_initial_attempts.jsonl is retained as excluded evidence. Baseline status and production_integrity.json document the dirty starting tree and unchanged game/data content. No credentials, .env or production session contents are intentionally packaged.
