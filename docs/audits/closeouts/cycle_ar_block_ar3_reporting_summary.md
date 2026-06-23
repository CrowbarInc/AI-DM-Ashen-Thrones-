# Cycle AR — Block AR3: Owner Drift Reporting Integration Summary

**Date:** 2026-06-06  
**Prerequisites:** [`cycle_ar_block_ar1_drift_taxonomy.md`](cycle_ar_block_ar1_drift_taxonomy.md), [`cycle_ar_block_ar2_implementation_summary.md`](cycle_ar_block_ar2_implementation_summary.md)

---

## Objective

Surface `owner_drift_bucket` classifications in replay diagnostic artifacts — reporting/display only, with no governance, assertion, or pass/fail changes.

---

## Files modified

| File | Change |
| --- | --- |
| `tests/helpers/replay_drift_taxonomy.py` | Added `summarize_owner_drift_buckets()` |
| `tests/helpers/failure_dashboard_report.py` | Owner drift column + breakdown/summary sections in protected report, dashboard, and rerun scorecard markdown |
| `docs/testing/protected_replay_manifest.md` | Cycle AR Reporting Addendum |
| `tests/test_replay_drift_taxonomy.py` | +5 rendering/aggregation tests |
| `tests/test_golden_replay.py` | Protected report + scorecard markdown assertions |

**Not modified:** `game/**`, replay assertions, classifier category/severity/routing, protected scenario count, CI gates.

---

## New report sections

### Protected Replay Failure Report

1. **Failure Table** — additive column `Owner Drift Bucket` (last column; existing columns unchanged in order).
2. **Owner Drift Breakdown** — dot-aligned rollup after Classification Summary:

```text
## Owner Drift Breakdown

```
speaker_drift .......... 1
```
```

### Failure Dashboard (`render_failure_dashboard_markdown`)

1. **Main table** — additive column `Owner Drift Bucket` (via `FAILURE_DASHBOARD_TABLE_COLUMNS`).
2. **Owner Drift Breakdown** — same rollup helper as protected report.

### Rerun Drift Scorecard Markdown

1. **Owner Drift Summary** — inserted after existing `## Summary` bullet list, before `## Semantic Delta Frequency`:

```markdown
## Owner Drift Summary

| Owner Drift Bucket | Count |
|---|---:|
| `speaker_drift` | `1` |
| `route_drift` | `1` |
```

Empty scorecards: `No owner drift classifications.`

---

## Shared helper

```python
summarize_owner_drift_buckets(classifications) -> dict[str, int]
```

- Input: any sequence of rows with `owner_drift_bucket` (failure classifications or `owner_drift_classifications`).
- Output: counts for all 9 `ALLOWED_OWNER_DRIFT_BUCKETS` (zeros included internally; renderers show non-zero only).
- Used by protected report breakdown, dashboard breakdown, and rerun scorecard summary — no duplicated counting logic.

---

## Sample output (protected failure)

```markdown
| Scenario | Test Node | Turn | ... | Investigate First | Owner Drift Bucket |
|---|---|---:|---|---|---|---|
| synthetic_protected_bridge | tests/... | 0 | ... | game/speaker_contract_enforcement.py | speaker_drift |

## Owner Drift Breakdown

```
speaker_drift .......... 1
```
```

## Sample output (rerun scorecard)

```markdown
## Summary

- Total turns compared: `1`
- Speaker deltas: `1`
...

## Owner Drift Summary

| Owner Drift Bucket | Count |
|---|---:|
| `speaker_drift` | `1` |
| `route_drift` | `1` |
| `replay_drift_unclassified` | `1` |

## Semantic Delta Frequency
...
```

---

## Test coverage added

| Test | Verifies |
| --- | --- |
| `test_summarize_owner_drift_buckets_counts_classifications` | Aggregation counts |
| `test_summarize_owner_drift_buckets_empty_input` | All buckets zero |
| `test_render_protected_replay_failure_report_includes_owner_drift_bucket` | Column + breakdown |
| `test_render_rerun_scorecard_includes_owner_drift_summary` | Summary table + `report_only` |
| `test_render_rerun_scorecard_empty_owner_drift_summary` | Empty handling |
| `test_protected_golden_assertion_failure_records_canonical_report` (extended) | End-to-end protected report |
| `test_rerun_drift_scorecard_markdown_summarizes_fabricated_scorecard` (extended) | Scorecard markdown |

**Regression:** 196 tests in scope — all green.

---

## Compatibility verification

| Check | Result |
| --- | --- |
| Measurement drift buckets unchanged | Pass |
| Category / severity / owner routing unchanged | Pass |
| Required classification fields unchanged | Pass |
| Rerun `report_only: true` | Pass |
| Rerun pass/fail logic | Pass — no comparator changes |
| Existing scorecard sections preserved | Pass — Owner Drift Summary inserted between Summary and Semantic Delta Frequency only |
| JSON scorecard payload | Pass — unchanged keys except existing AR2 `owner_drift_classifications` |

---

## Governance verification

| Constraint | Status |
| --- | --- |
| No replay expansion | Pass |
| No new protected scenarios | Pass |
| No runtime changes | Pass |
| No assertion changes | Pass |
| No acceptance blocking from owner drift | Pass — documented in manifest addendum |
| Owner drift does not replace category/owners | Pass — documented and preserved in reports |

---

## Acceptance

**PASS** — owner drift buckets visible in protected failure reports, failure dashboard, and rerun scorecard markdown; aggregation centralized; replay behavior and governance unchanged; tests green.
