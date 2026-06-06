# Cycle AR — Block AR2: Owner Drift Classification Implementation Summary

**Date:** 2026-06-06  
**Design input:** [`cycle_ar_block_ar1_drift_taxonomy.md`](cycle_ar_block_ar1_drift_taxonomy.md)

---

## Objective

Implement the AR1 owner-oriented replay drift taxonomy as an **additive reporting layer** on existing replay diagnostics — without changing protected replay behavior, measurement drift buckets, category logic, severity, or owner routing.

---

## Files changed

| File | Change |
| --- | --- |
| `tests/helpers/replay_drift_taxonomy.py` | **New.** `ALLOWED_OWNER_DRIFT_BUCKETS`, `classify_owner_drift_bucket`, `classify_rerun_delta_owner_drift_bucket`, `owner_drift_classifications_from_per_turn_deltas` |
| `tests/failure_classification_contract.py` | Re-export `ALLOWED_OWNER_DRIFT_BUCKETS`; add optional `owner_drift_bucket` to row allowlist |
| `tests/helpers/failure_classifier.py` | Emit `owner_drift_bucket` on every `classify_replay_failure` row; validate in `validate_failure_classification_row` |
| `tests/helpers/golden_replay.py` | `compare_golden_replay_reruns` returns `owner_drift_classifications` |
| `tests/helpers/failure_classification_sync.py` | Extension field count lock 15 → 16 |
| `tests/test_failure_classification_contract.py` | Extension field count assertion 15 → 16 |
| `tests/test_replay_drift_taxonomy.py` | **New.** Focused taxonomy + integration + rerun tests |

**Not modified:** `game/**`, protected replay scenarios, assertion helpers, measurement drift bucket assignment, `CATEGORY_RULES`, severity/investigate_first policy, CI workflow, protected replay manifest scenario/path counts.

---

## Bucket counts

| Surface | Count |
| --- | --- |
| `ALLOWED_OWNER_DRIFT_BUCKETS` | **9** |
| Single-run rows enriched | All `classify_replay_failure` outputs |
| Rerun delta keys classified | **7** (`speaker`, `route`, `fallback`, `runtime_lineage`, `response_delta`, `scaffold`, `text_fingerprint`) |

### Owner drift buckets

1. `route_drift`
2. `speaker_drift`
3. `fallback_drift`
4. `ownership_drift`
5. `emission_drift`
6. `semantic_drift`
7. `lineage_drift`
8. `projection_drift`
9. `replay_drift_unclassified`

---

## Test coverage added

**New module:** `tests/test_replay_drift_taxonomy.py` — **22** collected tests:

- Parametrized single-run bucket coverage (8 cases spanning all non-rerun buckets used in probes)
- Rerun delta bucket mapping (8 parametrized cases including fallback family vs owner-only split)
- `owner_drift_classifications_from_per_turn_deltas` unit test
- Classifier integration: `owner_drift_bucket` emitted + contract validation passes
- Classifier integration: `category`, `primary_owner`, `secondary_owner`, `severity`, `investigate_first` unchanged for speaker probe
- Rerun integration: `owner_drift_classifications` on multi-delta scorecard
- Rerun integration: empty classifications on identical runs; `report_only` preserved

**Regression suites run green:**

- `tests/test_replay_drift_taxonomy.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_golden_replay.py` (68 tests)

---

## Compatibility verification

| Check | Result |
| --- | --- |
| Measurement buckets unchanged (`exact_drift`, `structural_drift`, `semantic_drift`) | Pass — no edits to `classify_golden_drift` bucket assignment |
| `category` / `primary_owner` / `secondary_owner` / `investigate_first` logic | Pass — classifier routing untouched |
| Severity logic | Pass — no edits to `classify_failure_severity` |
| Required classification fields | Pass — `owner_drift_bucket` optional only |
| Existing replay tags | Pass — no tag additions |
| Rerun scorecard `report_only: true` | Pass — unchanged |
| Rerun pass/fail behavior | Pass — comparator still never raises |
| Contract TypedDict ↔ optional evidence alignment | Pass — sync locks updated for +1 extension field |
| Runtime code | Pass — zero `game/**` changes |

---

## Governance verification

| Constraint | Status |
| --- | --- |
| No replay expansion | Pass — no new scenarios or protected paths |
| No protected assertion changes | Pass |
| No acceptance criteria changes | Pass |
| No CI gate promotion | Pass — rerun classifications advisory only |
| Lineage excluded from protected drift | Pass — `lineage_drift` only via rerun delta adapter |
| AO5 runtime vs acceptance boundary | Pass — taxonomy module is replay-side only |

---

## Output shapes (additive)

### Classification row (new optional field)

```python
{
  # ... existing required/optional fields unchanged ...
  "owner_drift_bucket": "speaker_drift",
}
```

### Rerun scorecard (new key)

```python
{
  "schema_version": 1,
  "report_only": True,
  # ... existing summary / frequencies / per_turn_deltas unchanged ...
  "owner_drift_classifications": [
    {"turn_index": 0, "owner_drift_bucket": "speaker_drift", "delta_key": "speaker"},
  ],
}
```

---

## AR3 recommendation (concise)

1. **Reporting:** Add `owner_drift_bucket` column to `render_protected_replay_failure_report` and `render_rerun_drift_scorecard_markdown` (display-only).
2. **Manifest:** Cycle AR addendum in `docs/testing/protected_replay_manifest.md` documenting owner drift buckets as reporting vocabulary (no gate promotion).
3. **Optional:** Wire `classify_golden_drift` failure dashboard rows to surface bucket summary counts for operators.
4. **Defer:** Markdown-only consumers, longitudinal drift storage, collapsing `category` into owner buckets.
