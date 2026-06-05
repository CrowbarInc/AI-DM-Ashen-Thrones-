# Cycle AS — Downstream Dependency Reduction Closeout

**Date:** 2026-06-04  
**Status:** **CLOSED**  
**Scope:** AS1–AS6 complete; behavior unchanged (import / facade / harness relocation only)

**Artifacts:** Recon `cycle_as_downstream_dependency_reduction_recon.md`; block summaries `cycle_as_block_as1_implementation_summary.md` through `cycle_as_block_as6_implementation_summary.md`; machine-readable `cycle_as_gate_consumer_inventory.json`, `cycle_as_dependency_map.json`.

---

## Executive summary

Cycle AS reduced **downstream concentration** on gate-owned modules by splitting the monolithic `final_emission_gate_fixtures` hub, introducing **narrow test-helper facades**, thinning **FEM read paths**, decoupling **repairs-layer** imports, and **centralizing equivalence harness** monkeypatch seams—without changing emitted game behavior.

At recon start, **268 direct import edges** from gate-owned modules across **112 consumer files** were classified; **163 REDIRECT** candidates drove the block plan. After AS1–AS6:

- **`tests/helpers/final_emission_gate_fixtures.py`** — retired (zero importers; deleted AS4).
- **Registry-listed downstream gate consumers** — zero direct `game.final_emission_gate` imports (AS2).
- **AS3 candidate repair consumers** — zero direct `game.final_emission_repairs` imports; routed through `repairs_consumer_facade`.
- **Primary FEM read thinning** — downstream smoke/transcript/C4/API/block suites use `emission_smoke_assertions` or replay helpers; lineage reads use `final_emission_replay_projection` where appropriate.
- **Block S/T/U equivalence tests** — no `import game.final_emission_gate as feg`; no test-to-test fixture imports; private `feg._*` confined to documented helper modules.

**Verdict:** **Close Cycle AS.** Optional AS7 is low-priority cleanup outside required scope (see [Optional follow-ups](#optional-follow-ups)).

---

## Work completed by AS1–AS6

| Block | Focus | Outcome |
| --- | --- | --- |
| **AS1** | Fixture hub split | Split hub into `emission_smoke_assertions`, `opening_fallback_evidence`, `strict_social_harness`, `opening_fallback_gate_harness`; **22 consumers** migrated off hub; shim re-export only until AS4 delete |
| **AS2** | Registered downstream gate thinning | `test_turn_pipeline_shared`, AC/RD, interaction continuity, diegetic fallback → smoke facade; **zero direct gate imports** in target suites |
| **AS3** | Repairs-layer decoupling | New `repairs_consumer_facade`; NA/N5/AEP/boundary convergence suites off `game.final_emission_repairs` private seams |
| **AS4** | FEM read-path redirect | Deleted `final_emission_gate_fixtures.py`; FEM reads via smoke/replay helpers; lineage off meta compat re-export; bounded/social fallback → repairs facade |
| **AS5** | Test-to-test / convergence retirement | `fallback_behavior_fixtures`, `boundary_semantic_repair_fixtures`, expanded repairs facade; FEM thinning in high-read non-owner suites |
| **AS6** | Block S/T/U equivalence decoupling | `block_stu_equivalence_fixtures`, `gate_equivalence_monkeypatch`; S/T/U/golden direct-seam off `feg` imports and test-to-test imports |

---

## Dependency reductions achieved

### Hub and facade concentration (primary wins)

| Before | After |
| --- | --- |
| 22 suites → `final_emission_gate_fixtures` (gate + private `feg._*`) | **0** — hub deleted; narrow modules only |
| Registered downstream suites → `apply_final_emission_gate` + `read_final_emission_meta_dict` | Smoke facade: `apply_final_emission_gate_consumer`, `final_emission_meta_from_output`, layer seams |
| Non-owner suites → `game.final_emission_repairs._apply_*` | `repairs_consumer_facade` (lazy delegates) |
| 60+ tests → direct `read_final_emission_meta_dict` (recon) | Major transcript/C4/API/block/high-read suites redirected; single delegate remains in smoke facade |
| Block S/T/U → inline `feg` + test-to-test fixtures | Helpers + public gate entry only in test modules |

### Test-to-test imports (gate-cluster targets)

| Pattern | Status |
| --- | --- |
| Transcript → `test_fallback_behavior_gate._fallback_contract` | **Retired** (AS1/AS5) → `fallback_behavior_fixtures` |
| Block T/U/golden → `test_block_s._locked_runner_contract` | **Retired** (AS6) → `block_stu_equivalence_fixtures` |
| Answer completeness → `test_social_escalation._session_with_pressure` | **Retired** (pre-AS) → `social_escalation_fixtures` |

### Equivalence harness

| Before | After |
| --- | --- |
| Private `feg._*` scattered in S/T/U test files | Centralized in `gate_equivalence_monkeypatch` + `post_speaker_finalize_probe` with documented retention reasons |
| Phase-order constants in `test_block_s` | `speaker_gate_order` + `install_strict_social_trunk_phase_trackers` |

---

## Deleted / retired compatibility surfaces

| Surface | Block | Notes |
| --- | --- | --- |
| `tests/helpers/final_emission_gate_fixtures.py` | AS1 shim → **AS4 delete** | Zero Python importers before deletion |
| Downstream imports of hub symbols | AS1 | Migrated to narrow helpers |
| `build_fem_runtime_lineage_events` via `game.final_emission_meta` in tooling/replay helpers | AS4 | Consumers use `game.final_emission_replay_projection` (meta re-export retained for production normalize path only) |

**Not removed (intentional):**

- `game.final_emission_meta.build_fem_runtime_lineage_events` re-export for production observability
- `opening_fallback_gate_harness` private `feg._*` (owner-adjacent attach-then harness; isolated module)

---

## New helper / facade boundaries

Use these modules by intent—do not add generic dumping grounds.

| Module | Role | Import when |
| --- | --- | --- |
| `tests/helpers/emission_smoke_assertions.py` | **Downstream HTTP/pipeline smoke** — gate consumer, route/phrase smoke, `final_emission_meta_from_output`, `read_turn_debug_notes`, AC/RD layer seams | Integration smoke; registered downstream consumers |
| `tests/helpers/repairs_consumer_facade.py` | **Repairs-layer consumer** — `_apply_*` layer delegates, `repair_fallback_behavior` | Non-owner tests needing repair seams; not gate legality |
| `tests/helpers/golden_replay_projection.py` | **Golden replay acceptance** — protected observation paths, `read_fem_meta_from_gate_output`, lineage projection | Replay/drift tests only |
| `tests/helpers/opening_fallback_evidence.py` | Opening FEM scaffolds, owner-bucket asserts | Opening fallback wiring |
| `tests/helpers/strict_social_harness.py` | `runner_strict_bundle`, strict-social gate cases | Strict-social harness consumers |
| `tests/helpers/opening_fallback_gate_harness.py` | Attach-then opening gate (private `feg._*` **localized here**) | Opening owner + diegetic downstream |
| `tests/helpers/fallback_behavior_fixtures.py` | Shipped `fallback_behavior` / `answer_completeness` contract shapes | Gate/transcript/validator wiring |
| `tests/helpers/boundary_semantic_repair_fixtures.py` | Boundary semantic-repair FEM flags + dialogue policy scaffold | `test_final_emission_boundary_no_semantic_repair` |
| `tests/helpers/narrative_mode_validator_fixtures.py` | CTIR stubs, `build_validator_narrative_mode_contract` | NMO-adjacent wiring tests |
| `tests/helpers/block_stu_equivalence_fixtures.py` | Block S/T/U shared contracts + strict-social stub metadata | Equivalence + golden direct-seam |
| `tests/helpers/gate_equivalence_monkeypatch.py` | **Equivalence-only** gate monkeypatch + phase-order trackers | Block S ordering proof; patch speaker/build |
| `tests/helpers/speaker_relocation_shadow_harness.py` | Shadow dual-run, finalize-stack fixture | Block T/U shadow equivalence |
| `tests/helpers/post_speaker_finalize_probe.py` | Post-speaker layer divergence inventory | Block U/V/W probes |
| `tests/helpers/speaker_gate_order.py` | Phase subsequence asserts, normalized text compare | Block S/T equivalence |

**Owner suites** (`test_final_emission_gate.py`, `test_final_emission_meta.py`, `test_final_emission_repairs.py`, etc.) **keep** direct production imports.

---

## Retained private seams (with reasons)

| Location | Seam | Reason |
| --- | --- | --- |
| `opening_fallback_gate_harness` | `feg._opening_scene_safe_fallback_selection`, `feg._enforce_response_type_contract` | Opening attach-then harness; owner-adjacent; isolated from downstream smoke |
| `gate_equivalence_monkeypatch` | `feg._enforce_response_type_contract`, `feg._apply_narrative_authenticity_layer`, tone/authority/anti-railroading/scene-state anchors | **Strict-social trunk ordering proof** (Block S) |
| `post_speaker_finalize_probe` | 15+ `feg._apply_*`, `feg._strip_dialogue_from_text`, `feg._finalize_emission_output`, … | **Per-layer normalized divergence inventory**; not observable via public gate entry alone |
| `speaker_relocation_shadow_harness` | `feg.enforce_emitted_speaker_with_contract` wrap; `sce._apply_speaker_contract_repairs` | **Gate vs isolated shadow equivalence** |
| `emission_smoke_assertions` (internal) | `read_final_emission_meta_dict`, `read_debug_notes_from_turn_payload` | Single smoke delegate to meta read API |
| `golden_replay_projection` (internal) | `read_final_emission_meta_dict` in `read_fem_meta_from_gate_output` | Single replay diagnostic read concentration point |
| `tools/run_scenario_spine_validation.py` | `read_final_emission_meta_dict` | CLI tooling post-gate FEM read (documented) |
| Production (`api_turn_support`, `stage_diff_telemetry`, …) | Gate/meta/replay as designed | Valid owner/production boundaries |

---

## Validation commands and results (closeout run)

**Date:** 2026-06-04

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_ownership_registry.py tests/test_final_emission_debt_retirement.py -q` | **PASS** (24) |
| `python -m pytest tests/test_golden_replay.py -q` | **PASS** (68) |
| `python -m pytest tests/test_turn_pipeline_shared.py -q` | **PASS** (69) |
| `python -m pytest tests/test_block_s_speaker_local_rebind_equivalence.py tests/test_block_t_speaker_relocation_shadow_equivalence.py tests/test_block_u_finalize_stack_divergence.py -q` | **PASS** (14) |

**Closeout sweep total:** **175 tests PASS** (no failures).

Per-block validation during AS1–AS6 is recorded in each `cycle_as_block_as*_implementation_summary.md`.

---

## Optional follow-ups (AS7 — not started)

Low priority; outside required Cycle AS scope:

1. **Repo-wide test-to-test imports** — e.g. `test_n5` → `test_narrative_plan_prompt_regressions`, `test_referential_clarity_player_coref` → visibility owner, `test_prompt_context_public_prompt_boundary` → `test_prompt_context`.
2. **Incremental FEM read thinning** — remaining non-owner suites still calling `read_final_emission_meta_dict` directly (e.g. `test_social_emission_quality.py`, `test_dialogue_plan_final_emission_gate.py`, `test_fallback_overwrite_containment.py`).
3. **Repairs facade expansion** — `test_final_emission_boundary_no_semantic_repair` gate private `feg._apply_referent_clarity_pre_finalize`; legacy downstream files listed in AS3 summary.
4. **Production observation hooks** — public per-layer probes could eventually retire `post_speaker_finalize_probe` private wraps (**gate-owner change**, high effort).
5. **Refresh machine-readable inventory** — re-run AST scan to update `cycle_as_dependency_map.json` post-AS (documentation hygiene).

---

## Final verdict

**Close Cycle AS.**

AS1–AS6 met the recon goals: downstream suites no longer depend on the deleted fixture hub; registered consumers and AS3 repair candidates use narrow facades; FEM reads and equivalence harnesses are thinned and documented; block S/T/U tests use public gate entry points with private seams confined to named helpers.

**Do not begin AS7** unless explicitly requested. AS7 items are optional maintenance, not blockers for AS closure.
