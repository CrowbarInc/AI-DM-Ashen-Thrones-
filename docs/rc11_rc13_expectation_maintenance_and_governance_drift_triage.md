# RC-11 / RC-13 Expectation Maintenance & Governance Drift Triage

## Executive Summary

RC-11 and RC-13 were modernized using the preceding high-confidence investigation. GD-01 was classified `STALE_EXPECTATION` with high confidence and repaired in its validator. No product runtime file, fixture, replay input, or validation authority classification changed.

## Starting Baseline

The pre-maintenance suite collected 6,448 tests: 6,342 passed, seven failed, and 99 skipped. The failures were RC-10 (one), RC-11 (one), RC-13 (one), RC-21 (three), and GD-01 (one).

## RC-11

The old test required whole-dictionary equality between a preserved pre-BU2-C inline sequence and the modern helper. That representation was obsolete because the helper now records governed mutation attribution.

The maintained test separately protects behavioral equivalence and provenance. It requires identical accepted player-facing text, complete emission-debug equality, and identical candidate/emitted previews. It then requires exactly one modern write-site row with the expected family, file, function, owner, source, mutation reason, `diagnostic_only` status, active-stream selection, non-candidate-only classification, and changed semantic hash.

The opening/fallback/attribution family passed. No product code changed.

## RC-13

The historical profile independently capped mutation events at 14. The current governed inventory contains six categories: fallback 7, final-emission 4, referential-clarity replacement 1, response-type repair 2, sealed replacement 4, and speaker repair 1.

The profile now derives its aggregate ceiling of 19 from those subtype ceilings. The assertion bridge also requires observed aggregate events to reconcile exactly with subtype totals and rejects unrecognized mutation kinds. Recurrence permissions are generated from the same subtype inventory.

The healthy deterministic 25-turn replay passes. Synthetic controls prove that both an unknown mutation kind and an excessive known subtype remain rejected. Replay and projection behavior did not change.

## GD-01

The failing validator required `Governance context (CO98)` in BQC4, while the active generated artifact and CO102 audit require and preserve `Governance context (CO99)`. The substantive requirements remain current: failure-classification governance is closed, attribution governance is separate, architectural constraints remain documented, and recurrence operational graduation remains false.

Classification: `STALE_EXPECTATION`, high confidence. The validator and test name were advanced to CO99; the active document and historical records were not rewritten.

## Product Behavior

No gameplay, narration, final-emission, mutation production, fallback, routing, state, or replay semantics changed.

## Validation Authority

No test family was promoted or demoted, and no Evidence Standard, portfolio authority, architecture gate, or calibration authority changed. No test was skipped, xfailed, or deleted.

## Ending Baseline

The post-maintenance suite collected 6,450 tests: 6,347 passed, four failed, and 99 skipped. Collection grew by two passing RC-13 negative controls. RC-11, RC-13, and GD-01 became green; no new failure appeared.

## Remaining Failures

Only RC-10 and RC-21 are expected to remain. RC-10 requires a local raw-token boundary policy decision. RC-21's three tests require a destination-redirect authority policy decision. Neither was modified.

The exact remaining nodes are recorded in `artifacts/expectation_maintenance/remaining_red_audit.json`.

## Technical Baseline Status

No known unresolved technical defect remains in the red baseline. The remaining red tests represent explicit policy choices, not unexplained technical behavior.

## Recommended Next Campaign

Review this technical baseline, then consider a separate RC-10 / RC-21 Policy Resolution campaign. This campaign does not begin that work.
