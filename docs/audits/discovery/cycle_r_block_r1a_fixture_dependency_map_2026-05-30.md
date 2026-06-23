# Cycle R / R1-A — Fixture Extraction Impact Map

**Date:** 2026-05-30  
**Scope:** Read-only dependency analysis. No files modified. No extraction performed.

---

## 1. Definition Sites

All three symbols are defined in **`tests/test_final_emission_gate.py`** (gate orchestration owner module).

| Symbol | Line (approx.) | Type | Returns / value |
| --- | --- | --- | --- |
| `_runner_strict_bundle` | 503 | function | `(session, world, sid, resolution)` — strict-social question turn, NPC `runner` / "Tavern Runner", scene `scene_investigate` |
| `_opening_gm_output` | 3835 | function | Fresh GM dict: frontier_gate opening curated facts, prompt_context, response_policy, emission_debug metadata |
| `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | 3870 | constant | Canonical deterministic opening fallback prose (4-sentence frontier-gate paragraph) |

### Internal dependencies (must move with extraction)

| Helper | Line | Used by |
| --- | --- | --- |
| `_opening_validation_context()` | 3822 | `_opening_gm_output()`; also called directly in gate opening-validation tests (4021–4036) |
| `_response_type_contract(required)` | 3785 | `_opening_gm_output()` (local gate variant; **not** the copies in `test_fallback_behavior_gate.py` / `test_fallback_behavior_repairs.py`) |

### `_runner_strict_bundle` runtime imports

```text
game.defaults.default_session, default_world
game.interaction_context.set_social_target, rebuild_active_scene_entities
game.storage.get_scene_runtime
```

### `_opening_gm_output` shape invariants (consumers assume)

- `opening_curated_facts` — 3 curated visible-fact strings
- `prompt_context.scene.public.id` == `"frontier_gate"`
- `metadata.emission_debug.opening_curated_facts_count` == 3
- `response_policy.response_type_contract` for `"scene_opening"`
- Upstream attach + gate opening path produce text **byte-equal** to `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK`

---

## 2. Complete Consumer Dependency Table

**Legend — layer:** Owner = gate semantic home; Downstream = consumes fixture for another module's contract; Replay = golden/direct-seam replay protection; Smoke = thin integration hook.

| Consumer File | Symbol(s) | Import Style | Purpose | Owner / Downstream / Replay | Safe To Repoint? |
| --- | --- | --- | --- | --- | --- |
| **`tests/test_final_emission_gate.py`** | all three + internal helpers | Local definition | Gate orchestration tests: opening fallback path, strict-social continuity, upstream attach, Block AI non-mutation probe | **Owner** | N/A (source); after extraction, **import from helper** and keep tests here |
| `tests/test_upstream_response_repairs.py` | `_opening_gm_output`, `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | Module-level `from tests.test_final_emission_gate import (...)` | Upstream prepared opening payload matches gate snapshot; attach/skip/preserve/replace behavior | **Downstream** (upstream repairs owner) | **Yes** |
| `tests/test_diegetic_fallback_narration.py` | `_opening_gm_output`, `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | Module-level import | Legacy diegetic family boundary on opening repair; FEM carry-through | **Downstream** | **Yes** |
| `tests/test_api_narration_path_selection.py` | `_opening_gm_output`, `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | Module-level import | `_finalize_player_facing_for_turn` scene_opening carries upstream opening payload | **Downstream** | **Yes** |
| `tests/test_run_scenario_spine_validation.py` | `_opening_gm_output`, `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | **Lazy import inside** `test_cycle_i_opening_attribution_survives_*` | Cycle-I opening attribution + FEM lineage (success + fail-closed curated-facts empty) | **Downstream / replay-adjacent** | **Yes** |
| `tests/test_golden_replay.py` | `_runner_strict_bundle`, `_opening_gm_output` | Module-level import (two lines) | Direct-seam structural invariants: declared-alias dialogue plan; canonical opening fallback ownership | **Replay** | **Yes** — preserve fixture **semantics** exactly |
| `tests/test_block_s_speaker_local_rebind_equivalence.py` | `_runner_strict_bundle` | Module-level import | Block S phase-order / local_rebind equivalence vs `_locked_runner_contract()` | **Downstream** (ordering harness) | **Yes** — docstring ties contract to bundle NPC id `runner` |
| `tests/test_block_t_speaker_relocation_shadow_equivalence.py` | `_runner_strict_bundle` | Module-level import | Block T shadow dual-run enforce equivalence (4 tests) | **Downstream** | **Yes** |
| `tests/test_block_u_finalize_stack_divergence.py` | `_runner_strict_bundle` | Module-level import | Pytest fixtures + divergence probes (5 call sites); mutates `resolution` via dialogue plan attach | **Downstream** | **Yes** |
| `tests/test_final_emission_boundary_convergence.py` | `_runner_strict_bundle` | Module-level import | Smoke: strict-social dialogue repair terminal fallback (`test_gate_strict_social_dialogue_repair_*`) | **Smoke** (registry: repairs smoke_suite neighbor) | **Yes** |
| `tests/test_gauntlet_regressions.py` | `_runner_strict_bundle` (**indirect**) | **Imports gate test function** `test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker` inside `test_gauntlet_slice_strict_social_narrative_authority_repair` | Thin gauntlet hook re-running canonical strict-social NA case | **Smoke** | **Repoint fixture yes**; **must also replace test-function import** (see §3) |

**Non-Python references (no repoint needed):** `docs/gate_cleanup_inventory.md`, `docs/audits/cycle_k_replay_promotion_recon_2026-05-26.md`, `docs/cycles/cycle_j_gate_cluster_extraction_recon_2026-05-26.md`, `docs/cycles/cycle_r_test_fanout_reduction_recon_2026-05-30.md`.

### Owner-module call volume (internal, for extraction sizing)

| Symbol | Approx. call sites in `test_final_emission_gate.py` |
| --- | --- |
| `_opening_gm_output()` | ~45 |
| `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | ~25 assert/comparison sites |
| `_runner_strict_bundle()` | ~18 |

---

## 3. Mutation, Identity, and Test-Function Imports

### 3.1 Consumers that **mutate** fixture output

All builders return **new objects per call**; mutation is in-place on the returned dict/session, not on shared module state.

| Consumer | Symbol | Mutation pattern | Risk on extract |
| --- | --- | --- | --- |
| `test_upstream_response_repairs.py` | `_opening_gm_output` | In-place: `maybe_attach_*` writes `UPSTREAM_PREPARED_OPENING_FALLBACK_KEY`; pops keys; stubs payload; mutates `metadata.emission_debug` | **Low** — expects fresh dict |
| `test_run_scenario_spine_validation.py` | `_opening_gm_output` | Sets prepared payload, `player_facing_text`, `tags`; fail-closed clears `opening_curated_facts` | **Low** |
| `test_api_narration_path_selection.py` | `_opening_gm_output` | Sets `player_facing_text`, `tags` before finalize | **Low** |
| `test_diegetic_fallback_narration.py` | `_opening_gm_output` | Sets `player_facing_text`, `tags`; one test uses valid candidate text | **Low** |
| `test_golden_replay.py` | `_opening_gm_output` | Sets `player_facing_text`, `tags` before `apply_final_emission_gate` | **Low** |
| `test_golden_replay.py` | `_runner_strict_bundle` | `attach_dialogue_social_plan_to_resolution(resolution, ...)` mutates **resolution** dict | **Low** — fresh bundle per test |
| `test_block_u_finalize_stack_divergence.py` | `_runner_strict_bundle` | Fixture attaches dialogue plan to `resolution` | **Low** |
| `test_final_emission_gate.py` | `_opening_gm_output` | Extensive in-place mutation (upstream attach, empty facts, deepcopy baseline); **one test uses `copy.deepcopy(_opening_gm_output())`** to assert helper non-mutation | **Low** if helper keeps returning new dicts |
| `test_final_emission_gate.py` | `_runner_strict_bundle` | Session/world passed through gate (may be mutated by gate path) | **Low** — new bundle per test |

**No consumer** caches a module-level singleton of these fixtures.

### 3.2 Consumers relying on **object identity**

| Consumer | Pattern | Assessment |
| --- | --- | --- |
| `test_final_emission_gate.py` (`test_block_ai_non_strict_terminal_selector_does_not_mutate_gm_output_when_opening_branch`) | `snap = copy.deepcopy(gm)` then `assert gm == snap` after gate helper | **Value equality**, not `id()` — safe |
| `test_final_emission_gate.py` (line ~5692) | `_opening_gm_output()` called twice in one test for `gm_output` vs `scene` arg | **Intentionally separate instances** — must remain two fresh dicts |
| All others | Compare text/meta fields or structural keys | **No identity reliance** |

### 3.3 Consumers importing **test functions** instead of helpers

| File | Import | Problem | Recommended R1-A follow-up |
| --- | --- | --- | --- |
| `tests/test_gauntlet_regressions.py` | `from tests.test_final_emission_gate import test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker` then calls it as a function | Couples gauntlet to pytest collection in gate module; indirect `_runner_strict_bundle` dependency | Extract **`run_strict_social_motive_overclaim_gate_case(monkeypatch)`** (or similar) into `tests/helpers/final_emission_gate_fixtures.py` or a small `gate_regression_harness.py`; gauntlet calls helper, gate test becomes thin wrapper |

**No other test-file imports of gate `test_*` functions** were found for these fixtures.

### 3.4 Cross-fixture coupling notes (preserve on extract)

| Coupling | Detail |
| --- | --- |
| **Runner NPC id** | `_runner_strict_bundle` uses `social.npc_id == "runner"`. Block S `_locked_runner_contract()` documents match to `runner`. Golden replay dialogue plan uses `speaker_id="tavern_runner"` with alias override — **intentional seam**, not fixture bug. |
| **Opening text lock** | `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` must stay aligned with `_opening_validation_context()` facts and gate/upstream builders; changing one without the other breaks 6+ downstream files. |
| **Block S/T/U harness imports** | Block U imports `_locked_runner_contract` from **block S test module** (separate R1 follow-up); only `_runner_strict_bundle` comes from gate file today. |

---

## 4. Recommended Helper Module Location

### Recommendation: **`tests/helpers/final_emission_gate_fixtures.py`** (new module)

| Criterion | `final_emission_gate_fixtures.py` | `opening_fallback_evidence.py` (existing) |
| --- | --- | --- |
| **Current role** | N/A (new) | FEM-shaped **observation dicts** for classifier/replay (`successful_opening_fem_meta`, `fail_closed_opening_observed_fields`, …) |
| **Fixture scope** | Full GM output scaffold + strict-social session bundle + canonical prose constant | Post-emission metadata snippets only |
| **Dependencies** | `game.defaults`, `game.interaction_context`, `game.storage`, local `_response_type_contract` + `_opening_validation_context` | `game.final_emission_meta`, `game.upstream_response_repairs` constants |
| **Ownership story** | Support residue for gate-adjacent harnesses; **semantic owner stays** `test_final_emission_gate.py` | Stays replay/classifier evidence owner |

**Do not fold** `_opening_gm_output` / `_runner_strict_bundle` into `opening_fallback_evidence.py` — different abstraction layer (harness setup vs observed FEM fields). Optional **cross-link** in module docstrings.

### Proposed module contents (R1 extraction target)

```text
tests/helpers/final_emission_gate_fixtures.py
├── opening_validation_context()          # move from gate (or public alias)
├── response_type_contract(required)       # gate-local variant only
├── opening_gm_output()                   # rename: drop leading _ or keep for compat re-export
├── runner_strict_bundle()
├── EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
└── (optional) run_strict_social_motive_overclaim_gate_case(monkeypatch)  # gauntlet decouple
```

### Repoint strategy

1. Create helper module with moved definitions (unchanged semantics).
2. Update **10 external consumer files** (+ gate owner) to import from helper.
3. Optionally re-export from `test_final_emission_gate.py` for one-release compat shim (deprecated comment).
4. Replace gauntlet **test-function import** with shared callable.
5. Run:

```text
py -3 -m pytest tests/test_final_emission_gate.py tests/helpers/ -q
py -3 -m pytest tests/test_upstream_response_repairs.py tests/test_diegetic_fallback_narration.py tests/test_api_narration_path_selection.py -q
py -3 -m pytest tests/test_golden_replay.py -m golden_replay -q
py -3 -m pytest tests/test_block_s_speaker_local_rebind_equivalence.py tests/test_block_t_speaker_relocation_shadow_equivalence.py tests/test_block_u_finalize_stack_divergence.py tests/test_final_emission_boundary_convergence.py -q
py -3 -m pytest tests/test_run_scenario_spine_validation.py::test_cycle_i_opening_attribution_survives_prepared_payload_gate_lineage_and_diagnostics -q
py -3 -m pytest tests/test_gauntlet_regressions.py::test_gauntlet_slice_strict_social_narrative_authority_repair -q
```

---

## 5. Extraction Risk Summary

| Risk | Level | Mitigation |
| --- | --- | --- |
| Import-only repoint for 9 direct consumers | **Low** | Mechanical import path change |
| Golden replay opening/seam tests | **Low–medium** | Run full `test_golden_replay.py -m golden_replay`; no assertion changes |
| Gauntlet test-function decoupling | **Medium** | Extract callable body shared with gate test |
| Co-moving `_response_type_contract` / `_opening_validation_context` | **Low** | Keep gate-local variant; do not merge with fallback_behavior_* copies |
| NPC id `runner` vs `tavern_runner` in replay/block tests | **None for extract** | Document only; pre-existing intentional |

---

*R1-A recon complete. Ready for R1-B extraction PR.*
