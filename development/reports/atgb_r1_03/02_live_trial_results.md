# 02 — Live Trial Results

| Trial | Routing | Subject interpretation | Evidence | Response | Authority | Admissions | ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | INDETERMINATE | INDETERMINATE | INDETERMINATE | FAIL | PASS | 1 | 1781.25 |
| L2 | INDETERMINATE | INDETERMINATE | INDETERMINATE | FAIL | PASS | 1 | 7471.197 |
| L3 | INDETERMINATE | PASS (correct subject; unnecessary clarification posture) | FAIL | FAIL | PASS | 1 | 3459.428 |
| L4 | FAIL in disabled-interpretation fallback; live control INDETERMINATE | INDETERMINATE (no model interpretation) | INDETERMINATE (no live selection) | FAIL | FAIL (invalid live-control setup) | 0 | 406.866 |


## L1

Player: I meant the people, not the weather.

AI-DM: I couldn't interpret that just now, so no gameplay action was taken.

Provider failure before model interpretation: APIConnectionError. Host fallback inadequate for the request; not evidence of a conversational model defect.

Measured tokens input/output/total: None/None/None; end-to-end 1781.25 ms. Cost unavailable. See setup.json, trace.json, response.json, before.json, after.json and accounting.json under artifacts/atgb/atgb_r1_03/L1/.

## L2

Player: I meant the people, not the weather.

AI-DM: I couldn't interpret that just now, so no gameplay action was taken.

Provider failure before model interpretation: InternalServerError. Host fallback inadequate for the request; not evidence of a conversational model defect.

Measured tokens input/output/total: None/None/None; end-to-end 7471.197 ms. Cost unavailable. See setup.json, trace.json, response.json, before.json, after.json and accounting.json under artifacts/atgb/atgb_r1_03/L2/.

## L3

Player: No, I was asking about the people, not the weather.

AI-DM: Do you want a description of the people present at the gate district instead of the weather?

GM/CLARIFICATION, evidence_refs=[], no unresolved references. Bridge NEEDS_CLARIFICATION stops before revision gate. No mechanical misrouting observed, but repaired seam not exercised.

Measured tokens input/output/total: 2008/212/2220; end-to-end 3459.428 ms. Cost unavailable. See setup.json, trace.json, response.json, before.json, after.json and accounting.json under artifacts/atgb/atgb_r1_03/L3/.

## L4

Player: Instead, make that a question about the lamp.

AI-DM: The action was resolved, but live narration was not requested because it would exceed the provider budget.

INVALID LIVE CONTROL: fixture import activated experiments/pr_dq/__init__.py environment defaults. Live interpretation skipped; generic resolution consumed a turn, cleared pending intention and updated factions. Narration refused before admission by existing input-token ceiling.

Measured tokens input/output/total: 0/0/0; end-to-end 406.866 ms. Cost unavailable. See setup.json, trace.json, response.json, before.json, after.json and accounting.json under artifacts/atgb/atgb_r1_03/L4/.

All six dimensions are graded independently; no automated gameplay scorer was run. These are provisional AI-assisted judgments, not authenticated human review. L1/L2 response FAIL describes the delivered failure fallback, not model semantic quality. L3 correctly identifies people, so subject interpretation passes; choosing clarification and no evidence still fails adequacy. Routing is indeterminate because the interpretation bridge stops before the repaired gate. L4 has an observed unauthorized mutation relative to the fixture's revise-without-execution contract, but is excluded from live regression conclusions because its environment was invalid. No original trial successfully reached the repaired seam. Four designated attempts, only one valid completed live trial; no reruns.
