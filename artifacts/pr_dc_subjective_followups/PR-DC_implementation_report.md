# PR-DC Implementation Report

MODE: SUBJECTIVE FOLLOW-UP CLASSIFICATION

LIVE CALLS: 0

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The worktree was already dirty. It was not reset. Production saves were not used.

PR-DB inherited decision: A — SPEAKER GROUNDING REPAIRED

## Baseline

The three-turn frontier-gate exchange was replayed through `play_turn` before any classifier edit.

| Turn | Resolver | Interlocutor | Reply plan | Incidental subjective | Speech authority | Speakers |
|---|---|---|---|---|---|---|
| 1 prefer standing watch | social | guard_captain | harmless_subjective_response_permitted | true | claim_only | [guard_captain] |
| 2 harder to keep watch | social | guard_captain | genuine_uncertainty | false | none | [guard_captain] |
| 3 easier after a while | social | guard_captain | genuine_uncertainty | false | none | [guard_captain] |

Speaker grounding from PR-DB was already intact. Reduced context stayed off on turns 2 and 3 because `reply_plan_kind` was `genuine_uncertainty`.

## Cause

D — overly narrow phrase matching.

`_HARMLESS_SUBJECTIVE_REPLY_RE` recognizes preference and recommendation wording. Turn 1 matches the bare token `prefer`. Turns 2 and 3 do not contain any token in that pattern, so `_bounded_social_reply_plan_for_missing_topic` assigns `genuine_uncertainty` for a question with no authored topic.

The speaker, resolver, and conversation continuity were already present. The missing piece was recognition of a closed ordinary-experience frame. That is incomplete subjective-intent coverage inside the same phrase matcher, not a missing follow-up record and not a policy that experiential questions must stay uncertain. The existing plan already limits accepted matches to claim-only speech with no objective world-fact authority.

## Change

`game/social.py` only.

`_harmless_experiential_question` may also select `harmless_subjective_response_permitted` when all of the following hold:

- the action is `question` or `social_probe`
- no authored topic is already revealed
- the restricted-information pattern and a hostile disposition do not match
- the consequential-information pattern does not match
- the line matches a closed experiential frame: subjective difficulty of ordinary watch or work, getting used to it, discomfort, fatigue, direct enjoyment of the work, bother, or stress
- an authority-blocker pattern does not match
- the grammatical subject is not a named third-party role

The plan fields are unchanged: `incidental_subjective_allowed` follows the kind, `npc_speech_authority` is `claim_only` only for that kind, `objective_world_fact_authority` stays `none`, and durable mutation stays false.

PR-CW projection predicates, speaker selection, and authority ownership were left as they were.

## Result

Turns 2 and 3 now use `harmless_subjective_response_permitted`, `claim_only`, and one `guard_captain` speaker. `build_messages` selects `harmless_social_incidental_dialogue_v1` for those turns through the existing projector. The assassination question and the missing-patrol question stay `genuine_uncertainty`, and their prompt hashes are unchanged.

## Decision

A — SUBJECTIVE FOLLOW-UPS VERIFIED
