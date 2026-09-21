# RC-13 Root Cause

The direct-intrusion replay remains structurally healthy: 25 turns, seven fallback turns, no fallback-owner changes, session-health score 100, classification `clean`, `overall_passed: true`, and no progressive degradation.

The failure is isolated to the diagnostic lineage profile. Its mutation cap is 14 and its four modeled subtype caps sum to 14. Current governed projection reports those same 14 events plus four `sealed_replacement_mutation` events and one `referential_clarity_replacement_mutation`, for 19 total.

The first semantic-model mismatch is `act_02`, where sealed replacement receives its own mutation event. Referential-clarity replacement appears at `act_14`. The aggregate count first exceeds 14 at `act_19`.

Provenance supports expectation drift. The cap entered as a historical exact diagnostic snapshot in commit `1603880`; `sealed_replacement_mutation` was introduced later by `adc374b` as part of semantic replacement attribution completeness. The projector accurately reports the expanded governed vocabulary.

Finding: `STALE_EXPECTATION`, confidence `HIGH`. Future work should recalibrate the supporting diagnostic profile around governed subtype expectations and derive or reconcile the aggregate cap. This investigation makes no such change.
