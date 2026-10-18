# PR-CJ Root-Cause Clusters

Suite result: 33 failed, 32 passed. Live provider calls: 0.

The 33 failures are not 33 independent defects. They are nine clusters. No single cluster is both the majority and a one-line repair.

## A — Non-social text is contracted as a social ask

- Affected tests: 11
- Confidence: CONFIRMED
- Representative failures:
  - `test_action_and_chat_investigate_both_mark_runtime_discovery_memory`
  - `test_chat_targeted_retry_scene_stall_only`
  - `test_chat_passive_scene_prefers_already_introduced_suspicious_figure`
  - `test_action_and_chat_mutate_runtime_before_request_build[via_api_chat]`
- Probable root cause: `_operation` defaults unmatched text to `ask`. `_INSPECT_RE` does not include `investigate`. Leftover asks get `resolution_subject=social`. `select_ordinary_resolver` returns `social`, and `stage_permitted` then blocks exploration, world action, and passive wait.
- Evidence: contract probe. "I investigate the desk.", "I wait.", "Where are we?", and "I remain silent and observe." all return `resolver=social`, `permits_exploration=false`, `permits_passive_wait=false`. Direct `/api/action` investigate still returns `kind=discover_clue`.
- Runtime impact: chat investigation does not discover the desk clue. Waits lose scene-stall retry and concrete pressure. Hard-valid atmosphere is replaced by safe nonresolution.
- Authority implications: authorized clue state is not applied. No provider fact is written as a clue.
- Repair scope: changing the default operation or the social subject fallback changes ordinary resolver selection for the whole campaign. That is a selection-policy change, not a local patch.

## B — Place questions are adjudicated before narration retry

- Affected tests: 2
- Confidence: CONFIRMED
- Representative failures:
  - `test_chat_targeted_retry_unresolved_question_only`
  - `test_chat_targeted_retry_prefers_highest_priority_failure_first`
- Probable root cause: "Where is the missing patrol report?" is `ask` / `place_location`, so the resolver is adjudication and the provider is not called.
- Evidence: HTTP probe, 0 provider calls, `kind=adjudication_query`, player text "No nearby that place is currently established in this scene."
- Runtime impact: report-location questions get a place adjudication instead of an unresolved-question retry.
- Authority implications: the answer is engine text. It does not promote a provider fact. It also does not answer from the patrol-report clue.
- Repair scope: separate from cluster A. The place-location family is doing what `select_resolver_family` specifies. The shared retry tests disagree with that family.

## C — Immutable retry prompt replaced the validator-voice target

- Affected tests: 1
- Confidence: CONFIRMED
- Representative failure: `test_chat_targeted_retry_validator_voice_only`
- Probable root cause: the second call exists, but `regeneration_feedback` emits the `unauthorized_resolution_decision_fact` narration-only prompt. The test still requires `Retry target: validator_voice.`
- Evidence: assertion text contains "The previous attempt was rejected for: unauthorized_resolution_decision_fact." The first candidate is "Based on what's established, we can determine very little here.", which matches `_HARD_META_VOICE_RE`.
- Runtime impact: meta voice is retried as an unauthorized world fact.
- Authority implications: the retry does not authorize a new fact. The failure class is the wrong one for this sentence.
- Repair scope: prompt precedence inside immutable regeneration. It must not weaken the decision audit.

## D — Chat returns a resolution shell instead of null

- Affected tests: 2
- Confidence: CONFIRMED
- Representative failures:
  - `test_chat_fallback_preserves_endpoint_specific_no_resolution_shape`
  - `test_chat_social_pressure_line_prefers_dialogue_over_adjudication`
- Probable root cause: `chat()` starts `resolution` as a dict and returns it after stamping `ordinary_contract_established`, even when no engine kind was resolved.
- Evidence: both failures assert `resolution is None` and receive a dict whose keys are metadata, prompt, and world tick events.
- Runtime impact: clients that treat a present resolution as an engine outcome see a kind-less shell.
- Authority implications: the shell carries the contract. It does not by itself mutate clues.
- Repair scope: response-shape decision. Either the endpoint contract changes, with the tests updated only after that contract is accepted, or the shell stays internal and the HTTP field stays null. That choice was not unambiguous.

## E — Stock and scaffold phrases survive emission

- Affected tests: 4
- Confidence: SUPPORTED
- Representative failures:
  - scene-hold filler
  - visible-intro filler
  - `planner:` scaffold
  - "from here, no certain answer presents itself"
- Probable root cause: the strict-social emission branch assigns player text without `sanitize_player_facing_output`. These tests are social or question turns, so this is not the same bug as cluster A.
- Evidence: `_build_turn_response_payload` skips the sanitizer when `strict_social_emission_will_apply` is true. The failing phrases are exactly the banned stock lines.
- Runtime impact: internal and stock wording can reach the player on social turns.
- Authority implications: presentation leak, not a new objective fact.
- Repair scope: a sanitizer-on-social-path change would touch final emission and needs its own regression against strict-social tests.

## F — Speaker, reply kind, and progression repairs do not run

- Affected tests: 8
- Confidence: SUPPORTED
- Representative failures:
  - `reply_kind` is answer/explanation/refusal rather than unknown
  - repeated social text keeps the rain line and drops "tavern runner"
  - interruption line is identical on the second turn
  - refusal phrases absent
  - wrong speaker becomes safe nonresolution
  - `speaker_contract_enforcement_reason` is null
- Probable root cause: the immutable mutator inventory marks speaker enforcement, social response-structure repair, and deterministic retry fallback as removed from the critical path. Safe nonresolution also replaces the candidate before speaker rewrite.
- Evidence: failure strings above, plus `MUTATOR_MIGRATION` in `game/immutable_valid_response.py`. "Who attacked them?" is a real social question, so cluster A does not explain this group.
- Runtime impact: NPC voice, refusal progression, and speaker repair are skipped or replaced.
- Authority implications: no provider claim was observed becoming clue state. Speaker identity is dropped rather than reassigned to an unauthorized NPC, except where the generic safe line replaces both the wrong speaker and the canonical one.
- Repair scope: several emission repairs. Restoring them wholesale would reverse the mutator migration.

## G — Exploration is selected, mixed-investigation metadata still fails

- Affected tests: 3
- Confidence: POSSIBLE
- Representative failures: "I check the notice", "I examine the broken lantern", "I study the strange brass device"
- Probable root cause: these utterances select `exploration` / `inspect`. JUnit stored only `AssertionError`, so the first assert inside the test was not recovered.
- Evidence: contract probe permits exploration. The sibling notice-board case does not, and is in cluster A.
- Runtime impact: unknown until one of the three is rerun with a full traceback.
- Authority implications: unknown.
- Repair scope: do not patch until the assert is identified.

## H — Owned contract drops embedded roll metadata

- Affected tests: 1
- Confidence: SUPPORTED
- Representative failure: `test_chat_mixed_dialogue_with_parenthetical_rules_uses_social_main_lane`
- Probable root cause: `kind == question` already passed. `embedded_adjudication` is attached only when the contract is not owned.
- Evidence: test line asserts category `roll_requirement_query` on `metadata.embedded_adjudication`, which is `{}`.
- Runtime impact: the parenthetical roll question is not surfaced beside the social lane.
- Authority implications: the social lane remains the main resolution. The roll requirement is omitted, not invented.
- Repair scope: one attachment site, after confirming the full-utterance contract should still record the parenthetical.

## I — Referential follow-up becomes a clarification

- Affected tests: 1
- Confidence: SUPPORTED
- Representative failure: `test_chat_known_follow_up_bypasses_uncertainty_fallback`
- Probable root cause: "Where do I find that person?" abstains with `insufficient_discourse_context` and request kind `clarification`. Player text asks which referent is meant. Retry debug notes are empty.
- Evidence: contract probe and the failure text "Which do you mean?"
- Runtime impact: a follow-up that the test treats as known becomes a clarification.
- Authority implications: the clarification does not assert a location.
- Repair scope: discourse binding for "that person", separate from cluster A.
