# PR-DE Benchmark Design

Harness: `tools/measure_pr_de_affordability.py`.

It reconstructs the PR-DD fixtures through `measure_pr_dd._social`, `_explore`, and `_messages_for`, then `build_messages`. It does not call a language model and does not write `data/session.json` or the other production saves.

## Boundary

The hash is SHA256 of the `build_messages` blob: system prompt, newline, user JSON. User JSON uses `ensure_ascii=False`. The later API rewrite with `ensure_ascii=True` is not this hash.

Token estimate is `ceil(chars/4)`. `tiktoken` is not installed, so exact token counts are null.

Run the harness with `PYTHONHASHSEED=0`. Notice-board clue digests use Python's `hash()`, which changes between processes unless the seed is pinned. The seed is a measurement setting. Gameplay code was not changed to freeze that digest.

## Storage

- `artifacts/affordability/baseline/pr_de.json` and `pr_de.csv` — pre-omission payloads
- `artifacts/affordability/post_change/pr_de.json` and `pr_de.csv` — after omission
- `artifacts/affordability/*/payloads/<fixture>.json` — user JSON for normalized comparison
- `artifacts/pr_de_contract_deduplication/PR-DE_prompt_measurements.csv` — paired before/after rows

Each fixture records id, class, player input, resolver, envelope, projection, bytes, characters, estimated tokens, exact tokens, SHA256, system bytes, policy bytes, instruction bytes, history bytes, speaker, authority outcome, source, and authored/synthetic designation.

## Rerun

```
$env:PYTHONHASHSEED = "0"
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe tools\measure_pr_de_affordability.py --phase post
```

`--phase baseline` records the current code. Use it only when the omission step is not active. The stored baseline in this cycle was captured with omission disabled, then post was captured with omission enabled. Both used seed 0.
