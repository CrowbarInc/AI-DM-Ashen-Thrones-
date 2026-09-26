# PR-BN - Bounded DM Improvisational Authority

Date: 2026-09-26
Base HEAD: `a5bfdd9e0376173c5aeb4fc762ada259e24bd638`

## 1. Executive summary

PR-BN adds the first production-capable bounded improvisational authority lane for the AI-DM. The runtime now has a typed proposal schema for low-consequence incidental details and NPC claims, validates them with an explicit positive authority policy, persists accepted entries in a separate runtime ledger, projects that ledger back into prompt context, suppresses destructive retry for accepted bounded improvisation, and lets final-emission narrative-authority validation recognize clean accepted bounded proposals as legitimate authority.

This does not grant the model authority over mechanics, hidden facts, authored world truth, quest-critical facts, geography/faction/history changes, player agency, or scene transitions.

## 2. Architecture before PR-BN

Before PR-BN, the runtime had:

- Engine/authored authoritative state.
- Candidate GPT narration.
- Legacy `scene_update` and `world_updates` proposal adoption.
- Retry and final-emission validators that favored provable authored/state-backed text.

It did not have a positive runtime answer to: "May the DM invent this mundane fictional detail?" Ordinary invented details were therefore either ephemeral narration, legacy scene updates, unsupported social facts, or final-emission/retry failures.

## 3. Architecture after PR-BN

PR-BN adds `game.bounded_improvisation` as the owner for bounded improvisational authority. The turn flow is now:

1. The GM may emit `improvisation_proposals`.
2. The API evaluates those proposals with scene/session/world/resolution context before retry.
3. Valid bounded proposals suppress retry failures that previously represented lack of authored provenance.
4. Final emission treats clean accepted bounded proposals as a legitimate narrative-authority source.
5. Post-GM persistence promotes accepted entries into `session["bounded_improvisation"]`.
6. Prompt context projects accepted entries for follow-up consistency.

## 4. New authority taxonomy/schema

The proposal shape supports:

- `kind`: `incidental_fact`, `npc_claim`, or `consequential_proposal`.
- `category`: small allowed category sets for incidental details and NPC claims.
- `content`: player-visible fact/claim text.
- `scope`: `turn`, `scene`, or `session`.
- `consequence_level`: `none`, `low`, or `incidental`.
- `source`: e.g. `dm_improvisation`, `npc:<id>`, `observation`.
- `speaker_id`: optional NPC/source attribution.
- `epistemic_status`: `known`, `grounded`, `rumor`, `hearsay`, `uncertain`, or `speculative` for claims.

Accepted runtime entries carry `authority="bounded_improvisation"` and remain distinct from authored world truth.

## 5. Promotion/persistence behavior

Accepted entries are promoted by `promote_accepted_bounded_improvisation()` into `session["bounded_improvisation"]["entries"]`.

Scene-scoped and session-scoped retrieval is exposed by `prompt_projection_for_bounded_improvisation()`, which is included in prompt context as `bounded_improvisation`.

Contradictory reinvention is rejected by policy. Scope is intentionally conservative; scene scope is the default.

## 6. NPC claim semantics

NPC claims are stored as claims, not world facts. Accepted claim entries use `truth_status="not_world_truth"` and preserve `speaker_id`, `source`, and `epistemic_status`.

This supports rumors/hearsay/speculation continuity without asserting that the reported event, culprit, monster, route, faction, or quest state is true.

## 7. Final-emission integration

`game.final_emission_narrative_authority.skip_narrative_authority_layer()` now recognizes `validated_bounded_improvisation` only when:

- there is at least one accepted bounded proposal, and
- there are no rejected proposals in the same payload.

Mixed payloads with rejected consequential content still run through the existing safeguards.

## 8. Retry integration

`game.gm_retry.detect_retry_failures()` suppresses provenance-collapse failure classes only when the GM output has valid bounded improvisation. Suppressed classes are:

- `unresolved_question`
- `npc_contract_failure`
- `scene_stall`
- `followup_soft_repetition`

Validator voice, generic filler, echo/repetition, and other genuine failures remain active.

## 9. Files changed

- `game/bounded_improvisation.py` - new owner module.
- `game/gm.py` - GM JSON schema and bounded-authority prompt instructions; narrowed adjudication question-rule exemption.
- `game/api.py` - proposal evaluation before retry; promotion in post-GM updates.
- `game/prompt_context.py` - prompt projection for accepted runtime entries.
- `game/gm_retry.py` - retry suppression for valid bounded improvisation.
- `game/final_emission_narrative_authority.py` - final-emission authority recognition.
- `game/response_policy_enforcement.py` - proposal normalization in state-update validation.
- `tests/test_bounded_improvisation_authority.py` - capability tests.

## 10. Tests added/updated

Added `tests/test_bounded_improvisation_authority.py`, covering:

- Incidental detail acceptance and persistence.
- Prompt projection for consistency.
- NPC rumor persistence as claim rather than world truth.
- Consequential/secret invention rejection.
- Mechanical authority rejection.
- Contradictory reinvention rejection.
- Final-emission recognition of clean accepted bounded proposals.
- Retry suppression for valid bounded improvisation.

An existing adjudication question-rule exemption was narrowed so `must_answer` still repairs unresponsive generated text when an adjudication-shaped resolution does not include engine-authored player-facing adjudication text.

## 11. Regression results

Passing:

```text
tests/test_bounded_improvisation_authority.py
tests/test_gm_retry.py
tests/test_prompt_context.py
tests/test_response_policy_enforcement_mutation.py
tests/test_final_emission_gate_diagnostics.py
tests/test_world_updates_and_clue_normalization.py

Result: 177 passed
```

Wider targeted batch:

```text
tests/test_state_authority.py
tests/test_narrative_authority_rules.py
tests/test_social.py
tests/test_social_speaker_grounding.py
tests/test_social_target_authority_regressions.py
tests/test_social_interaction_authority.py
tests/test_strict_social_emergency_fallback_dialogue.py
tests/test_final_emission_narrative_mode_output.py
tests/test_final_emission_visibility.py
tests/test_final_emission_validators.py
tests/test_anti_railroading_retry_alignment.py
tests/test_transcript_regression.py

Result: 230 passed, 2 failed, 1 warning
```

Failures observed:

- `tests/test_social_speaker_grounding.py::test_transcript_runner_asks_about_aldric_followup_stays_runner`
- `tests/test_social_speaker_grounding.py::test_transcript_where_is_aldric_repeated_followups_stay_runner`

Both fail because `resolve_social_action()` returns `success=None` where the tests assert `success is True`. These tests also fail when run independently. No PR-BN source changes touched `game/social.py` or `tests/test_social_speaker_grounding.py`.

## 12. Diagnostic scenario results

Synthetic diagnostic scenarios were covered through capability tests rather than canned transcript replay:

- Innkeeper/food-style ordinary composition: accepted as scene-scoped incidental fact.
- Follow-up consistency: accepted entry projects back into prompt context.
- Traveler/stablehand rumor or detail: NPC claim/detail can persist with speaker attribution.
- Rumor follow-up: claim remains available without becoming world truth.
- Quest-critical secret: rejected as consequential.
- Contradiction: rejected.
- Mechanical outcome/price/HP/inventory-style authority: rejected.
- Final emission: clean accepted proposal is recognized as `validated_bounded_improvisation`.
- Retry: valid proposal suppresses destructive retry collapse.

Evidence is summarized in `artifacts/pr_bn/diagnostic_scenario_evidence.json`.

## 13. Known limitations

- The policy is conservative and lexical in parts; it intentionally rejects many terms that may later become safe under richer typed systems.
- No full economy simulator was added; monetary/mechanical changes remain outside bounded improvisation.
- No complete deception/lie model was added; NPC claims support only known/grounded/rumor/hearsay/uncertain/speculative.
- Persistence is runtime/session data, not campaign-wide authored canon.
- The system does not infer typed improvisation from arbitrary prose; the model must provide `improvisation_proposals`.

## 14. Recommended next step

Build PR-BN.2 around affordance contracts for advertised mundane services, so authored scene text like "runner sells stew and rumors" maps to explicit supported interactions without converting every service into full economy simulation.

