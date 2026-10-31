# 02 — Repository Baseline

Cycle: PR-EG-R6-R5. Recorded before the valid production baseline.

## Checkpoint

| Item | Value |
|---|---|
| Commit | `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9` |
| Subject | fix: create pytest temp parent on clean CI checkouts |
| Branch | `feature/product-realization` |
| Upstream | `origin/feature/product-realization` (status line shows the branch tracking that remote with no ahead/behind marker) |
| Working tree | 1765 dirty porcelain entries at baseline capture. This cycle does not commit them and does not rewrite history. |
| Author of HEAD | CrowBarInc |

Protected-replay CI is present in `.github/workflows/convergence-checks.yml`: `pytest -m golden_replay` and `python tools/refresh_protected_replay_manifest.py --check`.

Machine-readable copy: `artifacts/pr_eg_r6_r5/repository_baseline.json`.

## Provider

| Item | Value |
|---|---|
| Configured default model | `gpt-4.1-mini` |
| Model routing default | on (`ENABLE_MODEL_ROUTING`) |
| API key | present in the local environment; the value is not recorded (`api_key_recorded: false`) |
| Semantic plan temperature | existing production setting (0) |
| SDK retries | disabled for this measurement (`ASHEN_DISABLE_PROVIDER_RETRIES=1`) |

Returned model id on the valid baseline is recorded per call in `baseline.jsonl`. The pilot and the valid rerun both observed `gpt-4.1-mini-2025-04-14`.

## Routing used as the production baseline

| Flag | Production default | This cycle |
|---|---|---|
| `ASHEN_UNIFIED_SEMANTIC_PLANNING` | off | on |
| `ASHEN_HOST_CONSTRAINED_CANDIDATES` | off | off |
| Expression generation | on | on |
| Live interpretation | on | on, but skipped when the planner returns a decision |

The baseline is the current information path: the R6 semantic planner with expression left on. It is not the legacy flag-off path and not architectures B or C from PR-EG-R6-R4-R1. No production migration of those architectures is authorized.

## Existing owners

| Concern | Owner in code |
|---|---|
| Source resolution | `authorize_information_turn` scans `_topic_rows` for the grounded addressee. Model `candidate_source_ids` do not select evidence. |
| NPC knowledge and disclosure | `npc_source_permitted`. A source the host does not permit is `hidden` and is not ranked. |
| Referent storage | session `conversational_context` question referents in `game/conversational_referents.py`. Host-owned. Noncanonical. |
| Final response | `accepted_response` seal via `verify_delivery_record`. Delivered text is compared with history. |

## Regression status

This cycle's offline diagnostic test is `tests/test_pr_eg_r6_r5_diagnostic.py` (4 tests, passed before the provider run). The full suite was not run. The working tree already contained extensive unrelated changes, including the prior ATGB review state. Those are pre-existing. This cycle does not modify `game/`.

## Invalid first baseline

A first full-process attempt wrote `baseline_ledger_collision.jsonl`. The provider ledger refuses to reopen an existing file (`open(..., "x")` in `game/provider_budget.py`). After the two-turn pilot, the second process failed closed with `RuntimeError` and zero provider calls. Those rows are not the production baseline. The valid baseline uses a new ledger file per process and is `baseline.jsonl`.
