# 37 — Source and Evidence Inventory

## Commands

```
python -m pytest tests/test_pr_eg_r6_r5_diagnostic.py -q
python -m experiments.pr_eg_r6_r5.run --phase baseline
python -m experiments.pr_eg_r6_r5.run --phase interventions --partitions validation
python -m experiments.pr_eg_r6_r5.run --phase expression --partitions validation
python -m experiments.pr_eg_r6_r5.analyze
python -m experiments.pr_eg_r6_r5.report
python tools/build_review_handoff.py --config artifacts/pr_eg_r6_r5/handoff_config.json
```

## Code

- `experiments/pr_eg_r6_r5/corpus.py` — frozen labels
- `experiments/pr_eg_r6_r5/gold.py` — diagnostic substitutions
- `experiments/pr_eg_r6_r5/score.py` — rubric and first-failure rules
- `experiments/pr_eg_r6_r5/run.py` — `/api/chat` baseline and arms
- `experiments/pr_eg_r6_r5/analyze.py` — paired summary
- `experiments/pr_eg_r6_r5/report.py` — these artifacts
- `tests/test_pr_eg_r6_r5_diagnostic.py` — offline security and rubric checks
- Production path read, not modified: `game/api.py`, `game/conversational_orchestration.py`, `game/unified_semantic_planning.py`, `game/conversational_referents.py`, `game/semantic_correspondence.py`, `game/semantic_operations.py`, `game/dialogue_authority.py`

## Measured files

| File | Role |
|---|---|
| `freeze.json` | Corpus hash and quotas |
| `frozen_corpus.json` | Full labels, including restricted fixture text. Local replay only. Excluded from the review zip. |
| `experiments/pr_eg_r6_r5/corpus.py` | Same restricted fixture sentences. Local replay only. Excluded from the review zip. |
| `repository_baseline.json` | Commit, branch, flags |
| `baseline.jsonl` | 164 production turns |
| `baseline_ledger_collision.jsonl` | Invalid ledger-reuse run. Not scored. |
| `interventions.jsonl` | 756 valid validation arm rows |
| `interventions_schema_rejected.jsonl` | First arm run. Not scored. |
| `expression_control.jsonl` | 54 I10C rows |
| `summary.json` | Rates, interactions, performance |
| `first_failures.json` | Per-turn first codes |
| `human_review_packet.json` | Pending review items |
| `snapshots/` | Pre-turn worlds. Contain fixture secrets. Excluded from the review zip. |

## Production surfaces used as evidence

- `authorize_information_turn` order: proposal, schema, bind, witness, addressee, topic scan, coverage, select, lock
- `npc_source_permitted` as the hidden-topic test
- `verify_delivery_record` as the seal test
- Provider ledger purposes and token counts

Hash: `871f124e7ddb452303a1a24d3fea76e5c62c9791e84c5718f64bf2f8bf8bc221`
Commit: `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`
