# PR-BK — Unauthored Reply Text Must Not Become a Reusable Structured Fact

Date: 2026-09-24

Lane: AI Experience. Secondary: gameplay integrity / continuity.

## Invariant

Conversational memory is not automatically factual authority.

`topic_pressure.last_answer` may keep what an NPC said. That text may be selected through an authority-bearing structured-fact path only when provenance identifies an authoritative source:

- `topic_revealed`
- `authored_topic` (a revealed NPC topic)
- `clue_knowledge`
- `canonical_fact`

Otherwise the commit records `last_answer_provenance = generative_reply`. The line stays for continuity. The selector and `prior_same_dimension_answer_exists` do not treat it as a fact.

When the reply paraphrases an already-authoritative payload, `last_answer` keeps the spoken line and `last_answer_authoritative_text` keeps the payload. Selection uses the payload.

Absence of authority does not invent authority. The existing refusal / no-candidate path remains.

## Provenance rule

1. Eligible provenance is one of the four sources above, or a stored line that matches one of those payloads already on the resolution, revealed topics, or scene clue knowledge.
2. Provenance is established in `_commit_topic_progress` via `classify_stored_answer_provenance`.
3. It is stored on the topic-pressure entry as `last_answer_provenance` and, when present, `last_answer_authoritative_text`.
4. It is checked in `structured_fact_text_from_topic_pressure`, used by the social selector and by escalation’s prior-answer flag.
5. Generative provenance, or no matching payload, yields no structured-fact text.
6. Conversational continuity remains: the reply is still stored on `last_answer` unless it is an interruption cutoff.
7. The selector fails closed to `refusal` / `none` when no other authoritative candidate exists.
8. A refusal reply is classified `generative_reply` and is not mined for facts.
9. An unanswered question stays unanswered: no `topic_revealed` is created from the prose.
10. Model prose can still be remembered as something an NPC said without becoming world truth.

## What changed

Production:

- `game/social.py` — provenance helpers; selector paths A and C; escalation prior-answer text.
- `game/response_policy_enforcement.py` — commit records provenance from the resolution, world, and session.

Tests:

- `tests/test_unauthored_reply_structured_fact_integrity.py` — probes A–H and the human-shaped access claim.
- Authoritative fixtures that already meant “this stored sentence is the answer” now set `last_answer_provenance`. Assertions that the sentence is selected were not removed.
- One escalation fixture whose stored line is a refusal now expects `prior_same_dimension_answer_exists` false.

Not changed: `recent_contextual_leads`, narrative-authority validation, `Word is`, cutoff wording, NPC topics, clocks, compound turns.

## Anti-overfitting

1. The repair does not mention Tavern Runner.
2. It does not mention Guard Captain.
3. It does not depend on curfew.
4. It does not depend on `Word is`.
5. It does not depend on Cinderwatch.
6. It does not inspect exact model sentences from the transcript.
7. It does not blacklist phrases.
8. It does not stop storing answers.
9. Authored follow-up reuse remains (PR-BG).
10. Probes cover a kiln porter and a wharf tally clerk, plus the existing PR-BG fixtures.
11. Authority comes from provenance and existing payloads, not from wording lists.
12. The same rule would apply if the human transcript had never existed: a remembered line is a fact only when an authoritative payload says so.

Full suite (`python -m pytest -q --tb=no`): 7,053 collected, 6,926 passed, 28 failed, 99 skipped.

That run is separate from the previous recorded baseline of 6,450 collected, 6,351 passed, 0 failed, 99 skipped. After that run, the playability smoke location assertion was pointed at the authored east-lanes clue instead of the mock sentence `east gate yard`. The suite was not re-run after that one-line assertion change.

## Residue

- A model can still say an unsupported sentence once. PR-BK stops later machinery from promoting that sentence into a reusable structured fact. Narrative-authority validation still reported `narrative_authority_failed = false` on the playtest and was not redesigned.
- `recent_contextual_leads` still stores fragments for prompt context. It is not the structured-fact selector. Figure-kind leads can still be copied into visible facts by an existing scene-fact helper. That was not the captain-claim path.
- Untargeted inspection, notice-board ownership, the empty `The guard` label, question-only sole-NPC lock, diegetic time, and compound-turn execution stay deferred.

## Validation Closeout

Validation did not change production code or tests. The historical full-suite line above stays as implementation history.

Initial rerun, before any closeout edit (`python -m pytest -q --tb=no`, progress marks in `development/tmp/pr_bk_validation_full_suite_initial.txt`):

```text
7053 collected
6927 passed
27 failed
99 skipped
```

That is one fewer failure than the historical 28. The only assertion changed between those runs is `tests/test_playability_smoke.py`: `east gate yard` became `east lanes`. The original 28-node list was not saved. The missing failure is that playability assert. The other 27 nodes are listed in `artifacts/pr_bk/validation_failure_inventory.md`. Each of them also fails on committed `90fdcc3`.

Classification of the 27: A 0, B 0, C 0, D 27, E 0, F 0. No production defect was found. No fixture was migrated during closeout. The `east gate yard` change is a wording assertion against the authored east-lanes clue (`They were seen near the east lanes.` in the runner seed). The mock location is not the fact. The new assertion passed. It is semantically correct.

Focused semantic run: 124 collected, 124 passed, 0 failed, 0 skipped. Includes `tests/test_unauthored_reply_structured_fact_integrity.py` (9) and the PR-BG, PR-BI, social-answer, escalation, refusal, and grounded-absence families named in `PR-BK_validation_closeout.md`.

`prior_same_dimension_answer_exists` now reads authoritative structured-fact text. A correction reask can still force the flag for conversational pressure. That flag does not select `last_answer` prose. No second flag was added.

`recent_contextual_leads` was not repaired. Figure-kind leads can still be copied into visible facts. That path is not the structured-fact selector, and the tattered-man tests already fail on `90fdcc3`.

Narrative-authority validation was not changed.

Final rerun (`development/tmp/pr_bk_validation_full_suite_final.txt`): 7,053 collected, 6,927 passed, 27 failed, 99 skipped. Same 27 nodes. All are unrelated to PR-BK.

PR-BK is CLOSED.

## Next action

Start a fresh human playtest. Do not continue the contaminated seven-turn session.
