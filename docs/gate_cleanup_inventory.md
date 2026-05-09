# Gate Cleanup Inventory

## Status Summary

**Gate layer status: maintenance-grade converged (Block AB closeout).** See `docs/gate_convergence_closeout.md` for the formal freeze, intentional residue list, protected invariants, and stop-point decision. Further cleanup is **optional** and should be bug/audit/perf-driven; broad refactors are not currently justified. This inventory remains the per-seam reference for Blocks A–AA work that delivered the convergence.

Gate appears **mostly converged with orchestration density**. The main `apply_final_emission_gate` path now treats many formerly semantic repair layers as validation/metadata-only and records `*_boundary_semantic_repair_disabled` markers. It is not fully semantically closed: active fallback selection, strict-social/speaker replacement, response-type fallback selection, opening fallback compatibility composition, interaction-continuity Gate-local repair residue (`validate_only=False` helper paths / malformed-bridge repair), and narrow referential substitution still create or substitute player-facing text inside the Gate path. **Block AB freezes this state as intentional residue rather than open work.**

## Gate Role

Current intended role: **Gate = deterministic legality/orchestration boundary, not semantic author**. It may package, sanitize, normalize, validate, reject, and replace with sealed deterministic fallback text when a hard legality contract fails. It should not invent missing narrative meaning, prose-polish awkward but legal output, repair answer substance, or re-author dialogue/content that belongs upstream.

## Active Text Mutation Inventory

| Symbol / call site | File | Mutation behavior | Classification | Current owner | Risk | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `sanitize_player_facing_output(..., sanitizer_boundary_mode="strip_only")` during strict-social suppression | `game/final_emission_gate.py` | Strip-only sanitizer result assigned to `player_facing_text` before normal gate flow | PACKAGING_ALLOWED | Gate sanitizer integration | Low | Used when strict-social coercion is suppressed for non-social narration. |
| `_apply_upstream_fallback_pregate_containment` | `game/final_emission_gate.py` | Restores selector snapshot when fallback provenance shows pre-gate drift | PACKAGING_ALLOWED | Gate provenance containment | Low | Preservation path, not authoring. |
| `build_final_strict_social_response` | `game/final_emission_gate.py` -> `game/social_exchange_emission.py` | Normalizes or replaces strict-social candidate with deterministic social emission/fallback | UPSTREAM_OWNER / LEGALITY_ALLOWED | `game.social_exchange_emission` | Medium | Active Gate call, but strict-social terminal shaping is explicitly owned by social emission. |
| `_enforce_dialogue_plan_invariant_on_strict_social` | `game/final_emission_gate.py` | May subtract dialogue when strict-social dialogue plan forbids it; can fail closed | LEGALITY_ALLOWED / SEMANTIC_DISALLOWED risk | Gate strict-social legality | Medium | Subtractive and guarded, but alters dialogue shape. |
| `_enforce_response_type_contract` for `answer` / `action_outcome` | `game/final_emission_gate.py` | Selects `upstream_prepared_emission.prepared_*_fallback_text` | UPSTREAM_OWNER | Upstream response repairs, Gate selector | Low | Gate selects prepared prose; authorship lives in `game/upstream_response_repairs.py`. |
| `_enforce_response_type_contract` for `dialogue` | `game/final_emission_gate.py` | Builds/minimal social fallback or strict-social ownership fallback | LEGALITY_ALLOWED / UPSTREAM_OWNER | Social emission / Gate selector | Medium | Deterministic fallback, but still active dialogue substitution. |
| `_enforce_response_type_contract` for `scene_opening` | `game/final_emission_gate.py` | Preserves valid opening, otherwise selects upstream opening fallback or compatibility composer | UPSTREAM_OWNER / COMPATIBILITY_RESIDUE | Upstream prepared opening fallback; Gate compatibility | Medium | Local re-invocation of opening composer remains as compatibility residue. |
| `_apply_answer_completeness_layer` | `game/final_emission_repairs.py` | Validation and metadata only; no answer repair | SEMANTIC_DISALLOWED fenced | Final emission repairs | Low | Records unsatisfied boundary state, no text change. |
| `_apply_answer_exposition_plan_layer` | `game/final_emission_repairs.py` | May move an existing required-answer sentence to front | PACKAGING_ALLOWED | Final emission repairs / Gate | Medium | Classified allowlisted as bounded non-inventive permutation, but still meaning-order adjacent. |
| `_apply_response_delta_layer` | `game/final_emission_repairs.py` | Validation and metadata only; no delta rewrite | SEMANTIC_DISALLOWED fenced | Final emission repairs | Low | No reorder/compression repair in Gate. |
| `_apply_social_response_structure_layer` | `game/final_emission_repairs.py` | Validation and metadata only; list-to-prose/dialogue repairs disabled | SEMANTIC_DISALLOWED fenced | Final emission repairs | Low | Tests lock no boundary social structure repair. |
| `_apply_narrative_authenticity_layer` | `game/final_emission_repairs.py` | Validation and metadata only; no narrative authenticity rewrite | SEMANTIC_DISALLOWED fenced | Final emission repairs / NA validator | Low | Records `semantic_repair_must_occur_upstream`. |
| `_apply_tone_escalation_layer` | `game/final_emission_gate.py` | Validation and metadata only; no tone rewrite | SEMANTIC_DISALLOWED fenced | Gate | Low | Narrow repair helper remains nearby but not used by the layer. |
| `_apply_narrative_authority_layer` | `game/final_emission_gate.py` | Validation and metadata only; no hidden-fact/outcome rewrite | SEMANTIC_DISALLOWED fenced | Gate | Low | Helper functions for sentence replacement remain dead/disabled in current layer. |
| `enforce_emitted_speaker_with_contract` / `_apply_speaker_contract_repairs` | `game/final_emission_gate.py` | Local speaker rebind, canonical strict-social rewrite, or neutral bridge line | SEMANTIC_DISALLOWED / LEGALITY_ALLOWED need review | Gate speaker contract | High | Active speaker/attribution repair can alter dialogue ownership and mutate effective resolution social fields. |
| `_apply_anti_railroading_layer` | `game/final_emission_gate.py` | Validation and metadata only; no route/prose rewrite | SEMANTIC_DISALLOWED fenced | Gate | Low | Narrow repair helpers remain nearby but layer disables rewrite. |
| `_apply_context_separation_layer` | `game/final_emission_gate.py` | Validation and metadata only; no context rewrite | SEMANTIC_DISALLOWED fenced | Gate | Low | Current path records failure only. |
| `_apply_player_facing_narration_purity_layer` | `game/final_emission_gate.py` | Validation and metadata only; no minimal purity repair | SEMANTIC_DISALLOWED fenced | Gate | Low | Tests assert no scaffold/coaching/UI label repair success flags. |
| `_apply_answer_shape_primacy_layer` | `game/final_emission_gate.py` | Validation and metadata only; no pressure/payload reordering | SEMANTIC_DISALLOWED fenced | Gate | Low | Former order repair now disabled. |
| `_apply_scene_state_anchor_layer` | `game/final_emission_gate.py` | Validation and metadata only; no anchor rewrite | SEMANTIC_DISALLOWED fenced | Gate | Low | Repair helpers remain unused in active layer. |
| `_apply_fast_fallback_neutral_composition_layer` | `game/final_emission_gate.py` | Validation and metadata only; malformed fallback composition repair disabled | SEMANTIC_DISALLOWED fenced | Gate | Low | Active composer helper exists but current layer returns original text. |
| `_apply_interaction_continuity_emission_step` | `game/final_emission_gate.py` | `apply_final_emission_gate` call sites use `validate_only=True` (metadata + validation only; `repair_interaction_continuity` not invoked). The helper still supports `validate_only=False` for malformed-speaker-bridge / strong-failure repair and strict-social sealed fallback (compatibility / tests). | `interaction_continuity_validation_attach` = PACKAGING; `interaction_continuity_repair` + `interaction_continuity_malformed_speaker_bridge` = SEMANTIC_DISALLOWED; `interaction_continuity_strict_social_fallback` = LEGALITY_ALLOWED | Gate + `game.interaction_continuity` | High | See **Block D**; final attach uses `_attach_interaction_continuity_validation` (validate-only). |
| `_apply_fallback_behavior_layer` / `repair_fallback_behavior` | `game/final_emission_repairs.py` | Strips meta fallback voice, fabricated authority, overcertain spans | PACKAGING_ALLOWED | Final emission repairs | Medium | Subtractive only; no template synthesis. |
| `_apply_visibility_enforcement` | `game/final_emission_gate.py` | Hard-replaces visibility-illegal text with sealed visibility-safe fallback | LEGALITY_ALLOWED | Gate visibility legality | Medium | Includes multiple fallback selectors, some context-grounded. |
| `_apply_first_mention_enforcement` | `game/final_emission_gate.py` | Hard-replaces first-mention-illegal text with sealed fallback | LEGALITY_ALLOWED | Gate visibility/first-mention legality | Medium | Replacement can be context-composed via visibility-safe fallback candidates. |
| `_apply_referential_clarity_enforcement` strict-social local substitution | `game/final_emission_gate.py` | Replaces one ambiguous pronoun with grounded speaker phrase | SEMANTIC_DISALLOWED / LEGALITY_ALLOWED need review | Gate referential clarity | High | Active semantic substitution, tightly guarded and revalidated. |
| `_apply_referential_clarity_enforcement` fallback path | `game/final_emission_gate.py` | Hard-replaces referentially unclear text with sealed fallback | LEGALITY_ALLOWED | Gate referential clarity | Medium | Safer than substitution, but still authored replacement. |
| `_apply_referent_clarity_pre_finalize` | `game/final_emission_gate.py` | Calls referent layer with `allow_semantic_text_repair=False`; assigns same text | SEMANTIC_DISALLOWED fenced | Gate / final emission repairs | Low | Direct assignment remains but text repair disabled. |
| `_apply_acceptance_quality_n4_floor_seam` pass path | `game/final_emission_gate.py` -> `game/acceptance_quality.py` | Normalizes and may accept subtractively repaired text from canonical N4 seam | PACKAGING_ALLOWED / SEMANTIC_DISALLOWED need review | Acceptance quality | Medium | Terminal sentence drop can change meaning; documented as bounded subtractive N4 behavior. |
| `_apply_acceptance_quality_n4_floor_seam` fail path | `game/final_emission_gate.py` | Replaces failed N4 candidate with sealed strict-social or scene fallback | LEGALITY_ALLOWED | Acceptance quality + Gate selector | Medium | Tests lock sealed replacement and no invention. |
| Non-strict replace path in `apply_final_emission_gate` | `game/final_emission_gate.py` | Replaces failed candidate with selected terminal sealed fallback | LEGALITY_ALLOWED | Gate | Medium | Central hard-replace path. |
| `_finalize_emission_output` | `game/final_emission_gate.py` | HTML/text sanitizer, appended global stock strip, whitespace assignment, sidecar packaging | PACKAGING_ALLOWED | Gate finalizer | Low | Sentence decompression / fragment repair / micro smoothing are explicitly disabled. |
| `_finalize_upstream_fallback_overwrite_containment` | `game/final_emission_gate.py` | Restores selector snapshot during finalize when provenance mismatch proves overwrite | PACKAGING_ALLOWED | Gate provenance containment | Low | Preservation path with sanitizer-only cleanup. |
| `_reassert_scene_opening_accepted_candidate` | `game/final_emission_gate.py` | Restores accepted opening candidate if later phase drifted | PACKAGING_ALLOWED | Gate opening preservation | Low | Protects accepted upstream/GPT candidate from later mutation. |
| `append_strict_social_spoken_refinement_cashout_if_needed` | `game/upstream_response_repairs.py` | Appends spoken refinement tail to `player_facing_text` upstream | UPSTREAM_OWNER | Upstream response repairs | Medium | Not Gate behavior, but active after realization before Gate sees candidate. |

## Orchestration Inventory

| Phase | Reads | Writes | Text mutation? | Order-sensitive? | Existing test coverage | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Bundle materialization / upstream prepared merge | GM output, session, response policy, prompt context | `response_policy`, `_gate_turn_packet_cache`, `upstream_prepared_emission`, `upstream_prepared_opening_fallback` | No direct candidate mutation | Yes | `tests/test_final_emission_gate.py`, upstream repair suites | Routing and compatibility setup. |
| Strict-social route resolution / suppression | Resolution, session, world, scene id, merged player prompt | route flags, possible sanitized `player_facing_text` | Yes, strip-only on suppression | Yes | Strict-social gate tests | Legality/routing, not semantic rescue. |
| Gate entry / fallback provenance containment | Fallback provenance metadata | `player_facing_text`, provenance metadata, snapshots | Yes | Yes | Fallback provenance/gate tests | Packaging preservation. |
| Strict-social candidate normalization | Pre-gate text, effective resolution, tags, session/world | `text`, strict-social details | Yes | Yes | Strict-social gate/social exchange tests | Social emission owner. |
| Response-type contract | Candidate text, response policy, upstream prepared emissions, opening fallback snapshot | `text`, `response_type_debug` | Yes | Yes | `tests/test_final_emission_gate.py` response-type/opening tests | Selector seam for upstream prose. |
| Answer completeness | Text, response policy, resolution | FEM fields, extra rejection reasons | No | Yes | Boundary no-semantic tests and gate order tests | Validation-only. |
| Answer exposition plan | Text, answer plan | Text and AEP meta | Yes, bounded reorder only | Yes | `tests/test_final_emission_gate.py` | Only moves existing sentence. |
| Response delta | Text, response policy | FEM fields, extra rejection reasons | No | Yes | Boundary no-semantic tests | Validation-only. |
| Social response structure | Text, response policy | FEM fields | No | Yes | `tests/test_final_emission_gate.py`, no-semantic tests | Must run after response delta and before tone. |
| Narrative authenticity | Text, NA contract | FEM fields, rejection reason | No | Yes | Boundary no-semantic tests | Validation-only. |
| Tone escalation | Text, tone contract | FEM/debug flags | No | Yes | `tests/test_final_emission_gate.py` | Validation-only. |
| Narrative authority | Text, narrative authority contract | FEM/debug flags | No | Yes | Gate tests | Validation-only. |
| Speaker contract enforcement | Text, speaker selection contract, effective resolution | Text, speaker enforcement debug, effective/resolution social fields | Yes | Yes | Speaker/continuity tests in `tests/test_final_emission_gate.py` | Active semantic-risk seam. |
| Anti-railroading | Text, anti-railroading contract | FEM/debug flags | No | Yes | Gate tests | Validation-only. |
| Context separation | Text, context contract | FEM/debug flags | No | Yes | Gate tests | Validation-only. |
| Narration purity | Text, purity contract | FEM/debug flags | No | Yes | Gate purity tests | Validation-only. |
| Answer shape primacy | Text, player prompt, resolution | FEM/debug flags, rejection reason | No | Yes | Gate ASP tests | Validation-only. |
| Scene-state anchor | Text, shipped scene anchor contract | FEM/debug flags | No | Yes | Scene-state anchor gate tests | Validation-only. |
| Fast-fallback neutral composition | Text, scene/session/tags | FEM/debug flags | No | Yes | Fast fallback gate tests | Validation-only. |
| Interaction continuity pre-final step | Text, IC contract, speaker bridge | In live gate: metadata/validation only (`validate_only=True`); repair-capable behavior only inside `_apply_interaction_continuity_emission_step(validate_only=False)` (residue) | Yes in helper when `validate_only=False` | Yes | `tests/test_final_emission_gate.py` Block D + IC tests | Live orchestration is validate-only; repair remains for compatibility. |
| Fallback behavior | Text, fallback behavior contract | Text, FEM/debug flags | Yes, subtractive strip only | Yes | Fallback behavior/gate tests | Packaging cleanup only, no synthesis. |
| Candidate acceptance / replace decision | Accumulated reasons, candidate validation flags | FEM route, tags, debug notes, text for replace path | Yes on replace | Yes | Sealed branch/order tests | Core legality branch. |
| Visibility / first mention / referential clarity | Text, visibility contracts, scene/world/session | Text, tags, FEM | Yes | Yes | Visibility, first mention, referential clarity tests | Hard replacement plus local pronoun substitution seam. |
| Narrative mode output | Text, shipped narrative mode contract | FEM trace and possible strict-social fallback | Sometimes | Yes | Narrative mode output tests | Non-strict failure contributes reasons; strict-social can hard replace. |
| Acceptance quality N4 | Text, shipped narrative plan/AQ contract | Text, tags, FEM | Yes | Yes | N4 tests and order tests | Canonical N4 seam, may repair subtractively or sealed-replace. |
| Interaction continuity validation attach | Final text, IC contract | Metadata/FEM | No | Yes | `test_acceptance_quality_n4_runs_before_interaction_continuity_attachment` and IC tests | Metadata-only attach. |
| Finalize / public projection | Final text, metadata, provenance | Sanitized/stripped text, FEM, public/debug sidecar | Yes, packaging only | Yes | Finalizer/global visibility stock tests | Last-mile packaging and public payload projection. |

## Semantic-Risk Seams

| Seam | Why risky | Current guard/test | Recommended next action |
| --- | --- | --- | --- |
| Speaker contract repair (`local_rebind`, `canonical_rewrite`, `narrator_neutral`) | Changes attribution/dialogue ownership and can mutate effective resolution social fields | Speaker and continuity-adjacent tests in `tests/test_final_emission_gate.py` | Block B candidate: inventory and fence as legality-only replacement vs upstream speaker realization, without moving behavior yet. |
| Strict-social local pronoun substitution | Substitutes referent text inside final dialogue | Revalidation against referential clarity, first mention, visibility; referent boundary tests | Keep fenced; decide whether this belongs to social emission or referent upstream. |
| Interaction-continuity repair path | `validate_only=False` can call `repair_interaction_continuity` or strict-social sealed fallback; live `apply_final_emission_gate` does not use that path | Block D tests; `test_apply_final_emission_gate_validate_only_ic_never_calls_repair_interaction_continuity` | Future move: `game.interaction_continuity` or upstream social/continuity realization—not packaging in taxonomy. |
| Opening fallback compatibility composer | Gate can compose opening prose when upstream prepared snapshot is absent | Opening deterministic fallback and selector tests | Convert later to fail-closed or upstream-only once compatibility callers are known. |
| Response-type dialogue fallback selection | Gate creates minimal/ownership social dialogue fallback | Strict-social tests and response-type tests | Keep as legality fallback for now; document social emission ownership. |
| N4 subtractive repair | Terminal sentence drop can remove meaning, even when bounded | N4 canonical seam tests and no-invention tests | Treat as acceptance-quality owned; consider explicit taxonomy note for subtractive N4. |
| AEP answer sentence reorder | Reorders answer/exposition content | AEP convergence tests | Keep narrow; future review whether this should become upstream-only. |
| Visibility / first-mention / referential hard replacements | Replace user-visible text with fallback that may be context-composed | Visibility/first mention/referential tests | Keep as legality fallback; ensure selectors remain snapshot-tested. |
| Fallback behavior strip of overcertain claims | Removes clauses/spans from fallback narration | Fallback behavior tests; mutation allowlist | Keep as packaging/subtractive; avoid adding replacement synthesis. |
| Disabled repair helper residue near layers | Helpers for tone/NA/AR/context/scene-anchor/fast-fallback remain near active code | Boundary no-semantic tests | Mark as compatibility/dead residue before removal. |

## Compatibility Residue

| Residue | Why retained | Risk level | Suggested future handling |
| --- | --- | --- | --- |
| `_gm_probe_for_answer_pressure_contracts` alias | Older repair/gate imports may still use previous helper name | Safe fenced residue | Remove after import scan and deprecation window. |
| `_default_narrative_authenticity_meta` / `_merge_narrative_authenticity_meta` wrappers | Preserve older private imports while schema ownership moved to `final_emission_meta` | Safe fenced residue | Probably removable later after tests stop importing private wrappers. |
| Local opening composer at Gate (`_deterministic_opening_fallback_text_and_meta` when no usable prepared snapshot) | Gate compatibility when `upstream_prepared_opening_fallback` absent/unusable | Dangerous residue requiring tests first | Upstream-prepared attachment or fail-closed policy; `compose_opening_fallback_compatibility_local` remains SEMANTIC_DISALLOWED. |
| `_opening_scene_safe_fallback_tuple` local re-invocation path | Hard-replace selector prefers upstream snapshot but still composes locally on absence | Dangerous residue requiring tests first | Block B should map callers and add/adjust docs/tests before behavior change. |
| `repair_fallback_behavior` public helper | Downstream suites may call black-box repair; live path now strip-only | Safe fenced residue | Keep until fallback behavior direct-owner suite confirms no synthesis dependency. |
| Disabled narrow repair helpers for tone/narrative authority/anti-railroading/context/scene anchor/fast fallback | Historical repair helpers remain near validation layers | Probably removable later | Remove only with import scan and targeted no-semantic tests. |
| `enforce_emitted_speaker_with_contract` mutating `eff_resolution` / syncing to `resolution` | Legacy strict-social/speaker repair requires state alignment | Dangerous residue requiring tests first | Audit ownership; likely move to social/speaker upstream later. |
| Top-level / legacy FEM fallback reads in `game/final_emission_meta.py` | Older mixed dicts and fixtures still use top-level metadata | Safe fenced residue | Keep until fixtures and callers use nested FEM consistently. |
| Private sealed selector helpers importable in tests | Regression anchors for branch/order selectors | Safe fenced residue | Keep while gate remains dense; remove only after API-level replacement. |
| Local upstream fallback overwrite containment | Protects fallback selector text from later drift | Unclear | Keep; later decide if provenance system can own containment outside Gate. |

## Test Ownership Map

| Invariant | Direct owner test | Neighbor/consumer tests | Gaps |
| --- | --- | --- | --- |
| Mutation taxonomy | `tests/test_final_emission_boundary_no_semantic_repair.py`; boundary contract assertions in gate tests | `docs/final_emission_boundary_audit.md` references | No single concise test maps every active mutation call site. |
| No semantic boundary repair | `tests/test_final_emission_boundary_no_semantic_repair.py` | Late sections of `tests/test_final_emission_gate.py` for SRS, response delta, referent, N4 | Speaker and interaction-continuity active repairs remain outside the no-semantic umbrella. |
| `apply_final_emission_gate` orchestration order | `tests/test_final_emission_gate.py` header-owned suite, order tests near response delta/SRS/tone, N4 before IC, visibility before N4 | Social exchange and transcript consumers | No exhaustive whole-pipeline order snapshot; tests are targeted. |
| Final emission meta/provenance | `tests/test_final_emission_gate.py`; `game/final_emission_meta.py` consumer tests where present | Stage diff/provenance/fallback suites | Compatibility fallback reads are broad. |
| Sealed fallback replacement | `tests/test_final_emission_gate.py` sealed selector/order snapshots and N4 replace tests | Boundary no-semantic N4 hard-illegal test | Selector composition remains dense. |
| Acceptance-quality seam | `tests/test_final_emission_gate.py` N4 block | `tests/test_final_emission_boundary_no_semantic_repair.py` | None obvious for current scope. |
| Visibility replacement | `tests/test_final_emission_gate.py` visibility and sealed branch tests | Narration visibility tests | Local fallback composition ownership remains mixed. |
| Strict-social gate behavior | `tests/test_final_emission_gate.py`; `tests/test_social_exchange_emission.py` for social owner behavior | Retry/social prompt tests | Gate still calls social owner directly. |
| Referent pre-finalize behavior | `tests/test_final_emission_gate.py::test_referent_clarity_pre_finalize...`; no-semantic referent test | N5 boundary regression tests | Active strict-social local pronoun substitution needs explicit taxonomy classification. |
| Scene-state anchor validation | `tests/test_final_emission_gate.py` scene anchor tests; scene-state anchoring direct tests | Validation layer separation docs | Disabled repair helpers not separately documented in tests. |
| Interaction continuity validation | `tests/test_final_emission_gate.py` IC attach/repair/bridge tests + Block D taxonomy | `tests/test_interaction_continuity_validation.py`, `tests/test_interaction_continuity_repair.py` | Validate-only orchestration vs repair-helper residue documented in Block D. |

## Block B — Speaker / Strict-Social Referential Fencing

| Seam | Active behavior | Classification | Why it is tolerated | Required guard/test | Future owner candidate |
| --- | --- | --- | --- | --- | --- |
| Missing speaker contract path | `enforce_emitted_speaker_with_contract` validates with the empty contract and returns original text without a repair payload | LEGALITY_ALLOWED sealed/bounded correction: no-op validation | Legacy and mixed fixtures may lack a shipped speaker contract; Gate must not invent stricter policy | `test_apply_final_emission_gate_strict_social_contract_missing_skips_tightening` asserts no `repair` payload and no tightening | Speaker-selection contract owner / upstream social planning |
| Local speaker rebind | `_apply_speaker_contract_repairs` replaces an opening wrong speaker label with canonical speaker name while preserving quoted content | SEMANTIC_DISALLOWED but temporarily tolerated | Prevents continuity-locked strict-social dialogue from attributing the live response to the wrong speaker; behavior predates this fencing pass | `test_block_b_speaker_local_rebind_is_metadata_visible_and_sync_traceable` asserts `repair.local_rebind_applied` and boundary classification is not packaging | Upstream strict-social realization or speaker-selection owner |
| Canonical speaker rewrite | `_apply_speaker_contract_repairs` rewrites to `strict_social_ownership_terminal_fallback` after speaker mismatch / generic fallback speaker | UPSTREAM_OWNER semantic repair still invoked from Gate | Used as a deterministic legality fallback for invalid strict-social speaker ownership, but it authors replacement dialogue shape | Boundary taxonomy classifies `speaker_contract_canonical_rewrite` as `SEMANTIC_DISALLOWED`; existing strict-social speaker tests cover emitted behavior | `game.social_exchange_emission` / speaker-selection owner |
| Narrator neutral bridge | `_apply_speaker_contract_repairs` emits `neutral_reply_speaker_grounding_bridge_line` and marks `reply_speaker_grounding_neutral_bridge` | UPSTREAM_OWNER semantic repair still invoked from Gate | Avoids illegal invented dialogue ownership when no allowed speaker exists; replacement prose is deterministic but semantic | Boundary taxonomy classifies `speaker_contract_neutral_bridge` as `SEMANTIC_DISALLOWED`; speaker enforcement payload records `narrator_neutral_applied` when used | Upstream social emission / interaction continuity owner |
| Strict-social pronoun substitution | `_try_strict_social_local_pronoun_substitution_repair` replaces one ambiguous pronoun with grounded interlocutor phrase after revalidation | SEMANTIC_DISALLOWED but temporarily tolerated (see **Block E** for full ownership fencing) | Narrowly avoids hard fallback when strict-social answer text is otherwise valid and the only issue is one grounded speaker pronoun | `test_block_b_strict_social_pronoun_substitution_records_explicit_metadata` asserts attempted/applied/token/replacement metadata and non-packaging taxonomy; Block E adds non-strict / non-dialogue / suppressed-turn guards | Referent tracking upstream or strict-social realization |
| Effective resolution social sync | `_sync_eff_social_to_resolution` copies repaired social speaker fields from effective resolution back to caller resolution | COMPATIBILITY_RESIDUE / SEMANTIC_DISALLOWED | Keeps legacy caller-visible resolution metadata aligned after speaker repair; not a text mutation but accompanies semantic speaker correction | `test_block_b_speaker_local_rebind_is_metadata_visible_and_sync_traceable` asserts sync result is paired with visible speaker repair metadata; taxonomy classifies `effective_social_resolution_sync` as `SEMANTIC_DISALLOWED` | Upstream effective-resolution materialization / social route owner |

## Block C — Opening Fallback Compatibility Fencing

| Seam | Active behavior | Classification | Why tolerated | Required guard/test | Future owner candidate |
| --- | --- | --- | --- | --- | --- |
| Upstream prepared opening fallback selector | `_opening_scene_safe_fallback_tuple` and `_enforce_response_type_contract` prefer a usable `upstream_prepared_opening_fallback` payload and copy its prepared text/meta into the emitted path | LEGALITY_ALLOWED selector / UPSTREAM_OWNER prose; taxonomy kind `select_upstream_prepared_opening_fallback` | Gate may select prepared opening fallback for a failed opening candidate, but it is not the opening prose author; authorship remains `OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED` | `test_opening_scene_safe_fallback_tuple_prefers_upstream_prepared_payload`, `test_opening_failure_recovers_via_upstream_prepared_payload_when_present`, `test_block_ai_opening_upstream_prepared_snapshot_remains_preferred_over_compatibility_local`, and `test_block_c_opening_fallback_mutation_kinds_are_fenced_by_ownership` | `game.upstream_response_repairs` / opening realization preparation |
| Local compatibility opening composition | The compatibility branch in `_opening_scene_safe_fallback_tuple` / `_enforce_response_type_contract` calls `_deterministic_opening_fallback_text_and_meta` when the upstream payload is absent or structurally unusable | COMPATIBILITY_RESIDUE and SEMANTIC_DISALLOWED if treated as a final-boundary mutation; taxonomy kind `compose_opening_fallback_compatibility_local` is not packaging | Legacy callers may reach the Gate without an attached prepared payload; keeping the path avoids changing emitted prose while making the residue observable through `opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` | `test_opening_scene_safe_fallback_tuple_exact_text_and_classification_snapshot`, `test_opening_failure_falls_back_to_gate_local_when_upstream_payload_incomplete`, `test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome`, and `test_block_c_opening_fallback_mutation_kinds_are_fenced_by_ownership` | Caller audit, then upstream prepared opening fallback attachment or fail-closed policy |
| Accepted scene-opening candidate restoration | `_reassert_scene_opening_accepted_candidate` restores a candidate already accepted by the scene-opening response-type path if a later boundary phase drifts back to stale text | PACKAGING_ALLOWED preservation; taxonomy kind `restore_accepted_scene_opening_candidate` | It preserves selected candidate text rather than composing new opening prose, and records candidate/emitted preview metadata for traceability | `test_scene_opening_accepted_candidate_promotes_over_short_stale_player_text` and `test_block_c_opening_fallback_mutation_kinds_are_fenced_by_ownership` | Gate finalizer / response-type selector containment |
| Opening-mode terminal sealed replace selector | `_select_non_strict_replace_path_terminal_sealed_fallback` routes opening-mode hard replacement to `_opening_scene_safe_fallback_tuple` before generic non-strict fallbacks | LEGALITY_ALLOWED selector, with authorship decided by the selected prepared-vs-compatibility branch | Opening-mode terminal replacement must stay opening-classified and first-impression-safe; future deletion of the compatibility branch requires caller audit, not casual removal | Selector/order snapshots including `test_selector_snapshot_opening_rt_repair_vs_generic_terminal_families` plus upstream-vs-compatibility tests above | Gate sealed replacement selector, then upstream opening fallback owner |

## Block D — Interaction Continuity Repair Fencing

**Conclusions**

- Gate may attach interaction-continuity validation metadata (`interaction_continuity_validation_attach`).
- Gate-local semantic continuity repair remains compatibility/legacy residue inside `_apply_interaction_continuity_emission_step` when `validate_only=False` (not used by live `apply_final_emission_gate` orchestration).
- `validate_only=True` paths are preferred and remain metadata-only with respect to prose repair (`repair_interaction_continuity` not invoked).
- `validate_only=False` paths require explicit visibility in metadata/tests (repair payloads, bridge markers, enforced flag).
- Future movement should likely target `game.interaction_continuity` or upstream realization/social planning, not `final_emission_gate`, without deleting malformed-speaker-bridge handling.

| Seam | Active behavior | Classification | Why tolerated | Required guard/test | Future owner candidate |
| --- | --- | --- | --- | --- | --- |
| IC validation attach (live gate) | `_attach_interaction_continuity_validation`, strict-social mid-pipeline IC pass, and non-strict pre-candidate IC pass call `_apply_interaction_continuity_emission_step(..., validate_only=True)` | PACKAGING_ALLOWED / legality metadata only; taxonomy `interaction_continuity_validation_attach` | Orchestration must surface continuity diagnostics without invoking semantic repair in live gate flow | `assert_final_emission_mutation_allowed("interaction_continuity_validation_attach", ...)` at attach sites; `test_attach_interaction_continuity_validation_populates_debug_and_final_meta`; `test_apply_final_emission_gate_validate_only_ic_never_calls_repair_interaction_continuity` | Gate orchestration (stable) |
| Malformed speaker-attribution bridge | `_maybe_apply_speaker_binding_bridge_to_payload` augments validation when speaker-binding indicates malformed attribution under continuity | SEMANTIC_DISALLOWED compatibility residue; taxonomy `interaction_continuity_malformed_speaker_bridge` | Keeps continuity checks aligned with speaker-contract mismatch signals without silently accepting illegal attribution | `test_apply_interaction_continuity_step_records_bridge_metadata_when_bridge_fires`; bridge metadata non-packaging in `test_block_d_interaction_continuity_mutation_kinds_are_fenced_by_ownership` | `game.interaction_continuity` bridge owner |
| `repair_interaction_continuity` text change | When `validate_only=False` and validation fails, gate invokes `repair_interaction_continuity` and may adopt repaired text | SEMANTIC_DISALLOWED; taxonomy `interaction_continuity_repair` | Historical helper tests and narrow malformed-bridge recovery; not packaging | `test_apply_interaction_continuity_step_repairs_malformed_bridge_case_before_enforcement`; metadata `interaction_continuity_repair` / `repair_type` | `game.interaction_continuity` / upstream continuity realization |
| Strict-social continuity hard fallback | After enforced continuity failure with `strict_social_path=True`, substitute `minimal_social_emergency_fallback_line(strict_fallback_resolution)` | LEGALITY_ALLOWED sealed deterministic fallback; taxonomy `interaction_continuity_strict_social_fallback` | Terminal-safe minimal social line when continuity cannot be repaired under strict-social routing | `assert_final_emission_mutation_allowed` on fallback branch; `test_block_d_strict_social_continuity_hard_fallback_is_legality_sealed_not_packaging` | `game.social_exchange_emission` / strict-social planner |

## Block E — Strict-Social Referential Substitution Fencing

**Conclusions**

- Local pronoun substitution (`_try_strict_social_local_pronoun_substitution_repair`) is **SEMANTIC_DISALLOWED** at the final emission boundary (taxonomy kind `strict_social_referential_substitution`; mirrored in `game/final_emission_boundary_contract.py`).
- It is temporarily tolerated only as a **narrow strict-social compatibility seam**: it is the only Gate-local path that can substitute referent text inside an otherwise-valid strict-social dialogue line instead of hard-replacing with a sealed fallback.
- It is **not packaging**: replacement of an ambiguous pronoun with a grounded interlocutor phrase changes meaning surface (referent specification), even though the substitution is conservative, deterministic, and re-validated.
- Substitution must remain **metadata-visible**: every attempted/applied/rejected pass must surface `referential_clarity_local_substitution_*` and `referential_clarity_fallback_*` keys; `assert_final_emission_mutation_allowed("strict_social_referential_substitution", ...)` must never run at the boundary.
- The seam **never runs on non-strict-social paths**: the `_apply_referential_clarity_enforcement` gate guards on `strict_social_active and response_type_required == "dialogue" and not strict_social_suppressed_non_social_turn`. Even if the helper were called directly with a non-strict configuration, internal guards (single-id violation alignment, `eff_resolution.social.npc_id` match, visible person-like interlocutor) fail-closed.
- Future owner is upstream **referent tracking**, **upstream strict-social realization**, or **social emission**, not the Gate finalizer. Do not relocate behavior in this block — mirror Block D: honest taxonomy + observability first.

**Call site map**

- `_try_strict_social_local_pronoun_substitution_repair` is invoked from exactly one site: `game/final_emission_gate.py::_apply_referential_clarity_enforcement` (the strict-social-dialogue branch after referential-clarity validation has failed).
- `_apply_referential_clarity_enforcement` itself is reached from two sites inside `_apply_first_mention_enforcement` (visibility/first-mention OK case and post-replacement re-validation case). `_apply_first_mention_enforcement` is reached from `_apply_visibility_enforcement`, which is invoked from four `apply_final_emission_gate` paths (strict-social validate path, strict-social replace path, strict-social pre-finalize path, non-strict path).
- The substitution helper is therefore **only** reachable when `strict_social_active=True`, `response_type_required=="dialogue"`, and the suppressed-non-social-turn flag is False. Non-strict paths cannot silently use it.

**Substitution preconditions (gate guard + helper guards)**

| Layer | Required condition |
| --- | --- |
| Outer gate (`_apply_referential_clarity_enforcement`) | Referential clarity validation failed; `strict_social_active=True`; `response_type_required=="dialogue"`; not `strict_social_suppressed_non_social_turn` |
| Helper precondition | Exactly one violation, kind `ambiguous_entity_reference`, ≤1 candidate entity id |
| Helper precondition | Single candidate id matches `active_interlocutor` |
| Helper precondition | Token (lower-cased) in `_LOCAL_STRICT_SOCIAL_PRONOUN_SUBSTITUTION_TOKENS` |
| Helper precondition | Single visibility-sentence; single regex match for the token |
| Helper precondition | `eff_resolution.social.npc_id` equals `active_interlocutor` |
| Helper precondition | Active interlocutor is visible person-like (per narration visibility contract) |
| Helper precondition | Strict-social dialogue payload is substantive (length ≥28 chars, no `starts to answer`, not route-illegal global stock fallback, has clue/refusal/direction signal) |
| Helper post-validation | Re-runs `validate_player_facing_referential_clarity`, `validate_player_facing_first_mentions`, `validate_player_facing_visibility` on the repaired text — all three must pass. Any failure flips `referential_clarity_fallback_after_failed_local_repair=True` and the helper returns `None` |

**Metadata contract (must remain visible)**

- `referential_clarity_local_substitution_attempted`
- `referential_clarity_local_substitution_applied`
- `referential_clarity_local_substitution_token`
- `referential_clarity_local_substitution_replacement`
- `referential_clarity_fallback_avoided`
- `referential_clarity_fallback_after_failed_local_repair`
- Tag (when applied): `referential_clarity_local_substitution`
- Tags (on hard-replace fallback): `final_emission_gate_replaced`, `referential_clarity_enforcement_replaced`, `referential_clarity_violation:<kind>`

**Hard-replace decision**

When the gate guard is *not* satisfied (non-strict, non-dialogue, suppressed turn) or the helper rejects/post-validation fails, `_apply_referential_clarity_enforcement` falls through to `_standard_visibility_safe_fallback` and asserts the **legality** kind `hard_replace_illegal_output_with_sealed_fallback`. The substitution kind itself is never asserted at the boundary.

| Seam | Active behavior | Classification | Why tolerated | Required guard/test | Future owner candidate |
| --- | --- | --- | --- | --- | --- |
| `_try_strict_social_local_pronoun_substitution_repair` (single call site in `_apply_referential_clarity_enforcement`) | Replaces one ambiguous pronoun (e.g. `she`/`her`) with grounded interlocutor phrase (`The Tavern Runner`) inside a single-sentence strict-social dialogue line, after revalidation against referential clarity, first mention, and visibility | SEMANTIC_DISALLOWED (taxonomy kind `strict_social_referential_substitution`); tolerated narrow strict-social compatibility seam | Avoids hard-replacing an otherwise-valid strict-social dialogue line whose only defect is one grounded speaker pronoun; conservative single-token substitution preserves the upstream-authored payload | `test_block_e_strict_social_referential_substitution_*` (taxonomy + non-strict guard + suppressed-turn guard + non-dialogue guard + post-validation rejection); existing `test_block_b_strict_social_pronoun_substitution_records_explicit_metadata`; existing `tests/test_referential_clarity_strict_social_local_repair.py` direct-owner suite | Upstream referent tracking / strict-social realization / `game.social_exchange_emission` |
| `_apply_referential_clarity_enforcement` strict-social branch (gate guard around helper) | Guards `_try_strict_social_local_pronoun_substitution_repair` invocation on `strict_social_active and response_type_required == "dialogue" and not strict_social_suppressed_non_social_turn`; otherwise proceeds to sealed fallback | SEMANTIC_DISALLOWED gate (kind = the helper above); selector itself is not separately assertable at the boundary | Restricts substitution to the only emission shape where it can be honestly grounded to a strict-social interlocutor | `test_block_e_strict_social_referential_substitution_skipped_on_non_strict_path`; `test_block_e_strict_social_referential_substitution_skipped_on_non_dialogue_response_type`; `test_block_e_strict_social_referential_substitution_skipped_when_suppressed_non_social_turn` | Upstream strict-social planner / referent tracking |
| `_apply_referential_clarity_enforcement` fallback path | Hard-replaces referentially unclear text via `_standard_visibility_safe_fallback` and asserts `hard_replace_illegal_output_with_sealed_fallback` | LEGALITY_ALLOWED sealed fallback; never asserts the substitution kind | This is the only legality-honest exit when substitution is unavailable or rejected | Existing referential clarity replace tests in `tests/test_final_emission_visibility.py` and `tests/test_final_emission_gate.py`; `test_assert_sites_never_use_semantic_disallowed_kinds` (boundary-contract contract enforcement) | Gate visibility legality (stable) |

## Block F — Speaker Contract Repair Relocation Prep

**Conclusions**

- Speaker contract repair remains **active semantic mutation inside Gate** (`enforce_emitted_speaker_with_contract` → `_apply_speaker_contract_repairs`). It is **not** packaging; taxonomy kinds `speaker_contract_local_rebind`, `speaker_contract_canonical_rewrite`, and `speaker_contract_neutral_bridge` stay **SEMANTIC_DISALLOWED**.
- It is tolerated **only** as **strict-social compatibility residue**: live `apply_final_emission_gate` invokes enforcement **only** inside the `if strict_social_turn:` composition trunk (after narrative-authority layer, before anti-railroading). Non-strict and strict-social-suppressed narration paths **do not** call `enforce_emitted_speaker_with_contract`.
- **`local_rebind` / `canonical_rewrite` / `narrator_neutral`** must remain **SEMANTIC_DISALLOWED** (honest classification for relocation; they must **not** be passed to `assert_final_emission_mutation_allowed`).
- **`_sync_eff_social_to_resolution`** is **compatibility residue** paired with strict-social speaker repair: it copies mutated `eff_resolution.social` fields back to the caller `resolution` when those dicts differ. It is **not** a prose mutator but accompanies speaker repair state alignment; taxonomy kind `effective_social_resolution_sync` is **SEMANTIC_DISALLOWED** and must **not** be asserted at the boundary.
- **Future owner candidates**: `game.social_exchange_emission`, upstream speaker-selection contract realization, or strict-social route materialization — **do not relocate behavior** until caller audits complete.

**Call-site map**

| Symbol | Location | Notes |
| --- | --- | --- |
| `enforce_emitted_speaker_with_contract` | `game/final_emission_gate.py` — **only** `apply_final_emission_gate` strict-social trunk (~9583) | Single live Gate orchestration caller |
| `enforce_emitted_speaker_with_contract` | `tests/test_final_emission_gate.py`, `tests/test_speaker_contract_enforcement.py`, `tests/test_social_exchange_emission.py` | Direct tests / social emission harness |
| `_apply_speaker_contract_repairs` | `game/final_emission_gate.py` — **only** `enforce_emitted_speaker_with_contract` | Private repair ladder |
| `_sync_eff_social_to_resolution` | `game/final_emission_gate.py` — **only** immediately after `enforce_emitted_speaker_with_contract` in `apply_final_emission_gate` strict trunk (~9591) | No other production call sites in-module |

**Paths into `_apply_speaker_contract_repairs`**

Only from `enforce_emitted_speaker_with_contract` when `validate_emitted_speaker_against_contract` returns `ok=False`. If `ok=True`, repairs are skipped and no `repair` key is required.

**Branch / precondition table** (`validate_emitted_speaker_against_contract` → `repair_mode`)

| Repair branch | Preconditions (summary) | `_apply_speaker_contract_repairs` behavior |
| --- | --- | --- |
| `local_rebind` | `continuity_locked`; explicit attribution; wrong speaker **not** in allowed set; **not** interruption-justified; `canonical_name` and salvage (`repair_mode` from validation chooses local_rebind when quoted salvage exists); `eff_resolution` present | Rewrites opening wrong label to canonical name via `_try_local_rebind_opening_speaker`; mutates `eff_resolution.social` npc fields on success |
| `canonical_rewrite` | e.g. forbidden generic fallback; unjustified switch; interruption denied; offscene speaker; continuity-locked mismatch **without** salvage path when canonical id exists; etc. (`repair_mode == canonical_rewrite`) | Replaces text with `strict_social_ownership_terminal_fallback`; updates `eff_resolution.social` |
| `narrator_neutral` | Allowed list empty but dialogue ownership invented; or no primary/allowed speaker when rewrite unavailable | Emits `neutral_reply_speaker_grounding_bridge_line`; sets neutral-bridge flags on `eff_resolution.social` |
| None | Contract missing (`contract_missing`): validation returns **ok=True** with `skipped: no_contract` — **no tightening**, no repair | Original text unchanged; **no** `repair` payload from `_apply_speaker_contract_repairs` |

**Metadata contract** (`speaker_contract_enforcement` in `metadata.emission_debug` / merged FEM)

- Always record enforcement payload via `_merge_speaker_enforcement_into_outputs`: `contract_present`, `validation`, `final_reason_code`.
- On repair: `repair` dict includes branch flags (`local_rebind_applied`, `canonical_rewrite_applied`, `narrator_neutral_applied`, `canonical_rewrite_failed_resolution`, `initial_repair_mode`) so semantic repair is **never** mistaken for packaging.
- Match path: no `repair` key (validation-only success).
- Edge case: `canonical_rewrite_failed_resolution` may be set when rewrite cannot apply resolution-backed canonical fallback — text may remain unchanged but failure is still visible in `repair`.

**Non-strict / suppression**

- **Non-strict** (`strict_social_turn` false): full gate uses the non–strict-social trunk; **`enforce_emitted_speaker_with_contract` is not invoked** (`test_block_f_apply_final_emission_gate_non_strict_never_invokes_enforce_emitted_speaker_with_contract`).
- **Strict-social suppressed non-social narration**: coercion suppressed → `strict_social_turn` becomes false → same non-strict trunk; speaker repair **not** invoked (`test_block_f_apply_final_emission_gate_suppressed_non_social_turn_never_invokes_enforce_emitted_speaker_with_contract`).

**Future relocation notes**

- Keep `_sync_eff_social_to_resolution` adjacent to any future move of speaker repair so caller resolution stays aligned with emitted dialogue ownership.
- Relocation should preserve metadata visibility and SEMANTIC_DISALLOWED taxonomy for the three speaker repair kinds and `effective_social_resolution_sync`.

| Seam | Active behavior | Classification | Why tolerated | Required guard/test | Future owner candidate |
| --- | --- | --- | --- | --- | --- |
| `enforce_emitted_speaker_with_contract` (strict-social trunk only) | Validates emitted dialogue vs `speaker_selection_contract`; may invoke `_apply_speaker_contract_repairs` | Repair kinds **SEMANTIC_DISALLOWED**; active semantic mutation in Gate | Strict-social continuity and ownership legality without upstream speaker realization on all callers | Non-strict + suppression never call enforcement; missing contract does not tighten (`test_apply_final_emission_gate_strict_social_contract_missing_skips_tightening`); semantic kinds never `assert_final_emission_mutation_allowed` | `game.social_exchange_emission` / upstream speaker-selection |
| `speaker_contract_local_rebind` | Opening label rewrite preserving quoted span | **SEMANTIC_DISALLOWED** | Wrong explicit speaker under continuity lock | `test_block_b_speaker_local_rebind_is_metadata_visible_and_sync_traceable`; Block F taxonomy + packaging denial | Upstream strict-social realization |
| `speaker_contract_canonical_rewrite` | Terminal strict-social ownership fallback line | **SEMANTIC_DISALLOWED** | Deterministic replacement when rebind impossible | `tests/test_speaker_contract_enforcement.py::test_enforce_canonical_rewrite_when_local_rebind_unsafe`; Block F metadata/taxonomy | `game.social_exchange_emission` |
| `speaker_contract_neutral_bridge` | Neutral grounding bridge when no allowed speaker | **SEMANTIC_DISALLOWED** | Avoids illegal NPC attribution when contract allows no speaker | `tests/test_speaker_contract_enforcement.py::test_enforce_narrator_neutral_clears_npc_and_sets_bridge_marker`; Block F | Upstream social emission |
| `effective_social_resolution_sync` (`_sync_eff_social_to_resolution`) | Copies social fields from eff resolution to caller resolution | **SEMANTIC_DISALLOWED** (state alignment, not packaging) | Legacy caller visibility after eff-resolution speaker repair | Single call site next to enforcement; `test_block_b_speaker_local_rebind_is_metadata_visible_and_sync_traceable`; `tests/test_speaker_contract_enforcement.py::test_sync_eff_social_to_resolution_copies_bridge_and_canonical_fields` | Upstream effective-resolution materialization |

## Block G — Opening Fallback Compatibility-Local Removal Prep

**Conclusions**

- **`upstream_prepared_opening_fallback`** (from `build_upstream_prepared_opening_fallback_payload` in `game/upstream_response_repairs.py`) is the **canonical** prepared snapshot for gate selection: non-empty `prepared_opening_fallback_text`, `opening_fallback_composition_meta`, `opening_fallback_meta`, plus provenance fields. **`maybe_attach_upstream_prepared_opening_fallback_payload`** auto-attaches at `apply_final_emission_gate` entry when `resolution.kind == scene_opening` and **usable** `opening_curated_facts` exist — idempotent if text already present.
- **Compatibility-local composition** (Gate calls **`_deterministic_opening_fallback_text_and_meta`** when the prepared snapshot is absent or structurally unusable) remains **SEMANTIC_DISALLOWED** taxonomy kind **`compose_opening_fallback_compatibility_local`** / compatibility residue — **not** packaging. Authorship is **`opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL`** in tuple/meta/FEM.
- ~~**`_compat_opening_fallback_text_from_gm`**~~ **Removed (Block K):** repo-wide scan showed zero call sites; dead shim deleted from `game/final_emission_gate.py`.
- **Removal / fail-closed is not yet globally safe**: tests and fixtures still rely on compatibility-local authorship and gate-local re-invocation when upstream payload is missing or incomplete; **`_upstream_prepared_opening_fallback_payload_if_usable`** treats partial dicts (text-only, missing composition/meta) as unusable and falls through to compatibility.
- **Future removal** should either **require** upstream-prepared attachment before Gate for scene-opening turns, or **fail closed** with explicit `opening_deterministic_fallback_failed_closed` / sealed replacement — not silent deletion of the compatibility branch without a caller audit.

**Caller map (`_opening_scene_safe_fallback_tuple`)**

| Call site | Location | When |
| --- | --- | --- |
| `_select_non_strict_replace_path_terminal_sealed_fallback` | `game/final_emission_gate.py` | Opening-mode terminal sealed replace for rejected non-strict candidate |
| `_standard_visibility_safe_fallback` | `game/final_emission_gate.py` | Visibility-safe fallback when `_opening_mode_active_for_turn` |

**Paths that invoke local deterministic opening composition (compatibility)**

| Path | Trigger |
| --- | --- |
| `_opening_scene_safe_fallback_tuple` | Stub recovery / usable upstream snapshot → upstream tuple; else Block H sealed marker when no attachable curated strings; else `_deterministic_opening_fallback_text_and_meta` only when **no** stub recovery applied and payload key absent or recovery unnecessary |
| `_enforce_response_type_contract` (opening mode, failed candidate) | Same ordering as tuple (`_recover_upstream_opening_fallback_stub_payload` first) |

**Upstream-prepared availability (`maybe_attach_upstream_prepared_opening_fallback_payload`)**

| Condition | Attached? |
| --- | --- |
| `resolution.kind != scene_opening` | No |
| `opening_curated_facts` missing / empty / no non-empty strings | No |
| Existing payload with non-empty `prepared_opening_fallback_text` | No (preserve idempotent) |
| Build raises | No (leaves gm_output unchanged; gate may still compat-compose) |

**`_upstream_prepared_opening_fallback_payload_if_usable` (selection)**

| Payload shape | Usable? |
| --- | --- |
| Full snapshot from `build_upstream_prepared_opening_fallback_payload` | Yes |
| Dict with only `prepared_opening_fallback_text` | **No** (missing `opening_fallback_composition_meta` or `opening_fallback_meta`) |
| Empty or whitespace text | **No** |

**Compatibility-local dependency table**

| Scenario | Upstream prepared | Result |
| --- | --- | --- |
| Normal scene-opening with curated facts | Auto-attached at gate entry | Selector uses prepared path; authorship **upstream_prepared** (`test_final_gate_auto_attaches_upstream_opening_fallback_before_emission`, `test_opening_failure_recovers_via_upstream_prepared_payload_when_present`) |
| Prepared text present but snapshot incomplete | Unusable at selector | **Rebuilt** via `build_upstream_prepared_opening_fallback_payload` in `maybe_attach` / `_recover_upstream_opening_fallback_stub_payload`; authorship **upstream_prepared** (`test_opening_failure_recovers_upstream_snapshot_when_upstream_payload_incomplete`, `test_maybe_attach_upstream_opening_replaces_text_only_stub_with_full_snapshot`) |
| No attachment + full `_opening_gm_output()` facts | None until attach | Same deterministic text as upstream build; compat authorship (`test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome`) |
| Empty curated / failed closed | Skipped or marker text | Fail-closed / sealed paths; **not** silent generic curated prose (`test_scene_opening_fallback_fail_closes_with_empty_curated_facts`, `test_final_gate_scene_opening_empty_curated_facts_skips_upstream_opening_payload`) |

**Test ownership map (compatibility-local authorship assertions)**

| Suite / test | Role |
| --- | --- |
| `tests/test_final_emission_gate.py` | Opening tuple snapshots, `_enforce_response_type_contract`, full gate FEM (`opening_fallback_authorship_source` upstream vs compatibility) |
| `tests/test_upstream_response_repairs.py` | Payload build + `maybe_attach` behavior |
| `tests/test_diegetic_fallback_narration.py` | Compatibility vs upstream FEM |
| `tests/test_api_narration_path_selection.py` | Finalize path upstream payload |

**Future removal plan**

1. Enumerate production entrypoints that call `apply_final_emission_gate` with `scene_opening` without curated facts or without successful `maybe_attach` (telemetry or static audit).
2. Require **`build_upstream_prepared_opening_fallback_payload`** + attach at orchestration boundary for all scene-opening turns that need deterministic fallback, or explicitly route to fail-closed sealed replacement.
3. ~~Delete **`_compat_opening_fallback_text_from_gm`** once confirmed unused~~ **Done (Block K).** Narrow **`_opening_scene_safe_fallback_tuple`** compatibility branch after payloads are guaranteed.
4. Keep taxonomy honest: **`compose_opening_fallback_compatibility_local`** remains SEMANTIC_DISALLOWED until the branch is removed.

## Block H — Opening Compatibility-Local Fail-Closed Execution

**Path changed (narrow)**

| Location | Behavior |
| --- | --- |
| `_opening_scene_safe_fallback_tuple` in `game/final_emission_gate.py` | When `upstream_prepared_opening_fallback` is **unusable** **and** `opening_curated_facts` does not contain at least one non-empty string (same precondition family as `maybe_attach_upstream_prepared_opening_fallback_payload` skipping attachment), the gate **does not** call `_deterministic_opening_fallback_text_and_meta`. It emits the existing sealed marker `OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER` and merges composition/meta via `_opening_fail_closed_meta_upstream_missing_insufficient_curated_facts`. |
| `_enforce_response_type_contract` (opening-mode repair branch) | Same condition: prepared snapshot unusable + no attachable curated strings → sealed marker path **without** local deterministic composer. |

**Paths intentionally left unchanged**

- Upstream-prepared opening fallback selection when `_upstream_prepared_opening_fallback_payload_if_usable` returns a full snapshot (auto-attach at gate entry when curated facts are usable).
- Compatibility-local **full** deterministic composition only when **no** upstream stub key is present and curated facts are attachable but snapshot was never attached (same prose as upstream build; Block I added stub recovery so incomplete dicts no longer hit this silently).
- `opening_curated_facts` **missing** from `gm_output` on `_enforce_response_type_contract`: explicit fail-closed sealed marker + metadata (**Block J**); composition compatibility-local remains skipped.
- Realization stop-points, other Gate phases.

**Before / after (retired branch only)**

| Dimension | Before | After |
| --- | --- | --- |
| Local composer | `_deterministic_opening_fallback_text_and_meta` invoked (returned sealed marker + meta for empty facts) | Not invoked; marker + meta assembled without running composer |
| Emitted sealed text | `[opening_fallback_failed_closed: empty_curated_facts]` | Same marker |
| `opening_fallback_authorship_source` | `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` when no usable upstream snapshot | Unchanged |
| Block H metadata | — | `opening_fallback_compatibility_local_disabled`, `opening_fallback_missing_upstream_prepared_payload` (plus existing `opening_fallback_failed_closed` / context fields) |

**Metadata / provenance expectations**

- Fail-closed branch records `opening_fallback_failed_closed=True`, `opening_fallback_compatibility_local_disabled=True`, `opening_fallback_missing_upstream_prepared_payload=True` (upstream snapshot absent or structurally unusable at selection time).
- Taxonomy kind `compose_opening_fallback_compatibility_local` remains **SEMANTIC_DISALLOWED** for paths that still invoke local composition; the retired branch avoids invoking that composer and does not broaden packaging assertions.

**Remaining removal plan**

1. ~~Retire compatibility-local composition when upstream prepared is **incomplete** but curated facts are still attachable~~ — addressed by Block I (stub recovery / `maybe_attach` structural usability).
2. ~~Handle `opening_curated_facts` **missing** at `_enforce_response_type_contract` via explicit fail-closed instead of `opening_context_from_gm_output` assertion (caller audit + tests).~~ Done in **Block J**.
3. ~~Remove dead `_compat_opening_fallback_text_from_gm` after external import scan.~~ Done in **Block K**.

**Tests**

- `tests/test_final_emission_gate.py`: Block H tests assert local deterministic composer is not invoked on empty-curated fail-closed path; empty-curated full-gate and contract tests assert new FEM/debug keys.

## Block I — Opening Stub Payload Retirement

**Path changed**

| Layer | Behavior |
| --- | --- |
| `is_structurally_usable_upstream_prepared_opening_fallback_payload` | New predicate in `game/upstream_response_repairs.py`: requires non-empty `prepared_opening_fallback_text`, dict `opening_fallback_composition_meta`, dict `opening_fallback_meta`. |
| `maybe_attach_upstream_prepared_opening_fallback_payload` | Replaces **incomplete** stubs (including text-only dicts) with `build_upstream_prepared_opening_fallback_payload` when scene-opening + usable curated facts. Skips **only** structurally complete payloads. |
| `_recover_upstream_opening_fallback_stub_payload` (`game/final_emission_gate.py`) | Before selecting opening fallback: if a stub dict exists and curated facts are attachable, rebuild via upstream repairs helper in-place; records recovery metadata. On build failure → seal fail-closed marker path (`_opening_fail_closed_meta_upstream_stub_rebuild_failed`) without compatibility-local compose. |
| `_opening_scene_safe_fallback_tuple` / `_enforce_response_type_contract` | Invoke stub recovery first; merge stub telemetry into composition/debug meta. |

**Paths left unchanged**

- Fully usable upstream-prepared snapshot (happy path) unchanged.
- Absent payload + usable curated facts: still compatibility-local deterministic composition at Gate **when no stub key exists** (same deterministic module as upstream ownership).
- Block H empty-/non-attachable-curated-facts fail-closed paths unchanged.
- `opening_curated_facts` missing / ill-typed → explicit fail-closed on `_enforce_response_type_contract` (**Block J**), not `AssertionError`.

**Before / after (incomplete stub + usable curated facts)**

| Dimension | Before | After |
| --- | --- | --- |
| Selection | `_upstream_prepared_opening_fallback_payload_if_usable` → None → silent `_deterministic_opening_fallback_text_and_meta` at Gate | Stub rebuild via `build_upstream_prepared_opening_fallback_payload` → usable upstream snapshot; authorship **upstream_prepared** |
| `maybe_attach` | Non-empty text only → early return, blocking replacement | Structural usability required to skip attach |
| Emitted fallback prose | Same deterministic opening text | Same (composed only inside upstream-owned builder / shared module) |

**Metadata expectations**

- `opening_fallback_upstream_payload_unusable=True` when a stub dict was present but selector refused it (recovery attempted).
- `opening_fallback_upstream_payload_recovered=True` when rebuild succeeded.
- `opening_fallback_compatibility_local_disabled=True` when recovery succeeded (Gate did not author via compatibility-local path) or when stub rebuild failed (fail-closed branch).
- FEM merge via `_merge_response_type_meta` (`opening_fallback_upstream_payload_unusable`, `opening_fallback_upstream_payload_recovered`).

**Remaining compatibility-local inventory**

- `_deterministic_opening_fallback_text_and_meta` when **`upstream_prepared_opening_fallback` key absent** and attachable curated facts exist (or tests that bypass `maybe_attach`).
- Taxonomy: `compose_opening_fallback_compatibility_local` remains **SEMANTIC_DISALLOWED** for any remaining gate-local selection of that kind.

**Next recommended block (see Block L below)**

**Tests**

- `tests/test_final_emission_gate.py`: `test_opening_failure_recovers_upstream_snapshot_when_upstream_payload_incomplete`, `test_opening_scene_safe_fallback_tuple_recovers_text_only_stub_without_compat_local`, Block H regressions.
- `tests/test_upstream_response_repairs.py`: `test_maybe_attach_upstream_opening_replaces_text_only_stub_with_full_snapshot`.

## Validation Notes

Targeted validation run for this audit:

- `PYTHONPATH=.\\.venv\\Lib\\site-packages <bundled-python> -m pytest tests\\test_final_emission_boundary_no_semantic_repair.py -q` -> passed, 9 tests.
- `PYTHONPATH=.\\.venv\\Lib\\site-packages <bundled-python> -m pytest tests\\test_final_emission_gate.py -q` -> passed, 188 tests.
- Block B follow-up: `PYTHONPATH=.\\.venv\\Lib\\site-packages <bundled-python> -m pytest tests\\test_final_emission_boundary_contract.py -q` -> passed, 77 tests.

Plain `python -m pytest ...` could not run because `python` is not on PATH, and `.venv\\Scripts\\pytest.exe` points at a missing `Python312` launcher. No test failures were observed after invoking the repo `.venv` packages through the bundled Codex Python.

**Block E follow-up validation** (Strict-Social Referential Substitution Ownership Fencing):

- `.venv\\Scripts\\python.exe -m pytest tests\\test_final_emission_boundary_contract.py -q` -> passed, 91 tests.
- `.venv\\Scripts\\python.exe -m pytest tests\\test_final_emission_boundary_no_semantic_repair.py -q` -> passed, 9 tests.
- `.venv\\Scripts\\python.exe -m pytest tests\\test_final_emission_gate.py -q` -> passed, 199 tests (188 baseline + 6 new Block E tests + 5 prior additions).
- `.venv\\Scripts\\python.exe -m pytest tests\\test_referential_clarity_strict_social_local_repair.py tests\\test_final_emission_visibility.py -q` -> passed, 57 tests.
- Extended sanity run (boundary contract + no-semantic + audit + convergence + gate + referent + visibility) -> passed, 399 tests.

The repo `.venv` python launcher is now usable directly (`.venv\\Scripts\\python.exe`); previous notes about a missing `Python312` launcher no longer apply.

## Block J — Scene-Opening Missing Curated Facts Fail-Closed

**Path changed**

| Location | Behavior |
| --- | --- |
| `_enforce_response_type_contract` (`game/final_emission_gate.py`) | When `opening_mode` is active and `opening_curated_facts` is **absent** or **not a list**, the gate **no longer** calls `opening_context_from_gm_output(gm_output)` unnormalized (which asserted). Context for validation is built via `_gm_output_normalized_for_opening_context` (synthetic `opening_curated_facts=[]` + existing prompt_context), telemetry records **missing schema**, then the existing opening fallback selector runs: usable `upstream_prepared_opening_fallback` still wins; otherwise the same sealed marker as Block H (`OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER`) **without** invoking `_deterministic_opening_fallback_text_and_meta` on the missing-key path. |
| `_opening_fail_closed_meta_upstream_missing_insufficient_curated_facts` | Empty-list branch records `opening_fallback_missing_curated_facts=False`; schema-invalid / missing-key branch records `opening_fallback_missing_curated_facts=True`. |
| `merge_response_type_meta` (`game/final_emission_validators.py`) | FEM visibility for `opening_fallback_missing_curated_facts`. |

**Before / after**

| Dimension | Before | After |
| --- | --- | --- |
| Missing key / wrong type | `AssertionError` from `opening_context_from_gm_output` | Sealed marker + explicit debug/FEM keys; no assertion |
| Empty list `[]` | Block H fail-closed (unchanged) | Unchanged |
| Upstream prepared snapshot usable | Preferred (unchanged) | Preferred (unchanged) |

**Metadata expectations**

- `opening_fallback_missing_curated_facts=True` when the key is missing or value is not a list; **False** when the key holds a list (including empty list — Block H distinction preserved).
- `opening_fallback_failed_closed`, `opening_fallback_compatibility_local_disabled`, `opening_fallback_missing_upstream_prepared_payload` align with the sealed marker path (same marker text as empty curated facts).
- `blocked_repair_kind` may be `opening_missing_curated_facts` when fail-closing **without** consuming a usable upstream prepared opening snapshot (upstream win does not set this repair kind).

**Remaining compatibility-local paths**

- `_deterministic_opening_fallback_text_and_meta` when attachable curated strings exist and prepared snapshot absent/unusable (unchanged).
- `opening_deterministic_fallback.opening_context_from_gm_output` still asserts if called **without** normalization — gate entry uses normalization for opening-mode validation; deterministic composer remains unreachable when facts are missing (same attachability gate as Block H).

## Block K — Dead Opening Compatibility Shim Removal

**Scan**

- Repo-wide search for `_compat_opening_fallback_text_from_gm`: **only** the definition in `game/final_emission_gate.py` (plus historical doc/artifact mentions). **No** imports, **no** call sites, **no** tests invoking the symbol.

**Change**

- **Removed** the unused shim from `game/final_emission_gate.py`. Active compatibility-local paths already call **`_deterministic_opening_fallback_text_and_meta`** directly; upstream-prepared selection and Block H/J fail-closed behavior unchanged.

**Tests**

- No new tests added; existing opening fallback suites continue to cover `_deterministic_opening_fallback_text_and_meta` and prepared-snapshot selection.

**Recommended Block L** — see **Block L — Opening Compatibility-Local Remaining Usage Audit** (audit complete; local composition **not** removed).

## Block L — Opening Compatibility-Local Remaining Usage Audit

**Removal decision: do not retire Gate-local `_deterministic_opening_fallback_text_and_meta` yet.**

Upstream-prepared guarantees are **incomplete** for a safe delete: production narrows the happy path, but tests and silent attach failures still rely on the compatibility-local composer.

**1. Production (`apply_final_emission_gate` entry)**

| Step | Notes |
| --- | --- |
| `maybe_attach_upstream_prepared_opening_fallback_payload` | Runs immediately after `merge_upstream_prepared_emission_into_gm_output`, before `record_final_emission_gate_entry` and all gate layers (`game/final_emission_gate.py`). |
| Preconditions | `resolution.kind == scene_opening`, non-empty attachable `opening_curated_facts`, no structurally usable existing payload (or stub replaced per Block I). |
| Live narration | `game/api.py` asserts `"opening_curated_facts" in gm` for `scene_opening` turns before downstream work; `api_turn_support` calls the gate with that gm (`game/api_turn_support.py`). |

**2. Classified surfaces**

| Surface | Classification |
| --- | --- |
| Normal `apply_final_emission_gate` + `scene_opening` + usable facts | **Should auto-attach** — `maybe_attach` builds `upstream_prepared_opening_fallback`; gate then prefers prepared snapshot over compatibility-local (`tests/test_final_emission_gate.py::test_final_gate_auto_attaches_upstream_opening_fallback_before_emission`, `test_block_l_apply_final_emission_gate_scene_opening_maybe_attach_runs_before_deterministic_opening_composer`). |
| `maybe_attach` skips (`build_upstream_prepared_opening_fallback_payload` raises — caught internally) | **Closed (Block N)** — full gate fails closed (no compat-local compose); FEM retains Block M `opening_upstream_prepare_attach_*` plus `blocked_repair_kind=opening_upstream_prepare_attach_failed`. |
| Direct `_enforce_response_type_contract` / `_opening_scene_safe_fallback_tuple` in tests | **Valid legacy/test fixtures** — bypass `maybe_attach`; intentionally exercise compatibility-local authorship and selector ordering. |
| Block H / J (empty non-attachable facts, missing schema) | **Should fail closed** — sealed marker paths; compatibility-local composer skipped (unchanged). |
| Stripped `upstream_prepared_opening_fallback` in regression tests | **Valid regression fixtures** — prove compat vs upstream and stub recovery (Block G/I). |

**3. Callers still depending on compatibility-local composition**

- Internal gate branches: `_enforce_response_type_contract` (opening repair ladder), `_opening_scene_safe_fallback_tuple` (terminal sealed replace / visibility-safe fallback when opening mode), after stub recovery exhausts usable upstream but attachable facts remain.
- **Tests** that call gate helpers directly without full `apply_final_emission_gate` entry (large `tests/test_final_emission_gate.py` opening section).

**4. Concrete next step (not executed in Block L)**

- Removing the composer requires either: (a) migrating helper-only tests to run attach then delegate, or inject prepared payloads; (b) treating `maybe_attach` build failure as explicit fail-closed instead of falling through to compat compose; (c) proving no production path hits (b) via telemetry.

**Recommended Block M** — see **Block M — Opening Prepared-Payload Attach Failure Observability** below.

## Block M — Opening Prepared-Payload Attach Failure Observability

**Behavior change:** none to emitted opening prose or selector precedence — metadata-only.

**Metadata added**

| Key | When set |
| --- | --- |
| `opening_upstream_prepare_attach_build_failed` | `build_upstream_prepared_opening_fallback_payload` raised inside `maybe_attach_upstream_prepared_opening_fallback_payload`. |
| `opening_upstream_prepare_attach_failure_exc_type` | Exception class name (e.g. `RuntimeError`), or cleared on successful rebuild path. |
| `opening_upstream_prepare_attach_no_usable_payload_after_attempt` | True when attach failed after a rebuild was required (usable curated facts, no structurally usable existing payload). |

**Surfacing**

- Written on `gm_output["metadata"]["emission_debug"]` by `maybe_attach_upstream_prepared_opening_fallback_payload` (`game/upstream_response_repairs.py`).
- Merged into `response_type_debug` / `_final_emission_meta` via `_merge_opening_upstream_prepare_attach_observability_into_response_type_debug` at `apply_final_emission_gate` contract boundaries (`game/final_emission_gate.py`) and `_merge_response_type_meta` (`game/final_emission_validators.py`).
- Successful silent attach removes stale Block M keys from `emission_debug` after a successful build.

**Measurement**

- Attach build failures were observable on FEM after Block M; **Block N** stops falling through to compatibility-local composition on that full-gate path while preserving telemetry.
- Block L gap row (“swallowed build failure”) is **observable** (Block M) and **policy-closed** (Block N).

**Tests**

- `tests/test_upstream_response_repairs.py`: build failure emission_debug; successful attach clears stale keys.
- `tests/test_final_emission_gate.py`: `test_block_n_opening_attach_build_failure_fails_closed_preserves_block_m_telemetry`; happy path unchanged telemetry flags.

**Recommended Block N** — **implemented (policy closed)** — see **Block N — Opening Attach-Failure Fail-Closed Policy** below.

## Block N — Opening Attach-Failure Fail-Closed Policy

**Policy decision:** When `maybe_attach_upstream_prepared_opening_fallback_payload` **attempted** upstream preparation (`build_upstream_prepared_opening_fallback_payload`) and **build failed**, full-orchestration `apply_final_emission_gate` scene-opening selection **fails closed**: it does **not** call `_deterministic_opening_fallback_text_and_meta` for compatibility-local opening prose. It selects the same sealed marker text as Block H (`OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER`). Block M telemetry on `metadata.emission_debug` remains merged into `response_type_debug` / FEM unchanged.

**Scope (narrow):** Applies only when emission_debug records `opening_upstream_prepare_attach_build_failed` **and** stub recovery did not yield a usable upstream snapshot **and** curated facts still satisfy the attachable-string predicate (the branch that previously fell through to compatibility-local compose). Direct helper-only calls (no gate-entry attach telemetry) keep compatibility-local deterministic fallback behavior.

**Before / after (attach build failure + attachable facts + full gate)**

| Dimension | Before (post–Block M) | After (Block N) |
| --- | --- | --- |
| `_deterministic_opening_fallback_text_and_meta` at Gate | Invoked; same prose as upstream build | **Not** invoked |
| Emitted RT fallback text (pre–visibility layers) | Deterministic opening paragraph | Sealed marker `[opening_fallback_failed_closed: empty_curated_facts]` |
| `opening_fallback_authorship_source` | `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` | `None` (no compat authorship) |
| `opening_fallback_failed_closed` / `opening_fallback_compatibility_local_disabled` | Absent / false for this branch | `True` / `True` |
| `blocked_repair_kind` | Typically unset in this branch | `opening_upstream_prepare_attach_failed` |
| Block M FEM keys | Preserved | Preserved (`opening_upstream_prepare_attach_*`) |

**Final player-facing text:** As with Block H/J sealed-marker paths, later layers (visibility / acceptance-quality terminal replace) may still substitute **global visibility-safe stock** (e.g. `For a breath, the scene holds while voices shift around you.`). Assertions in full-gate tests target FEM and response-type repair classification, not necessarily raw marker persistence through finalize.

**Remaining compatibility-local composition paths**

- **Unchanged:** No attach-failure telemetry (tests/helpers bypassing `maybe_attach`, or attach skipped because resolution is not `scene_opening` / no attachable curated strings).
- **Unchanged:** Absent prepared payload with usable curated facts when gate entry did **not** record attach build failure — deterministic composer still runs (same prose module as upstream builder).
- **Unchanged:** Happy-path upstream-prepared snapshot selection; stub recovery success → upstream_prepared authorship.

**Recommended Block O** — **implemented (harness + selective conversions)** — see **Block O — Opening Helper Harness Alignment** below.

---

**Archived pointer (superseded):**

- **Policy choice** after reviewing FEM counts: fail-closed vs compat-local when `opening_upstream_prepare_attach_build_failed` → **resolved: fail-closed** (Block N).
- Alternatives still open: **Speaker contract repair relocation** (Block F), or further harness adoption (Block O below).

## Block O — Opening Helper Harness Alignment

**Production vs tests**

| Surface | Dependency |
| --- | --- |
| **`apply_final_emission_gate` (live)** | Always runs `merge_upstream_prepared_emission_into_gm_output` then **`maybe_attach_upstream_prepared_opening_fallback_payload`** before gate layers; opening fallback selection normally sees an upstream-prepared snapshot when scene-opening + attachable curated facts allow it. |
| **Direct `_enforce_response_type_contract` / `_opening_scene_safe_fallback_tuple` tests (legacy)** | Historically called helpers **without** `maybe_attach`, exercising compatibility-local branches more often than production. |

**Harness (tests only)**

- `tests/test_final_emission_gate.py`: **`opening_gate_attach_then_opening_scene_safe_fallback_tuple`**, **`opening_gate_attach_then_enforce_response_type_contract`** — run **`maybe_attach_upstream_prepared_opening_fallback_payload`** then the chosen helper (mutates `gm_output` like gate entry).

**Converted to harness (aligned with gate entry attach)**

- `test_opening_scene_safe_fallback_tuple_exact_text_and_classification_snapshot` — expectations updated to **upstream_prepared** authorship after attach.
- `test_opening_scene_safe_fallback_tuple_prefers_upstream_prepared_payload`
- `test_opening_failure_recovers_via_upstream_prepared_payload_when_present`
- `test_block_ai_opening_upstream_prepared_snapshot_remains_preferred_over_compatibility_local`
- `test_scene_opening_candidate_not_rejected_for_lacking_action_result_language`

**Intentionally **not** harnessed (explicit seam coverage)**

- **`test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome`** — no prior `maybe_attach`; asserts **`OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL`** for legacy compatibility-local selection.
- **`test_opening_scene_safe_fallback_tuple_recovers_text_only_stub_without_compat_local`** — direct tuple call preserves **tuple-path** stub-recovery telemetry (`opening_fallback_upstream_payload_recovered` merged from `_recover_upstream_opening_fallback_stub_payload`); running `maybe_attach` first would attach before the tuple and skip that merge.
- **`test_opening_failure_recovers_upstream_snapshot_when_upstream_payload_incomplete`** — same telemetry/stub-recovery contract; remains direct.

**Production behavior:** unchanged (test-only helpers + assertions).

**Remaining compatibility-local inventory (post–Block N/O)**

- Helper-only calls **without** harness (above), Block H/J fail-closed paths, and attach-failure fail-closed (Block N) — unchanged from Block N doc.
- **`test_deterministic_opening_fallback_helper_exact_text_and_meta_snapshot`** — still targets `_deterministic_opening_fallback_text_and_meta` directly (shared module with upstream builder), not the gate harness.

## Block P — Opening Compatibility Stop-Point Review

**Stop-point recommendation: STOP (safe).** Opening compatibility work is at a reasonable boundary: production paths are covered (attach, stub recovery, Block N fail-closed, Block O harness for representative gate-aligned tests). Remaining direct `_enforce_response_type_contract` / `_opening_scene_safe_fallback_tuple` calls are either **attach-skipping fixtures** (empty/missing curated facts), **intentional bypass anchors**, or **optional future harness candidates** — not evidence of an unfinished migration crisis.

**Production behavior:** unchanged by this review (documentation only).

### Classification — remaining direct opening helpers (`tests/test_final_emission_gate.py`)

**Intentional compatibility-local anchor**

| Test | Why direct |
| --- | --- |
| `test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome` | Documents **`OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL`** when **`maybe_attach`** did not run (legacy helper bypass vs production). |

**Intentional stub-recovery anchors** (telemetry / ordering differs if **`maybe_attach`** runs first)

| Test | Why direct |
| --- | --- |
| `test_opening_scene_safe_fallback_tuple_recovers_text_only_stub_without_compat_local` | Asserts tuple **`stub_patch`** merge (`opening_fallback_upstream_payload_recovered`, etc.). |
| `test_opening_failure_recovers_upstream_snapshot_when_upstream_payload_incomplete` | Asserts contract **`debug`** stub-recovery flags after **`_recover_upstream_opening_fallback_stub_payload`**. |

**Intentional fail-closed / attach-skip anchors** (`maybe_attach` would not attach — empty facts, missing key, or minimal `gm`)

| Test | Why direct |
| --- | --- |
| `test_block_g_fail_closed_empty_curated_facts_emits_marker_not_composed_scene_opening_prose` | Block G/H sealed marker; no attachable facts. |
| `test_block_h_empty_curated_facts_skips_gate_local_deterministic_opening_composer` | Block H monkeypatch guard on empty facts. |
| `test_block_h_opening_scene_safe_fallback_tuple_skips_local_composer_when_empty_curated_facts` | Same for tuple path. |
| `test_removing_opening_curated_facts_fail_closes_with_explicit_metadata` | Block J-style missing key path. |
| `test_scene_opening_fallback_fail_closes_without_curated_context` | Minimal `gm_output` (no facts). |
| `test_scene_opening_fallback_fail_closes_with_empty_curated_facts` | Empty list. |
| `test_block_j_missing_curated_facts_skips_gate_local_deterministic_opening_composer` | Block J monkeypatch on absent key. |

**Should use harness (optional polish — low risk where payload already exists or attach is a no-op)**

| Test | Notes |
| --- | --- |
| `test_block_g_opening_scene_safe_fallback_prefers_upstream_when_usable` | Same shape as **`test_opening_scene_safe_fallback_tuple_prefers_upstream_prepared_payload`**; **`maybe_attach`** skips when snapshot already usable. |
| `test_valid_scene_opening_skips_deterministic_fallback` | Attach then contract preserves valid candidate; aligns with production ordering. |

**Should use harness with assertion refresh (compat-local → upstream_prepared after attach)**

| Test | Notes |
| --- | --- |
| `test_empty_scene_opening_uses_deterministic_fallback` | Today asserts compat authorship; after harness matches production (**upstream_prepared** once attach runs). |

**Fine either way / contextual fallback behavior** (harness optional; assertions mostly unchanged)

| Test | Notes |
| --- | --- |
| `test_scene_opening_fallback_with_opening_seed_facts_emits_seed_facts` | Custom Ash Quay `gm_output`; attach builds canonical snapshot from curated facts. |
| `test_scene_opening_fallback_prefers_opening_curated_facts` | Curated-vs-visibility precedence. |
| `test_opening_fallback_ignores_contaminated_public_scene_visible_facts` | Contamination guardrails. |
| `test_opening_fallback_never_uses_polluted_narration_visibility_facts` | Curated vs narration_visibility. |
| `test_failed_scene_opening_never_emits_generic_the_scene_fallback` | Degenerate anchors / prose shape. |
| `test_opening_failure_fallback_classification_excludes_observe_family` | Classification meta (`fallback_template_metadata`). |
| `test_frontier_gate_opening_fallback_uses_top_level_curated_facts` | Top-level curated facts wiring. |

**Different helper seam (not the attach + opening tuple/contract harness)**

| Test | Notes |
| --- | --- |
| `test_opening_visibility_safe_fallback_routes_to_opening_family_not_observe` | **`_standard_visibility_safe_fallback`** entry — visibility stack, not RT-only harness. |

**Obsolete / removable later**

| Test | Notes |
| --- | --- |
| _None flagged._ | **`test_block_g_opening_scene_safe_fallback_prefers_upstream_when_usable`** overlaps **`test_opening_scene_safe_fallback_tuple_prefers_upstream_prepared_payload`** but remains a short Block G anchor; retire only if duplicated assertions become maintenance noise. |

**Out of opening-harness scope**

| Item | Notes |
| --- | --- |
| `test_enforce_response_type_contract_marks_upstream_absent_for_answer_without_prepared_text` | Answer contract, not scene-opening. |
| `test_deterministic_opening_fallback_helper_exact_text_and_meta_snapshot` | Direct **`_deterministic_opening_fallback_text_and_meta`** — shared builder module, intentionally not gated through **`maybe_attach`**. |

### Recommended Block Q — superseded by audit

Opening pivot guidance from Block P is folded into **Block Q — Speaker Repair Relocation Decision Audit** below. Optional opening harness rows remain optional polish only.

---

## Block Q — Speaker Repair Relocation Decision Audit

**Executive decision**

| Question | Answer |
| --- | --- |
| Is speaker repair **ready for actual relocation** (moving prose mutation upstream out of `apply_final_emission_gate`)? | **No.** Treat speaker enforcement as **fenced compatibility residue** until prerequisites complete (see branch table). |
| Should **Block R** **start** relocation (upstream mutation)? | **No.** Block R should be **preparation only** (extraction / invariants / tests), not moving repair side effects into `social_exchange_emission` yet. |
| Production / prose behavior | **Unchanged** by this audit (documentation only). |

**Why not relocate now**

1. **Pipeline position lock:** Live `enforce_emitted_speaker_with_contract` runs **only** on the strict-social trunk **after** `build_final_strict_social_response` and multiple gate layers (response-type through **narrative authority** and **tone escalation**, then **speaker**, then anti-railroading / context separation / …). Moving repairs into `build_final_strict_social_response` or earlier social emission would **change ordering** relative to NA/tone unless those layers move with it — a large refactor, not a lift-and-shift.
2. **Contract + validation implementation module:** `get_speaker_selection_contract`, `validate_emitted_speaker_against_contract`, `_apply_speaker_contract_repairs`, and related helpers are implemented in **`game/speaker_contract_enforcement.py`**. The **orchestrator entry** `enforce_emitted_speaker_with_contract` remains on **`game/final_emission_gate.py`** (see **Block R**) so gate-level test hooks and contract patches keep working. Upstream relocation still implies **shared module ownership first** to avoid duplicate semantics.
3. **Upstream already ships contract snapshot:** `game.social_exchange_emission` materializes `speaker_selection_contract` onto resolution metadata for Gate consumption (“no re-resolve” comment path). Repairs remain the **terminal legality** step on emitted dialogue text after shaping layers.

**Branch-by-branch relocation classification**

| Branch / unit | Classification | Notes |
| --- | --- | --- |
| **`local_rebind`** (`_try_local_rebind_opening_speaker`) | **Needs more tests + extraction prerequisite** | Smallest textual mutation (opening wrong label → canonical); still depends on validation output and **post-layer** dialogue string. Candidate **first** upstream mutation **only after** pipeline equivalence and shared module extract. |
| **`canonical_rewrite`** | **Should remain Gate legality fallback** (until full pipeline co-migration) | Invokes `strict_social_ownership_terminal_fallback` (upstream-owned generator) but **orchestration timing** is Gate-positioned after NA/tone; premature upstream move risks skipping layer interactions. |
| **`narrator_neutral`** | **Should remain Gate legality fallback** | Deterministic neutral bridge when contract allows no NPC speaker; same ordering constraint as canonical rewrite. |
| **`_sync_eff_social_to_resolution`** | **Relocate only paired with repair relocation** | Not prose; copies `eff_resolution.social` → caller `resolution`. Must stay **adjacent** to wherever repairs mutate `eff_resolution` — not a standalone first move. |
| **`enforce_emitted_speaker_with_contract` (orchestrator)** | **Not ready** | Single live orchestration call site (`apply_final_emission_gate` strict trunk); relocation is an architectural cut, not a branch-level tweak. |
| **Deletion** | **None** | No branch identified as safe to remove; all remain load-bearing for strict-social legality. |

**Tests / docs reviewed (non-exhaustive)**

- **Block F** inventory in this document; **`tests/test_speaker_contract_enforcement.py`** (contract retrieval, validation, repairs, sync); **`tests/test_final_emission_gate.py`** Block B/F guards (non-strict / suppression never invoke enforcement); **`tests/test_social_exchange_emission.py`** (social emission + contract attachment path).

### Recommended Block R — Preparation phase (no upstream prose relocation)

1. **Extract** `get_speaker_selection_contract`, `validate_emitted_speaker_against_contract`, `_apply_speaker_contract_repairs`, `_try_local_rebind_opening_speaker`, `_sync_eff_social_to_resolution` into a dedicated module (e.g. under `game/speaker_contract_*`) **without** changing call sites or emitted text — pure move + import rewires.
2. **Freeze an invariant doc:** speaker enforcement runs **after** the same gate layers as today (strict-social trunk ordering snapshot / test).
3. **Add integration coverage** (optional): scenarios where NA/tone would interact with speaker labels — **before** any upstream mutation experiment.

**Block R — defer:** Moving **`local_rebind`** or other mutations into **`social_exchange_emission`** until Block R preparation is done and ordering equivalence is proven.

## Block R — Speaker Contract Extraction Prep

**Status:** structural prep only. **No** intended change to emitted prose, strict-social ordering, repair sequencing, fallback wording, or legality semantics.

**What moved to `game/speaker_contract_enforcement.py`**

- Taxonomy / reason tokens: `SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES`, public `SPEAKER_REASON_SPEAKER_BINDING_MISMATCH` (same string as the private mismatch token; used for continuity-bridge comparison in the gate).
- Contract loading and signature/validation: `get_speaker_selection_contract`, `detect_emitted_speaker_signature`, `validate_emitted_speaker_against_contract`, and private helpers (regexes, label matching, empty-contract factory).
- Repair ladder: `_try_local_rebind_opening_speaker`, `_apply_speaker_contract_repairs` (local rebind, canonical rewrite, narrator-neutral bridge).
- Post-repair resolution alignment: `_sync_eff_social_to_resolution`.
- Metadata merge helper: `_merge_speaker_enforcement_into_outputs`.

**What intentionally stayed in `game/final_emission_gate.py`**

- `apply_final_emission_gate` orchestration: strict-social-only invocation timing; branch order (including tone escalation → narrative authority → speaker enforcement → `_sync_eff_social_to_resolution` → anti-railroading / downstream layers).
- **`enforce_emitted_speaker_with_contract`** is still **defined** on the gate module: it delegates to speaker-contract helpers but resolves **`get_speaker_selection_contract` through gate globals** so existing tests that monkeypatch `game.final_emission_gate.get_speaker_selection_contract` (and `enforce_emitted_speaker_with_contract`) behave as before. Moving only the implementation module without this entrypoint broke patch semantics.

**Orchestration invariants (test-backed)**

- `tests/test_speaker_contract_enforcement_extraction.py` locks repair taxonomy tuple order, a missing-contract validation snapshot, strict-social trunk regex fragment (tone → NA → enforce → sync → anti-railroading), and import wiring.
- `tests/test_final_emission_gate.py::test_block_f_sync_eff_social_to_resolution_single_call_site_in_final_emission_gate` expects a **single** non-definition call site in the gate for `_sync_eff_social_to_resolution` (paired with enforcement) and a **single** definition in `speaker_contract_enforcement.py`.

**Remaining relocation blockers (carried from Block Q)**

- **Pipeline position lock:** moving repair earlier than today’s strict-social position without co-moving NA/tone (or re-proving cross-layer interaction) can change legality outcomes.
- **`_sync_eff_social_to_resolution`** must move **with** repair / `eff_resolution` mutation, not as a standalone first step.
- **`canonical_rewrite` / `narrator_neutral`** should stay Gate-timed legality fallbacks until a deliberate co-migration; **`local_rebind`** remains the smallest future candidate **after** ordering equivalence and harness coverage.

## Block S — Speaker Local-Rebind Relocation Equivalence Harness

**Status:** test/doc harness only. **No** upstream relocation of `local_rebind`, **no** emitted-prose or ordering changes in production.

**What equivalence is now covered**

- **Strict-social phase order (integration):** `tests/test_block_s_speaker_local_rebind_equivalence.py::test_block_s_strict_social_phase_order_wrapped_build` records milestone ordering — `build_final_strict_social_response` → `_enforce_response_type_contract` → `_apply_narrative_authenticity_layer` → `_apply_tone_escalation_layer` → `_apply_narrative_authority_layer` → `enforce_emitted_speaker_with_contract` → `_apply_anti_railroading_layer` → `_apply_scene_state_anchor_layer`. Assertions use `tests/helpers/speaker_gate_order.py::assert_phase_subsequence`.
- **Speaker-boundary prose for `local_rebind`:** same module `test_block_s_local_rebind_gate_entry_preserves_full_line_same_as_block_b_direct` proves **at the gate entrypoint** `enforce_emitted_speaker_with_contract` still yields canonical opener + preserved quoted span (`normalized_player_text_equal` vs baseline line).
- **Full `apply_final_emission_gate` path — branch metadata only:** `test_block_s_local_rebind_full_gate_metadata_not_canonical_or_neutral` asserts `speaker_contract_enforcement.repair.local_rebind_applied`, FEM `speaker_contract_enforcement_reason == continuity_locked_speaker_repair`, and absence of canonical / narrator-neutral repair flags. Final player text may still be reshaped by **later** Gate layers (scene anchor, purity, N4, visibility stack, etc.) under default fixtures — the test **does not** claim end-to-end prose identity through finalize for this harness.
- **Comparison helper:** `tests/helpers/speaker_gate_order.py::normalized_player_text_equal` for future A/B (relocation candidate vs Gate baseline).

**What remains before experimental relocation**

- **End-to-end prose equivalence** under production-ish contracts (scene-state anchor, purity, visibility, N4, IC attach) — either controlled fixtures that satisfy downstream layers or explicit bypass inventory documented per layer.
- **Dev-flag shadow path** comparing upstream-placed `local_rebind` vs Gate baseline **normalized text** (not implemented here).
- **Doc/table refresh:** Block F mutation inventory rows still citing old paths for `_apply_speaker_contract_repairs` — optional pass.

**Is `local_rebind` ready for experimental relocation?** See **Block AA** — conditional go at speaker boundary; finalize parity still downstream-dependent (**Block T** / **U**).

---

## Block T — Speaker Relocation Shadow-Equivalence Harness

**Status:** tests/helpers only. **No** runtime ordering change, **no** upstream move of `local_rebind`, **no** edits to `apply_final_emission_gate` orchestration.

**Harness**

| Artifact | Role |
| --- | --- |
| `tests/helpers/speaker_relocation_shadow_harness.py` | `install_dual_run_enforce` monkeypatches `enforce_emitted_speaker_with_contract` to deep-copy `gm_output` / `eff_resolution` / `resolution` **before** enforcement runs, apply `run_isolated_enforce_mirror` (validation + `speaker_contract_enforcement._apply_speaker_contract_repairs` without FEM merge), then call the real Gate entry. Builds `SpeakerShadowEquivalence`. |
| `with_finalize_delta` | After full gate returns, attach final `player_facing_text` and set `downstream_finalize_delta` when normalized post-speaker text ≠ normalized finalize output. |

**Fixtures (focused)**

| Fixture | Intent |
| --- | --- |
| Continuity-locked opening mismatch | Wrong explicit speaker label under runner lock → `local_rebind`; asserts Gate vs isolated match at speaker boundary. |
| Quoted dialogue + downstream stack | Same strict-social shape through validation-only NA/tone/narrative-authority layers; records whether finalize still reshapes vs post-speaker text. |
| No `canonical_rewrite` / no `narrator_neutral` | Repair-flag slice excludes those branches for the continuity-lock local_rebind scenarios. |

**Equivalence dimensions — what already matches (Gate vs isolated at pre-speaker snapshot)**

| Dimension | Holds? |
| --- | --- |
| Normalized player text after speaker enforcement | **Yes** (shadow + direct unit test). |
| Repair flags (`local_rebind_applied`, `canonical_rewrite_applied`, `narrator_neutral_applied`, `initial_repair_mode`, …) | **Yes** for captured slice. |
| `final_reason_code` | **Yes** between Gate payload and isolated mirror. |
| Post-validation `ok` (when present) | **Yes**. |
| FEM merge / `metadata.emission_debug` speaker block shape | **Not compared** in harness (isolated path skips `_merge_speaker_enforcement_into_outputs`); Gate-only provenance still applies at runtime. |

**Downstream layers that can still diverge (post-speaker vs finalize)**

Anti-railroading / scene-state anchor / context separation / narration purity / answer-shape primacy / fallback-behavior strip / visibility / first mention / referential clarity / narrative mode / acceptance-quality N4 / interaction-continuity attach / finalize sanitizer — any phase after `enforce_emitted_speaker_with_contract` may change normalized text; Block T records `downstream_finalize_delta` but does not enumerate per-layer diffs in code.

**Experimental relocation viability**

- **At the speaker boundary only:** relocation of *logic* is **shadow-equivalent** to current Gate repair (`local_rebind` path under same contract snapshot): isolated mirror matches Gate entry.
- **End-to-end finalize equivalence:** **not** proven; downstream reshaping can still change prose after speaker enforcement. Treat upstream relocation of **`local_rebind` timing** as **experimentally viable only behind** matching post-speaker stack behavior or extended dual-run through finalize — **not** as a drop-in move yet. See **Block U** for the first post-speaker normalized diverger on the default local_rebind fixture.

---

## Block U — Speaker Relocation Finalize-Stack Divergence Inventory

**Status:** tests only (`tests/test_block_u_finalize_stack_divergence.py`, `tests/helpers/post_speaker_finalize_probe.py`). **No** production ordering change, **no** emitted-prose change, **no** speaker repair move.

**Harness (extends Block T)**

| Piece | Role |
| --- | --- |
| `install_post_speaker_text_probes(..., phase=)` | Wraps post-speaker Gate layers + late stack + `_finalize_emission_output`; compares normalized text in/out per call. |
| `phase` + `chain_enforce_phase_marker` | Sets `phase.after_enforce` after `enforce_emitted_speaker_with_contract` returns so `_apply_answer_exposition_plan_layer` can be labeled **pre** vs **post** speaker (strict-social trunk calls it twice). |
| `_strip_dialogue_from_text` wrapper | Records **`dialogue_plan_subtractive_strip`** only when `phase.after_enforce` (skips pre-speaker dialogue-plan uses). |
| `first_post_speaker_normalized_divergence` | First changed probe skipping `answer_exposition_plan_pre_speaker`. |

**Divergence table — `_runner_strict_bundle` + continuity-lock `local_rebind` (Block S/T line)**

| Ordering | Layer / seam | Normalized text changed? |
| --- | --- | --- |
| Post-speaker trunk | Anti-railroading | No |
| | Context separation | No |
| | Narration purity | No |
| | Answer shape primacy | No |
| | Scene-state anchor | No |
| | Fast-fallback neutral composition | No |
| **First diverger** | **Inline dialogue-plan subtractive strip** (`_strip_dialogue_from_text` after FFNC when `dialogue_plan_blocked` + deferred subtractive path in `apply_final_emission_gate`) | **Yes** — removes quoted payload for this fixture (observed final prefix `Tavern Runner says,`). |
| Late stack | Answer exposition plan (post-speaker call), visibility, IC step, fallback behavior, referent pre-finalize, N4, IC validation attach, finalize | No further normalized change in probe runs after strip for this fixture |

**Safe layers (for this fixture, at normalize granularity):** anti-railroading, context separation, narration purity, answer-shape primacy, scene-state anchor, fast-fallback neutral composition — all validation/metadata-only at this text grain.

**Risky / diverging seams**

| Risk | Why |
| --- | --- |
| **Dialogue-plan subtractive strip** | Not a named `_apply_*` layer; runs inline after FFNC; can drop dialogue while enforcing dialogue-social-plan legality. |
| Visibility / first-mention / referential / N4 / finalize | Not exercised as **first** diverger here; still risky on other candidates or when AQ/N4 contracts ship stricter policy. |

**Contract-driven vs fixture-driven**

- **Both:** First divergence on the **default** bundle is **fixture-driven** (no `dialogue_social_plan` attached → `dialogue_plan_blocked`) *and* **contract-driven** because dialogue-plan enforcement is the shipped legality mechanism that triggers subtractive strip — not an artifact of `local_rebind` itself.
- **Attribution alignment:** canonical-only plans **without** declared alias rows still fail `attributed_speaker_mismatch` when pregate uses an undeclared alias (**Block W**). With **Block Z** declared `allowed_pregate_speaker_labels` / `writer_attribution_label` (valid provenance), pregate alias matches pass dialogue-plan validation **before** speaker repair.

**Relocation implication**

- Speaker-boundary equivalence (Block T) remains intact; **finalize parity** for relocation experiments must either **ship a valid dialogue-social plan** that matches **pregate** attribution (or otherwise avoid `dialogue_plan_blocked` subtractive strip) on strict-social turns, or explicitly dual-run including this inline seam — otherwise perceived “finalize drift” dominates unrelated to speaker timing.

---

## Block V — Strict-Social Passing Dialogue-Plan Divergence Probe

**Status:** tests only (`tests/test_block_u_finalize_stack_divergence.py`). **No** production behavior change. Uses `tests.helpers.dialogue_social_plan.make_valid_dialogue_social_plan` + `attach_dialogue_social_plan_to_resolution`.

**Does a passing dialogue plan avoid subtractive strip?**

- **Yes**, when the plan is **structurally valid** *and* **`speaker_id` / `speaker_name` match pregate attributed labels** extracted from the candidate line (`Ragged stranger` for the continuity-lock wrong-label opener). Dialogue-plan invariant runs **before** `build_final_strict_social_response` and **before** `local_rebind`; it does **not** see “Tavern Runner” yet.

**Default vs passing-plan first diverger (Block U probes)**

| Fixture | First post-speaker normalized diverger (`first_post_speaker_normalized_divergence`) |
| --- | --- |
| Default bundle (no `dialogue_social_plan`) | `dialogue_plan_subtractive_strip` |
| Passing bundle (`dialogue_social_plan` for **Ragged stranger** / `ragged_stranger`) | **None** — no probed layer records a normalized delta (`None`); post-speaker `dialogue_plan_subtractive_strip` calls show `normalized_changed=False`; quoted payload preserved through finalize for this harness |

**Was dialogue-plan strip fixture-driven in Block U?**

- **Primarily yes** for the default bundle (missing plan attachment). A **partial** plan that mismatches pregate attribution behaves like “still blocked” — **not** weakening enforcement; tests document this by using the correct writer-facing speaker strings.

**Next diverging layer (passing-plan fixture)**

- **None observed** at Block U probe granularity — visibility / N4 / finalize did not change normalized text vs post-speaker output for this narrow `_runner_strict_bundle` + locked-contract run.

**Relocation implication**

- **`local_rebind` relocation is closer to experimentally viable** for **finalize-normalized parity** *when* upstream ships a dialogue-social plan aligned with **pregate** dialogue attribution and continuity constraints — at least for this fixture class; other scenes/contracts may still surface visibility or AQ/N4 first.

---

## Block W — Pregate vs Post-Rebind Dialogue-Plan Reconciliation Audit

**Status:** documentation + tests (`tests/test_block_u_finalize_stack_divergence.py::test_block_w_canonical_dialogue_plan_with_pregate_alias_fails_before_speaker_repair`). **No** production ordering change, **no** `local_rebind` move, **no** emitted-prose change, **no** weakening of dialogue-plan enforcement.

### Current timing (authoritative)

| Question | Answer |
| --- | --- |
| Where does `_enforce_dialogue_plan_invariant_on_strict_social` run? | Inside `apply_final_emission_gate`, only when `strict_social_turn` is true — immediately **before** `build_final_strict_social_response` (see `game/final_emission_gate.py`: comment *Objective C1-D* + call chain). |
| What text is validated? | **`pre_gate_text`** — the strict-social candidate after upstream/pregate containment on `player_facing_text`, **not** text after `enforce_emitted_speaker_with_contract`. |
| What is compared to the plan? | **`_dialogue_bearing_signals(text)["attributed_speakers"]`** extracted from that pregate string vs `dialogue_social_plan.speaker_id` and `speaker_name` (loaded via `_get_dialogue_social_plan_from_emission_debug` → `resolution.metadata.emission_debug.dialogue_social_plan` / effective resolution). |
| Pregate vs post-`local_rebind`? | **Pregate only.** `enforce_emitted_speaker_with_contract` (where `local_rebind` applies) runs **after** the strict-social trunk layers — **after** dialogue-plan enforcement, response-type contract, AC/AEP/RD/SRS/NA/TE/NA layers. |
| How are CTIR / canonical speaker ids represented upstream? | `game/dialogue_social_plan.build_dialogue_social_plan` resolves `speaker_id` / `speaker_name` from **CTIR + `referent_tracking`** via `_pick_speaker_from_ctir_and_referents` (entity ids and display names), **not** from model-written opener aliases such as “Ragged stranger”. |

### Policy options (design space — no shipped behavior change in Block W)

| Option | Mechanism | Pros | Cons |
| --- | --- | --- | --- |
| **A — Pregate-aligned plans** | Upstream bundle/planner emits `dialogue_social_plan` whose `speaker_id` / `speaker_name` match **writer opening attribution** when an alias/wrong-label opener is likely (continuity-lock class). | No gate reorder; keeps **fail-closed** subtractive semantics; **relocation-safe** with Block U/V harness as-is. | Requires planner/narration path to know **writer-facing** labels or to dual-write plan rows — extra upstream contract. |
| **B — Validation after speaker repair** | Move invariant (or a second pass) to **after** `enforce_emitted_speaker_with_contract`. | Plan stays canonical-only; compares to post-`local_rebind` text. | **Out of scope** for Block W (explicit **no timing move**); large behavioral/ordering risk; must not weaken checks when implemented. |
| **C — Canonical-after-rebind equivalence** | Keep timing; extend comparison so alias openers **equate** canonical plan ids to post-rebind labels **without** dropping enforcement strength. | Theoretically preserves canonical plan source of truth. | Needs a **carefully bounded** equivalence map (alias registry / continuity snapshot); easy to accidentally widen inference — design-heavy. |
| **D — `local_rebind` before dialogue-plan validation** | Reorder gate so speaker repair runs first. | Aligns text with canonical plan earlier. | **Forbidden** for Block W; same class of risk as **B**; violates current “check writer candidate first” objective (C1-D). |

### Recommended **relocation-safe** option (policy)

**Prefer option A** for strict-social turns that can ship both a **CTIR-canonical** interlocutor and a **writer-alias** opener: treat `dialogue_social_plan` speaker fields as **pregate-attribution contracts** (what the opening line will say), not only as canonical registry ids — or attach an explicit **writer-attribution** companion field in the bundle in a later design (**Block X**) so planners do not have to duplicate semantic meaning in prose.

Until upstream attaches **declared** alias rows (or uses canonical opening labels), **canonical-only** plans against **undeclared** alias openers still hit `attributed_speaker_mismatch` and subtractive strip **before** `local_rebind`.

### Is `local_rebind` relocation blocked by plan attribution?

**No** at the code level (ordering can still be discussed independently). **Yes** for **practical** relocation/finalize-parity work when the plan is **canonical-only** *and* includes **no** declared alias rows while the writer emits an alias; **Block Z** removes that dialogue-plan blocker when declared aliases are present (remaining parity gaps may still be downstream layers — **Block U**).

### Recommended **Block X** (schema design)

See **Block X — Dialogue Plan Speaker Alias Schema Design** below (canonical vs pregate alias fields, migration, Gate non-inference rule).

---

## Block X — Dialogue Plan Speaker Alias Schema Design

**Status:** documentation + optional contract pins (`tests/test_dialogue_social_plan_block_x_contract_pins.py`). **No** runtime change to `validate_dialogue_social_plan`, **no** change to `_enforce_dialogue_plan_invariant_on_strict_social`, **no** alias acceptance in Gate, **no** `local_rebind` move, **no** emitted-prose change.

### Audit — where the plan lives and how it is consumed

| Piece | Role |
| --- | --- |
| `build_dialogue_social_plan` (`game/dialogue_social_plan.py`) | Builds the structural plan from **CTIR + `referent_tracking` + bounded session hints** only. Populates **`speaker_id`**, **`speaker_name`**, **`speaker_source`**, plus intent/reply/tone/relationship metadata. **Does not** read player-facing prose or writer drafts. |
| `attach_dialogue_social_plan_to_resolution` (`tests/helpers/dialogue_social_plan.py`; production path via `gm.py` / bundle → `emission_debug`) | Deep-copies a plan dict under `resolution.metadata.emission_debug.dialogue_social_plan` (default test path). Transport/storage only. |
| `_get_dialogue_social_plan_from_emission_debug` (`game/final_emission_gate.py`) | Reads **`eff_resolution` then `resolution`** and returns the first mapping at `metadata.emission_debug.dialogue_social_plan`. |
| `_enforce_dialogue_plan_invariant_on_strict_social` (`game/final_emission_gate.py`) | For each extracted **pregate** attributed speaker label, requires a match to **`speaker_id`** (slug equality on attributed label) **or** **`speaker_name`** (case-insensitive string equality). **No other plan fields** participate in attribution matching today. |

### Proposed extension fields (design — **not** implemented)

All names are illustrative; final naming should follow `dialogue_social_plan` versioning and stay JSON-safe, bounded, and non-prose.

| Field | Type (proposal) | Purpose |
| --- | --- | --- |
| **`canonical_speaker_id`** | string (slug) | **Authoritative** CTIR/registry speaker id (same role as today’s `speaker_id` if we split semantics). |
| **`canonical_speaker_name`** | string or null | Registry/display name for telemetry and downstream consumers. |
| **`writer_attribution_label`** | string or null | Single **expected** opening attribution surface form for the **next** writer emission (pregate contract). Mutually exclusive policy choice vs allow-list below. |
| **`allowed_pregate_speaker_labels`** | list[str], bounded (e.g. ≤8), normalized storage | Explicit **closed** set of attribution strings allowed to match pregate extracted labels (canonical name + aliases + role descriptors). |
| **`speaker_alias_resolution_source`** | bounded enum string | **Where** alias strings came from: e.g. `continuity_snapshot`, `referent_tracking`, `interaction_continuity`, `manual_bundle_override`. **Never** `inferred_from_prose`. |

**Recommended schema direction (conceptual):**

1. **Keep** existing **`speaker_id` / `speaker_name`** as the stable **canonical** identity for CTIR alignment (or rename in a version bump to `canonical_*` with a migration shim — see migration risks).
2. **Add** either **`writer_attribution_label`** *or* **`allowed_pregate_speaker_labels`**, not both unchecked: prefer **allow-list** when multiple aliases are legitimate (introducer + registry name).
3. Require **`speaker_alias_resolution_source`** whenever alias fields are present so Gate and audits can prove provenance.

Gate enforcement (future Block, **not** this inventory change) would treat pregate attributed text as matching if it hits **canonical ids/names** **or** any entry in **`allowed_pregate_speaker_labels`** / **`writer_attribution_label`** per policy — **without** parsing prose for new aliases.

### Migration risks

| Risk | Mitigation |
| --- | --- |
| **`validate_dialogue_social_plan` currently allows unknown top-level keys** (no strict allowlist). Silent drift if producers sprinkle undocumented fields. | Bump **`version`** (e.g. v2) or add explicit **allowlist** validation when alias fields ship. |
| **Duplicate identity**: both legacy `speaker_id` and new `canonical_speaker_id` | One migration: deprecate duplicate fields in docs; single writer in `build_dialogue_social_plan`. |
| **Bundle size / prompt projection**: `gm.py` projects a subset of keys to the model; extra canonical/alias fields must stay **structural** and **bounded**. | Extend allowlist projection explicitly; never send freeform prose. |
| **Tests/fixtures**: `make_valid_dialogue_social_plan` must gain optional kwargs for alias fields once schema exists. | Update helpers in one PR with validator changes. |

### Why Gate must **not** infer aliases from prose

- **Objective C1-D** (same module header): dialogue social plan is **derivative from CTIR and bounded artifacts**, not reverse-engineered from emitted lines. Inferring “this line sounds like X” would **move adjudication into pattern matching** on writer output and **bypass** CTIR authority.
- **Security / consistency**: prose inference would let models **steer** acceptable attribution by changing wording, weakening **`attributed_speaker_mismatch`** fail-closed semantics without explicit policy.
- **Operational clarity**: alias acceptance belongs in **declared** bundle fields with **`speaker_alias_resolution_source`**, auditable and deterministic.

### Migration path (recommended phases)

1. **Schema + validator only** (**Block Y**): optional declared-alias fields + conservative builder population.
2. **Gate comparison update** (**Block Z**): `_enforce_dialogue_plan_invariant_on_strict_social` uses `pregate_attributed_label_matches_dialogue_social_plan` — exact matches only; **no** weakening for undeclared aliases.
3. **Cleanup**: deprecate redundant fields; tighten validator allowlist if unknown keys caused drift.

### `local_rebind` relocation vs this schema

**Unchanged from Block W:** reordering speaker repair remains **orthogonal** to alias schema. **Block Z** ships Gate comparison against declared alias rows; finalize-parity work can still **stall** on **downstream** layers unrelated to dialogue-plan attribution (**Block U**).

### Recommended **Block Y** (Phase 1 implementation)

See **Block Y — Dialogue Social Plan Alias Schema Phase 1** below.

---

## Block Y — Dialogue Social Plan Alias Schema Phase 1

**Status:** **Implemented** (`game/dialogue_social_plan.py`, `game/gm.py` prompt projection allowlist, tests). Phase 2 alias-aware Gate matching is **Block Z** (below).

### Implemented fields (optional)

| Field | Semantics |
| --- | --- |
| **`allowed_pregate_speaker_labels`** | Bounded list (≤8) of declared attribution strings; normalized items (length / no embedded newlines). |
| **`writer_attribution_label`** | Single optional declared writer-facing attribution string (same bounds). |
| **`speaker_alias_resolution_source`** | Required when either alias field carries data; must be one of `SPEAKER_ALIAS_RESOLUTION_SOURCES` in `game/dialogue_social_plan.py` (`continuity_snapshot`, `referent_tracking`, `interaction_continuity_contract`, `manual_bundle_override`). **`inferred_from_prose` is not allowed.** |

### Builder population (conservative)

- **`build_dialogue_social_plan`** reads optional keys **only** from **`ctir.interaction.continuity_snapshot`** and **`referent_tracking`** root when those mappings declare **`allowed_pregate_speaker_labels`** / **`writer_attribution_label`**.
- **No** inference from prose, entity-id slugging, or automatic alias synthesis.
- **`interaction_continuity_contract`** is a valid **manual / bundle** resolution source for attached plans (`manual_bundle_override`) but is **not** auto-filled by the builder from session hints in Phase 1 (hints remain atom-only in `bounded_session_hints`).

### Migration status

| Phase | Status |
| --- | --- |
| **1 — Schema + validator + builder + projection** | **Shipped** (optional fields; **`version` remains `1`** — additive-only). |
| **2 — Gate comparison uses declared aliases** | **Shipped** — **Block Z** (`pregate_attributed_label_matches_dialogue_social_plan` + `_enforce_dialogue_plan_invariant_on_strict_social`). |
| **3 — Optional strict top-level allowlist / deprecation cleanup** | Open (**Block AA**). |

### Unknown-key behavior

Unchanged: `validate_dialogue_social_plan` does **not** reject undocumented top-level keys (migration risk unchanged; tightening is **Block AA**).

### Recommended **Block Z** (Phase 2 alias-aware Gate)

See **Block Z — Alias-Aware Dialogue Plan Validation** below.

---

## Block Z — Alias-Aware Dialogue Plan Validation (Phase 2)

**Status:** **Implemented** (`game/dialogue_social_plan.pregate_attributed_label_matches_dialogue_social_plan`, `game/final_emission_gate._enforce_dialogue_plan_invariant_on_strict_social`, tests).

### Accepted alias forms (exact match only)

A pregate attributed speaker fragment matches the plan when **any** of these hold (case-fold on comparison; `speaker_id` compared via whitespace→underscore slug of the attributed fragment):

| Rule | Match |
| --- | --- |
| Canonical slug | `speaker_id` (slug) equals attributed label slug. |
| Canonical display | `speaker_name` equals attributed label (lower string equality). |
| Writer label | `writer_attribution_label` equals attributed label (when structurally valid per validator). |
| Allow-list | Attributed label equals one entry in `allowed_pregate_speaker_labels`. |

**No** fuzzy/partial/substring matching. **No** inference from freeform prose beyond attributed-speaker extraction already performed by `_dialogue_bearing_signals`.

### Safety / fail-closed (unchanged posture)

| Still fails | Reason |
| --- | --- |
| **Undeclared** pregate alias | Not in canonical fields or declared alias rows (e.g. “Town crier” vs plan allowing only “Ragged stranger”). |
| **Invalid plan** | `validate_dialogue_social_plan` errors (including alias rows **without** `speaker_alias_resolution_source`, or **`inferred_from_prose`** / unknown source) → `plan_invalid:*` **before** permissive alias acceptance applies to semantics. |
| **Missing dialogue plan** / **applies false** / missing required fields | Unchanged. |

### Relocation / finalize parity

**Canonical plan + declared pregate alias** (with valid provenance) now **passes** dialogue-plan attribution validation — subtractive strip does **not** fire for that mismatch class. **`local_rebind` timing** is still unchanged; remaining blockers for relocation experiments are **downstream finalize layers** (Block U inventory), not dialogue-plan attribution alone.

### Recommended **Block AA** (relocation readiness closeout)

See **Block AA — Speaker Local-Rebind Relocation Readiness Closeout** below.

---

## Block AA — Speaker Local-Rebind Relocation Readiness Closeout

**Status:** documentation + proof test (`tests/test_block_t_speaker_relocation_shadow_equivalence.py::test_block_aa_dual_run_declared_alias_dialogue_plan_shadow_equivalence`). **No** runtime ordering change, **no** upstream move of `local_rebind`.

### Evidence reviewed (Blocks S / T / U / V / Z)

| Block | What it proves |
| --- | --- |
| **S** | Strict-social milestone ordering through `enforce_emitted_speaker_with_contract`; gate entry preserves continuity-lock **`local_rebind`** branch metadata and normalized opener repair vs direct enforcement baseline. |
| **T** | **Shadow equivalence:** isolated mirror matches Gate speaker enforcement (`normalized_text_match`, repair flags, `final_reason_code`) for continuity-lock wrong-label opener; **`downstream_finalize_delta`** may still be true after full gate. |
| **U** | **First post-speaker diverger** on *default* bundle (no plan / blocked plan) was dialogue-plan subtractive strip — **not** caused by `local_rebind` itself. |
| **V** | Passing **`dialogue_social_plan`** aligned with pregate attribution avoids subtractive strip as first diverger (narrow harness). |
| **Z** | Canonical plan + **declared** alias rows passes dialogue-plan attribution; undeclared alias / invalid provenance still fail closed. |

### Decision: go / no-go

| Question | Verdict |
| --- | --- |
| Is **`local_rebind` logic relocation** ready for **controlled experimentation** (dual-run / shadow compare at speaker boundary, behind tests)? | **Yes — conditional GO.** Block **T** equivalence + Block **S** ordering give a reproducible safety net for **moving where repairs run**, as long as **the same contract snapshot + enforcement semantics** apply. |
| Is **upstream timing relocation** (speaker repair before / after other gate phases) ready as a **drop-in production move**? | **No — NO-GO.** Block **T** / **U**: **finalize-normalized parity is not proven**; post-speaker layers may still reshape text; FEM merge shape differs from isolated mirror. |
| Is **Gate cleanup** on dialogue-plan + alias + speaker-contract **inventory** at a practical stop-point? | **Yes.** Blocks **Y / Z** delivered schema + alias-aware validation; remaining work is **experimentation / product choice**, not missing fence docs for this thread. |

### Remaining blockers (after Block Z)

1. **Downstream finalize stack** — anti-railroading, visibility, first mention, referential clarity, N4, IC attach, finalize sanitizer, etc. may change normalized text after speaker enforcement (**Block U**).
2. **Harness limits** — isolated path does not replay `_merge_speaker_enforcement_into_outputs`; Gate-only metadata (**Block T** table).
3. **Operational dependency** — alias-opener strict-social turns need **declared** bundle rows (`allowed_pregate_speaker_labels` / `writer_attribution_label` + provenance) or canonical pregate labels; otherwise dialogue-plan mismatch risk returns (**Block W / Z**).
4. **No dev-flag relocation sandbox** in production — still “not implemented” from earlier inventory; experiments remain **test-driven / branch-only**.

### Recommended **Block AB** (pick one)

| Track | Next action |
| --- | --- |
| **Relocation experiment** | Implement a **branch-only** or **flagged** early `local_rebind` (or extracted helper) with **mandatory** Block **T**-style dual-run in CI for touched scenarios; extend probes through `_finalize_emission_output` when touching ordering. |
| **Stop Gate cleanup** | Treat speaker / dialogue-plan **cleanup inventory as closed** for this release line; file follow-ups only when changing finalize layers or bundle producers. |
| **Optional probe** | Single **finalize-layer enumeration** fixture (which layer first changes normalized text after speaker for canonical+alias+`local_rebind`) — only if product needs stronger relocation ROI data. |

---

**Archived pointer (superseded):**

- Block O “Recommended Block P” checklist → satisfied by **Block P** classification above.

---

## Block AB — Gate Convergence Closeout & Freeze

**Status:** **Closeout / freeze.** See **`docs/gate_convergence_closeout.md`** for the formal freeze artifact. **No** runtime behavior change in this block.

**Decision:** **Gate layer is maintenance-grade converged.** The Gate cleanup initiative ends at Block AB for this release line. Further work should be **bug-driven**, **audit-driven**, or **performance-driven** — not broad refactor. Experimental relocation belongs on **isolated branches only** with mandatory Block T / Block U dual-run extended through `_finalize_emission_output`.

**Closeout doc summary**

| Section | Content |
| --- | --- |
| **Original Problems** | Hidden semantic mutation; fallback authorship ambiguity; speaker-repair ownership blur; opening compatibility-local prose authorship; dialogue-plan vs speaker timing ambiguity; orchestration density; invisible compatibility residue. |
| **What Was Converged** | Mutation taxonomy; semantic-disallowed fencing; upstream-prepared opening preference; fail-closed opening attach policy; compatibility-local visibility; speaker-contract extraction; shadow-equivalence harnesses; alias-aware dialogue-plan validation; relocation readiness criteria. |
| **Intentional Remaining Residue** | `local_rebind` Gate-timed; `canonical_rewrite` / `narrator_neutral` legality fallbacks; finalize divergence downstream-dependent; compatibility-local opening helpers retained; helper-level bypass tests retained. |
| **Protected Architectural Invariants** | Gate does not infer meaning from prose; semantic repair classified honestly; no mutation path masquerades as packaging; upstream-prepared opening fallback canonical; dialogue-plan alias acceptance declared-only; no inferred speaker aliases; no fuzzy speaker matching; speaker relocation requires parity harnesses. |
| **Stop-Point Decision** | Further cleanup optional; future work bug/audit/perf-driven; no broad refactor justified; experimental relocation branch-only. |
| **Recommended Future Work** | Optional branch-only relocation experiment; finalize divergence attribution tooling; stricter `dialogue_social_plan` allowlist / versioning; CI shadow-equivalence mode. |

**Closeout test**

- `tests/test_gate_convergence_closeout.py` asserts the closeout doc still references current `SEMANTIC_DISALLOWED` taxonomy kinds, the canonical taxonomy module path, and key exported taxonomy surfaces — and that this inventory points back to the closeout doc and marks the layer as maintenance-grade converged.

**Recommendation: Gate cleanup officially ends at Block AB.** Reopen specific seams only when bug, audit, or perf evidence requires it.
