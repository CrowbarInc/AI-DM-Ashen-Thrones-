# AR-BS - Split-Owner Count and Report Automation Implementation

## 1. Executive Summary

Package 5 was implemented by reducing duplicated manual split-owner report counts and routing report-facing summaries through executable data derived from the canonical split-owner acceptance matrix.

The package preserves the existing split-owner governance model. It does not change ownership semantics, acceptance matrix meaning, CI policy, replay behavior, provenance behavior, production runtime behavior, or generated audit artifacts.

The implementation introduces a single derived report summary helper for split-owner counts and updates script/test expectations to consume that helper instead of repeating literal report values.

## 2. Existing Maintenance Analysis

The split-owner acceptance matrix already uses an executable canonical source:

| Surface | Repository location | Existing role |
| --- | --- | --- |
| Canonical split-owner rows | `tests/helpers/failure_classification_split_owner.py` | Defines the authoritative acceptance matrix rows used by classifier, dashboard, lineage, FEM, and report checks. |
| Report rendering | `tests/helpers/failure_classification_split_owner.py` | Renders `docs/audits/BU15_split_owner_acceptance_matrix.md` from the executable matrix. |
| Refresh script | `scripts/refresh_split_owner_acceptance_matrix.py` | Writes the generated audit report. |
| Check script | `scripts/check_split_owner_acceptance_matrix.py` | Verifies the checked-in generated audit report is current. |
| Shared script operations | `scripts/split_owner_acceptance_matrix_ops.py` | Provides refresh/check helpers and count formatting. |

Manual duplication remained in report-facing count assertions and CLI count expectations. The report renderer, check output, and tests each encoded closely related summary facts separately. That made future matrix changes require updates in multiple places even though the counts are derivable from the canonical matrix and dashboard probe definitions.

The existing expected-count constants remain in place because they are governance locks. Removing those constants would weaken the current contract rather than merely reduce report maintenance.

## 3. Automation Overview

The implementation adds `split_owner_acceptance_matrix_report_summary()` to derive report summary values from the executable split-owner matrix and associated dashboard probe helpers.

The summary derives:

| Derived field | Source |
| --- | --- |
| `total_rows` | `SPLIT_OWNER_ACCEPTANCE_MATRIX` |
| `dashboard_covered_rows` | Matrix rows with `dashboard_case_id` |
| `fem_projection_rows` | Matrix rows not excluded from FEM projection |
| `legacy_only_rows` | Matrix rows marked legacy-only |
| `dashboard_probes` | `split_owner_matrix_controlled_failure_cases()` |
| `sealed_non_legacy_rows` | `split_owner_sealed_matrix_rows_requiring_dashboard_probe()` |
| `sealed_non_legacy_dashboard_rows` | Sealed non-legacy rows with dashboard coverage |

The report renderer now uses this summary for its visible count lines. The split-owner CLI count formatter can include the derived sealed parity count when provided. Tests that validate report and refresh output now derive their expected summary values from the same helper.

## 4. Canonical Source Mapping

| Reported value | Canonical executable source | Consumer after implementation |
| --- | --- | --- |
| Total split-owner rows | `SPLIT_OWNER_ACCEPTANCE_MATRIX` | Report renderer, count formatter tests, classifier report assertion |
| Dashboard-covered rows | `SPLIT_OWNER_ACCEPTANCE_MATRIX` row metadata | Count formatter tests |
| FEM projection rows | `split_owner_fem_projection_excluded()` over matrix rows | Count formatter tests |
| Legacy-only rows | `split_owner_matrix_legacy()` over matrix rows | Count formatter tests |
| Dashboard probes | `split_owner_matrix_controlled_failure_cases()` | Report renderer, classifier report assertion |
| Sealed non-legacy parity | `split_owner_sealed_matrix_rows_requiring_dashboard_probe()` | Report renderer, CLI count output, classifier report assertion |

Executable sources remain authoritative. Documentation and generated reports continue to be downstream views.

## 5. Repository Changes

| File | Change | Purpose |
| --- | --- | --- |
| `tests/helpers/failure_classification_split_owner.py` | Added `split_owner_acceptance_matrix_report_summary()` and routed report/count rendering through it. | Establish one derived source for report-facing split-owner summary counts. |
| `scripts/split_owner_acceptance_matrix_ops.py` | Extended count formatting to include sealed parity when available. | Preserve existing count structure while exposing a derived report summary value through script output. |
| `tests/test_failure_classifier.py` | Replaced literal report summary assertions with summary-derived assertions. | Remove duplicated manual report values from classifier report verification. |
| `tests/test_refresh_split_owner_acceptance_matrix.py` | Replaced hard-coded refresh count snippet values with summary-derived expectations. | Remove duplicated manual CLI/report count values from refresh verification. |
| `AR-BS_split_owner_count_report_automation_implementation.md` | Added this implementation closeout. | Provide package evidence and external review instructions. |

No production code, replay schemas, provenance behavior, governance policy, generated audit output, or runtime behavior was modified.

## 6. Verification Strategy

Verification focused on proving that counts are derived from canonical executable data and that existing split-owner governance behavior remains intact:

1. Run the split-owner acceptance matrix contract tests.
2. Run the split-owner refresh/check tests.
3. Run the checked-in split-owner matrix report verification script.
4. Run the classifier report alignment test that validates visible report summary prose.
5. Confirm the generated audit report was not modified.
6. Confirm production/runtime paths were not modified.
7. Inspect the diff to ensure only report automation and verification expectations changed.

## 7. Verification Results

| Verification | Result |
| --- | --- |
| `python -m pytest tests\test_split_owner_acceptance_matrix_contract.py tests\test_refresh_split_owner_acceptance_matrix.py -q -m split_owner_matrix_contract --basetemp=codex_pytest_tmp_bs1` | Passed: 22 tests. |
| `python scripts\check_split_owner_acceptance_matrix.py` | Passed: `split-owner acceptance matrix contract: OK (rows=16 dashboard=15 fem=15 legacy=1 sealed=6/6)`. |
| `python -m pytest tests\test_failure_classifier.py::test_cross_family_split_owner_acceptance_matrix_stays_aligned -q --basetemp=codex_pytest_tmp_bs2` | Passed: 1 test. |
| Generated audit report scope check | Passed: `docs/audits/BU15_split_owner_acceptance_matrix.md` was not modified. |
| Production/runtime scope check | Passed: no changes under `game`, `data`, `artifacts`, or `.github`. |

The bundled Python runtime was used for verification because `python` and `py` were not available on `PATH` in this environment.

## 8. Risks

| Risk | Assessment | Mitigation |
| --- | --- | --- |
| Governance lock weakening | Low. Expected-count constants were intentionally retained. | The implementation derives report-facing summaries without removing existing governance constants. |
| Report drift | Low. The checked-in audit report verification passes and the generated report file was not changed. | Keep `scripts/check_split_owner_acceptance_matrix.py` as the verification gate. |
| Consumer ambiguity | Low. Existing count keys remain available and sealed parity is additive. | `format_split_owner_matrix_counts()` only prints sealed parity when the summary keys exist. |
| Maintenance confusion | Low. Summary derivation is centralized in the split-owner helper module. | Future report assertions should consume `split_owner_acceptance_matrix_report_summary()`. |
| Scope creep into governance behavior | Low. No governance policy or CI enforcement files were changed. | Changes were limited to script support, test helper derivation, and tests. |

## 9. Package Closeout

Was split-owner report automation successfully implemented?

Yes. Report-facing split-owner counts now derive from `split_owner_acceptance_matrix_report_summary()`, which computes values from the canonical executable matrix and dashboard probe helpers.

Were duplicated maintenance points reduced?

Yes. Literal report values were removed from classifier report assertions and refresh count snippet expectations. The report renderer also consumes the derived summary rather than recomputing the same values inline.

Do executable sources remain authoritative?

Yes. The canonical matrix and executable helper functions remain the source of truth. Documentation and generated reports remain downstream outputs.

## 10. Campaign Assessment

Campaign 5 can continue after Package 5. The split-owner reporting surface now has reduced manual maintenance while preserving the existing acceptance matrix semantics and governance checks.

No additional Package 5 refinement is required before moving forward.

## 11. Recommended Next Cycle

Recommendation: Proceed to Package 6.

Repository evidence:

| Evidence | Result |
| --- | --- |
| Split-owner contract tests | Passing. |
| Split-owner report check script | Passing. |
| Classifier/report alignment test | Passing. |
| Generated audit report | Unchanged. |
| Production/runtime paths | Unchanged. |

## 12. Files Required for External Review

### Required

| File | Reason |
| --- | --- |
| `tests/helpers/failure_classification_split_owner.py` | Contains the derived report summary helper and report/count routing. |
| `scripts/split_owner_acceptance_matrix_ops.py` | Contains updated count formatter behavior. |
| `tests/test_failure_classifier.py` | Verifies report summary prose using derived counts. |
| `tests/test_refresh_split_owner_acceptance_matrix.py` | Verifies refresh/check output using derived counts. |
| `AR-BS_split_owner_count_report_automation_implementation.md` | Package implementation closeout. |

### Optional

| File | Reason |
| --- | --- |
| `scripts/check_split_owner_acceptance_matrix.py` | Existing verification entry point for checked-in report consistency. |
| `scripts/refresh_split_owner_acceptance_matrix.py` | Existing refresh entry point for the generated audit report. |
| `docs/audits/BU15_split_owner_acceptance_matrix.md` | Generated audit report confirmed unchanged by this package. |
| `tests/test_split_owner_acceptance_matrix_contract.py` | Contract test coverage proving matrix governance remains intact. |
