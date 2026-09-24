# PR-BK — Validation Closeout

Date: 2026-09-24

## Executive Summary

PR-BK is safe to close.

Unsupported generative prose stored on `topic_pressure.last_answer` is not selected as a structured fact. Authored follow-ups, clue and canonical payloads, refusal fail-closed behavior, and cutoff exclusion still pass. The 27 remaining full-suite failures also fail on committed `90fdcc3`, before this change. Validation made no production or test edit.

## Initial Full-Suite Rerun

Command, against the tree as it existed at the start of this closeout:

```text
python -m pytest -q --tb=no
```

Log: `development/tmp/pr_bk_validation_full_suite_initial.txt`.

The capture did not flush pytest's final stats line. Counts are the progress marks on the percentage lines:

```text
7053 collected
6927 passed
27 failed
99 skipped
```

## Historical 28-Failure Reconciliation

The implementation report recorded:

```text
7053 collected
6926 passed
28 failed
99 skipped
```

The original node list was not saved. What can be established:

- Collection size and skip count match this rerun.
- Passed count rose by 1 and failed count fell by 1.
- The only test assertion edited after that run is `tests/test_playability_smoke.py`, from `east gate yard` to `east lanes`.
- That test is not among the 27 failures.
- The other 27 node ids fail both now and on `90fdcc3`.

Answers:

1. Provenance-fixture migrations among those 28 failures: 0. Fixture provenance added during implementation belongs to tests that already passed in that run.
2. Failures that exposed a previously unsafe expectation and were reclassified here: 0. The 27 were already red before PR-BK, so they are not new evidence of an unsafe expectation created by this change.
3. Actual PR-BK regressions: 0.
4. Unrelated: 27. The 28th was the playability wording assert.
5. Duplicates of one cause, inside the 27: BY3/BY4 generator gap (3), BV14C import registry (2), frontier-gate golden replay (3), duplicate test-name governance (2), rain-sentence adjudication exemption (2), Aldric `success is None` (2), concrete-pressure helper (2), tattered-man atmosphere (3).
6. `east gate yard` was the failure removed by the post-suite assertion edit.
7. That edit is semantically correct. See East-Lanes Assertion Audit.

What cannot be established: the verbatim pytest line for the 28th failure, because that log was not kept. The identification rests on the count delta plus the one recorded assertion edit.

## Failure Inventory

Full entries: `artifacts/pr_bk/validation_failure_inventory.md`.

| Class | Count |
| --- | --- |
| A — legitimate fixture migration | 0 |
| B — genuine PR-BK regression | 0 |
| C — previously unsafe expectation | 0 |
| D — unrelated pre-existing | 27 |
| E — brittle wording | 0 |
| F — infrastructure | 0 |

## Production Corrections

None. `game/social.py` and `game/response_policy_enforcement.py` were not edited during validation.

## Fixture/Test Migrations

None during validation.

Implementation, already present before this closeout, had added `last_answer_provenance` on fixtures whose stored line was the answer the test meant to reuse (`authored_topic` plus `last_answer_authoritative_text` where the line itself is the payload). One escalation fixture whose stored line is a refusal now expects `prior_same_dimension_answer_exists` false. Those edits were not repeated here, and they were not used to turn the 27 reds green.

## East-Lanes Assertion Audit

`tests/test_playability_smoke.py::test_playability_smoke_direct_answer_pressure` seeds the runner with authored topic text `They were seen near the east lanes.` The mocked model line says `east gate yard`.

That mock location is generated prose. It is not an authoritative payload. After PR-BK the second turn emits the authored east-lanes clue, so `east gate yard` is absent and `east lanes` is present. The test passed in both closeout suite runs.

The new assertion checks the authoritative payload. It is the correct semantic assertion. It was not reverted and not weakened.

## Focused Semantic Validation

Command:

```text
python -m pytest -q --tb=line tests/test_unauthored_reply_structured_fact_integrity.py tests/test_followup_topic_continuity_public_clue_paraphrase.py tests/test_interruption_progression_catalog_residue.py tests/test_social_answer_candidate.py tests/test_social_topic_anchor.py tests/test_social_escalation.py tests/test_social_answer_retry_prioritization.py tests/test_grounded_refusal_realization_grammar.py tests/test_grounded_refusal_topic_hook_integrity.py tests/test_grounded_social_absence_live_model_non_invention.py tests/test_playability_smoke.py::test_playability_smoke_direct_answer_pressure
```

Result: 124 collected, 124 passed, 0 failed, 0 skipped. Exit code 0.

| File | Collected |
| --- | --- |
| `tests/test_unauthored_reply_structured_fact_integrity.py` | 9 |
| `tests/test_followup_topic_continuity_public_clue_paraphrase.py` | 15 |
| `tests/test_interruption_progression_catalog_residue.py` | 5 |
| `tests/test_social_answer_candidate.py` | 8 |
| `tests/test_social_answer_retry_prioritization.py` | 3 |
| `tests/test_social_escalation.py` | 20 |
| `tests/test_social_topic_anchor.py` | 6 |
| `tests/test_grounded_refusal_realization_grammar.py` | 26 |
| `tests/test_grounded_refusal_topic_hook_integrity.py` | 16 |
| `tests/test_grounded_social_absence_live_model_non_invention.py` | 15 |
| `tests/test_playability_smoke.py::test_playability_smoke_direct_answer_pressure` | 1 |

Required semantic checks, from `tests/test_unauthored_reply_structured_fact_integrity.py` unless noted:

1. Unsupported generative reply stays on `last_answer` and is not selected. Pass (`test_probe_a_unsupported_prose_is_not_selected`).
2. Same-turn self-promotion does not become a fact. Pass (`test_probe_f_same_turn_prose_cannot_promote_itself`).
3. Cross-turn promotion does not become a fact. Pass (`test_probe_g_cross_turn_prose_stays_continuity`).
4. Authored follow-up remains reusable. Pass (`test_probe_b_authored_prior_answer_remains_reusable` and the PR-BG file).
5. Authoritative paraphrase selects the payload. Pass (`test_probe_e_paraphrase_keeps_payload_not_prose`).
6. Refusal does not become a fact. Pass (`test_probe_d_refusal_commit_does_not_become_fact`).
7. Cutoff stays out of fact selection. Pass (`test_probe_c_cutoff_stays_ineligible` and the PR-BI file).
8. No invented provenance. Pass (`test_human_shape_unsupported_access_claim_fails_closed`). A factual-sounding access claim stays `generative_reply`, does not set `topic_revealed`, and the follow-up answer kind is `refusal`.

### `prior_same_dimension_answer_exists`

The flag is set from `structured_fact_text_from_topic_pressure`, so a generative `last_answer` does not count as a prior factual answer. `correction_reask` can still force the flag true. That is conversational reassertion pressure. The flag is copied onto the social resolution and can affect topic-exhaustion bookkeeping. It does not read raw `last_answer` into the structured-fact selector. `force_partial_answer` remains a prompt instruction in `game/gm.py`. Continuity readers (`_topic_progress_score`, and the "this speaker has a stored answer" check) still read the raw line. One flag is enough. No second subsystem was added.

### `recent_contextual_leads`

Not modified. `remember_recent_contextual_leads` still stores fragments for prompt context. `_augment_scene_with_runtime_visible_leads` can copy only `visible_suspicious_figure`, `recent_named_figure`, and `visible_named_figure` into visible facts as "{subject} lingers {position}". That copy does not create `topic_revealed`, clue knowledge, a canonical fact, or a `structured_fact` candidate. It is not the captain-claim path. The tattered-man tests that exercise it fail on `90fdcc3`. Left as separate residue.

### Narrative authority

Not modified. A model may still say an unsupported sentence once.

## Final Full Suite

Command:

```text
python -m pytest -q --tb=no
```

Log: `development/tmp/pr_bk_validation_full_suite_final.txt`.

```text
7053 collected
6927 passed
27 failed
99 skipped
```

Same 27 nodes as the initial rerun. No code changed between the two runs.

## Anti-Gaming Review

1. Did any failing test receive fake provenance solely to make it pass? No. No fixture was edited during validation.
2. Were any assertions weakened? No.
3. Were any tests skipped or marked xfail? No.
4. Was any semantic evaluator loosened? No.
5. Did production code gain a test-specific branch? No production edit.
6. Did any repair depend on Tavern Runner, Guard Captain, curfew, Cinderwatch, or `Word is`? No repair was made.
7. Can unsupported prose still become a structured fact through another `last_answer` reader? The authority-bearing readers are `select_best_social_answer_candidate` paths A and C, and they call `structured_fact_text_from_topic_pressure`. Generative provenance returns no fact text. Continuity readers still see the raw line and do not emit it as a structured fact.
8. Can authoritative PR-BG follow-ups still succeed? Yes. `tests/test_followup_topic_continuity_public_clue_paraphrase.py`: 15 passed.
9. Does refusal still fail closed? Yes. Refusal probe and grounded-refusal / grounded-absence files passed.
10. Does the implementation still preserve conversational memory? Yes. Probe A keeps the prose on `last_answer` with `generative_reply`.

## Remaining Residue

Unrelated reds, all pre-existing on `90fdcc3`. Do not treat them as PR-BK work:

- BY3/BY4 semantic-mutation generators (unknown first source / attribution gap).
- Frontier-gate 25-turn golden replay (three tests).
- BV14C social-exchange import registry.
- Duplicate test name `test_anti_overfitting_generic_helpers_have_no_calibration_special_case`.
- Rain-sentence question-resolution tests. Adjudication is exempt. `game/gm.py` was not edited.
- Manifest redirect source label `topic_pressure:last_answer` versus `:redirect` (recorded since PR-AO).
- Two speaker-grounding tests where `success` is `None` (recorded in PR-BJ).
- Open-solicitation gauntlet still emits `The guard says`.
- Investigate discovery id `desk` versus `inv-desk`.
- Passive-pressure / tattered-man atmosphere tests.
- Dialogue establishment for "to the guard", shipped-contract retry `TypeError`, and response-type skip reason.

Play residue to watch on the next human run, not a repair queue:

- untargeted inspection emits unrelated visible stock
- notice-board ownership
- empty `"The guard"` label
- question-only sole-NPC dialogue lock
- missing diegetic time
- missing authored information
- compound-turn execution
- one-turn unsupported generative statements / narrative-authority weakness
- figure-kind leads copied into visible facts

## Closeout Decision

```text
PR-BK CLOSED — fresh human playtest recommended.
```
