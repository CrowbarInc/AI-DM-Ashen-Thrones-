# BR2 — Attribution Completeness Regression Guard

Guard date: 2026-06-20

Scope: validation and reporting only. No runtime attribution behavior, replacement behavior, projection, or taxonomy changes.

Implementation: `tests/helpers/attribution_regression_guard.py`

Generator CLI: `tools/attribution_regression_guard_report.py`

Artifact: `artifacts/attribution_regression_guard_report.md`

Validation:

```powershell
pytest tests/test_attribution_regression_guard.py tests/test_attribution_completeness_metric.py tests/test_attribution_contract.py tests/test_replacement_attribution_inventory.py -q
python tools/attribution_regression_guard_report.py
python tools/attribution_regression_guard_report.py --strict-exit
```

Related: `docs/BR1_attribution_completeness_metric.md`, `tests/helpers/attribution_completeness_metric.py`

---

## 1. Purpose

BR2 prevents future repository changes from **silently degrading** attribution completeness, contract compliance, or taxonomy consistency.

BR1 established repeatable measurement. BR2 adds **guardrails** that fail fast when guarded metrics regress below recorded baselines or fixed thresholds.

---

## 2. Guarded Metrics

| Metric | Guard severity | Source |
|---|---|---|
| **Resolved completeness %** | Required | BR1 `overall.current.resolved_completeness_pct` |
| **Contract compliance %** | Required | BS3 `contract_integration.current.contract_compliance_score_pct` |
| **Taxonomy consistency %** | Required | BS3 `contract_integration.current.taxonomy_consistency_score_pct` |
| **Strict completeness %** | Informational | BR1 `overall.current.strict_completeness_pct` |

All required metrics are evaluated through `evaluate_attribution_regression_guard()`, which reuses `build_attribution_completeness_report()` from BR1.

---

## 3. Repository Thresholds

Initial thresholds (frozen in `BR2_GUARD_THRESHOLDS`):

| Metric | Threshold | Rule |
|---|---|---|
| Contract compliance | **100%** | Current value must be ≥ 100% |
| Taxonomy consistency | **100%** | Current value must be ≥ 100% |
| Resolved completeness | **32.65%** | Current value must be ≥ recorded BR2 baseline |
| Strict completeness | _none_ | Reported only; does not fail the guard |

Recorded baseline (`BR2_RECORDED_BASELINE`) captures the live corpus snapshot at BR2 establishment:

- Resolved completeness: 32.65% (16/49 records)
- Contract compliance: 100%
- Taxonomy consistency: 100%
- Strict completeness: 0% (informational)

When resolved completeness legitimately improves, update `BR2_RECORDED_BASELINE` and `BR2_GUARD_THRESHOLDS` in the same change that documents the improvement (see §6).

---

## 4. Acceptable Movement

### Required metrics — allowed

- **Increase** in resolved completeness, contract compliance, or taxonomy consistency
- **No change** when edits are documentation-only or do not touch attribution inventory inputs
- **Corpus fixture changes** that maintain or improve resolved completeness after updating the recorded baseline in the same PR

### Required metrics — not allowed without baseline update

- Any decrease in contract compliance below 100%
- Any decrease in taxonomy consistency below 100%
- Any decrease in resolved completeness below the recorded BR2 baseline (32.65%)

### Strict completeness — acceptable movement

Strict completeness may increase, decrease, or remain at 0% without failing BR2. Track it in the guard report for producer-stamp accountability (BS4), not as a hard gate.

---

## 5. Regression Definitions

A **regression** occurs when any required guard check fails:

1. **Completeness regression** — `resolved_completeness_pct < BR2_GUARD_THRESHOLDS.resolved_completeness_pct_min`
2. **Compliance regression** — `contract_compliance_score_pct < 100`
3. **Taxonomy regression** — `taxonomy_consistency_score_pct < 100`

The guard report lists each failed check under **Regression Warnings**. Tests in `tests/test_attribution_regression_guard.py` verify detection using synthetic degraded metrics without modifying runtime behavior.

Use `assert_attribution_metrics_not_regressed()` in CI or local validation with `--strict-exit` on the CLI tool.

---

## 6. Maintenance Expectations

### When to update the recorded baseline

Raise `BR2_RECORDED_BASELINE.resolved_completeness_pct` (and matching threshold) when:

- A BS4/BS5 cycle legitimately improves resolved completeness on the baseline corpus
- New baseline fixtures are added that increase complete records without removing previously complete coverage

Do **not** lower thresholds to absorb accidental regressions.

### When the guard should pass unchanged

- Runtime replacement behavior changes with no inventory impact
- Reporting-only edits to BR1/BR2 markdown or renderers
- Test refactors that preserve corpus completeness outcomes

### Periodic maintenance

1. Regenerate `artifacts/attribution_completeness_report.md` (BR1)
2. Regenerate `artifacts/attribution_regression_guard_report.md` (BR2)
3. Run the validation pytest suite
4. If resolved completeness improved, update `BR2_RECORDED_BASELINE` before merging

---

## 7. Future Maintainer Guidance

### When completeness falls

1. Regenerate the BR1 and BR2 artifacts to confirm the drop is real, not a generator bug.
2. Compare `artifacts/attribution_completeness_report.md` path and field coverage tables to locate the regression.
3. Check recent changes to:
   - `tests/helpers/replacement_attribution_inventory.py` (corpus builders)
   - `game/final_emission_replay_projection.py` (projection reads)
   - Producer stamp modules (`game/final_emission_meta.py`, path-specific FEM modules)
4. Restore completeness or revert the offending change.
5. Do not lower `BR2_GUARD_THRESHOLDS.resolved_completeness_pct_min` unless the baseline corpus was intentionally reduced and documented.

### When contract compliance falls

1. Inspect `artifacts/bs3_contract_compliance_report.md` layer audit for non-compliant field values.
2. Identify invalid tokens entering populated slots (normalization gaps, new repair kinds without contract registration).
3. Fix taxonomy validation failures in read-side inventory or add canonical tokens to `tests/helpers/attribution_contract.py` **only when** the new token is intentional and documented in BS3.
4. Contract compliance must return to **100%** before merge.

### When taxonomy consistency falls

1. Review structural union checks in `calculate_attribution_maturity_scores()`.
2. Look for divergent registries between `attribution_contract.py` and `failure_classification_contract.py`.
3. Restore registry alignment; taxonomy consistency must return to **100%** before merge.

### CLI usage

```powershell
# Write report; exit 0 even on failure (warnings to stderr)
python tools/attribution_regression_guard_report.py

# Write report; exit 1 on required guard failure
python tools/attribution_regression_guard_report.py --strict-exit
```

---

## 8. Integration with Existing Tooling

| Module | Role in BR2 |
|---|---|
| `tests/helpers/attribution_completeness_metric.py` | Supplies current metric payload via `build_attribution_completeness_report()` |
| `tests/helpers/attribution_contract.py` | Supplies contract compliance and taxonomy consistency via BR1 contract integration |
| `tests/helpers/replacement_attribution_inventory.py` | Supplies baseline corpus and completeness scoring (unchanged) |
| `tests/helpers/attribution_regression_guard.py` | Guard evaluation, assertions, report rendering |

BR2 adds no parallel scoring logic. It evaluates thresholds on top of the BR1 structured report.

---

## 9. Success Criteria

- Attribution metrics are guarded against silent regression
- Compliance, taxonomy, and completeness regressions are detectable in tests and artifacts
- No runtime behavior changes
- No attribution behavior changes
- No taxonomy changes
