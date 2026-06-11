# Cycle BD — Gate Dependency Compression Closeout

**Date:** 2026-06-10  
**Status:** **CLOSED**  
**Scope:** BD-1 through BD-7 complete; behavior unchanged (import-path / facade / governance only)

**Artifacts:** Recon via Cycle BD dependency inventory (gate consumer map); governance guard in `tests/test_ownership_registry.py` (`test_bd6_gate_dependency_compression_*`).

---

## Executive summary

Cycle BD reduced **downstream test dependency pressure** on compressed gate-owned structures by routing non-owner consumers through purpose-specific helper facades, then locking the compression with a static import guard (BD-6). No runtime or emitted-game behavior changed.

After BD-1–BD-6:

- **Speaker-contract symbols** no longer import from `game.final_emission_gate` in the speaker-contract owner suite (BD-1).
- **Non-owner gate entry** (`apply_final_emission_gate`) redirects to `apply_final_emission_gate_consumer` across integration/smoke/transcript/replay consumers (BD-2); **8 owner/equivalence suites** retain direct gate entry.
- **Non-owner FEM reads** route through `final_emission_meta_from_output` or `read_fem_meta_from_gate_output` (BD-3); **6 allowed direct FEM-read import sites** remain (owners + facade delegates).
- **Non-owner replay projection** routes through `tests.helpers.golden_replay_projection` (BD-4); **3 allowed direct replay-projection import sites** remain (meta owner, facade delegate, AO5 governance).
- **Owner-bucket constants** route through `opening_fallback_evidence` / `golden_replay_projection` (BD-5); **0** non-allowlisted bucket imports.
- **BD-6 guard violation count:** **0** (scan date 2026-06-10).

**Verdict:** **Close Cycle BD.** Future regressions are caught by `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` in CI (`tests/test_ownership_registry.py`).

---

## Work completed by BD-1–BD-6

| Block | Focus | Outcome |
| --- | --- | --- |
| **BD-0 (recon)** | Gate dependency inventory | Mapped gate/meta/replay exports, consumer purposes, and ranked compression candidates; informed block ordering |
| **BD-1** | Speaker-contract compat redirect | `tests/test_speaker_contract_enforcement.py` imports speaker-contract symbols from `game.speaker_contract_enforcement` (and `detect_emitted_speaker_signature` from `game.emitted_speaker_signature`); gate compat re-exports unchanged |
| **BD-2** | Non-owner gate entry redirect | **19 consumers** → `tests.helpers.emission_smoke_assertions.apply_final_emission_gate_consumer`; monkeypatch/equivalence owners kept on `game.final_emission_gate` |
| **BD-3** | Non-owner FEM read compression | **26 consumers** → `final_emission_meta_from_output` (smoke) or `read_fem_meta_from_gate_output` (golden/replay); redundant reads removed where consumer tuple already returns FEM |
| **BD-4** | Replay projection export compression | **2 consumers** + facade helpers → `build_runtime_lineage_events_from_fem`, re-exported `SEALED_REPLACEMENT_SUBKINDS` via `golden_replay_projection` |
| **BD-5** | Gate-owned constant export compression | **9 files** → opening/sealed/visibility bucket constants through `opening_fallback_evidence` / `golden_replay_projection` |
| **BD-6** | Compression guard | Added `gate_dependency_compression_guard` with **27-path allowlist** and facade replacement messages in `tests/test_ownership_registry.py` |

---

## Files changed by block

### BD-1 (1 file)

- `tests/test_speaker_contract_enforcement.py`

### BD-2 (19 files)

- `tests/test_scene_destination_binding.py`
- `tests/test_final_emission_scene_integrity.py`
- `tests/test_anti_reset_emission_guard.py`
- `tests/test_dialogue_social_convergence.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_fallback_shipped_contract_propagation.py`
- `tests/test_anti_railroading_transcript_regressions.py`
- `tests/test_lead_npc_payoff_and_fallback.py`
- `tests/test_upstream_fast_fallback_block_l.py`
- `tests/test_lead_lifecycle_block3_transcript_regression.py`
- `tests/test_dialogue_plan_final_emission_gate.py`
- `tests/test_golden_replay.py`
- `tests/test_narration_transcript_regressions.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_c4_narrative_mode_live_pipeline.py`
- `tests/test_referential_clarity_strict_social_local_repair.py`
- `tests/test_tone_escalation_rules.py` (partial: 3 of 4 gate-path tests)
- `tests/test_run_scenario_spine_validation.py` (Cycle I local consumer)
- `tests/helpers/strict_social_harness.py`

### BD-3 (26 files)

**Smoke facade (`final_emission_meta_from_output`):**

- `tests/test_turn_packet_stage_diff_integration.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_fallback_shipped_contract_propagation.py`
- `tests/test_social_emission_quality.py`
- `tests/test_retry_tone_alignment.py`
- `tests/test_contextual_minimal_repair_regressions.py`
- `tests/test_empty_social_retry_regressions.py`
- `tests/test_referential_clarity_strict_social_local_repair.py`
- `tests/test_anti_railroading_retry_alignment.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_social_interaction_authority.py`
- `tests/test_referential_clarity_player_coref.py`
- `tests/test_anti_reset_emission_guard.py`
- `tests/test_manual_play_latency.py`
- `tests/test_observational_telemetry_confidence.py`
- `tests/test_dead_turn_detection.py`

**Golden replay facade (`read_fem_meta_from_gate_output`):**

- `tests/test_transcript_gauntlet_actor_addressing.py`
- `tests/test_dead_turn_evaluation_threading.py`
- `tests/helpers/behavioral_gauntlet_eval.py`

**Redundant FEM reads removed (already on consumer tuple from BD-2):**

- `tests/test_scene_destination_binding.py`
- `tests/test_mixed_state_recovery_regressions.py`
- `tests/test_dialogue_plan_final_emission_gate.py`
- `tests/test_final_emission_scene_integrity.py`
- `tests/test_anti_railroading_transcript_regressions.py`
- `tests/test_dialogue_social_convergence.py`
- `tests/test_lead_npc_payoff_and_fallback.py`

### BD-4 (3 files)

- `tests/helpers/golden_replay_projection.py` (added `build_runtime_lineage_events_from_fem`; re-exported `SEALED_REPLACEMENT_SUBKINDS`)
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`

### BD-5 (9 files)

- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/failure_classification_contract.py`
- `tests/test_golden_replay.py`
- `tests/test_golden_replay_fallback_projection.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_classification_contract.py`
- `tests/helpers/failure_dashboard_fixtures.py`
- `tests/helpers/failure_classification_sync.py`

### BD-6 (1 file)

- `tests/test_ownership_registry.py` (guard constants, collectors, `test_bd6_*`)

---

## Dependency reductions achieved

| Surface | Before (Cycle BD start) | After (BD-7 scan) |
| --- | --- | --- |
| Direct `apply_final_emission_gate` import in non-owner tests | ~24 modules (BD-2 recon) | **0** non-allowlisted; **8** allowed owner/equivalence files |
| Direct forbidden FEM read imports (`read_final_emission_meta_dict`, turn-payload reads) in non-owners | Dozens of smoke/transcript/replay consumers | **0** non-allowlisted; **6** allowed sites (owners + 2 facade delegates) |
| Direct `game.final_emission_replay_projection` in non-owners | Golden replay + spine validation + scattered observation | **0** non-allowlisted; **3** allowed sites (meta owner, facade delegate, AO5 governance) |
| Owner-bucket constants from compressed owner modules outside facades | Classifier/golden/dashboard helpers | **0** outside allowlist |
| `apply_final_emission_gate_consumer` adoption | Sparse | **~30** test/helper modules (integration/smoke/transcript path) |
| BD-6 compressed-import violations | N/A (guard added) | **0** |

### Informational inventory (2026-06-10, `tests/**/*.py`)

| Metric | Count |
| --- | ---: |
| Files importing `game.final_emission_gate` (any symbol) | 32 |
| Files importing `apply_final_emission_gate` symbol | 8 (all allowlisted) |
| Files importing forbidden FEM read symbols | 6 (all allowlisted) |
| Files importing `game.final_emission_replay_projection` | 3 (all allowlisted) |
| **BD-6 guard violations** | **0** |

---

## Remaining allowed direct consumers and why

### Gate entry (`apply_final_emission_gate`)

| Path | Reason |
| --- | --- |
| `tests/test_final_emission_gate.py` | Gate orchestration owner |
| `tests/test_fallback_behavior_gate.py` | Gate-adjacent behavior owner |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | Boundary owner; private `feg._*` seams |
| `tests/test_block_s_speaker_local_rebind_equivalence.py` | Speaker equivalence / orchestration-order proof |
| `tests/test_block_t_speaker_relocation_shadow_equivalence.py` | Speaker equivalence / orchestration-order proof |
| `tests/test_block_u_finalize_stack_divergence.py` | Finalize-stack divergence proof |
| `tests/test_social_exchange_emission.py` | Strict-social emission legality owner |
| `tests/test_tone_escalation_rules.py` | Layer-order monkeypatch on `feg` namespace |

Other gate namespace imports (`import game.final_emission_gate as feg`) remain in monkeypatch harnesses and owner-adjacent suites that patch private seams but do **not** import compressed symbols guarded by BD-6.

### FEM read symbols

| Path | Reason |
| --- | --- |
| `tests/test_final_emission_meta.py` | FEM projection / packaging owner |
| `tests/test_final_emission_gate.py` | Gate orchestration owner (orchestration + FEM co-assertions) |
| `tests/test_final_emission_visibility.py` | Visibility semantics owner |
| `tests/test_final_emission_channel_separation.py` | FEM channel packaging owner-adjacent |
| `tests/helpers/emission_smoke_assertions.py` | Smoke facade delegate (single internal import site) |
| `tests/helpers/golden_replay_projection.py` | Golden replay facade delegate |

### Replay projection

| Path | Reason |
| --- | --- |
| `tests/test_final_emission_meta.py` | Runtime-lineage projection owner |
| `tests/helpers/golden_replay_projection.py` | Centralized acceptance/replay facade delegate |
| `tests/test_ownership_registry.py` | AO5 governance: runtime vs acceptance module boundary |

### Owner-bucket constants (direct from `game.final_emission_meta`)

| Path | Reason |
| --- | --- |
| `tests/test_final_emission_gate.py` | Gate orchestration owner |
| `tests/test_final_emission_meta.py` | FEM registry / projection owner |
| `tests/test_opening_fallback_owner_bucket.py` | Opening bucket mapping owner |
| `tests/test_final_emission_opening_fallback.py` | Opening fallback owner |
| `tests/test_final_emission_sealed_fallback.py` | Sealed fallback owner |
| `tests/test_final_emission_visibility_fallback.py` | Visibility fallback owner-adjacent |
| `tests/helpers/opening_fallback_evidence.py` | Opening facade delegate |
| `tests/helpers/golden_replay_projection.py` | Golden replay facade delegate |

Non-owner classifier/golden/dashboard consumers import bucket constants **only** through the facades above (BD-5).

---

## Guard added in BD-6

**Name:** `gate_dependency_compression_guard`

**Location:** `tests/test_ownership_registry.py`

**Enforcement:**

- `collect_gate_dependency_compression_guard_violations()`
- `iter_gate_dependency_compression_guard_scan_paths()`
- `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports`
- `test_bd6_gate_dependency_compression_guard_detects_synthetic_violation`
- `test_bd6_gate_dependency_compression_allowlist_entries_have_non_empty_reasons`

**Forbidden outside allowlist:**

- `game.final_emission_gate.apply_final_emission_gate`
- `game.final_emission_meta.read_final_emission_meta_dict` (and turn-payload read helpers)
- Any import from `game.final_emission_replay_projection`
- `OPENING_FALLBACK_OWNER_*`, `SEALED_FALLBACK_OWNER_*`, `VISIBILITY_FALLBACK_OWNER_*`, `FINAL_EMISSION_META_KEY` from compressed owner modules

**Allowlist:** 27 documented paths in `_BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST` (owners, BD-2–BD-5 KEEP suites, facade delegates, gate monkeypatch helpers, audit fixture modules, governance module).

---

## Final scan result (BD-7)

Scan method: AST walk of all `tests/**/*.py` against BD-6 compressed-import rules and allowlist (2026-06-10).

| Check | Result |
| --- | --- |
| BD-6 guard violations | **0** |
| Unexpected `apply_final_emission_gate` imports | **0** |
| Unexpected forbidden FEM read imports | **0** |
| Unexpected replay-projection imports | **0** |
| Owner-bucket constants outside allowlist/facades | **0** |

Production `game/*` paths unchanged and out of BD test-import guard scope.

---

## Test results

### BD-7 closeout command

```text
python -m pytest tests/test_ownership_registry.py tests/test_final_emission_gate.py tests/test_final_emission_meta.py -q --tb=short
```

**Result:** **272 passed**, 0 failed (~128s)

| Module | Tests collected |
| --- | ---: |
| `tests/test_ownership_registry.py` | 42 |
| `tests/test_final_emission_gate.py` | 166 |
| `tests/test_final_emission_meta.py` | 64 |

### Prior block validation (representative)

| Block | Focused suite | Result |
| --- | --- | --- |
| BD-2 | ownership + gate owner + 18 redirected modules | PASS |
| BD-3 | ownership + meta owner + 24 redirected modules | **308 passed** |
| BD-4 | ownership + meta + golden replay + spine validation | **146 passed** |
| BD-5 | ownership + gate/meta owners + classifier/golden suites | **400 passed** |
| BD-6 | `pytest tests/test_ownership_registry.py -k bd6` | **3 passed** |

---

## Facade reference (preferred non-owner surfaces)

| Need | Use |
| --- | --- |
| Run full gate for smoke/integration | `tests.helpers.emission_smoke_assertions.apply_final_emission_gate_consumer` |
| Read FEM from gate output (smoke) | `tests.helpers.emission_smoke_assertions.final_emission_meta_from_output` |
| Read FEM for golden/replay observation | `tests.helpers.golden_replay_projection.read_fem_meta_from_gate_output` |
| Runtime lineage events after gate | `tests.helpers.golden_replay_projection.build_runtime_lineage_events_from_fem` |
| Opening fallback bucket/route constants | `tests.helpers.opening_fallback_evidence` |
| Sealed/visibility bucket constants (replay/classifier) | `tests.helpers.golden_replay_projection` |

---

## Optional follow-ups (out of scope for BD closeout)

- Extend guard to flag `import game.final_emission_gate as feg` in new non-owner files when no monkeypatch/private seam is present (heuristic; higher false-positive risk).
- Regenerate a machine-readable BD consumer inventory JSON (similar to `cycle_as_gate_consumer_inventory.json`) on the next ownership audit pass.
- Thin remaining **non-compressed** gate imports (e.g. `enforce_emitted_speaker_with_contract`, private `feg._*`) only when a dedicated owner/facade block is scoped.
