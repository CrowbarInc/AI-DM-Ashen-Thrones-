# BU1 — Stack/Pipeline Contract Surface Reduction Discovery

Date: 2026-06-20

## Executive summary

BJ successfully moved orchestration out of `game/final_emission_gate.py` into explicit stack/pipeline hubs, but those hubs **re-imported the same layer/fallback/meta surface the gate previously fanned into**. This discovery asks whether that surface can shrink **without merging paths or changing runtime behavior**.

**Verdict:** Yes — there is a meaningful reduction opportunity, but it is mostly **import-surface and argument-bundle consolidation**, not deletion of underlying policy owners. The stacks/pipelines need most layer modules at runtime; what they do not need is to **personally import** every merge helper, telemetry stamper, fallback candidate provider, and cross-cutting meta builder.

| Module | Top-level fan-out | Total imports (incl. lazy) | Primary reducible pattern |
|---|---:|---:|---|
| `final_emission_strict_social_stack` | 22 | 22 | Layer-meta bundle + FEM assembly owns debug merges |
| `final_emission_non_strict_stack` | 19 | 19 | Pre-stack context bundle; drop per-layer merge imports |
| `final_emission_terminal_pipeline` | 14 | 14 | Narration-constraint debug owner; visibility as black box |
| `final_emission_finalize` | 7 | 7 | Already lean; minor lazy-import hoist only |
| `final_emission_visibility_fallback` | 18 | 18 | Candidate-selector facade; hoist lazy imports |
| `final_emission_response_type` | 10 | 10 | Moderate; opening upstream bundle |

Estimated **low-risk BU2 savings:** 15–25 direct import edges across the three orchestration hubs (strict stack, non-strict stack, terminal pipeline), mainly by:

1. Replacing per-layer `merge_*_into_emission_debug` imports with a single FEM-assembly or typed `LayerMetaBundle` merge call.
2. Moving narration-constraint debug assembly out of terminal pipeline.
3. Treating visibility enforcement as an opaque step (terminal pipeline keeps one import; visibility module consolidates lazy fallback providers).
4. Passing a pre-built `SceneEmitIntegrityBundle` / `GatePreflightReasons` into stacks instead of importing preflight helpers at the hub.

**Non-goals for BU2:** Reordering layers, merging strict/non-strict trunks, or collapsing visibility/first-mention/referential-clarity chains.

---

## Method

- Read target modules and enumerate every `game.*` import (top-level and function-local).
- Classify each import by contract role (orchestration, policy, fallback, speaker, metadata, telemetry, text, test seam, legacy).
- Map call order from source; cross-check against orchestration tests and BJ delegator locks.
- Cross-reference fan-in/fan-out from `docs/audits/BU_import_fan_in_fan_out.csv` (AST discovery script `scripts/bu_final_emission_coupling_discovery.py`).
- **No runtime code changes** in this block.

---

## Import classification tables

Classification key: **O** orchestration · **P** policy/validation · **F** fallback · **S** speaker · **M** metadata/schema · **T** telemetry/replay · **X** text/composition · **E** test seam · **L** legacy/possibly removable

### `game/final_emission_strict_social_stack.py` (22 imports)

| Import | Category | Why it exists | Reduction note |
|---|---|---|---|
| `final_emission_finalize` | O | Exit tail | Keep (1 edge) |
| `final_emission_terminal_pipeline` | O | Late enforcement | Keep (1 edge) |
| `dialogue_social_plan` | P | Pre-build invariant + late strip | Keep — order-sensitive |
| `final_emission_fem_assembly` | M | FEM base + layer meta merge | **Expand** — absorb merge imports |
| `final_emission_repairs` | P | AC/AEP/RD/SRS/NAT layers | Keep module; hub could take `RepairsResult` |
| `final_emission_response_type` | P | RT contract + observability merge | Keep |
| `final_emission_meta` (×2 blocks) | M/T | FEM keys, source inference, decision payload | **Dedupe** duplicate import block |
| `final_emission_sealed_fallback` | F/M | Replace-path realization family | Keep on replace branch only (lazy/local ok) |
| `final_emission_fast_fallback_composition` | P | FFNC layer | Keep |
| `final_emission_answer_shape_primacy` | P | ASP layer + merge | **Merge import** → fem_assembly |
| `final_emission_scene_state_anchor` | P | SSA layer + merge | **Merge import** → fem_assembly |
| `final_emission_context_separation` | P | CS layer + merge | **Merge import** → fem_assembly |
| `final_emission_player_facing_narration_purity` | P | Purity layer + merge | **Merge import** → fem_assembly |
| `final_emission_anti_railroading` | P | AR layer + merge | **Merge import** → fem_assembly |
| `final_emission_tone_escalation` | P | TE layer + merge + pregate flag | **Merge import** → fem_assembly |
| `final_emission_narrative_authority` | P | NA layer + merge | **Merge import** → fem_assembly |
| `final_emission_scene_emit_integrity` | P | Integrity bundle for finalize | Keep — could be input bundle |
| `final_emission_text` | X | Normalize helpers | Keep (shared primitive) |
| `fallback_provenance_debug` | F/M | Provenance realign after FFNC | Move to FFNC owner return meta |
| `speaker_contract_enforcement` | S | Speaker enforce + sync | Keep — order-sensitive |
| `social_exchange_emission` | P/F/T | Build, logging, emergency lines | **Split** — logging via assembly |
| `stage_diff_telemetry` | T | Stage snapshot | Keep or bundle with finalize |

### `game/final_emission_non_strict_stack.py` (19 imports)

| Import | Category | Why it exists | Reduction note |
|---|---|---|---|
| `final_emission_boundary_contract` | P | IC validate-only assert | Keep |
| `fallback_provenance_debug` | F/M | FFNC provenance realign | Move to FFNC owner |
| `final_emission_finalize.patch_scene_opening_*` | M | Opening candidate debug patch | **Move** to response_type/opening_fallback |
| `final_emission_repairs` | P | Layer stack + FB layer + merges | Keep repairs; drop merge imports |
| `final_emission_fast_fallback_composition` | P | FFNC | Keep |
| `final_emission_answer_shape_primacy` | P | ASP + merge | Merge via fem_assembly |
| `final_emission_scene_state_anchor` | P | SSA + merge | Merge via fem_assembly |
| `final_emission_context_separation` | P | CS + merge | Merge via fem_assembly |
| `final_emission_player_facing_narration_purity` | P | Purity + merge | Merge via fem_assembly |
| `final_emission_anti_railroading` | P | AR + merge | Merge via fem_assembly |
| `final_emission_tone_escalation` | P | TE + merge | Merge via fem_assembly |
| `final_emission_narrative_authority` | P | NA + merge | Merge via fem_assembly |
| `interaction_continuity` | P | Validate-only IC step | Keep — order-sensitive |
| `final_emission_opening_fallback` | F | Scene-opening accept promotion | Keep |
| `final_emission_response_type` | P | RT contract | Keep |
| `final_emission_passive_scene_pressure` | P | Preflight reason | **Input bundle** from gate preflight |
| `final_emission_narrative_mode_output` | P | Pre-fork NMO assessment | Keep (feeds terminal override) |
| `final_emission_scene_emit_integrity` | P | Integrity bundle | Input bundle candidate |
| `final_emission_text` | X | Normalize | Keep |

**Local duplicate:** `_CONCRETE_INTERACTION_PATTERNS` / `_reply_already_has_concrete_interaction` mirrors `visibility_fallback` — **L** candidate for shared helper (behavior-neutral if extracted verbatim).

### `game/final_emission_terminal_pipeline.py` (14 imports)

| Import | Category | Why it exists | Reduction note |
|---|---|---|---|
| `final_emission_acceptance_quality` | P | N4 floor seam | Keep — order-sensitive (late) |
| `interaction_continuity` | P | Strict IC step + attach validation | Keep |
| `final_emission_boundary_contract` | P | Mutation asserts | Keep |
| `final_emission_finalize.reassert_scene_opening_*` | M | Generic accept reassert | **Move** to opening owner or accept bundle |
| `final_emission_meta` | M | FEM, narration constraint debug, producer stamps | **Split** — debug builder extraction |
| `final_emission_sealed_fallback` | F/M | Emergency patch stamps | Keep on strict paths |
| `final_emission_narrative_mode_output` | P | NMO assessment + trace merge | Keep |
| `final_emission_referential_clarity` | P | Pre-finalize referent clarity + exemption | Keep |
| `final_emission_repairs` | P/F | FB layer, referent clarity layer, merges | Keep |
| `final_emission_text` | X | Normalize | Keep |
| `final_emission_visibility_fallback` | F/P | Visibility → FM → RC chain | Keep single entry (`apply_visibility_enforcement`) |
| `narration_visibility` | P | Build visibility contract for debug | **Move** to narration-constraint owner |
| `social_exchange_emission` | F | Emergency fallback lines | Keep |
| `speaker_contract_enforcement` | S/M | Speaker selection contract for debug | **Move** with narration-constraint owner |

### `game/final_emission_finalize.py` (7 imports)

| Import | Category | Why it exists | Reduction note |
|---|---|---|---|
| `fallback_provenance_debug` | F/M | Exit containment + gate exit record | Keep |
| `final_emission_boundary_contract` | P | Mutation asserts | Keep |
| `final_emission_meta` | M | FEM packaging, sidecars, lineage | Keep (+1 lazy import — hoist) |
| `final_emission_text` | X | Sanitize/normalize | Keep |
| `final_emission_validators` | P | Sentence split for strip helper | Keep |
| `stage_diff_telemetry` | T | Exit snapshot | Keep |
| `state_channels` | M/T | Public/debug/author projection | Keep — replay surface |

### `game/final_emission_visibility_fallback.py` (18 imports: 6 top + 12 lazy)

| Import | Category | Why it exists | Reduction note |
|---|---|---|---|
| `final_emission_meta` | M | Producer stamps, owner buckets | Keep |
| `exploration` | P | NPC pursuit session key | Keep |
| `final_emission_text` | X | Normalize | Keep |
| `interaction_context` | P | Mode inspect (lazy duplicate of top) | Dedupe lazy/top |
| `narration_visibility` | P | Validate visibility/FM/RC | Keep |
| `social` | P | Social kinds constant | Keep |
| `final_emission_opening_fallback` | F | Opening safe selection | Lazy — **facade** |
| `social_exchange_emission` | F | Strict-social emergency lines | Lazy — facade |
| `final_emission_passive_scene_pressure` | F | Passive candidates | Lazy — facade |
| `diegetic_fallback_narration` | F | NPC pursuit neutral | Lazy — facade |
| `anti_reset_emission_guard` | F | Anti-reset continuation | Lazy — facade |
| `final_emission_scene_emit_integrity` | F | Global fallback selection | Lazy — facade |
| `final_emission_opening_mode` | P | Opening mode gate | Lazy — facade |
| `final_emission_sealed_fallback` | F | Branch selector | Lazy — keep in sealed owner |
| `final_emission_first_mention_composition` | F | Grounded intro candidates | Lazy — facade |
| `final_emission_scene_facts` | P | Scene augmentation | Lazy — facade |
| `final_emission_boundary_contract` | P | Mutation asserts (in apply_* ) | Hoist to top |
| `final_emission_referential_clarity` | P | Default meta + local repair | Hoist to top |

### `game/final_emission_response_type.py` (10 imports)

| Import | Category | Why it exists | Reduction note |
|---|---|---|---|
| `final_emission_meta` | M | Default debug, opening bucket | Keep |
| `final_emission_opening_fallback` | F | Opening safe contract | Keep |
| `final_emission_opening_mode` | P | Opening mode detection | Keep |
| `final_emission_text` | X | Normalize | Keep |
| `final_emission_validators` | P | Contract validators | Keep |
| `opening_deterministic_fallback` | F | Opening context | Keep |
| `realization_provenance` | M | Fallback family attach | Keep |
| `response_policy_contracts` | P | Contract resolution | Keep |
| `social_exchange_emission` | F | Dialogue repairs | Keep |
| `upstream_response_repairs` | F | Upstream prepared emission | Keep |

Policy hub is appropriately scoped; stacks call `enforce_response_type_contract` only.

---

## Stack/pipeline call-order map

### Strict-social trunk (`run_strict_social_composition_trunk`)

```
1.  enforce_dialogue_plan_invariant_on_strict_social     [P — must precede build]
2.  build_final_strict_social_response                    [P/F]
3.  (optional) emergency source retag if dialogue_plan_blocked
4.  enforce_response_type_contract                       [P]
5.  (optional) minimal_social_emergency_fallback + re-RT  [F]
6.  _compute_scene_emit_integrity_assessment             [P → bundle for finalize]
7.  _apply_answer_completeness_layer                      [P]
8.  _apply_answer_exposition_plan_layer                  [P]
9.  _apply_response_delta_layer                          [P]
10. _apply_social_response_structure_layer                [P]
11. _apply_narrative_authenticity_layer                   [P]
12. apply_tone_escalation_layer                           [P]
13. apply_narrative_authority_layer                      [P]
14. enforce_emitted_speaker_with_contract                [S — after NA, before AR]
15. _sync_eff_social_to_resolution                       [S]
16. apply_anti_railroading_layer                         [P]
17. apply_context_separation_layer                        [P]
18. apply_player_facing_narration_purity_layer           [P]
19. apply_answer_shape_primacy_layer                      [P]
20. apply_scene_state_anchor_layer                        [P]
21. apply_fast_fallback_neutral_composition_layer         [P]
22. (conditional) strip_dialogue_from_text / emergency    [P/F]
23. record_stage_snapshot                                [T]
24. (conditional) realign_fallback_provenance_selector    [F/M]
25. merge_* debug into emission_debug (7 layer merges)    [M]
26. merge_conversational_memory_inspection                [M]
27. infer_accept_path_final_emitted_source                [M]
28. [accept path] build_gate_accept_fem_base + flag_non_hostile_escalation
29. [accept path] _apply_answer_exposition_plan_layer (final text re-check)
30. merge_gate_layer_metas_into_fem                       [M]
31. run_gate_terminal_enforcement_pipeline                [O]
32. log_final_emission_trace                              [T]
33. finalize_emission_output                              [O]
--- replace path diverges at 28 with replace FEM + sealed stamps, same 29–33 ---
```

### Non-strict trunk (`run_non_strict_layer_stack`)

```
0.  (preflight) banned phrase + passive_scene_pressure reasons   [P]
1.  enforce_response_type_contract                              [P]
2.  (optional) scene_opening accept promote + patch debug         [M/F]
3.  _compute_scene_emit_integrity_assessment                      [P]
4.  _apply_answer_completeness_layer                              [P]
5.  _apply_answer_exposition_plan_layer                           [P]
6.  _apply_response_delta_layer                                   [P]
7.  _apply_social_response_structure_layer                        [P]
8.  _apply_narrative_authenticity_layer                           [P]
9.  apply_tone_escalation_layer                                   [P]
10. apply_narrative_authority_layer                               [P]
11. apply_anti_railroading_layer                                  [P]
12. apply_context_separation_layer                                [P]
13. apply_player_facing_narration_purity_layer                    [P]
14. apply_answer_shape_primacy_layer                               [P]
15. apply_scene_state_anchor_layer                                 [P]
16. apply_fast_fallback_neutral_composition_layer                  [P]
17. merge_* debug (7 layers) + conversational_memory               [M]
18. apply_interaction_continuity_emission_step (validate_only)     [P — before FB]
19. _apply_fallback_behavior_layer                                 [P/F]
20. merge_fallback_behavior_into_emission_debug                    [M]
21. _narrative_mode_output_legality_assessment (pre-fork)          [P]
→ NonStrictLayerStackResult returned to generic exit fork
```

### Terminal pipeline (`run_gate_terminal_enforcement_pipeline`)

```
1.  _strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id
2.  apply_visibility_enforcement                                   [F/P chain]
      → visibility validate → (route) → first_mention → referential_clarity
3.  [strict_accept] apply_interaction_continuity_emission_step (validate_only)
4.  [strict_*] _apply_fallback_behavior_layer + merge               [P/F]
5.  _apply_referent_clarity_pre_finalize                            [P]
6.  narrative_mode_output assessment (+ strict emergency patch)    [P/F]
7.  apply_acceptance_quality_n4_floor_seam                          [P]
8.  attach_interaction_continuity_validation                        [P]
9.  _merge_narration_constraint_debug_into_outputs                  [M]
10. [generic_accept] reassert_scene_opening_accepted_candidate       [M]
```

Profile gates (`strict_accept`, `strict_replace`, `generic_accept`, `generic_replace`) branch inside steps 3–6 and 10 without changing global step order.

### Finalize (`finalize_emission_output`)

```
1.  record_stage_snapshot
2.  pop _gate_turn_packet_cache
3.  _sanitize_output_text
4.  strip_appended_route_illegal_contamination_sentences (×2 reseal)
5.  ensure_final_emission_meta_dict + scene_emit_integrity merge
6.  _refresh_output_mutation_lineage
7.  record_final_emission_gate_exit + finalize_upstream_fallback_overwrite_containment
8.  reassert_scene_opening_accepted_candidate
9.  package_dead_turn_snapshot + channel sidecars
10. project_public_payload return
```

---

## Order-sensitive dependencies (must not move casually)

| # | Dependency | Location | Why order matters | Protecting tests |
|---|---|---|---|---|
| 1 | Dialogue plan invariant **before** `build_final_strict_social_response` | Strict stack | C1-D fail-closed; strip deferred | `test_dialogue_plan_final_emission_gate.py`, orchestration_order |
| 2 | Response-type **before** repair layers | Both stacks | Repairs assume RT debug shape | `test_final_emission_gate_orchestration_order.py` |
| 3 | Response-delta **before** speaker enforcement | Strict stack | Speaker reads post-repair text | `test_apply_final_emission_gate_runs_response_delta_before_speaker_enforcement` |
| 4 | Speaker enforcement **before** AR/CS/purity/ASP/SSA/FFNC | Strict stack | BT divergence risk if moved post-layers | `test_speaker_contract_enforcement_extraction.py`, `post_speaker_finalize_probe.py` |
| 5 | FFNC **before** dialogue subtractive strip | Strict stack | Strip must not undo FFNC repairs | orchestration_order, strict_social tests |
| 6 | Layer merges **before** FEM base build | Strict accept/replace | FEM expects emission_debug populated | `test_final_emission_gate_diagnostics.py` |
| 7 | AEP re-apply **after** layers, **before** terminal | Strict stack | Downstream mutation re-check | orchestration_order |
| 8 | Visibility **before** IC/fallback/NMO in terminal | Terminal pipeline | Visibility may hard-replace text | `test_final_emission_visibility*.py`, context_separation stubs |
| 9 | Referent clarity pre-finalize **before** NMO/N4 | Terminal pipeline | AN6 sequencing | `test_final_emission_boundary_no_semantic_repair.py` |
| 10 | N4 floor **after** NMO, **before** IC attach | Terminal pipeline | Block N4 contract | `test_final_emission_gate_n4.py` |
| 11 | IC validate-only **before** fallback behavior | Non-strict stack | C2 continuity model | `test_apply_final_emission_gate_runs_response_type_then_continuity_then_fallback` |
| 12 | Fallback behavior **after** composition layers | Non-strict stack | FB reads final composed text | `test_fallback_behavior_gate.py` |
| 13 | Provenance containment **before** final strip reseal | Finalize | Block I containment | `test_fallback_overwrite_containment.py` |

---

## Reducible dependency candidates

### Candidate reduction map

| Current module | Current import | Category | Reason it exists | Proposed reduction pattern | Risk | Protecting tests |
|---|---|---|---|---|---|---|
| strict_social_stack | 7× `merge_*_into_emission_debug` from layer modules | M | Stamp emission_debug before FEM | `fem_assembly.merge_pre_terminal_layer_debug(out, layer_meta_bundle)` | Low | diagnostics, orchestration_order |
| non_strict_stack | Same 7 merge imports + `merge_fallback_behavior_*` | M | Same | Single merge entry on `fem_assembly` or `repairs` | Low | diagnostics |
| strict_social_stack | `fallback_provenance_debug.realign_*` | F/M | FFNC repair provenance | Return `provenance_realign_hint` from FFNC layer meta | Low | fast_fallback_composition, overwrite_containment |
| non_strict_stack | `finalize.patch_scene_opening_candidate_emission_debug` | M | Opening accept telemetry | Move to `response_type` or `opening_fallback` accept helper | Low | opening_fallback, orchestration_order |
| terminal_pipeline | `narration_visibility` + `speaker_contract_enforcement` + `build_narration_constraint_debug` | M | Narration constraint debug payload | New `final_emission_narration_constraint_debug.build_and_merge()` | Low | visibility, speaker_contract |
| terminal_pipeline | `finalize.reassert_scene_opening_accepted_candidate` | M | Generic accept text restore | Accept-path bundle method on opening owner | Low | opening_fallback, orchestration_order |
| strict_social_stack | `social_exchange_emission.log_*` | T | Decision/trace logging | `fem_assembly.log_gate_decision(...)` with payload bundle | Low | gate_diagnostics, selector_snapshots |
| non_strict_stack | `final_emission_passive_scene_pressure` | P | Preflight reject reasons | Gate preflight `NonStrictPreflightContext` input | Medium | passive_scene_pressure |
| strict_social_stack | `final_emission_scene_emit_integrity` | P | Finalize bundle | Gate preflight computes bundle once | Medium | scene_emit_integrity |
| visibility_fallback | 12 lazy fallback provider imports | F | Candidate selection | `sealed_fallback.select_visibility_safe_candidate()` facade | Medium | visibility_fallback, sealed_fallback |
| non_strict_stack + visibility_fallback | `_reply_already_has_concrete_interaction` duplicate | L | Concrete beat detection | Shared `final_emission_text` or `interaction_beat` helper | Low | visibility, non_strict preflight |
| strict_social_stack | Duplicate `final_emission_meta` import block | L | Historical merge | Single import statement | Low | delegator_regression |
| finalize | Lazy `apply_sanitizer_producer_attribution_to_fem` | M | Circular import avoidance | Hoist if safe, or re-export from meta | Low | boundary_convergence |
| terminal_pipeline | Direct `_merge_fallback_behavior_meta` on `_final_emission_meta` | M | Strict-path FEM patch | FEM assembly strict-terminal patch helper | Medium | fallback_behavior_gate |

---

## Non-reducible / order-sensitive dependencies

These imports are **genuine direct orchestration** and should remain on the hub unless the hub itself is split by path (out of scope):

- **Strict stack:** `dialogue_social_plan`, `build_final_strict_social_response`, `enforce_emitted_speaker_with_contract`, `run_gate_terminal_enforcement_pipeline`, `finalize_emission_output`.
- **Non-strict stack:** `enforce_response_type_contract`, layer `apply_*` chain, `apply_interaction_continuity_emission_step`, `_apply_fallback_behavior_layer`.
- **Terminal pipeline:** `apply_visibility_enforcement`, `_apply_referent_clarity_pre_finalize`, `apply_acceptance_quality_n4_floor_seam`, `attach_interaction_continuity_validation`, strict-social emergency patch helpers.
- **Visibility fallback:** `validate_player_facing_*` trilogy and route selector `route_visibility_enforcement_after_failed_validation` (snapshot order locked).
- **Response type:** Full validator/repair ladder (policy owner — stacks should not re-import sub-validators).

---

## Recommended BU2 implementation block

**BU2-A — Layer meta bundle (strict + non-strict)**  
Add `LayerMetaBundle` TypedDict/dataclass populated by layer calls. Move all `merge_*_into_emission_debug` imports from stacks into `final_emission_fem_assembly.merge_pre_terminal_layer_debug`. Stacks retain `apply_*` imports only.  
Target: −7 to −8 import edges per stack.  
Tests: `test_final_emission_gate_diagnostics.py`, `test_final_emission_gate_orchestration_order.py`.

**BU2-B — Narration constraint debug extraction (terminal pipeline)**  
Create `game/final_emission_narration_constraint_debug.py` owning `_merge_narration_constraint_debug_into_outputs`. Terminal pipeline imports one module instead of meta + narration_visibility + speaker_contract.  
Target: −2 import edges, clearer ownership.  
Tests: `test_final_emission_visibility.py`, `test_speaker_contract_enforcement.py`.

**BU2-C — Opening accept debug ownership (non-strict + terminal + finalize)**  
Colocate `patch_scene_opening_candidate_emission_debug` and `reassert_scene_opening_accepted_candidate` under `final_emission_opening_fallback` (or small opening_emit module). Hubs call one opening owner.  
Target: −2 cross-hub edges.  
Tests: `test_final_emission_opening_fallback.py`, orchestration_order.

**BU2-D — Visibility candidate facade (visibility_fallback only)**  
Add `select_visibility_safe_fallback()` on `final_emission_sealed_fallback` that internally delegates to existing visibility helpers; hoist lazy imports inside visibility module behind that facade. **No change to branch order** in `standard_visibility_safe_fallback`.  
Target: fan-out accounting cleanup; easier future trimming.  
Tests: `test_final_emission_visibility_fallback.py`, `test_final_emission_sealed_fallback.py`.

**Explicitly defer:** Merging strict/non-strict trunks, moving speaker enforcement to terminal pipeline, reordering visibility/FM/RC chain.

**BU3 complete (2026-06-20):** governance locks consolidated in `tests/helpers/gate_delegator_governance.py`; delegator regression router direct `game.*` imports eliminated.

---

## Files ChatGPT should inspect next

1. `game/final_emission_fem_assembly.py` — natural home for debug-merge consolidation.
2. `game/final_emission_generic_exit.py` — non-strict fork + terminal handoff; preflight context injection point.
3. `game/final_emission_gate.py` + `game/final_emission_gate_context.py` — pre-stack bundle construction.
4. `game/final_emission_sealed_fallback.py` — visibility candidate facade target.
5. `tests/test_final_emission_gate_delegator_regression.py` — static import locks to update in BU2.
6. `tests/helpers/post_speaker_finalize_probe.py` — speaker/terminal order probe harness.
7. `docs/audits/BT_speaker_finalization_divergence_discovery.md` — speaker ordering constraints.

---

## Related tests (stack/pipeline touchpoints)

| Test file | What it locks |
|---|---|
| `tests/test_final_emission_gate_orchestration_order.py` | Layer order, RT→IC→FB, speaker placement |
| `tests/test_final_emission_gate_delegator_regression.py` | BJ static source/import locks |
| `tests/test_final_emission_gate_n4.py` | N4 vs IC attach order |
| `tests/test_final_emission_gate_diagnostics.py` | FEM/debug merge shapes |
| `tests/test_final_emission_gate_selector_snapshots.py` | Fallback selector snapshots |
| `tests/test_final_emission_visibility_fallback.py` | Visibility route order |
| `tests/test_final_emission_acceptance_quality.py` | N4 terminal pipeline wiring |
| `tests/test_speaker_contract_enforcement_extraction.py` | Strict trunk speaker fragment |
| `tests/helpers/post_speaker_finalize_probe.py` | Post-speaker layer + terminal order |
| `tests/test_final_emission_response_type.py` | RT owner contract |
| `tests/test_fallback_overwrite_containment.py` | Finalize provenance order |

---

## Validation performed

Static checks only (no runtime behavior changes):

```text
rg "^(from game\\.|import game\\.)" game/final_emission_strict_social_stack.py game/final_emission_non_strict_stack.py game/final_emission_terminal_pipeline.py game/final_emission_finalize.py game/final_emission_visibility_fallback.py game/final_emission_response_type.py

python -c "<import enumeration script>"  # 22/19/14/7/18/10 total game imports

git diff --check
```

Machine-readable classification: `docs/audits/BU1_stack_pipeline_dependency_classification.csv`.
