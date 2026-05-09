# Response Policy Enforcement Split Plan

This plan records the current subpaths inside
`game.gm.apply_response_policy_enforcement` without changing runtime behavior.
It is split-readiness documentation only: the function should stay intact until
the text-mutating paths have broader regression coverage.

## Current Shape

`apply_response_policy_enforcement` runs policy keys in `RESPONSE_RULE_PRIORITY`,
skips most mutating helpers when `strict_social_emission_will_apply(...)` is
true, commits topic progress from the final reply text, then projects policy and
fallback-behavior metadata. The function sits after GPT response generation and
before final emission, so any player-facing rewrite here is provenance-relevant
even when the rewrite is deterministic and bounded.

## Classification Map

| Subpath | Current helper / location | Classification | Mutates text? | Split note |
| --- | --- | --- | --- | --- |
| `fallback_behavior_contract` handling | inline metadata projection after enforcement loop | metadata-only projection | No | Can move to a projection helper once text-mutating enforcement is isolated. Preserve `metadata.emission_debug.fallback_behavior_contract` shape exactly. |
| question resolution enforcement | `enforce_question_resolution_rule` under `must_answer` | text-mutating enforcement | Yes | Prepends/appends grounded answer text through uncertainty rendering when a direct question was not answered. Keep after strict-social bypass until social ownership is separately documented. |
| NPC response contract enforcement | `enforce_npc_response_contract` under `prefer_specificity` | text-mutating enforcement | Yes | Adds a deterministic concrete next-step sentence when NPC specificity is missing. This is not fallback selection, but it authors prose after GPT output. |
| validator voice rewrite | `enforce_no_validator_voice` under `diegetic_only` | fallback/provenance-relevant mutation | Yes | Direct-question rewrites route through uncertainty rendering; non-question rewrites can fall back to a world/scene line. This path should carry explicit provenance expectations before extraction. |
| forbidden generic phrase rewrite | `enforce_forbidden_generic_phrases` under `prefer_specificity` | text-mutating enforcement | Yes | Replaces forbidden stock sentences with scene-anchored specificity. It should remain behavior-frozen until sentence-level snapshots cover all replacement labels. |
| scene momentum / passive escalation | `enforce_topic_pressure_escalation`, `escalate_passive_scene`, `enforce_scene_momentum` under `prefer_scene_momentum` | fallback/provenance-relevant mutation | Yes | May append or replace text with topic-pressure, passive-pressure, or deterministic scene momentum beats. `enforce_scene_momentum` calls diegetic fallback rendering, so future split should isolate line selection and provenance. |
| social response structure handling | strict-social bypass via `strict_social_emission_will_apply` | legacy/ambiguous | No direct text mutation here | This function does not currently enforce social response structure directly. Instead, strict social turns bypass most text-mutating helpers so social exchange emission owns structure elsewhere. Keep this as an explicit bypass classification. |
| state update validation | `validate_gm_state_update` under `forbid_state_invention` | validation-only | No | Normalizes proposed state/update payloads. It belongs with validation, not player-facing text enforcement. |
| secret leak guard | `guard_gm_output` under `forbid_secret_leak` | fallback/provenance-relevant mutation | Yes | Sanitizes leaks and may replace player-facing text with bounded uncertainty text. Treat as provenance-relevant before any split. |
| topic progress commit | `_commit_topic_progress` after enforcement loop | metadata-only projection | No | Updates runtime/topic tracking from already-final reply text. It is not prose authorship, but ordering matters. |
| policy snapshot and applied marker | inline `out["response_policy"]` and metadata marker | metadata-only projection | No | Preserve existing metadata keys and value shapes. |

## Proposed Future Split Order

1. Extract metadata-only projection last-step helpers:
   `fallback_behavior_contract`, response-policy snapshot, applied marker, and
   topic progress commit. These should remain text-preserving.
2. Separate validation-only state/update normalization from player-facing text
   enforcement.
3. Group deterministic text-mutating enforcement that does not select fallback
   families: question resolution, NPC contract, and forbidden generic phrase
   rewrite.
4. Leave fallback/provenance-relevant mutation in place until each branch has
   explicit provenance assertions: validator voice fallback, secret leak guard,
   topic pressure/passive pressure, and scene momentum fallback.
5. Keep strict social response structure outside this function unless ownership
   changes. This function currently records only the bypass decision, not the
   social structure repair itself.

## Non-Goals For This Block

- Do not refactor `apply_response_policy_enforcement`.
- Do not change emitted prose.
- Do not change fallback selection behavior.
- Do not touch `final_emission_gate`.
