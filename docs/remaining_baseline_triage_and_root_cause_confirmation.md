# Remaining Baseline Triage and Root-Cause Confirmation

## Executive Summary

The 36 post-rationalization failures reduce to 25 root-cause clusters. Four failing tests are confirmed product defects, ten are confirmed architecture defects, three are validation defects, eight are stale expectations, one is a stale fixture, four are governance drift, four require a policy decision, and two remain unresolved. Counts describe failing tests, not independent repairs.

The confirmed repair queue contains eight root-cause repairs: three product clusters and five architecture clusters. The highest priority is the undefined social-resolution helper, followed by scene-grounding loss, attribution completeness, facade/stamping violations, and validation-layer separation. No product, architecture, validation, fixture, or governance repair was performed.

## Baseline

The JUnit-backed pre-triage run recorded 6,440 collected, 6,305 passed, 36 failed, and 99 skipped. All 36 node IDs match the post-rationalization portfolio. The prior 6,439 summary was a report-generation counting semantic; JUnit contains 6,440 test cases and is authoritative.

## Investigation Method

Each failure was deterministically reproduced, mapped to its current validation family, traced to the requirement named by the relevant current architecture or closeout document, and assigned to exactly one cluster. Classification separates production repairs, architecture repairs, validation cleanup, governance maintenance, policy choices, and unresolved investigation. The complete per-test evidence is in `artifacts/baseline_triage/failure_investigation_registry.json`.

## Confirmed Product Defects

- **RC-12:** two final-emission tests show that an aligned, resolved destination can lose scene grounding and emit the blank-scene fallback.
- **RC-16:** the protected assertion bridge fails to record the canonical recurrence event.
- **RC-17 (P0):** the failed NPC-pursuit social path calls undefined `_question_prompt_for_resolution`, producing `NameError` instead of a usable fallback.

## Confirmed Architecture Defects

- **RC-01:** one current mutation record is unresolved/misclassified, lowering attribution completeness to 83.93% and driving six failures.
- **RC-04:** production and test consumers bypass the reconciled final-emission metadata facade. The production bypass is the repair target; test imports belong to cleanup.
- **RC-15:** a projection alias declared retired remains exported.
- **RC-19:** two visibility fallback writes bypass required producer stamping.
- **RC-23:** narrative-authenticity code imports a final-emission repair surface across the current validation-layer boundary.

## Ownership and Import Findings

The quarantined six-test group is not one problem. The final-emission production facade bypass is a current architecture defect (RC-04). The attribution test helper and social integration test import obsolete/internal surfaces and are validation defects (RC-05 and RC-06). The social fan-in cap is a consequence of that test-only import. Ownership write-path parity is registry drift (RC-18), while the direct visibility writes are an implementation defect (RC-19). Weakening the boundaries would resurrect transitional architecture and is not recommended.

## Validation Defects and Stale Inputs

RC-05 and RC-06 should be corrected in test helpers, not production. Eight stale expectations lock historical percentages, exact expanded dictionaries, debt snapshots, projection bytes, protected-test counts, source labels, or transitional import shapes (RC-03, RC-07, RC-09, RC-14, RC-20, RC-22, RC-24, RC-25). RC-02 is a stale canonical session fixture whose setup no longer exercises the valid eligibility path.

## Governance Drift

RC-08 covers three mutually inconsistent evidence/classifier governance manifests. RC-18 is the ownership registry’s omission of 29 discovered production write paths. These are maintenance corrections after owner review, not evidence that production behavior should be changed merely to satisfy snapshots.

## Replay and Protected Replay Findings

Projection byte identity (RC-14) is obsolete because current projection rows intentionally include attribution fields. The deprecated alias (RC-15) is a real architecture residue. Long-session diagnostic instability (RC-13) remains unresolved until the first divergent turn is captured. Protected replay remains authoritative: its bridge omission (RC-16) is a defect, while the six-to-seven count lock (RC-20) is stale because the current manifest includes the CO102 case.

## Final-Emission and Playability Findings

Final emission contains two player-facing defects (RC-12 and RC-17), one facade defect (RC-04), one unresolved debug-ordering case (RC-11), one stale debt snapshot (RC-09), and one raw-token boundary decision (RC-10). The playability failure (RC-07) is an exact-dictionary assertion that predates new diagnostic fields; the authoritative exclusion behavior remains present, so production and evaluator policy should not change.

## Unresolved Cases and Human Decisions

RC-10 needs an owner decision on whether local raw-token access is restricted exclusively to opening-fallback evidence. RC-21 needs an explicit choice between NPC pending-lead authority and discoverable-clue state for destination redirects. RC-11 and RC-13 require additional non-semantic tracing before either side should change.

## Repair Queue

The machine-readable and readable queues are `confirmed_repair_queue.json` and `confirmed_repair_queue.md`. Sequence RC-17 first; then RC-12, RC-01, RC-04, RC-19, and RC-23; then the limited RC-15 and RC-16 repairs. Validate each cluster with its listed focused tests before another full suite.

## Validation Cleanup Queue

`validation_cleanup_queue.json` contains validation defects, stale expectations, the stale fixture, and governance work. These red tests should not drive production changes. Policy and unresolved cases are intentionally excluded from both implementation queues.

## Post-Investigation Baseline

The post run recorded 6,445 collected, 6,310 passed, 36 failed, and 99 skipped. The failure set and skip count are unchanged. The five-count increase consists solely of the five new passing triage-tooling tests.

## Commands Executed

```powershell
python -m pytest -q --tb=no --junitxml=artifacts/baseline_triage/pre_triage_suite.xml
python tools/build_baseline_triage.py
python -m pytest tests/test_remaining_baseline_triage.py -q
python -m pytest -q --tb=no --junitxml=artifacts/baseline_triage/post_triage_suite.xml
python tools/build_review_handoff.py --config data/validation/review_handoffs/remaining_baseline_triage.json
```

## Limitations

Repository authority is insufficient for RC-10 and RC-21. RC-11 and RC-13 need finer trace capture. Classification establishes repair direction but does not prove that each proposed repair is risk-free or that gameplay quality improved.

## Recommended Next Campaign

Review and approve the root-cause queue, then run a repair campaign scoped to confirmed P0/P1 product and architecture defects. Do not combine it with validation cleanup, Calibration Round 2, State-to-Narration Consistency, browser validation, or general Product Realization.
