# BX Speaker Identity End-to-End Parity Discovery

Date: 2026-06-21  
Scope: discovery only; no runtime or test behavior changes

## Summary

Speaker identity has canonical authorities at routing and contract construction, but it is not represented by one end-to-end value. The runtime routes to a canonical actor ID, enforcement validates a prose-derived speaker label against a canonical ID/name contract, finalization carries text and enforcement metadata, and golden replay independently reconstructs `selected_speaker_id` from routing/state traces. Replay does not derive the selected speaker from final emitted prose.

The repository already has a measurable test-only **Speaker Contract Risk** model in `tests/helpers/speaker_contract_risk.py`. It compares pre-enforcement, post-enforcement, final emission, and replay checkpoints and scores divergence localization (`D`), speaker identity (`S`), text (`T`), and attribution evidence (`A`). The primary BX gap is not the absence of measurement primitives; it is the absence of protected cases that feed real routing aliases and role labels through the whole lifecycle, especially `guard` -> `guard_captain`.

Highest-risk finding: routing treats `guard` as an `address_roles` token for canonical scene actor `guard_captain`, while enforcement's core matching accepts canonical display/name forms and canonical-ID display forms, not the scene roster's role/alias map. A separate dialogue-plan lane permits only explicitly declared pregate labels. Replay then projects a canonical/state value without checking that the finalized prose resolves to that same actor. This allows text parity and routing parity to pass independently while speaker parity fails.

## Speaker lifecycle map

| lifecycle stage | authority and handoff | identity representation |
|---|---|---|
| Routing roster | `game.interaction_context.canonical_scene_addressable_roster` merges world NPCs and scene `addressables`; `resolve_authoritative_social_target` resolves explicit targets, vocatives, roles, continuity, and conservative substring matches | canonical actor row `id`; separate `name`, `address_roles`, and `aliases` |
| Routing result | `resolve_authoritative_social_target` returns `npc_id`, `npc_name`, `source`; social resolution and `social_turn_contract.reply_owner_actor_id` carry the chosen ID | canonical actor ID expected |
| Contract composition | `game.interaction_context._compose_speaker_selection_contract` consumes grounded `social.npc_id`; emits `primary_speaker_id`, `primary_speaker_name`, `primary_speaker_source`, `allowed_speaker_ids` and switch/continuity policy | canonical ID/name plus policy; roles/classes are dropped |
| Contract publication | `game.social_exchange_policy` writes `metadata.emission_debug.speaker_selection_contract`; `game.speaker_contract_enforcement.get_speaker_selection_contract` reads output metadata first, then resolution/trace copies | contract dict |
| Pregate alias declaration | `game.dialogue_social_plan._collect_declared_pregate_alias_fields` and plan validation carry `allowed_pregate_speaker_labels`, `writer_attribution_label`, `speaker_alias_resolution_source` | bounded labels with provenance, explicitly not inferred from prose |
| Emitted identity detection | `game.emitted_speaker_signature.detect_emitted_speaker_signature` parses `speaker_label`, `speaker_name`, explicit attribution/interruption and generic-fallback flags from text | prose label/name, not canonical ID |
| Enforcement | `game.final_emission_strict_social_stack.run_strict_social_stack` calls `enforce_emitted_speaker_with_contract`; validation compares the signature with canonical name/ID display; repairs locally rebind, canonically rewrite, or make output narrator-neutral | canonical ID remains metadata/state; text is rewritten to canonical display name when needed |
| Late finalization | strict-social stack continues through dialogue stripping and `run_gate_terminal_enforcement_pipeline`, then `game.final_emission_finalize.finalize_emission_output` sanitizes/packages final text and stamps FEM | final text plus enforcement reason; no authoritative final emitted canonical ID field |
| Post-emission state | `game.post_emission_speaker_adoption._unique_addressable_npc_id_for_label` may resolve final prose through roster names, IDs, roles/aliases and update/invalidate interlocutor state | canonical ID only when final label uniquely resolves |
| Replay projection | `tests.helpers.golden_replay_projection._resolve_selected_speaker_id` selects first from `social_contract_trace.final_reply_owner`, `reply_owner_actor_id`, `visible_grounded_speaker`; then snapshot latest target; then `resolution.social.npc_id` | one flattened `selected_speaker_id` plus `selected_speaker_source` |
| Golden transcript/comparison | `project_turn_observation` takes `final_text` from `snap.gm_text`; `tests.helpers.golden_replay` protects/compares `selected_speaker_id`, text/hash, speaker deltas, and speaker frequency | text and selected ID are parallel fields, not mutually validated by the replay projector |

### Representative line trace

The existing canonical-rewrite case in `artifacts/scenario_spine_validation/20260621T123556Z/frontier_gate_long_session/branch_social_inquiry/transcript.json` supplies a concrete trace for Tavern Runner:

1. **Route:** the social resolution supplies canonical `social.npc_id = "tavern_runner"`; `_compose_speaker_selection_contract` turns this into `primary_speaker_id = "tavern_runner"`, `primary_speaker_name = "Tavern Runner"`, and `allowed_speaker_ids = ["tavern_runner"]`.
2. **Enforcement handoff:** `run_strict_social_stack` passes normalized candidate text, output/resolution objects, world, and scene ID into `enforce_emitted_speaker_with_contract`. The artifact records `validation.canonical_speaker_id = "tavern_runner"` and `final_reason_code = "canonical_speaker_rewrite"`.
3. **Enforcement output:** `_apply_speaker_contract_repairs` synchronizes `eff_resolution.social.npc_id/name` and replaces/rebinds prose; post-validation records `speaker_label = "Tavern Runner"` and `speaker_contract_match`.
4. **Finalization handoff:** the returned text is assigned back to `out["player_facing_text"]`, passes post-speaker layers and `run_gate_terminal_enforcement_pipeline`, then enters `finalize_emission_output`.
5. **Replay projection:** API snapshot `gm_text` becomes golden `final_text`; `_resolve_selected_speaker_id` independently chooses a routing/state canonical ID and records its source.
6. **Golden value:** `project_turn_observation` emits parallel `selected_speaker_id` and `final_text`/`final_text_hash`; protected expectations and rerun comparisons consume these fields.

The exact missing handoff is between steps 4 and 5: production finalization does not stamp a canonical ID resolved from the final emitted line, and replay does not resolve one. BT test helpers can measure that join, but protected golden fixtures do not yet lock the `guard`/`guard_captain` case.

## Current speaker identity contract

- Canonical identity fields are `npc_id`, `target_actor_id`, `reply_owner_actor_id`, `primary_speaker_id`, `allowed_speaker_ids`, active/current interlocutor IDs, and replay `selected_speaker_id`.
- Display/prose fields are `npc_name`, `primary_speaker_name`, emitted `speaker_label`/`speaker_name`, and dialogue-plan writer labels.
- Routing source fields include `source`, `primary_speaker_source`, `routing_reason_code`, and replay `selected_speaker_source`.
- `address_roles` and roster `aliases` are separate from speaker ID. There is no persistent `speaker_class`, `speaker_type`, or `speaker_role` field carried across enforcement, finalization, and replay.
- Canonical IDs are expected in routing/social state, the speaker-selection contract, active interlocutor state, and replay `selected_speaker_id`.
- Aliases/roles are accepted while resolving player address against the canonical roster and during post-emission unique label resolution. Pregate writer aliases are accepted only when declared through the dialogue-plan fields with an allowed source.
- Enforcement validates before strict-social emission and post-validates after a repair. Late layers can still alter text afterward. There is no final production validation that resolves final prose back to a canonical ID immediately before emission or replay.

## Alias vs canonical handling

Routing is alias-aware and canonicalizing. `canonical_scene_addressable_roster` preserves actor `aliases` and `address_roles`; vocative/generic-role/declared-switch resolution returns the matching actor's canonical `id`. In the frontier-gate scene, `guard` is a role of canonical actor `guard_captain`, not its ID.

Enforcement is narrower. `_label_matches_primary_speaker` accepts `primary_speaker_name`, a display conversion of `primary_speaker_id`, and equivalent social resolution name/ID display. `_label_in_allowed_speaker_ids` applies the same canonical-display logic. It does not consume roster aliases or roles. The dialogue-social plan separately accepts declared labels via `writer_attribution_label` and `allowed_pregate_speaker_labels`; `speaker_alias_resolution_source` is mandatory and bounded. Tests in `test_block_u_finalize_stack_divergence.py` prove a canonical-only plan can reject an undeclared alias and that declaring the alias prevents the subtractive strip.

Post-emission adoption is broader again: `_label_matches_npc_entry` checks name, display, slug display, and reference tokens derived from roles/aliases, but only accepts a unique roster match. Thus the same label can be rejected by enforcement yet canonicalized after emission, depending on which lane sees it.

No inspected path intentionally converts a canonical ID back into an alias. Canonical rewrite converts the ID to a display name in prose. The risk is loss of the canonical join, not deliberate reverse aliasing.

## guard vs guard_captain handling

`data/scenes/frontier_gate.json` defines canonical addressable `guard_captain`, display name `Guard Captain`, and roles including `guard`, `watchman`, `sentry`, `guardsman`, and `captain`. Player address such as “guard” can therefore route to `guard_captain`. Elsewhere, fixtures and world data also define distinct canonical IDs such as `gate_guard`; `guard` is consequently not a globally unique class-to-ID mapping.

The repository contains an explicit historical mismatch example in `tests/test_backfill_bug_recurrence_history.py`: `selected_speaker_id` expected/observed values `guard` and `guard_captain`, classified as projection drift. Current Speaker Contract Risk tests also deliberately compare final emitted `runner` with replay `guard` and score the mismatch. These are synthetic metric/classifier controls, not a real frontier-gate end-to-end parity lock.

Failure behavior by stage:

- routing may correctly collapse role `guard` to canonical `guard_captain`;
- a raw `guard` ID from legacy/synthetic state can survive because replay does not canonicalize IDs;
- enforcement can treat prose label `guard` as a forbidden generic fallback or mismatch rather than a roster alias for `guard_captain`;
- post-emission resolution can map `guard` to `guard_captain` only when the roster match is unique;
- replay flattens whichever first source is populated and preserves it verbatim, so it can report `guard` even when final prose says `Guard Captain`, or `guard_captain` when final prose attributes a different actor.

## Existing test coverage

| concern | direct coverage | limitation |
|---|---|---|
| Alias/role routing to canonical actor | `test_vocative_direct_address_recovery.py`, `test_transcript_gauntlet_actor_addressing.py`, `test_directed_social_routing.py`, social-target authority suites | asserts routing/interlocutor state, not final/replay emitted identity parity |
| Speaker contract construction/grounding | `test_social_speaker_grounding.py`, `test_speaker_contract_enforcement.py` | mostly unit/path cases |
| Enforcement and repair | `test_speaker_contract_enforcement.py`, Block S/T relocation/equivalence tests | strong text/metadata parity; not real golden route-to-replay parity |
| Alias acceptance at pregate plan | `test_block_u_finalize_stack_divergence.py` Block W/Z cases | uses Ragged Stranger/Tavern Runner, not guard/captain ambiguity |
| Post-speaker finalization divergence | Block U tests and `post_speaker_finalize_probe.py` | test-only instrumentation; strict-social fixture focus |
| Final emitted vs replay identity | `test_speaker_contract_risk.py` BT2 tests | synthetic runner/guard cases; no live frontier-gate `guard` route |
| Replay projection and protected speaker field | `test_golden_replay_projection.py`, `test_golden_replay_structural_invariants.py`, `test_golden_replay_helper_contracts.py` | locks flattened selected ID, not canonical resolution or prose-to-ID parity |
| Golden/rerun speaker drift | `test_golden_replay.py`, `test_golden_replay_trend.py`, drift taxonomy/failure dashboard tests | speaker and text drift are compared independently |
| Post-emission canonical adoption | `test_post_emission_speaker_adoption.py`, stale interlocutor tests | state correction occurs after final text and is not replay authority in every payload |

No direct test was found that starts with a player `guard` alias/role, proves routing selected `guard_captain`, proves enforcement and final prose retain that actor, projects the same finalized turn, and asserts golden `selected_speaker_id == "guard_captain"` plus emitted-signature parity.

## Gaps / risks

1. **Alias emitted where canonical ID is expected:** replay sources are copied verbatim; no canonicalization occurs in `_resolve_selected_speaker_id`.
2. **Canonical-to-display join loss:** canonical rewrite emits a name, but the final record lacks a production canonical ID derived from that final prose.
3. **Guard/captain collapse:** broad role `guard` correctly resolves to `guard_captain` only in a specific unique roster; legacy `guard` or distinct `gate_guard` IDs make global normalization unsafe.
4. **Guard/captain split:** enforcement does not share routing's role/alias map, so it may reject `guard` even when routing canonically selected `guard_captain`.
5. **Speaker class lost:** `address_roles` do not cross contract composition; replay cannot distinguish whether `guard` was a role token, alias, display label, or canonical ID.
6. **Projection flattening:** replay selects one ID through precedence without retaining all candidate values or disagreement diagnostics.
7. **Text-only false confidence:** final text/hash can match while selected speaker differs; selected speaker can match while prose attribution differs.
8. **Normalization hiding drift:** text normalization/hashing does not canonicalize actor identity and can erase superficial label formatting differences; identity must be compared separately.
9. **Late mutation after validation:** speaker post-validation occurs before terminal/finalize layers; the test probe shows later layers can change speaker-bearing text.
10. **Fixture vocabulary drift:** tests use `guard`, `guard_captain`, and `gate_guard` as canonical-looking IDs in different scenarios. A global alias table would conflate distinct actors.

Existing Speaker Contract Risk is suitable for measuring BX: `S=40` for a resolved identity mismatch or final-emitted/replay mismatch, `S=20` for unresolved/ambiguous checkpoints, `T=25` for unexplained final/replay text mismatch, `D=15` for an unlocalized mismatch, and `A` increments for missing expected, enforcement, emitted-resolution, or replay-source attribution. Aggregate reports already support mean/max/bands and family rows.

## Recommended implementation blocks

### BX1 - Canonical speaker observation contract and guard matrix

Test-only first. Add real routing fixtures covering `guard` -> `guard_captain`, canonical `guard_captain`, distinct `gate_guard`, and ambiguous multiple-guard rosters. Feed their finalized outputs through `observe_final_to_replay_speaker_contract`. Assert every checkpoint, risk components, source evidence, and non-conflation. This is the recommended next block.

### BX2 - Final-emission canonical speaker stamp

After BX1 establishes behavior, add one canonical, provenance-bearing final speaker observation to FEM at the last safe point after late text mutation. It should distinguish `resolved`, `neutral`, `unattributed`, `ambiguous`, and `unresolved`; retain emitted label and resolution source; and never guess between multiple guards.

### BX3 - Replay parity projection

Project both routing-selected and final-emitted canonical speaker IDs with sources. Preserve legacy `selected_speaker_id` compatibility initially, add an explicit parity status/disagreement payload, and make protected replay expectations assert identity parity for social turns.

### BX4 - Alias policy convergence

Define one bounded canonicalization API over a supplied scene roster, then migrate enforcement and post-emission reads to it. Keep dialogue-plan declared pregate labels as provenance-bearing writer inputs, not a global alias registry. Do not map bare `guard` globally.

### BX5 - Golden regression and risk gate

Add protected frontier-gate turns and a family risk report. Require no increase in per-case risk band and fail on `guard`/`guard_captain`/`gate_guard` canonical drift even when normalized transcript text is unchanged.

## Files likely needed by ChatGPT

Primary implementation/read paths:

- `game/interaction_context.py`
- `game/dialogue_social_plan.py`
- `game/emitted_speaker_signature.py`
- `game/speaker_contract_enforcement.py`
- `game/final_emission_strict_social_stack.py`
- `game/final_emission_terminal_pipeline.py`
- `game/final_emission_finalize.py`
- `game/final_emission_meta.py`
- `game/post_emission_speaker_adoption.py`
- `game/api_turn_support.py`
- `tests/helpers/post_speaker_finalize_probe.py`
- `tests/helpers/speaker_contract_risk.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_fixtures.py`
- `data/scenes/frontier_gate.json`

Primary focused tests:

- `tests/test_speaker_contract_enforcement.py`
- `tests/test_speaker_contract_risk.py`
- `tests/test_block_u_finalize_stack_divergence.py`
- `tests/test_vocative_direct_address_recovery.py`
- `tests/test_transcript_gauntlet_actor_addressing.py`
- `tests/test_post_emission_speaker_adoption.py`
- `tests/test_golden_replay_projection.py`
- `tests/test_golden_replay_structural_invariants.py`

