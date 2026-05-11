# Golden Replay Readiness - Cycle Track A

Date: 2026-05-11

Scope: information-gathering only. No replay suite implemented. No runtime behavior changed.

## 1. Existing Replay / Snapshot / Scenario Test Infrastructure

| Path | Purpose | Reuse / extend / avoid | Important exposed surface |
|---|---|---|---|
| `tests/helpers/transcript_runner.py` | Thin deterministic chat transcript harness over `game.api.chat`, with storage patching, clean campaign reset, and per-turn snapshots. | Reuse and extend. This is the closest fit for compact golden replay scenarios. | `patch_transcript_storage`, `write_default_bootstrap_scenes`, `new_clean_campaign`, `run_transcript_turns`, `run_transcript`, `snapshot_from_chat_payload`, `compact_snapshot_summary`, `latest_target_id`, `latest_target_source`, `format_turn_debug`. |
| `tests/test_transcript_regression.py` | Existing multi-turn transcript regressions over FastAPI `TestClient`, focused on continuity, lead travel, retry exhaustion, and social follow-up. | Reuse fixtures/patterns, avoid adding broad golden assertions here. | Local seed helpers such as `_seed_tavern_patrol_lead_old_milestone`, `_seed_frontier_gate_eastern_square_stale_milestone_lead`, `_gm_response`, `_gm_with_non_authoritative_scene`. |
| `tests/test_turn_pipeline_shared.py` | Broad chat/action pipeline owner for route, sanitizer, dialogue-lock, action outcome, and strict-social pipeline smoke. | Extend only for owner-level regressions; use as source of fixture snippets. | Tests for directed questions, dialogue lock, sanitizer leak prevention, action-outcome contract, wrong-speaker strict-social repair. |
| `tests/test_snapshots.py` | Persistence snapshot/save-slot tests, not golden-output snapshots. | Avoid for replay golden suite except as storage pattern reference. | `_setup_data_dir`, `create_snapshot`, `load_snapshot`, `list_snapshots`. |
| `game/scenario_spine.py` and `tests/test_scenario_spine_contracts.py` | Deterministic scenario-spine schema and validation tests. | Reuse for scenario-spine three-branch replay fixture shape. | `ScenarioSpine`, `ScenarioBranch`, `ScenarioTurn`, anchors/checkpoints, `scenario_spine_from_dict`, `scenario_spine_to_dict`, `validate_scenario_spine_definition`. |
| `tools/run_scenario_spine_validation.py` and `tests/test_run_scenario_spine_validation.py` | CLI that drives spine branches through `/api/chat`, records transcript artifacts, runs offline evaluation. | Reuse concepts, probably not directly for compact golden tests because it is operator/artifact oriented. | `load_spine`, `resolve_branch_id`, `build_transcript_turn_meta`, transcript/run_debug artifact shape. |
| `game/scenario_spine_eval.py` | Offline health evaluator for scenario-spine transcript rows. | Reuse only for branch divergence and metadata completeness, not exact golden drift. | `evaluate_scenario_spine_session`, `evaluate_scenario_spine_branch_divergence`, `ensure_transcript_turn_meta_dict`, `minimal_complete_transcript_turn_meta`. |
| `tests/helpers/n1_scenario_spine_harness.py` / `tests/helpers/n1_scenario_spine_contract.py` | N1 long-session harness with stable run ids, fingerprints, branch comparisons, health artifact dicts. | Extend selectively for deterministic JSON/fingerprint helpers; avoid mixing N1 semantics into compact replay. | `deterministic_json_dumps`, `stable_n1_run_id`, `execute_n1_spine_branch_with_shared_prefix`, `compare_n1_branch_session_health_summaries`. |
| `tests/helpers/synthetic_runner.py`, `tests/helpers/synthetic_fake_gm.py` | Optional synthetic-player runner and deterministic fake GM. | Useful fallback for non-live model seams; less direct than transcript runner for route/FEM assertions. | `run_synthetic_session`, `make_deterministic_fake_responder`, `install_fake_responder_monkeypatches`. |

There is no obvious existing golden-replay framework that records canonical expected rows and classifies exact/structural/semantic drift. The closest reusable pieces are `tests/helpers/transcript_runner.py`, scenario-spine schema/eval, and deterministic JSON/fingerprint helpers in the N1 harness.

## 2. Current Scenario-Spine Model

| Path | Key data structures | Available fields | Missing for golden replay assertions |
|---|---|---|---|
| `game/scenario_spine.py` | `ScenarioSpine`, `ScenarioBranch`, `ScenarioTurn`, `ContinuityAnchor`, `ReferentAnchor`, `ProgressionAnchor`, `ScenarioCheckpoint`. | `spine_id`, `fixed_start_state`, `branches[].turns[].turn_id/player_prompt/notes`, continuity/referent/progression anchors, checkpoints, `smoke_only`, `title`, `notes`. | No expected runtime route, speaker, final-emission source, fallback family, exact/normalized text, or per-turn invariant assertions. No explicit shared-prefix branch point model. |
| `data/validation/scenario_spines/frontier_gate_long_session.json` | Canonical three-branch long-session fixture. | Branches: `branch_cautious_observe`, `branch_direct_intrusion`, `branch_social_inquiry`; anchors/checkpoints; fixed start state. | Branches are independent scripts, not golden assertions. No compact nine-scenario fixture rows. |
| `data/validation/scenario_spines/c1a_opening_convergence_paths.json` | Smoke-only opening convergence fixture. | Short branches for campaign start, location entry, post-transition, resume entry, multi-transition smoke. | Good near-match for opening fallback path, but lacks expected final route/source/fallback assertions. |
| `tests/helpers/n1_scenario_spine_contract.py` | N1-specific spine/branch point definitions. | `N1ScenarioSpineDefinition`, `N1BranchPointDefinition`, `N1BranchDefinition`, revisit/progression/anchor health fields. | Separate from `game.scenario_spine` and not used by `tools/run_scenario_spine_validation.py`; useful branch-point concepts but not canonical compact schema. |
| `game/scenario_spine_eval.py` | Offline evaluator around `ScenarioSpine`. | Turn row normalization, metadata completeness, branch coherence, divergence, opening/continuation convergence. | Health scoring, not golden replay. It does not compare expected exact values for route/speaker/FEM fields. |

Recommendation: model compact golden scenarios as a test-only fixture with `scenario_id`, `turns`, `gpt_outputs`, and `expectations` over invariant fields. For the three-branch replay, either add expected fields beside a small `ScenarioSpine` smoke fixture or keep a golden-specific fixture that references `ScenarioSpine` branch ids.

## 3. Runtime Pipeline Entry Points

| Entry point | Path | Expected inputs | Output shape | Mutates state | Replay suitability |
|---|---|---|---|---|---|
| Chat orchestrator | `game/api.py::chat(req: ChatRequest, ui_mode="player")` | `ChatRequest(text=...)`; reads storage-backed campaign/session/world/scene. | API dict: `ok`, `gm_output`, state payload, optional `resolution`, optional `gm_output_debug`. | Yes: session/world/combat/log/debug traces. | Best end-to-end replay target when paired with patched storage and monkeypatched `game.api.call_gpt`. |
| Engine/prompt pipeline | `game/api.py::_run_resolved_turn_pipeline(...)` | Loaded state, authoritative `resolution`, `normalized_action`, text, segmented turn, route, directed social entry. | `(scene, session, combat, gm, clue_updates, response_type_contract)`. | Yes: applies authoritative resolution mutation and builds narration. | Good integration seam, but more setup-heavy than `chat`; useful for focused action/final-emission cases. |
| GPT/expression seam | `game/gm.py::call_gpt(messages, **route_context)` called through `game.api.call_gpt`. | Message list plus route metadata (`purpose`, response policy, retry fields). | GM dict with `player_facing_text`, tags, metadata, optional state proposals. | No direct state mutation. | Mockable boundary. Existing tests monkeypatch `game.api.call_gpt`. |
| Prompt/planner entry | `game/gm.py::build_messages(...)` and `game/api.py::_build_gpt_narration_from_authoritative_state(...)` | Full state, recent log, user text, resolution, scene runtime, narration context. | Message list; `_build_gpt...` returns GM dict after retries/policy. | `_build_gpt...` mutates session debug/CTIR/plan attachments. | Use only if asserting prompt/planner metadata; otherwise observe through `chat`. |
| Planner convergence seam | `game/planner_convergence.py::build_planner_convergence_report(...)` | `path_label`, owner, session, optional prompt payload. | Report dict consumed by `planner_convergence_ok`. | No direct state mutation. | Assertable through turn meta/debug if needed, but not a golden baseline core. |
| Gate/legal validation | `game/final_emission_gate.py::apply_final_emission_gate(...)` | GM dict, resolution, session, scene id/envelope, world. | Finalized GM dict with sidecar/internal FEM and finalized text. | Mutates GM dict, not storage. | Best direct seam for fallback/source/no-semantic-mutation unit golden rows. |
| Final response packaging | `game/api_turn_support.py::_build_turn_response_payload(...)` | GM dict, optional resolution, include flag. | API response dict with stripped `gm_output` and optional `gm_output_debug`. | Reads storage; may finalize GM if not finalized. | Important because post-gate metadata is split between `gm_output` and `gm_output_debug`. |
| Strict-social emission | `game/social_exchange_emission.py::build_final_strict_social_response(...)` | Candidate text, resolution/session/world/scene context. | `(text, details)` where details includes source/fallback/provenance. | No storage mutation. | Good focused seam for wrong-speaker/strict-social source behavior; end-to-end should still go through `chat`. |
| Speaker legality | `game/speaker_contract_enforcement.py::enforce_emitted_speaker_with_contract(...)` | Text, resolution, metadata/trace. | Repaired text plus enforcement payload. | No storage mutation. | Direct owner for speaker mismatch assertions. |

## 4. Invariant Assertion Targets

| Invariant | Currently exposed? | Where exposed | Minimal instrumentation if absent | Likely owner |
|---|---|---|---|---|
| route | Yes | `trace["turn_trace"]["social_contract_trace"]["route_selected"]`; `resolution.kind`; `trace["canonical_entry_path"]`; `tests/helpers/transcript_runner.py` snapshot debug. | Snapshot helper should include latest `turn_trace` social contract trace explicitly. | `game/api_turn_support.py` for trace shape; test helper for capture. |
| speaker | Yes | `resolution.social.npc_id`; `speaker_selection_contract` in `resolution.metadata.emission_debug` / FEM; `social_contract_trace.reply_owner_actor_id/final_reply_owner`; interaction context. | Add a small snapshot projection for speaker contract and final reply owner. | `game/interaction_context.py`, `game/speaker_contract_enforcement.py`, test helper. |
| fallback family | Yes, mostly | FEM keys: `fallback_family_used`, `realization_fallback_family`; strict-social details include `final_emitted_source`. | None for post-gate; snapshot helper should read FEM from `gm_output_debug` too. | `game/final_emission_meta.py` read helpers; `game/final_emission_gate.py`. |
| final emission source | Yes | FEM `final_emitted_source`, `final_route`; strict-social details. | None if replay helper uses `read_final_emission_meta_from_turn_payload`, not only `gm_output`. | `game/final_emission_meta.py`. |
| no semantic mutation | Partly | FEM `final_emission_boundary_semantic_repair_disabled`, response-type upstream-prepared flags; stage/probe helpers for normalized text deltas. | Golden harness needs before/after normalized text capture for selected direct gate rows, or compare GPT candidate to final text with allowed packaging transforms. | `game/final_emission_gate.py` plus test-only probe/helper. |
| sanitizer/scaffold leakage | Yes | Final `gm_output.player_facing_text`; `game/output_sanitizer.py` detectors/patterns; tests in `test_turn_pipeline_shared.py` and `test_output_sanitizer.py`. | None; include leakage predicate in golden assertion helper. | `game/output_sanitizer.py`; test helper. |
| dialogue lock | Yes | `route_selected`, `resolution.kind`, `resolution.social.npc_id`, `social_turn_contract`, `interaction_context.active_interaction_target_id`. | Snapshot helper should expose `social_contract_trace`. | `game/interaction_routing.py`, `game/interaction_context.py`, `game/api_turn_support.py`. |
| alias/declaration handling | Yes | `canonical_entry` trace fields: `declared_switch_detected`, `declared_switch_target_actor_id`, `continuity_overridden_by_declared_switch`; dialogue plan alias fields in `game/dialogue_social_plan.py`. | For golden rows, include `trace.canonical_entry` in snapshot. | `game/interaction_context.py`, `game/dialogue_social_plan.py`, test helper. |
| vocative override behavior | Yes | `canonical_entry` trace fields: `spoken_vocative_detected`, `spoken_vocative_target_actor_id`, `continuity_overridden_by_spoken_vocative`; `resolution.social.target_source`. | Include `canonical_entry` in snapshot. | `game/interaction_context.py`, test helper. |
| strict-social speaker legality | Yes | `speaker_contract_enforcement` payload in emission debug/FEM; speaker contract fields; final text; strict-social tags. | Use `read_final_emission_meta_from_turn_payload` and expose `speaker_contract_enforcement_reason`. | `game/speaker_contract_enforcement.py`, `game/final_emission_gate.py`. |

## 5. Existing Canonical Fixtures or Near-Matches

| Target scenario | Exact existing fixture/test | Near-match fixture/test | Missing coverage | Best location to add |
|---|---|---|---|---|
| 1. Directed NPC question | `tests/test_turn_pipeline_shared.py::test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`; `test_chat_dialogue_lock_routes_npc_directed_question_regressions`. | `tests/test_directed_social_routing.py::test_resolve_adjudication_none_for_directed_runner_question`. | No compact golden row that records route + speaker + FEM source together. | New `tests/test_golden_replay.py` using transcript helper. |
| 2. Vocative override after prior continuity | `tests/test_dialogue_interaction_establishment.py::test_comma_vocative_overrides_prior_active_interlocutor_for_binding_and_emission`. | `tests/test_directed_social_routing.py::test_spoken_vocative_*_overrides_*_continuity`. | Need multi-turn replay expectation over prior continuity then vocative switch. | New golden replay fixture; reuse seed from directed social routing. |
| 3. Wrong-speaker strict-social emission | `tests/test_turn_pipeline_shared.py::test_pipeline_strict_social_wrong_opening_speaker_repaired_to_canonical`. | `tests/test_social_speaker_grounding.py` speaker grounding cases; `tests/test_speaker_contract_enforcement.py`. | Need exact invariant capture for final speaker/source and no illegal attribution. | New golden replay plus maybe direct gate fixture. |
| 4. Declared alias dialogue plan | `tests/test_block_u_finalize_stack_divergence.py::test_block_z_canonical_plan_with_declared_alias_passes_dialogue_plan_gate`; `test_block_z_canonical_plus_declared_alias_avoids_subtractive_strip_first`. | `tests/test_block_t_speaker_relocation_shadow_equivalence.py::test_block_aa_dual_run_declared_alias_dialogue_plan_shadow_equivalence`; `tests/test_dialogue_social_plan_block_y.py`. | Not end-to-end through `chat`; likely direct gate/plan baseline first. | New golden direct-gate row or extend a test-only fixture helper. |
| 5. Thin answer/action outcome at final emission | `tests/test_bounded_partial_quality.py::test_thin_generic_identity_line_triggers_substance_failure`; `tests/test_fallback_behavior_validator.py::test_validate_fallback_behavior_rejects_bare_thin_identity_line_without_known_and_lead`. | `tests/test_turn_pipeline_shared.py::test_chat_mixed_scene_object_investigation_question_recovers_action_outcome`; `tests/test_social_exchange_emission.py::test_strict_social_emission_action_outcome_contract_repairs_exposition_only_candidate`. | Golden needs final FEM source/route and response-type/action outcome assertion together. | New golden replay row, likely direct `chat` for action and direct gate for final-emission edge. |
| 6. Sanitizer scaffold leakage | `tests/test_turn_pipeline_shared.py::test_chat_final_output_sanitizer_blocks_internal_scaffold_labels`. | `tests/test_output_sanitizer.py`; `tests/test_diegetic_fallback_block4.py::test_enforce_scene_momentum_no_scaffold_headers`. | Golden should capture leaked input, final text, and final route/source. | New golden replay row with monkeypatched GPT scaffold text. |
| 7. Opening fallback path | `tests/test_start_campaign_api.py::*opening*`; `tests/test_upstream_response_repairs.py::*opening*`; `tests/test_final_emission_gate.py` opening fallback snapshots. | `data/validation/scenario_spines/c1a_opening_convergence_paths.json`; `tests/test_api_narration_path_selection.py::test_finalize_player_facing_scene_opening_carries_upstream_opening_fallback_payload`. | Need compact replay row for opening fallback authorship/source. | Golden row using `chat("Begin the campaign...")` or `start_campaign` direct API, plus FEM assertion. |
| 8. Lead follow-up with dialogue lock | `tests/test_transcript_regression.py::test_transcript_tavern_runner_patrol_wait_beat_then_follow_up_question`; `test_transcript_passive_wait_then_followup_then_departure_stays_coherent`. | `tests/test_scene_transition_authority.py::test_actionable_lead_declared_travel_authoritative_arrival_and_lead_metadata`. | Need record of route/dialogue lock, pending lead, and final speaker/FEM. | New multi-turn golden replay using existing tavern runner fixture. |
| 9. Scenario-spine three-branch replay | No exact golden replay. | `data/validation/scenario_spines/frontier_gate_long_session.json`; `tools/run_scenario_spine_validation.py`; `game.scenario_spine_eval.evaluate_scenario_spine_branch_divergence`. | Need compact three-branch smoke fixture and expected branch divergence/metadata rows. | New test fixture under `tests/fixtures` or `data/validation/scenario_spines/golden_replay_smoke.json`; test-only harness. |

## 6. Drift Recording Strategy

Current repo distinction:

- Exact drift: partial. N1 harness records stable SHA-256 fingerprints of normalized text, but no canonical golden expected file.
- Structural drift: yes. Scenario-spine evaluator checks metadata completeness, branch coherence, opening/continuation convergence, and test inventory classifies tests structurally.
- Semantic drift: advisory/heuristic. Audits flag ownership/semantic reconstruction risk; behavioral and playability evaluators detect coherence/agency drift, not golden semantic equivalence.

Relevant files:

| Path | Purpose | Can support golden replay? | Gaps |
|---|---|---|---|
| `tests/helpers/n1_scenario_spine_harness.py` | Stable fingerprints, deterministic JSON, run ids, branch health artifacts. | Yes for exact fingerprints and deterministic serialization. | N1-specific contracts and no expected-vs-actual diff classification. |
| `game/scenario_spine_eval.py` | Structural health and branch divergence scoring over transcript rows. | Yes for structural drift in scenario-spine branch replay. | Does not classify exact text drift or semantic invariant drift. |
| `tests/helpers/behavioral_gauntlet_eval.py` | Normalizes transcript-like rows and flags speaker/thread/reset contradictions. | Useful semantic-ish smoke. | Evaluator-oriented, not exact golden diff. |
| `tools/run_scenario_spine_validation.py` | Writes transcript, debug, session-health, and operator summaries. | Useful artifact model for drift report output. | CLI is larger than compact pytest golden suite; artifacts are timestamped/operator oriented. |
| `tools/final_emission_ownership_audit.py`, `tools/validation_layer_audit.py`, `tools/realization_layer_audit.py` | Advisory drift scans. | Use as conceptual labels only. | Static heuristics; not per-replay diff tools. |
| `tests/helpers/speaker_gate_order.py`, `tests/helpers/post_speaker_finalize_probe.py`, `tests/helpers/speaker_relocation_shadow_harness.py` | Normalized text comparison and layer delta probes. | Useful for no-semantic-mutation and speaker-finalization direct tests. | Too specialized for general replay unless wrapped. |

Recommended drift model for next phase:

- `exact_drift`: normalized final text hash differs from fixture expectation.
- `structural_drift`: route/speaker/FEM/source/contract field differs.
- `semantic_drift`: final text violates scenario-specific predicates such as scaffold leakage, wrong speaker, missing answer/action outcome, or branch non-divergence.

## 7. Recommended Implementation Plan

### A. Minimal harness / fixture shape

- Files likely modified: new `tests/test_golden_replay.py`, optional `tests/helpers/golden_replay.py`, optional fixture JSON under `tests/fixtures/golden_replay/`.
- Tests likely added: harness self-test with one directed NPC question.
- Risk: low.
- Parallel: can run in parallel with drift report artifact generation if fixture schema is agreed early.
- Notes: build on `tests/helpers/transcript_runner.py`; use monkeypatched `game.api.call_gpt`; capture `gm_text`, `resolution`, FEM via `read_final_emission_meta_from_turn_payload`, latest `turn_trace`, and `canonical_entry` from debug traces.

### B. Invariant capture

- Files likely modified: `tests/helpers/golden_replay.py` or `tests/helpers/transcript_runner.py` only.
- Tests likely added: assertions that route, speaker, final source, fallback family, scaffold leak status, and dialogue-lock fields are captured from one existing scenario.
- Risk: low-medium because metadata may live in `gm_output_debug` rather than stripped `gm_output`.
- Parallel: can run with C/D scenario authoring once capture schema is stable.

### C. First 3 scenarios

- Files likely modified: golden fixture + `tests/test_golden_replay.py`.
- Tests likely added: directed NPC question, vocative override after continuity, wrong-speaker strict-social emission.
- Risk: medium; wrong-speaker case may need direct gate input to stay deterministic.
- Parallel: can run in parallel with E after assertion result shape is final.

### D. Remaining 6 scenarios

- Files likely modified: golden fixture + test file; possibly small fixture seeds copied from existing tests.
- Tests likely added: declared alias dialogue plan, thin answer/action outcome, sanitizer scaffold leakage, opening fallback, lead follow-up/dialogue lock, three-branch scenario-spine smoke.
- Risk: medium-high. Opening fallback and declared alias plan may be more stable as direct seam tests than full `chat` tests.
- Parallel: can split by scenario if fixture rows are independent.

### E. Drift report artifact generation

- Files likely modified: `tests/helpers/golden_replay.py`; optional script `tools/run_golden_replay.py` only if pytest output is insufficient.
- Tests likely added: unit test for diff classification using synthetic expected/actual rows.
- Risk: low.
- Parallel: can run with C/D.
- Notes: start with pytest assertion diff plus optional JSON artifact under `artifacts/golden_replay/` for local runs; avoid introducing dependencies.

### F. CI or local command integration

- Files likely modified: `pytest.ini` markers and/or `Makefile`; maybe docs `tests/README_TESTS.md`.
- Tests likely added: none beyond marker smoke.
- Risk: low.
- Parallel: after A-E stabilize.
- Suggested command: `python -m pytest tests/test_golden_replay.py -q`.

## 8. Files to paste back into GPT

Smallest useful set for next-step block generation:

1. `audits/golden_replay_readiness_2026-05-11.md`
2. `tests/helpers/transcript_runner.py`
3. `game/scenario_spine.py`
4. `game/scenario_spine_eval.py` excerpts: public API and `_normalize_turn_row` / branch divergence helpers
5. `tools/run_scenario_spine_validation.py` excerpts: `build_transcript_turn_meta`, transcript row writing, branch execution
6. `game/api.py` excerpts: `chat`, `_run_resolved_turn_pipeline`, `_build_gpt_narration_from_authoritative_state`, `_complete_opening_turn_persistence_like_chat`
7. `game/api_turn_support.py` excerpts: `_build_turn_response_payload`, `_build_compact_turn_trace`, `build_social_contract_turn_trace`
8. `game/final_emission_meta.py` excerpts: `read_final_emission_meta_from_turn_payload`, `read_final_emission_meta_dict`, normalized observability helpers
9. `game/final_emission_gate.py` excerpts: `apply_final_emission_gate` FEM route/source sections
10. `game/interaction_context.py` excerpts: `resolve_directed_social_entry`, `resolve_authoritative_social_target`, `resolve_declared_actor_switch`, `build_speaker_selection_contract`
11. `game/dialogue_social_plan.py`
12. `game/social_exchange_emission.py` excerpts: `strict_social_emission_will_apply`, `build_final_strict_social_response`, strict-social details/fallback source sections
13. Existing near-match tests: `tests/test_turn_pipeline_shared.py` sections around directed question, sanitizer leakage, action outcome, wrong-speaker strict-social; `tests/test_transcript_regression.py` tavern runner lead follow-up section; `tests/test_directed_social_routing.py` vocative/declared switch cases.

Tests run: none. This pass was repository inspection plus report creation only.
