# BM Large Test File Decomposition Discovery

> **Status:** Completed (BM4–BM10). See `docs/refactor/BM_large_test_file_decomposition_completion.md` for the final file map, validation commands, and closure notes. The monolith paths below describe the **pre-decomposition baseline**.

## Scope

- Target files:
  - `tests/test_golden_replay.py`
  - `tests/test_final_emission_gate.py`

Discovery only — no tests moved, deleted, or refactored in this block.

## Baseline

| File | Lines | Tests | Fixtures/helpers | Primary production imports | Current status |
|---|---:|---:|---:|---|---|
| `tests/test_golden_replay.py` | 803 | 13 | 0 module-level; 7 inline nested `_fake_call_gpt` closures | `game.api.chat`, `game.storage`, `game.final_emission_meta`, `game.scenario_spine`, `game.scenario_spine_eval`, `game.models` | **13 passed** in ~14.7s (`pytest tests/test_golden_replay.py -q`) |
| `tests/test_final_emission_gate.py` | 2,917 | 159 (36 non-BJ + 123 BJ) | 9 module-level helpers + 3 module constants | `game.final_emission_gate` (+ 15 `game.final_emission_*` submodules), `game.acceptance_quality`, `game.final_emission_meta`, `game.realization_provenance`, `game.opening_deterministic_fallback`, `game.social_exchange_emission`, `game.interaction_context` | **159 passed** in ~2.2s (`pytest tests/test_final_emission_gate.py -q`) |

### Imported test helpers (by file)

**`test_golden_replay.py`**

| Helper module | Role |
|---|---|
| `tests/helpers/golden_replay.py` | Replay orchestration, observation projection, protected assertions, profile bundles |
| `tests/helpers/golden_replay_fixtures.py` | World seeds, `gm_response`, `golden_replay_chat_stubs` |
| `tests/helpers/golden_replay_profiles.py` | Long-session stability/lineage/fallback profile constants |
| `tests/helpers/transcript_runner.py` | Campaign bootstrap, storage patching, snapshots |
| `tests/helpers/failure_dashboard_report.py` | Protected replay failure recording |
| `tests/helpers/emission_smoke_assertions.py` | `apply_final_emission_gate_consumer` (direct-seam tests) |
| `tests/helpers/gate_equivalence_monkeypatch.py` | Speaker/strict-social patch helpers |
| `tests/helpers/strict_social_harness.py` | `runner_strict_bundle` |
| `tests/helpers/dialogue_social_plan.py` | Dialogue plan attachment |
| `tests/helpers/block_stu_equivalence_fixtures.py` | Locked runner contract stubs |
| `tests/helpers/opening_fallback_evidence.py` | Opening GM output scaffold |
| `tests/helpers/replay_observed_row_fixtures.py` | Synthetic protected-failure turn row |

**`test_final_emission_gate.py`**

| Helper module | Role |
|---|---|
| `tests/helpers/emission_smoke_assertions.py` | FEM smoke readers, response-type contract |
| `tests/helpers/gate_equivalence_monkeypatch.py` | Speaker contract patching |
| `tests/helpers/opening_fallback_evidence.py` | Sealed fallback owner-bucket asserts |
| `tests/helpers/strict_social_harness.py` | Strict-social gate cases |
| `tests/helpers/narrative_mode_validator_fixtures.py` | CTIR continuation fixture |
| `tests/helpers/gate_thin_boundary_locks.py` | BJ-129 thin-boundary shape lock (imported inside test) |

**`tests/conftest.py`** — session-level only (skip markers, dashboard artifact hooks). No fixtures shared by either target file.

---

## Ownership Clusters

### `tests/test_golden_replay.py`

| Cluster | Tests | Fixtures/helpers | Production owner | Suggested destination | Risk |
|---|---:|---|---|---|---|
| **Protected replay / failure classification** | 1: `test_protected_golden_assertion_failure_records_canonical_report` | `protected_speaker_failure_turn`, `clear_recorded_protected_replay_failures`, `recorded_protected_replay_failure_rows`, `write_protected_replay_failure_report_if_present` | `tests/helpers/failure_dashboard_report.py` + `tests/helpers/golden_replay.py` (protected bridge) | `tests/test_golden_replay_protected_bridge.py` | **Low** |
| **Short structural replay invariants** | 6: `directed_npc_question`, `vocative_override_after_prior_continuity`, `wrong_speaker_strict_social_emission`, `thin_answer_action_outcome_final_emission`, `sanitizer_scaffold_leakage`, `lead_followup_with_dialogue_lock` | `run_golden_replay`, `golden_replay_chat_stubs`, `gm_response`, world seeds (`seed_*`), `assert_protected_golden_turn_observation`, `protected_social_speaker_observation_expectation`, `protected_structural_expectation`, inline `_fake_call_gpt` | `tests/helpers/golden_replay.py` (orchestration); downstream owners exercised via full chat path | `tests/test_golden_replay_structural_invariants.py` | **Medium** (integration, ~1–2s each) |
| **Direct-seam gate consumer replay** (mixed ownership) | 2: `golden_direct_seam_declared_alias_dialogue_plan`, `golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership` | `apply_final_emission_gate_consumer`, `observed_turn_from_gate_output`, `runner_strict_bundle`, `patch_get_speaker_selection_contract`, `patch_build_final_strict_social_response`, `opening_gm_output` | Gate/opening owners via consumer seam; observation via golden replay projection | `tests/test_golden_replay_direct_seam.py` (or defer to gate/opening owner suites) | **Medium** — crosses gate + replay projection |
| **Long-session manifest / projection** | 3: `frontier_gate_social_inquiry_25_turn_structural_stability`, `frontier_gate_social_inquiry_25_turn_resume_persistence_supporting`, `frontier_gate_direct_intrusion_25_turn_diagnostic_stability` | `frontier_gate_branch_replay_fixture`, profile constants (`FRONTIER_GATE_*`), `assert_golden_replay_profile_bundle`, `summarize_long_session_replay_observations`, `evaluate_golden_replay_continuity_drift`, `render_long_session_replay_summary_markdown` | `tests/helpers/golden_replay.py` + `tests/helpers/golden_replay_profiles.py`; manifest from `data/validation/scenario_spines/frontier_gate_long_session.json` | `tests/test_golden_replay_long_session.py` | **Medium–High** (25-turn runs; resume test is custom) |
| **Scenario spine smoke / manifest** | 1: `scenario_spine_three_branch_structural_smoke` | `ScenarioSpine`/`ScenarioBranch`/`ScenarioTurn`, `validate_scenario_spine_definition`, `assert_golden_turn_observation`, `minimal_complete_transcript_turn_meta` | `game.scenario_spine`, `game.scenario_spine_eval` | `tests/test_golden_replay_scenario_spine.py` | **Medium** |
| **Shared fixtures/helpers** | — | All imported helpers above; no module-level fixtures in-file | — | Remain in `tests/helpers/*` | — |
| **Unclear / mixed ownership** | 2 direct-seam tests (see above) | Gate consumer + replay projection combined | Final emission gate + opening fallback + golden replay projection | Defer decision until gate vs replay boundary is explicit | **Medium** |

### `tests/test_final_emission_gate.py`

| Cluster | Tests | Fixtures/helpers | Production owner | Suggested destination | Risk |
|---|---:|---|---|---|---|
| **N4 acceptance-quality gate order** | 3: `acceptance_quality_n4_off_when_narrative_plan_absent`, `acceptance_quality_n4_replace_path_reruns_seam_on_fallback_and_fem_terminal`, `acceptance_quality_n4_runs_before_interaction_continuity_attachment` | `_minimal_n4_narrative_plan`, `_N4_*` constants | `game.final_emission_acceptance_quality` (order); scoring in `game.acceptance_quality` | `tests/test_final_emission_gate_n4.py` | **Low–Medium** |
| **Gate orchestration / layer order** | 20: `apply_final_emission_gate_runs_*`, `block_f_*`, `strict_social_preserves_*`, `non_strict_*`, `block_l_*`, `social_response_structure_layer_*`, `response_type_failure_skips_*`, `strict_social_narrative_mode_output_enforcement_terminal_fallback` | `_strong_interaction_continuity_contract`, `_ssa_contract`, `_secondary_social_response_structure_contract`, `_dialogue_response_policy_with_social_structure`, `_narrative_mode_plan_payload`, `runner_strict_bundle`, `patch_get_speaker_selection_contract` | `game.final_emission_gate` orchestrating stacks/pipeline | `tests/test_final_emission_gate_orchestration_order.py` | **Medium** (heavy monkeypatch) |
| **Final emission diagnostics / metadata** | 4: `final_emission_meta_and_emission_debug_merge_scene_state_anchor`, `apply_final_emission_gate_tolerates_missing_gm_output_for_narration_constraint_debug`, `apply_final_emission_gate_surfaces_narration_constraint_debug_in_metadata`, `final_gate_terminal_repair_branch_records_gate_terminal_family` | `_ssa_contract` (shared with orchestration) | `game.final_emission_terminal_pipeline`, `game.final_emission_meta` | `tests/test_final_emission_gate_diagnostics.py` | **Low–Medium** |
| **Selector snapshots / sealed-branch order (Block AG)** | 10: `selector_snapshot_*` (5), `sealed_branch_order_*` (2), `block_ai_block_ag_selector_order_snapshots_remain_entrypoints`, `final_gate_plain_valid_candidate_has_source_without_fallback_family` | `_visibility_offscene_npc_gate_bundle`, `_assert_known_realization_family`, `_assert_source_markers_in_order` | `game.final_emission_gate` selector entrypoints + `game.realization_provenance` | `tests/test_final_emission_gate_selector_snapshots.py` | **Low** (mostly static) |
| **Final-emitted source ownership (Block M4)** | 2: `block_m4_final_emitted_source_accept_precedence_ladders_are_locked`, `block_m4_replacement_final_source_ownership_is_locked` | `_assert_source_markers_in_order` (shared) | `game.final_emission_meta` (`infer_accept_path_final_emitted_source`) | `tests/test_final_emission_gate_source_ownership.py` | **Low** |
| **FEM assembly merge order** | 1: `bj47_merge_gate_layer_metas_into_fem_merge_order_locked` | Inline `_track` monkeypatch helpers | `game.final_emission_fem_assembly` | `tests/test_final_emission_fem_assembly.py` or stay with orchestration file | **Low** |
| **Gate thin boundary (BJ-129)** | 1: `bj129_gate_module_thin_boundary_source_shape_locked` | `tests/helpers/gate_thin_boundary_locks.py` | `game.final_emission_gate` module shape | `tests/test_final_emission_gate_boundary.py` | **Low** |
| **BJ delegator / reexport regression** | 123: `test_bj41_*` through `test_bj122_*` (pairs of removed-delegator + caller-direct tests), plus cross-file audits `bj120`–`bj122` | Mostly `inspect.getsource`; `bj121` reads peer test files from disk | Many `game.final_emission_*` submodules; regression locks refactors BJ-41–BJ-122 | `tests/test_final_emission_gate_delegator_regression.py` | **Low** (static source inspection; ~77% of file) |
| **Shared fixtures/helpers** | — | 9 module-level helpers listed below | — | Extract per-cluster or `tests/helpers/final_emission_gate_fixtures.py` | — |
| **Unclear / mixed ownership** | `bj120`–`bj122` audit tests reference other test modules and harness files | Cross-suite coupling | Harness conventions, not gate behavior | Keep in delegator regression file or `tests/test_gate_harness_conventions.py` | **Medium** |

**Module-level helpers in `test_final_emission_gate.py`**

| Helper | Primary clusters |
|---|---|
| `_minimal_n4_narrative_plan` | N4 |
| `_strong_interaction_continuity_contract` | Orchestration |
| `_ssa_contract` | Orchestration, diagnostics |
| `_assert_known_realization_family` | Selector snapshots |
| `_visibility_offscene_npc_gate_bundle` | Selector snapshots |
| `_assert_source_markers_in_order` | Selector snapshots, Block M4 |
| `_secondary_social_response_structure_contract` | Orchestration |
| `_dialogue_response_policy_with_social_structure` | Orchestration |
| `_narrative_mode_plan_payload` | Orchestration |

---

## Shared Helper Pressure

| Helper/fixture | Used by | Recommendation | Rationale |
|---|---|---|---|
| `run_golden_replay` / `golden_replay_chat_stubs` | All golden replay clusters except protected-bridge | **Remain in `tests/helpers/golden_replay.py`** | Core replay orchestration; duplication would drift |
| `assert_protected_golden_turn_observation` / `protected_structural_expectation` | Structural, long-session, direct-seam, spine | **Remain in `tests/helpers/golden_replay.py`** | Protected bridge is shared contract surface |
| `frontier_gate_branch_replay_fixture` + `FRONTIER_GATE_*` profiles | Long-session cluster only | **Remain in helpers**; long-session test file imports them | Profile data is not test-file-local |
| `apply_final_emission_gate_consumer` | Direct-seam golden tests | **Remain in `emission_smoke_assertions.py`** | Documented downstream facade (Cycle AS2) |
| `patch_get_speaker_selection_contract` / `patch_build_final_strict_social_response` | Golden direct-seam + gate orchestration | **Remain in `gate_equivalence_monkeypatch.py`** | Shared monkeypatch seam; BJ-120/121 lock target |
| `runner_strict_bundle` | Golden direct-seam + gate orchestration | **Remain in `strict_social_harness.py`** | Established strict-social harness |
| `_minimal_n4_narrative_plan` + `_N4_*` constants | N4 cluster only | **Move with N4 tests** to new file or **`tests/helpers/final_emission_gate_fixtures.py`** | Single-cluster ownership; safe to relocate |
| `_ssa_contract` / `_strong_interaction_continuity_contract` | Orchestration + diagnostics | **Move to focused test utility module** when orchestration file splits | Shared within gate-order cluster only |
| `_visibility_offscene_npc_gate_bundle` / `_assert_source_markers_in_order` | Selector + M4 clusters | **Move with selector/M4 files** or shared `final_emission_gate_fixtures.py` | Co-locate with snapshot tests |
| `clear_recorded_protected_replay_failures` | Protected-bridge test only | **Safe to duplicate locally** (try/finally wrapper) but prefer **remain in helper** | Global recording state; central clear API is safer |
| Inline `_fake_call_gpt` closures | Per-test in golden replay | **Safe to duplicate locally** in each test | Trivial one-liners; not worth extracting |
| `inspect.getsource` patterns in BJ tests | All 123 BJ tests | **Remain co-located** in delegator regression file | Mechanical regression suite; no shared fixture needed |

---

## Import / Execution Hazards

| Hazard | Location | Why it matters | Suggested mitigation |
|---|---|---|---|
| **Global protected-failure recording state** | `test_protected_golden_assertion_failure_records_canonical_report` | `clear_recorded_protected_replay_failures` / `recorded_protected_replay_failure_rows` use module-global collectors; leakage if `finally` omitted | Keep try/finally when moving; do not parallelize this test without isolation |
| **Real storage mutation (resume probe)** | `test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting` | Bypasses `run_golden_replay`; calls `chat` directly, `storage.create_snapshot` / `load_snapshot`, asserts `storage.load_session()` and `storage.load_log()` | Move last; run alone in CI shard; ensure `patch_transcript_storage(monkeypatch, tmp_path)` precedes any storage writes |
| **Filesystem bootstrap assumptions** | Resume test + all `tmp_path` golden tests | `write_default_bootstrap_scenes()`, `new_clean_campaign`, `SESSION_LOG_PATH` existence check | Preserve setup order; do not share `tmp_path` across moved files without per-test isolation |
| **Heavy monkeypatch on stack modules** | 20+ orchestration tests in `test_final_emission_gate.py` | Patches `strict_social_stack`, `non_strict_stack`, `terminal_pipeline` attributes | pytest monkeypatch auto-reverts per test; risk is **patching wrong seam** after refactors (BJ-120/121 guard this) |
| **Cross-module source audits** | `test_bj120_harness_patches_canonical_owner_seams`, `test_bj121_strict_social_build_patches_use_stack_seam_not_gate`, `test_bj122_scene_state_anchoring_tests_use_ssa_owner_bindings_not_gate` | Import/read other test modules and repo paths at runtime | Move together; update path lists if peer files move in later blocks |
| **Repo-relative file reads** | `test_bj121_*` | `pathlib.Path(__file__).resolve().parents[1]` + hardcoded peer file list | If decomposition moves peer files, update audited path list in same PR |
| **`inspect.getsource` fragility** | 123 BJ tests | Whitespace/refactor in production changes source strings | Expected; keep as dedicated regression file; run after any gate module edit |
| **Broad integration assertions** | Golden structural tests | Single test asserts speaker + final emission + sanitizer via protected observation | Acceptable for replay layer; do not split assertions across files without preserving `debug_context` |
| **Implicit gate-owner verification in golden replay** | Direct-seam + thin-answer tests | Replay suite asserts `response_type_*`, `final_emitted_source`, opening fallback via projection | Document as consumer coverage; avoid duplicating in gate orchestration file |
| **No explicit test-order dependency** | Both files | pytest collection order not relied upon | Safe to decompose by cluster |
| **Parametrized multi-owner tests** | None found | — | — |
| **Slow 25-turn integration** | 3 long-session golden tests | ~10s+ combined | Tag or shard long-session file separately in CI planning |

---

## Recommended BM Execution Blocks

### BM1 — Extract BJ delegator regression suite

| Field | Value |
|---|---|
| **Files touched** | Create `tests/test_final_emission_gate_delegator_regression.py`; shrink `tests/test_final_emission_gate.py` |
| **Tests to move** | All 123 `test_bj*` tests (`test_bj41_finalize_emission_output_strips_appended_stock_and_packages_sidecar` through `test_bj129_gate_module_thin_boundary_source_shape_locked` **except** move `bj47` and `bj129` only if keeping orchestration/boundary files separate — recommended: move all BJ tests including `bj47`/`bj129` to delegator file, then **split out** `bj47`/`bj129` in BM4/BM5) |
| **Helpers/fixtures to move** | None (BJ tests are self-contained; `bj129` imports `gate_thin_boundary_locks` inline) |
| **Validation** | `pytest tests/test_final_emission_gate_delegator_regression.py tests/test_final_emission_gate.py -q` |
| **Expected risk** | **Low** — static inspection; largest line-count win (~2,100 lines) |

### BM2 — Extract selector snapshots + Block M4 + sealed-branch cluster

| Field | Value |
|---|---|
| **Files touched** | Create `tests/test_final_emission_gate_selector_snapshots.py` (include Block M4 source-ownership tests) |
| **Tests to move** | 12 tests: all `selector_snapshot_*`, `sealed_branch_order_*`, `block_ai_block_ag_selector_order_snapshots_remain_entrypoints`, `final_gate_plain_valid_candidate_has_source_without_fallback_family`, both `block_m4_*` |
| **Helpers/fixtures to move** | `_visibility_offscene_npc_gate_bundle`, `_assert_known_realization_family`, `_assert_source_markers_in_order` |
| **Validation** | `pytest tests/test_final_emission_gate_selector_snapshots.py -q` |
| **Expected risk** | **Low** |

### BM3 — Extract gate orchestration order + N4 + diagnostics

| Field | Value |
|---|---|
| **Files touched** | Create `tests/test_final_emission_gate_orchestration_order.py`, `tests/test_final_emission_gate_n4.py`; optional `tests/helpers/final_emission_gate_fixtures.py` |
| **Tests to move** | 27 tests: 3 N4 + 20 orchestration/layer-order + 4 diagnostics/metadata (listed in clusters above) |
| **Helpers/fixtures to move** | `_minimal_n4_narrative_plan`, `_N4_*` constants, `_strong_interaction_continuity_contract`, `_ssa_contract`, `_secondary_social_response_structure_contract`, `_dialogue_response_policy_with_social_structure`, `_narrative_mode_plan_payload` |
| **Validation** | `pytest tests/test_final_emission_gate_n4.py tests/test_final_emission_gate_orchestration_order.py -q` |
| **Expected risk** | **Medium** — behavioral monkeypatch order tests |

### BM4 — Extract golden replay long-session cluster

| Field | Value |
|---|---|
| **Files touched** | Create `tests/test_golden_replay_long_session.py` |
| **Tests to move** | 3 frontier-gate 25-turn tests (resume test last within file) |
| **Helpers/fixtures to move** | None (keep imports from `golden_replay`, `golden_replay_profiles`, `transcript_runner`) |
| **Validation** | `pytest tests/test_golden_replay_long_session.py -q` |
| **Expected risk** | **Medium–High** — slow; resume test has storage hazard |

### BM5 — Extract golden replay structural + protected bridge

| Field | Value |
|---|---|
| **Files touched** | Create `tests/test_golden_replay_structural_invariants.py`, `tests/test_golden_replay_protected_bridge.py` |
| **Tests to move** | 6 structural + 1 protected-bridge |
| **Helpers/fixtures to move** | None |
| **Validation** | `pytest tests/test_golden_replay_structural_invariants.py tests/test_golden_replay_protected_bridge.py -q` |
| **Expected risk** | **Medium** |

### BM6 — Extract golden replay spine smoke + direct-seam (deferrable)

| Field | Value |
|---|---|
| **Files touched** | Create `tests/test_golden_replay_scenario_spine.py`, `tests/test_golden_replay_direct_seam.py` |
| **Tests to move** | 1 spine smoke + 2 direct-seam tests |
| **Helpers/fixtures to move** | None |
| **Validation** | `pytest tests/test_golden_replay_scenario_spine.py tests/test_golden_replay_direct_seam.py -q` |
| **Expected risk** | **Medium** — direct-seam tests cross gate/replay boundary; consider keeping in gate consumer suite instead |

**Suggested execution order:** BM1 → BM2 → BM3 → BM5 → BM4 → BM6 (largest low-risk gate win first; golden long-session near end due to runtime/storage).

---

## Files Needed For Next Planning Step

Pass back to ChatGPT:

1. **Generated discovery report:** `docs/refactor/BM_large_test_file_decomposition_discovery.md`
2. **Target test files:**
   - `tests/test_golden_replay.py`
   - `tests/test_final_emission_gate.py`
3. **conftest:** `tests/conftest.py`
4. **Shared helper modules:**
   - `tests/helpers/golden_replay.py`
   - `tests/helpers/golden_replay_fixtures.py`
   - `tests/helpers/golden_replay_profiles.py`
   - `tests/helpers/golden_replay_projection.py`
   - `tests/helpers/transcript_runner.py`
   - `tests/helpers/failure_dashboard_report.py`
   - `tests/helpers/emission_smoke_assertions.py`
   - `tests/helpers/gate_equivalence_monkeypatch.py`
   - `tests/helpers/strict_social_harness.py`
   - `tests/helpers/gate_thin_boundary_locks.py`
   - `tests/helpers/opening_fallback_evidence.py`
5. **Production modules directly imported by target tests:**
   - `game/final_emission_gate.py`
   - `game/final_emission_meta.py`
   - `game/final_emission_acceptance_quality.py`
   - `game/final_emission_fem_assembly.py`
   - `game/final_emission_terminal_pipeline.py`
   - `game/final_emission_strict_social_stack.py`
   - `game/final_emission_non_strict_stack.py`
   - `game/api.py` (chat entry)
   - `game/scenario_spine.py`
   - `game/scenario_spine_eval.py`
   - `data/validation/scenario_spines/frontier_gate_long_session.json` (long-session manifest)

---

## Test Command Results (baseline)

```
pytest tests/test_golden_replay.py -q --tb=no
.............                                                            [100%]
13 passed in ~14.7s

pytest tests/test_final_emission_gate.py -q --tb=no
........................................................................ [ 45%]
........................................................................ [ 90%]
...............                                                          [100%]
159 passed in ~2.2s
```
