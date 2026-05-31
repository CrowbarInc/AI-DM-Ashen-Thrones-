# Cycle AG — Residual Complexity Burn-Down Recon

**Date:** 2026-05-31  
**Scope:** Reconnaissance only — no runtime, test-behavior, fixture, or governance semantic changes in this pass.  
**Branch context:** Recent closure stack AA → AB → AC → AD → AE → AF landed on `feature/failure-locality` (HEAD `1e5fb76` at recon time).

---

## Executive Summary

Cycles AA–AF materially reduced gate authority sprawl, fallback topology ambiguity, replay harness duplication, test ownership blur, change-locality fanout, and dead governance surface. **Residual complexity is now concentrated in maintenance/process amplifiers and oversized test owners**, not in unresolved ownership splits.

The highest-confidence AG targets share three traits:

1. **Explicitly deferred from AE** (AE5 manifest/inventory decoupling; partial AE3 downstream smoke migration).
2. **Measurable size or co-edit frequency** without touching gate orchestration or protected replay semantics.
3. **Existing protection** via golden replay (59 tests), `test_final_emission_gate.py` (237+ gate tests), ownership registry (17 governance tests), and classifier/dashboard contract suites.

**Recommended first block (AG-1):** AE5 follow-on — wire `PROTECTED_OBSERVATION_FIELDS` into manifest refresh, add CI `--check` for manifest/registry parity, and isolate `test_inventory.json` regeneration from logic commits. **Zero runtime behavior risk; largest closure-commit fanout reduction.**

**Do not touch in AG:** `game/final_emission_gate.py` orchestration/policy layers (9118 LOC; AA5+ deferred), fallback topology merge (AB closed), scaffold-ban unification across HTTP vs replay layers (AC risk note), or visibility tuple retirement at the gate boundary (AB5 intentional remnant).

---

## Evidence Sources Reviewed

### Convergence / ownership artifacts

| Path | Use in this recon |
| --- | --- |
| `docs/architecture_ownership_ledger.md` | Runtime → direct-owner suite routing; drift-watch seams |
| `docs/convergence_ci_inventory.md` | CI-enforced closeout chain |
| `docs/testing/protected_replay_manifest.md` | 41 protected observation paths; dual-family contract |
| `docs/gate_convergence_closeout.md` | Gate freeze boundary (AB terminus) |
| `docs/final_emission_ownership_convergence.md` | FE-C2 repair ownership doctrine |

### Cycle AA–AF recon / closure (2026-05-31)

| Cycle | Artifact | Residual signal |
| --- | --- | --- |
| AA | `docs/cycles/cycle_aa_gate_authority_extraction_*` | Gate −614 LOC extracted; high-risk policy layers deferred |
| AB | `docs/cycles/cycle_ab_fallback_topology_collapse_*` | Topology closed; tuple/visibility compatibility edges remain |
| AC | `docs/cycles/cycle_ac_replay_surface_compression_*` | Harness extracted; `test_golden_replay.py` still 2336 LOC |
| AD | `docs/cycles/cycle_ad_test_authority_consolidation_*` | HTTP seed extraction deferred; turn_pipeline still 1860 LOC |
| AE | `docs/cycles/cycle_ae_change_locality_optimization_*` | AE1–AE4 done; **AE5 deferred**; AE3 partial |
| AF | `docs/cycle_af_dead_governance_removal_*` | Doc/archive hygiene done; runtime hotspots untouched |

### Test governance / inventory

| Path | Signal |
| --- | --- |
| `tests/test_ownership_registry.py` | 638 LOC; 17 governance tests; AD-3 neighbor locks |
| `tests/test_inventory.json` | **128,469 LOC** — closure amplifier |
| `tests/TEST_AUDIT.md` | Test routing discipline |
| `audits/cycle_q_replay_cost_compression_recon_2026-05-29.md` | Prior replay cost baseline |

### Inspection commands run

- Line counts on top Python modules (`game/`, `tests/`, `tests/helpers/`, `tools/`)
- Branch/condition density spot checks (`if`/`elif` counts in gate + golden replay)
- `git log --oneline -15 --name-only` for recent co-edit clusters
- Ripgrep: `protected_observation`, `from tests.test_turn_pipeline_shared`, sealed/tuple tests in gate owner, AE5 deferred references

---

## Top 10 Hotspot Ranking

Priority order: maintenance drag × low behavior risk → repeated logic → test ownership ambiguity → protected fallback/replay surfaces → future fanout reduction.

| Rank | Hotspot | Category | LOC / scale | Risk | Handle now? |
| ---: | --- | --- | ---: | --- | --- |
| **1** | Manifest ↔ registry CI decoupling (AE5) | maintenance | 105 LOC tool + 128k inventory | **Low** | **Yes — AG-1** |
| **2** | `test_turn_pipeline_shared.py` HTTP seed fixture extraction | test | 1860 LOC; **8** test-to-test importers | **Low–medium** | Yes — AG-2 |
| **3** | `test_final_emission_gate.py` Block AI sealed/visibility shape tests | test / gate | 5819 LOC; ~100 tests; ~70 sealed/tuple refs | **Medium** | Yes — AG-3 |
| **4** | Extend `emission_smoke_assertions.py` to remaining downstream HTTP suites | test | 138 LOC helper; 4+ unmigrated suites | **Low–medium** | Yes — AG-4 |
| **5** | `tests/helpers/golden_replay.py` protected social structural composer | replay / test | 1378 LOC; 51 defs | **Low–medium** | Yes — AG-5 |
| **6** | Block S/T/U finalize-stack harness consolidation | test / gate | 540 LOC across 4 files | **Medium** | Yes — AG-6 |
| **7** | Classifier synthetic row builder dedup | replay / test | 1342 + 788 LOC classifier modules | **Low** | Yes — AG-7 |
| **8** | `test_golden_replay.py` residual protected E2E boilerplate | replay | 2336 LOC; 57 tests | **Low** | Yes — AG-8 |
| **9** | Opening FEM literal scatter beyond `opening_fallback_evidence.py` | fallback / test | ~15 consumer files | **Low** | Yes — AG-9 |
| **10** | Ownership registry automated read-side assertion guard | maintenance / test | 638 LOC registry | **Low** | Yes — AG-10 |

---

## Hotspot Detail Table

| Rank | Path | Symbols / regions | Category | Why hotspot | Protected behavior / replay | Safe burn-down move | Risk | When | Protecting tests |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `tools/refresh_protected_replay_manifest.py`, `tools/test_audit.py`, `tests/test_inventory.json`, `docs/testing/protected_replay_manifest.md` | `render_generated_section`, `protected_field_paths` | maintenance | AE5 explicitly deferred; manifest still uses legacy frozensets not `PROTECTED_OBSERVATION_FIELDS`; inventory regen bundled in closure commits (128k-line diffs) | 41 protected paths unchanged; observation set stable since AE1 | Wire refresh tool to `protected_observation_field_registry()`; add pytest `test_manifest_matches_observation_registry`; document inventory-only regen workflow | low | **Now** | `test_golden_replay.py`, `test_failure_classification_contract.py`, `test_ownership_registry.py` |
| 2 | `tests/test_turn_pipeline_shared.py` + 8 importers | `FAKE_GPT_RESPONSE`, `_patch_storage`, `_seed_shared_world`, `_seed_runner_dialogue_context`, `_gm_response` | test | AD-1 thinned assertions but module still owns HTTP seeds; 8 suites import from test module (fanout + collection coupling) | Pipeline HTTP wiring, retry debug, storage parity | Extract `tests/helpers/turn_pipeline_http_fixtures.py`; repoint importers only | low–medium | **Now** | `test_turn_pipeline_shared.py`, `test_playability_smoke.py`, `test_start_campaign_api.py`, `test_narration_transcript_regressions.py` |
| 3 | `tests/test_final_emission_gate.py` | Block AI sealed tests ~4811–5229; legacy tuple round-trips ~4958–4996 | test / gate | Largest direct-owner suite (5819 LOC); helper-shape tests co-located with orchestration integration | Gate orchestration order; sealed selection semantics | Move dataclass/tuple round-trip + helper importability tests to `test_final_emission_sealed_fallback.py` / `test_final_emission_visibility_fallback.py` (1213 LOC visibility owner exists) | medium | **Now** (narrow slice) | `test_final_emission_gate.py`, `test_final_emission_visibility_fallback.py`, `test_gate_convergence_closeout.py` |
| 4 | `tests/test_interaction_continuity_repair.py`, `tests/test_social_speaker_grounding.py`, `tests/test_social_answer_candidate.py`, `tests/test_broadcast_open_call_social.py` | scattered FEM/route/phrase asserts | test | AE3 migrated 3 suites; AE closure lists 4 remaining downstream HTTP files | Downstream smoke only; gate owns legality | Import `emission_smoke_assertions` helpers; thin to route-class + owned-field smoke per AD-3 | low–medium | **Now** | Same modules + `test_turn_pipeline_shared.py` regression slice |
| 5 | `tests/helpers/golden_replay.py` | `protected_structural_expectation`, protected E2E fragments, runner | replay | Post-AC still 1378 LOC; AC recon noted optional `protected_social_structural_base` not added | Protected scenario IDs + drift evaluation (AC-4 dedup done) | Add composer wrapping existing `protected_*_expectation` spreads; no assertion semantic change | low–medium | **Now** | `test_golden_replay.py` full suite |
| 6 | `tests/test_block_s_*`, `tests/test_block_t_*`, `tests/test_block_u_*`, `tests/helpers/speaker_relocation_shadow_harness.py` | finalize-stack fixtures | test / gate | AE recon rank #9; gate ordering tweaks touch 3 equivalence suites together | Speaker relocation safety proofs | `build_finalize_stack_fixture()` in harness; block tests import only | medium | **Now** (after AG-3 if gate tests move) | Block S/T/U tests, `test_gate_convergence_closeout.py` |
| 7 | `tests/test_failure_classifier.py`, `tests/helpers/failure_classifier.py` | synthetic observed row builders | replay / test | Co-edited with golden replay 10×/30 commits (AE recon); inline FEM rows duplicate `opening_fallback_evidence` | Classifier routing taxonomy locked by contract | Extend `failure_classification_sync.py` with row builder facades for opening/social/sealed templates | low | **Now** | `test_failure_classifier.py`, `test_failure_classification_contract.py`, `test_failure_dashboard_controlled_failures.py` |
| 8 | `tests/test_golden_replay.py` | protected E2E integration block | replay | 2336 LOC after AC (−30 net at AC closure; grew with adjacent tests); still hosts all protected scenarios | 59 golden replay tests; manifest scenario IDs | Apply AG-5 composer across 7 protected E2E tests; no scenario deletion | low | **After AG-5** | `test_golden_replay.py`, `-m golden_replay` |
| 9 | `tests/helpers/opening_fallback_evidence.py` + scattered callers | `successful_opening_fem_meta`, inline FEM dicts | fallback / test | AE recon rank #6; opening bucket tests still hand-build partial FEM | Opening owner buckets; golden opening companion locks | Route new tests through evidence builders; migrate only non-prose literals | low | **Now** (incremental) | `test_opening_fallback_owner_bucket.py`, opening golden trio, `test_upstream_response_repairs.py` |
| 10 | `tests/test_ownership_registry.py` | `collect_ownership_governance_errors`, AD-3 neighbors | maintenance / test | AE4 added read-side lock tests but no CI guard against gate test read-side creep | Registry paths + neighbor semantics | Add governance test: gate direct-owner file must not import replay projection ownership helpers for read-side sub-kind asserts | low | **Now** | `test_ownership_registry.py` |

---

## Recommended Burn-Down Order

```text
AG-1  Manifest/registry/inventory decoupling (AE5)     ← start here
AG-2  Turn pipeline HTTP fixture extraction (AD follow-up)
AG-4  Downstream smoke facade extension (AE3 remainder)  ← parallel-safe with AG-2
AG-7  Classifier row builder facades                     ← parallel-safe with AG-1
AG-5  Protected social structural composer (golden_replay.py)
AG-8  Golden replay E2E boilerplate adoption (depends AG-5)
AG-3  Gate Block AI helper-shape test migration (narrow)
AG-6  Block S/T/U finalize-stack harness
AG-9  Opening FEM literal migration (incremental, file-by-file)
AG-10 Ownership registry read-side creep guard
```

**Parallel lanes:** AG-1 + AG-7; AG-2 + AG-4; AG-5 → AG-8 sequential.

**Success metrics (post-AG):**

- Closure commits no longer bundle 128k-line `test_inventory.json` diffs with logic
- `refresh_protected_replay_manifest.py --check` fails CI on registry drift
- Source-only median files/commit ≤ **6** on next 10 source-touching commits (AE target)
- `test_turn_pipeline_shared.py` test-to-test importers → **0**

---

## Replay/Test Protection Map

| Concern | Authority | Protecting tests / tools |
| --- | --- | --- |
| Protected replay observations (41 paths) | `tests/helpers/golden_replay_projection.py` | `tests/test_golden_replay.py`, `-m golden_replay`, `docs/testing/protected_replay_manifest.md` |
| Dual fallback-family projection | `project_replay_fallback_family_from_fem` | AB3/AB4 golden + meta tests |
| Sealed sub-kind read-side lineage | `game/final_emission_replay_projection.py` | `test_final_emission_meta.py`, golden recurrence-key allowlist |
| Gate orchestration | `game/final_emission_gate.py` | `tests/test_final_emission_gate.py`, `test_gate_convergence_closeout.py` |
| Classifier taxonomy | `tests/failure_classification_contract.py` | `test_failure_classifier.py`, `test_failure_dashboard_controlled_failures.py` |
| Test ownership neighbors | `tests/test_ownership_registry.py` | CI convergence-checks, `tools/test_audit.py` |
| Opening owner buckets | `game/final_emission_meta.py` + evidence helpers | `test_opening_fallback_owner_bucket.py`, opening golden locks |
| Downstream HTTP smoke | `tests/helpers/emission_smoke_assertions.py` | AD-1/AD-2 thinned suites; extend without gate-route exact locks |

**Validation slices (recommended per block):**

```bash
python -m pytest tests/test_golden_replay.py -q
python -m pytest -m golden_replay -q
python -m pytest tests/test_ownership_registry.py tests/test_failure_classification_contract.py -q
python -m pytest tests/test_turn_pipeline_shared.py -q
python -m pytest tests/test_final_emission_gate.py -k "sealed_fallback_selection or legacy_tuple" -q
python tools/refresh_protected_replay_manifest.py --check
python tools/validation_coverage_audit.py --strict
```

---

## Deferred / Unsafe Candidates

| Candidate | Why tempting | Why defer / reject |
| --- | --- | --- |
| `game/final_emission_gate.py` (9118 LOC, ~100 branches) | Largest production file | AA closed planned extractions; AA5+ policy layers are behavioral; gate convergence frozen |
| `game/prompt_context.py` (2874 LOC; 57 touches/60d) | High edit frequency | Planner convergence freeze; prompt bundle semantics — not a burn-down target |
| Merge `fallback_family_used` + `realization_fallback_family` | Simpler mental model | AB3/AB4 explicitly forbid; protected replay locks projected diegetic-first field |
| Visibility `from_legacy_tuple` retirement at gate | AB5 follow-on | Medium-high; selection boundary still tuple-shaped for compatibility |
| Unify scaffold-ban tokens across HTTP smoke + replay projection | Duplicated forbidden-term lists | AC Group G: **high** divergence risk across layers |
| `game/final_emission_repairs.py` semantic repair upstream moves | C2 convergence target | Behavioral; requires deliberate upstream moves + boundary tests |
| `game/final_emission_meta.py` normalization shrink (1724 LOC) | Co-edits with gate 6×/30 commits | Write-time FEM packaging; conflates with schema changes |
| Delete redundant golden scenarios | AC found 0 safe deletions | Companion locks and advisory lanes are intentional |
| `game/gm.py` / `game/api.py` bulk reduction | Large files | Turn pipeline behavioral core — out of AG scope |
| Further governance doc pruning | AF closed low-risk archive | Remaining docs have refs or medium merge risk per AF closure |

---

## Files to Pass Back to ChatGPT

### Recon outputs (this cycle)

- `audits/cycle_ag_residual_complexity_burndown_recon_2026-05-31.md` (this file)
- `audits/cycle_ag_hotspot_inventory.json`

### Prior cycle context (residual signals)

- `docs/cycles/cycle_ae_change_locality_optimization_closure_2026-05-31.md` (AE5 deferred)
- `docs/cycles/cycle_ad_test_authority_consolidation_closure_2026-05-31.md` (HTTP seed follow-up)
- `docs/cycles/cycle_ac_replay_surface_compression_closure_2026-05-31.md` (remaining replay LOC)
- `docs/cycles/cycle_ab_fallback_topology_collapse_closure_2026-05-31.md` (intentional seams)
- `docs/cycles/cycle_aa_gate_authority_extraction_closure_2026-05-31.md` (deferred gate policy)

### Hotspot source files (implementation targets)

**Maintenance / tooling**

- `tools/refresh_protected_replay_manifest.py`
- `tools/test_audit.py`
- `tests/test_inventory.json` (read-only sizing reference; regen via tool)
- `tests/helpers/golden_replay_projection.py` (`PROTECTED_OBSERVATION_FIELDS`)

**Test owners / helpers**

- `tests/test_turn_pipeline_shared.py`
- `tests/helpers/emission_smoke_assertions.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_visibility_fallback.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_fixtures.py`
- `tests/test_golden_replay.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/helpers/failure_classifier.py`
- `tests/test_failure_classifier.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/helpers/speaker_relocation_shadow_harness.py`
- `tests/test_ownership_registry.py`

**Governance**

- `docs/testing/protected_replay_manifest.md`
- `docs/architecture_ownership_ledger.md`
- `tests/TEST_AUDIT.md`

**Explicitly out of scope for AG blocks**

- `game/final_emission_gate.py` (orchestration / deferred policy)
- `game/prompt_context.py`
- `game/final_emission_repairs.py`

---

## Suggested First Implementation Block

### AG-1 — Closure decoupling tooling (AE5 completion)

| Field | Value |
| --- | --- |
| **Objective** | Decouple inventory/manifest maintenance from logic commits; enforce registry ↔ manifest parity in CI |
| **Files likely touched** | `tools/refresh_protected_replay_manifest.py`, `tests/test_golden_replay.py` (manifest contract test), optionally `.github/workflows/convergence-checks.yml`, `docs/testing/protected_replay_manifest.md` (generated section refresh only) |
| **Files to avoid** | All `game/**`, `tests/test_final_emission_gate.py`, protected replay scenario bodies |
| **Implementation sketch** | Import `protected_observation_field_registry()` / drift buckets in refresh tool; add `test_protected_replay_manifest_matches_observation_registry`; document `python tools/test_audit.py` as inventory-only workflow |
| **Validation** | `python tools/refresh_protected_replay_manifest.py --check`; `python -m pytest tests/test_golden_replay.py -k manifest -q`; `python -m pytest tests/test_ownership_registry.py -q` |
| **Risk** | **Low** — governance-only; no observation path set changes |
| **Behavior change** | **None** |

---

*Recon complete. No source or test files were modified during this pass.*
