# Baseline and scope

## Recorded baseline

| Item | Value |
| --- | --- |
| Repository commit | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Working tree | Already dirty with unrelated campaign, artifact, and gameplay edits. Those files were left untouched. |
| Predecessor | PR-PLAY-54, verdict B. Evidence in `artifacts/pr_play_54/`. |

PR-PLAY-54 scored results, reconfirmed on the current code before this cycle's claim changes and again after them:

- 49/49 consequential fabrications rejected by the new check.
- 0/31 false positives on the scored positive and paraphrase lines, for that check.
- 7/7 authorized paraphrases accepted by that check.
- 2 ambiguous lines (`R1`, `R2`) return `REVIEW_REQUIRED`. `R3` is an unauthorized acquisition and returns `FAIL`.
- Focused suite at the end of PR-PLAY-54: 520 passed, 3 previously known failures, 0 new regressions.

The three known failures were reproduced again and were not modified:

- `tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution`
- `tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues`
- `tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues`

## Reproduced gap

Against `notice_success`, before the edit:

| Sentence | Decision |
| --- | --- |
| You discover a ribbon beneath the board. | FAIL `unauthorized_discovery` |
| You find a ribbon beneath the board. | PASS |
| You notice a crack in the board. | PASS |
| You notice a ribbon beneath the board. | PASS |
| A ribbon lies in your hand after the search. | PASS |
| Your search leaves you holding a narrow strip of cloth. | PASS |
| You notice an unfamiliar marking near the door. | PASS |

`find` and `notice` only fired when the head noun was in a fixed consequential list. `ribbon` was not on that list. `discover` did not consult the list.

## Reproduced legacy rejects

| Id | Sentence | New check | Combined prelude gate | Reason |
| --- | --- | --- | --- | --- |
| P1 | At sundown, the guard makes his rounds along the west road. | PASS | reject | `ungrounded_authoritative_rule` |
| S21 | A little dust lies in your pack. | PASS | reject | `unsupported_mechanical_claim:items_added` |

P1 is classified as geography because "west road" is a compass locative. Grounding required every token of length 4 or more to occur in the engine corpus. `sundown`, `rounds`, `along`, and `west` are not the same strings as `dusk`, `patrols`, and `western`.

S21 matches the possession frame "lies in your pack". The captured object is dust. The frame then required an `items_added` grant.

## Scope

Changed:

- `game/consequential_narration_validation.py`
- `game/mechanical_claims.py` (debris inside possession frames)
- `game/proposition_authority.py` (geography grounding only)
- `tests/test_pr_play_54_consequential_validation.py` (the two lines are now required to pass the combined gate; a key in a pack and an east road still fail)

Added development fixtures, a frozen holdout, and this evidence package.

Not changed: canonical campaign fixtures, player-facing modules (`game/api.py`, `game/gm.py`, `game/exploration.py`), quarantine enablement, provider clients.
