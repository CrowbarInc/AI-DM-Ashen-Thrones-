# PR-DC Classifier Trace

LIVE CALLS: 0

## Source

Classification of an unauthored social reply is `_bounded_social_reply_plan_for_missing_topic` in `game/social.py`.

`resolve_social_action` calls it only after an addressable NPC is resolved and no topic record is selected for this question. The flag passed as `topic_revealed` is whether that NPC already has any revealed topic, not whether this sentence has an authored answer.

`_apply_social_reply_plan` copies the plan onto `resolution["social"]`. `normalize_noncombat_resolution` copies `reply_plan_kind`, `incidental_subjective_allowed`, `npc_speech_authority`, and `objective_world_fact_authority` into narration constraints. `build_dialogue_social_plan` reads those constraints. `build_messages` then evaluates `_project_harmless_social_provider_context` in `game/gm.py`. That projector was not edited.

## Inputs

- `action_type`
- player text (`raw_player_text` or the action prompt)
- NPC disposition / attitude
- whether a prior topic thread exists

The function does not read conversational history, pronouns, or the question mark.

## Order

1. Prior topic thread: `authoritative_answer_available`, reply kind `answer`.
2. `_RESTRICTED_SOCIAL_INFO_RE` or disposition `hostile`: `genuine_refusal`.
3. `_CONSEQUENTIAL_SOCIAL_INFO_RE`: `consequential_information_request`.
4. `_HARMLESS_SUBJECTIVE_REPLY_RE`, or a question / social probe that passes `_harmless_experiential_question`: `harmless_subjective_response_permitted`.
5. Other questions and probes: `genuine_uncertainty`.
6. Any other action type: `genuine_uncertainty` with reply kind `reaction`.

Speech authority is `claim_only` only for step 4. Objective world-fact authority is `authored_context_required` for refusal and consequential requests, and `none` otherwise. `durable_state_mutation_allowed` and `declared_claims_expected` stay false.

## Why turn 1 differed

Turn 1, "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?", matches `prefer` in `_HARMLESS_SUBJECTIVE_REPLY_RE`.

Turn 2, "Does the rain make it harder to keep watch?", and turn 3, "Does it get any easier after a while?", matched none of `prefer`, `favorite`, `recommend`, `what do you think`, `how do you feel`, or the adverbial "do you usually enjoy" frame. Both are `question` actions with no revealed topic, so step 5 assigned `genuine_uncertainty`.

That split is cause D, overly narrow phrase matching. The uncovered wording is ordinary subjective experience (cause C describes the same gap). It is not cause B: PR-DB had already kept `guard_captain` as the social target, obligation interlocutor, single allowed speaker, and discourse focus. It is not cause A: the claim-only plan already exists for harmless personal speech and does not grant world-fact authority.

## Experiential addition

`_harmless_experiential_question` returns true only when `_HARMLESS_EXPERIENTIAL_REPLY_RE` matches and both `_EXPERIENTIAL_AUTHORITY_BLOCK_RE` and `_THIRD_PARTY_EXPERIENCER_RE` do not.

The experiential pattern is a closed list:

- weather or work making it harder to keep watch, stand, wait, work, or stay awake
- "does it get any easier/harder after a while"
- standing, waiting, working, or sitting being uncomfortable
- long shifts, watches, hours, nights, or days leaving you tired
- "do you find ..." tiring, for a closed object list
- "do you enjoy working/standing/waiting/the work"
- noise, cold, heat, rain, wind, waiting, standing, work, crowd, or dust bothering you
- the work, job, shift, or waiting being stressful

Open "easier" and "harder" do not match. "Does rain make it easier to assassinate the captain?" stays on step 5.

The preference pattern was not widened. "Why do you prefer somewhere dry?" still matches `prefer` at step 4.
