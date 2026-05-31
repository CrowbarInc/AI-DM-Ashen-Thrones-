# Cycle AE — Change Locality Optimization Recon

**Date:** 2026-05-31  
**Branch at recon:** `feature/failure-locality` (HEAD `b54b311`)  
**Scope:** Recon / mapping only — no runtime, test, fixture, or behavior changes in this pass.

---

## Executive Summary

The repo **still shows high cross-file fix fanout**, but the pattern is **concentrated and partially improving**. In the last 30 commits:

| Metric | Raw (all paths) | Source-only (`game/**`, `tests/**`, `tools/**`, `.github/**`, `pytest.ini`) |
| --- | ---: | ---: |
| Median files/commit | 15.0 | **8.0** |
| Mean files/commit | 14.5 | 9.7 |
| Max files/commit | 45 (`b54b311`) | 40 (`b54b311`) |
| Commits ≥ 8 files | **22 / 30 (73%)** | **16 / 30 (53%)** |

Raw counts remain inflated by bundled cycle closure docs and audit markdown. Source-only counts are the actionable signal: **more than half of recent commits still touch 8+ source files**, and the median source fanout (**8**) is unchanged from Cycle T recon despite T1–T6 and AB helper work landing.

Fanout **concentrates in three overlapping clusters**:

1. **Golden replay + failure classification + protected manifest** — `tests/test_golden_replay.py` (18/30), `tests/helpers/golden_replay.py` (13/30), classifier/dashboard helpers (10–11/30). These files co-edit together in **6–13 commits** per pair.
2. **Final emission gate / meta / replay projection** — `game/final_emission_gate.py` + `game/final_emission_meta.py` co-edited **6 times** in 30 commits; gate tests still co-move with golden replay **8 times**.
3. **Cross-layer downstream assertion sprawl** — HTTP pipeline, social emission, answer-completeness, and block S/T/U equivalence suites re-lock `final_route`, phrase bans, and FEM fields that gate/meta owners already pin.

Recent wins (Cycles T, AA, AB) reduced **test-to-test imports** from `test_final_emission_gate.py` and centralized projection/fixtures — but **closure commits** (especially `b54b311`) still sweep 30–40 source files when inventory, registry, and multi-suite assertion updates ride along.

Cycle AE should prioritize **narrow adapters and assertion facades** that absorb recurring field-path and smoke-check edits — not further gate extraction unless scoped to a single read-side seam.

---

## Last 30 Commit Locality Table

Columns use **raw file count** for the 8+ threshold (matches the stated 23–24/30 pattern); **source-only count** in Notes where it diverges materially.

| Commit | Summary | Files Touched | 8+ File Commit? | Main Cluster | Notes |
| --- | --- | ---: | --- | --- | --- |
| `b54b311` | Close Cycle AB fallback topology collapse | 45 | yes | Fallback topology + gate/meta + test inventory/registry sweep | src=40; mixed prod+test; `test_inventory.json` mass regen; 7 cycle-R doc files bundled |
| `c45cfe0` | Finalize strict social fallback ownership extraction | 1 | no | Strict social emission | prod-only; **locality win** |
| `2469338` | Extract final emission gate authority boundaries | 7 | no | Gate authority extraction (AA) | src=6; gate−614 LOC moved to meta/sealed/debug |
| `0ef46f3` | T: reduce maintenance locality fanout | 22 | yes | Cycle T fixture/projection helpers | src=20; T1–T6 landed; golden_replay −568 LOC |
| `1f4e94e` | Cycle S: Runtime Drift Compression | 12 | yes | Golden replay + scenario spine drift | src=8; new compare tool + drift audit |
| `92f7213` | Cycle U: Sustained Session Validation | 13 | yes | Long-session golden replay | src=4 only — **8+ driven by docs** |
| `6ecb98e` | Cycle Q replay cost compression | 7 | no | Golden replay cost | test+doc |
| `1c5b9d8` | P: Collapse fallback family ownership ambiguity | 15 | yes | FEM meta + lineage + classifier | src=13; mixed |
| `77faefe` | O: Final Emission Gate Contraction | 9 | yes | Replay projection extraction | src=8; meta−396 LOC → replay_projection |
| `3582d48` | Complete Cycle N long-session stability | 5 | no | Golden replay harness | test+doc |
| `76fe80a` | M: Reduce maintenance drag | 15 | yes | Lineage telemetry + gate tests | src=11; mixed |
| `f36e834` | Cycle L: Test Ownership Compression | 9 | yes | Visibility fallback test split | src=3 — gate test −1448 LOC moved |
| `2619bb5` | K: Promote replay acceptance gate | 16 | yes | Golden replay CI + dashboard | src=6; docs-heavy |
| `6074e9e` | J: Gate Cluster Extraction | 5 | no | Opening fallback module extract | src=3; **good locality** |
| `fd5f1a9` | Cycle I: Contract opening fallback authorship | 16 | yes | Lineage + classifier + golden | src=13; mixed |
| `b086b75` | H: Runtime Lineage Instrumentation | 12 | yes | FEM meta + lineage telemetry | src=10; mixed |
| `6a402d2` | config: lazy-load OpenAI API key | 9 | yes | Import-safe test config | src=8; mixed |
| `aa9095a` | test: isolate snapshot helpers | 5 | no | Transcript snapshot isolation | test+doc |
| `cf6a89c` | ci: update actions for Node 24 | 2 | no | CI workflow only | other |
| `90adbbb` | G: Runtime Stability and Full-Suite Hygiene | 22 | yes | Suite hygiene + audit artifacts | src=7; docs/audits-heavy |
| `1ae07ea` | Cycle F: Maintenance Drag Measurement | 16 | yes | Classifier + gate test expansion | src=7; docs-heavy |
| `8ddb183` | E: Test Signal Ownership Thinning | 23 | yes | Fallback test thinning | src=13; test+doc |
| `6c00e6e` | D: Final Emission Gate Pressure Reduction | 17 | yes | Visibility/sealed fallback extract | src=15; mixed; gate major refactor |
| `a5c9146` | Cycle C: contract fallback ownership | 18 | yes | Fallback ownership + classifier birth | src=14; mixed |
| `98bc059` | Failure Classification Dashboard | 28 | yes | Classifier infrastructure | src=11; test+doc |
| `ac1ba90` | Add Golden Replay Baseline Suite | 6 | no | Golden replay suite birth | test+doc |
| `f04ef66` | Converge evaluator boundaries | 16 | yes | Governance artifacts | src=3; artifacts-heavy |
| `792de85` | Freeze Evaluator Convergence | 22 | yes | Evaluator + spine tools | src=15; mixed |
| `c89f2f4` | Gate Convergence + Relocation Readiness | 24 | yes | Gate + speaker + block S/T/U | src=22; **worst source-only fanout** |
| `0f03dd6` | Gate Boundary Convergence | 18 | yes | Gate + GM + validators + API | src=14; mixed |

**Classification mix (30 commits):** mixed prod+test **14**, test+doc **9**, prod-only **1**, prod+doc **0**, doc-only **0**, other **1**, test-only **0**.

**Trend:** Gate extraction blocks (J, AA, AB, strict-social) achieve **1–7 file** fanout. **Closure and inventory cycles** (`b54b311`, T, K, C, D) routinely hit **15–45 files** because they bundle registry refresh, multi-suite touch-ups, and markdown.

---

## Hotspot Frequency Table

### Last 30 commits (source files)

| File | Touch Count | Role | Common Co-Edited Files | Locality Risk |
| --- | ---: | --- | --- | --- |
| `tests/test_golden_replay.py` | 18 | Protected replay + structural drift owner | `helpers/golden_replay.py`, `failure_classifier.py`, `failure_dashboard_report.py`, `test_final_emission_gate.py` | **High** — observation field edits fan to classifier + dashboard |
| `tests/helpers/golden_replay.py` | 13 | Replay runner + observation contracts | `test_golden_replay.py`, `golden_replay_projection.py` | **High** |
| `tests/test_final_emission_gate.py` | 12 | Gate orchestration direct owner | `test_golden_replay.py`, `test_final_emission_meta.py`, `final_emission_gate.py` | **High** — still integration + helper-shape residue |
| `tests/helpers/failure_dashboard_report.py` | 11 | Dashboard row rendering | `failure_classifier.py`, `test_golden_replay.py` | **High** |
| `tests/test_failure_classifier.py` | 10 | Replay failure routing owner | `failure_classification_contract.py`, `test_golden_replay.py` | **High** |
| `game/final_emission_meta.py` | 9 | FEM read/normalize/projection | `final_emission_gate.py`, `final_emission_replay_projection.py`, `runtime_lineage_telemetry.py` | **High** |
| `game/final_emission_gate.py` | 8 | Final emission orchestration | `final_emission_meta.py`, `final_emission_sealed_fallback.py` | **Medium-high** — improving after AA/AB |
| `tests/test_final_emission_meta.py` | 8 | FEM schema/projection tests | `test_golden_replay.py`, `final_emission_meta.py` | **Medium-high** |
| `tests/test_failure_dashboard_controlled_failures.py` | 8 | Dashboard smoke | `failure_classifier.py`, `test_golden_replay.py` | **Medium-high** |
| `tests/test_run_scenario_spine_validation.py` | 8 | Scenario spine validation harness | `test_golden_replay.py`, `tools/run_scenario_spine_validation.py` | **Medium** |

### Last 60 days — production hotspots (excluding `data/session*` runtime churn)

| File | Touch Count (60d) | Role | Locality Risk |
| --- | ---: | --- | --- |
| `game/final_emission_gate.py` | 60 | Final emission orchestration | **High** |
| `game/prompt_context.py` | 57 | Prompt bundle / planner input | **High** — planner convergence touch pressure |
| `game/api.py` | 46 | HTTP turn entry | **Medium-high** |
| `game/gm.py` | 28 | GM turn pipeline | **Medium-high** |
| `game/final_emission_meta.py` | 27 | FEM packaging | **High** |
| `game/final_emission_validators.py` | 17 | Post-GM validators | **Medium** |
| `game/final_emission_repairs.py` | 17 | Gate repair derivation | **Medium** |
| `game/social_exchange_emission.py` | 17 | Strict-social emission | **Medium** |
| `game/final_emission_replay_projection.py` | 3 (30d) / newer | Read-side replay projection | **Medium** — growing as meta offload target |
| `game/final_emission_sealed_fallback.py` | 3 (30d) | Sealed fallback selection helpers | **Medium** — improving isolation |

---

## Co-Edit Clusters

### Cluster 1 — Golden replay ↔ failure classification

**Files involved:**  
`tests/test_golden_replay.py`, `tests/helpers/golden_replay.py`, `tests/helpers/golden_replay_projection.py`, `tests/helpers/failure_classifier.py`, `tests/helpers/failure_dashboard_report.py`, `tests/failure_classification_contract.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `docs/testing/protected_replay_manifest.md`

**Why coupled:** FEM field additions (owner buckets, lineage sub-kinds, dual fallback-family projection) must stay aligned across **observation projection**, **classifier routing rules**, **dashboard columns**, and **manifest declarations**. Co-edit pair `golden_replay.py` + `test_golden_replay.py` appears **13×** in 30 commits.

**Legitimate vs accidental:** **Mostly legitimate** at the observation layer, but **accidentally broad** when each field change manually updates 4–6 consumer files instead of a single projection registry.

**Likely intervention:** **Registry narrowing** — extend `golden_replay_projection.py` with a versioned `PROTECTED_OBSERVATION_FIELDS` map consumed by classifier sync (`failure_classification_sync.py`) and manifest generator (`tools/refresh_protected_replay_manifest.py`). **Fixture consolidation** for FEM-shaped dicts via `opening_fallback_evidence.py`.

---

### Cluster 2 — Final emission gate ↔ meta ↔ replay projection

**Files involved:**  
`game/final_emission_gate.py`, `game/final_emission_meta.py`, `game/final_emission_replay_projection.py`, `game/runtime_lineage_telemetry.py`, `game/final_emission_sealed_fallback.py`, `tests/test_final_emission_gate.py`, `tests/test_final_emission_meta.py`

**Why coupled:** Gate writes FEM; meta normalizes/packages; replay projection reads for lineage keys. AA/AB moved authority outward, but **schema drift** still touches gate + meta + projection + meta tests together (**6 co-edits** gate+meta in 30 commits).

**Legitimate vs accidental:** **Legitimate** for write-time schema changes; **accidental** when read-side projection tweaks still require gate test updates.

**Likely intervention:** **Local ownership** — treat `final_emission_replay_projection.py` + `test_final_emission_meta.py` as the **only** edit path for read-side lineage/sub-kind changes; gate tests assert orchestration only. **Helper extraction** complete for sealed selection; continue for visibility routing hooks.

---

### Cluster 3 — Opening / sealed / visibility fallback family

**Files involved:**  
`game/final_emission_opening_fallback.py`, `game/final_emission_sealed_fallback.py`, `game/final_emission_visibility_fallback.py`, `game/diegetic_fallback_narration.py`, `game/upstream_response_repairs.py`, `tests/helpers/final_emission_gate_fixtures.py`, `tests/helpers/opening_fallback_evidence.py`, `tests/test_final_emission_opening_fallback.py`, `tests/test_final_emission_visibility_fallback.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_diegetic_fallback_narration.py`

**Why coupled:** Fallback **selection** (gate), **prose** (diegetic/upstream), **owner buckets** (meta), and **harness setup** (fixtures) share canonical constants (e.g. frontier gate opening text).

**Legitimate vs accidental:** **Legitimate** coupling for end-to-end opening paths; **accidental** duplication of FEM dict literals and phrase assertions across 10+ test modules (partially fixed by T5/R1).

**Likely intervention:** **Fixture consolidation** — single `opening_fallback_evidence.py` + `final_emission_gate_fixtures.py` import surface; **assertion facade** for owner-bucket smoke checks. Avoid further gate prose growth.

---

### Cluster 4 — Cross-layer HTTP / pipeline downstream locks

**Files involved:**  
`tests/test_turn_pipeline_shared.py`, `tests/test_answer_completeness_rules.py`, `tests/test_response_delta_requirement.py`, `tests/test_interaction_continuity_repair.py`, `tests/test_social_answer_candidate.py`, `tests/test_social_speaker_grounding.py`, `tests/test_broadcast_open_call_social.py`, `tests/test_c4_narrative_mode_live_pipeline.py`

**Why coupled:** Full HTTP stack tests re-assert `final_route`, procedural phrase bans, and visibility stock fallbacks already owned by gate, sanitizer, and visibility suites.

**Legitimate vs accidental:** **Accidental** for phrase-level and exact-route duplicates; **legitimate** for one smoke per distinct HTTP route class.

**Likely intervention:** **Adapter/facade** — `tests/helpers/emission_smoke_assertions.py` with route-class presence checks; thin pipeline tests to wiring-only. **Registry narrowing** in `test_ownership_registry.py` to flag new duplicate families.

---

### Cluster 5 — Gate convergence / speaker relocation equivalence

**Files involved:**  
`tests/test_block_s_speaker_local_rebind_equivalence.py`, `tests/test_block_t_speaker_relocation_shadow_equivalence.py`, `tests/test_block_u_finalize_stack_divergence.py`, `tests/helpers/speaker_relocation_shadow_harness.py`, `game/speaker_contract_enforcement.py`, `game/upstream_response_repairs.py`

**Why coupled:** Equivalence proofs share harness fixtures and finalize-stack ordering; any gate ordering tweak touches block S/T/U tests together.

**Legitimate vs accidental:** **Legitimate** for relocation safety; fanout should **stabilize** now that gate convergence is frozen.

**Likely intervention:** **Helper extraction** only — shared finalize-stack fixture builder; avoid editing block tests individually when harness API suffices.

---

### Cluster 6 — Inventory / registry / manifest hygiene (closure amplifier)

**Files involved:**  
`tests/test_inventory.json`, `tests/test_ownership_registry.py`, `tests/TEST_AUDIT.md`, `docs/testing/protected_replay_manifest.md`, `tools/refresh_protected_replay_manifest.py`, cycle closure markdown under `docs/reports/` and `tests/cycle_r_*`

**Why coupled:** Closure commits regenerate inventory, refresh manifest sections, and bundle recon docs — inflating raw fanout without runtime risk.

**Legitimate vs accidental:** **Accidental process coupling** — should be **tool-driven single-file** updates.

**Likely intervention:** **Fixture consolidation** — manifest refresh from projection constants only; separate **docs-only** commits from source commits in future cycles.

---

## Change-Path Shortening Candidates

Ranked by expected locality benefit × frequency of touch.

| Rank | Candidate Name | Files Involved Today | Desired Future Edit Path | Likely Implementation Type | Expected Locality Benefit | Behavior Risk |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Protected observation field registry** | golden_replay, golden_replay_projection, failure_classifier, failure_classification_contract, failure_dashboard_report, protected_replay_manifest | Edit `golden_replay_projection.py` registry + run sync helper | Registry narrowing + contract sync | New FEM observation field: **1–2 files** instead of 6+ | Low |
| 2 | **Classifier/dashboard assertion facade** | test_failure_classifier, test_failure_dashboard_controlled_failures, failure_dashboard_report | Add field expectations via shared `assert_classifier_row_shape()` | Local helper / adapter | Dashboard/classifier column changes: **−2–3 files** | Low |
| 3 | **Downstream `final_route` smoke facade** | turn_pipeline_shared, answer_completeness, response_delta, interaction_continuity_repair, c4 pipeline | Import `assert_emission_route_class()` from helper | Adapter | Route assertion tweaks: **−4–6 test files** | Low–medium |
| 4 | **HTTP phrase-ban smoke thinning** | turn_pipeline_shared, social_speaker_grounding, social_answer_candidate, broadcast_open_call_social | Pipeline: tag/markers only; full matrix in output_sanitizer + visibility | Test fanout reduction | Phrase ban changes: **−3–5 files** | Medium — must keep one HTTP smoke per route |
| 5 | **Read-side lineage edit path lock** | final_emission_gate, final_emission_meta, final_emission_replay_projection, test_final_emission_gate | Read-side sub-kind/lineage: **replay_projection + test_final_emission_meta only** | Local ownership policy + lint/check | Lineage projection: **−2–3 files** | Low |
| 6 | **Opening FEM dict single builder** | opening_fallback_evidence, final_emission_gate_fixtures, classifier tests, golden replay | All opening FEM literals via `opening_fallback_evidence.py` | Fixture consolidation | Opening bucket tests: **−3–4 files** | Low |
| 7 | **Scenario spine validation adapter** | test_run_scenario_spine_validation, golden_replay, tools/run_scenario_spine_validation | Spine tool imports projection helpers only | Adapter | Spine validation field edits: **−2 files** | Low |
| 8 | **Closure decoupling (process)** | test_inventory.json, cycle markdown, source modules in same commit | Separate inventory/manifest commits from logic commits | Process / tooling | Closure commits: **−10–30 raw paths** | None |
| 9 | **Block S/T/U harness fixture builder** | block_s/t/u tests, speaker_relocation_shadow_harness | Single `build_finalize_stack_fixture()` | Helper extraction | Speaker ordering tweaks: **−2 files** | Medium |
| 10 | **Gate helper-shape test relocation** | test_final_emission_gate (helper-shape sections), test_final_emission_sealed_fallback (future), test_final_emission_visibility_fallback | Move extracted-helper shape tests to **owner module test files** | Local ownership | Gate test file churn: **−1 file** on helper-only edits | Medium |

---

## Test Fanout Candidates

Ranked test-side changes that reduce future churn (builds on Cycle R/T completions).

| Rank | Candidate | Test Files Most Touched | Shared Fixtures | Duplication Pattern | Narrower Fixture/Helper |
| --- | --- | --- | --- | --- | --- |
| 1 | **Observation projection registry consumer rewiring** | `test_golden_replay.py`, `test_failure_classifier.py`, `test_failure_dashboard_controlled_failures.py` | `golden_replay_projection.py`, `failure_classification_sync.py` | Inline FEM field paths repeated across classifier + golden | Extend projection registry; classifier imports paths from projection module |
| 2 | **Pipeline HTTP smoke facade** | `test_turn_pipeline_shared.py` (62 tests), `test_answer_completeness_rules.py`, `test_response_delta_requirement.py` | None centralized today | Full `final_route == "replaced"` + phrase bans | `tests/helpers/emission_smoke_assertions.py` |
| 3 | **Passive phrase-ban downstream thinning** | `test_turn_pipeline_shared.py`, `test_social_speaker_grounding.py`, `test_social_answer_candidate.py` | — | Same sanitizer phrases re-locked | Marker/tag smoke only in downstream; matrix in `test_output_sanitizer.py` |
| 4 | **Question-resolution outcome smoke** | `test_broadcast_open_call_social.py`, `test_social_exchange_emission.py` | `dialogue_social_plan.py` | Direct `question_resolution_rule_check` table duplication | Broadcast: pass/fail + one reason code only |
| 5 | **Gate helper-shape test migration** | `test_final_emission_gate.py` (~100 tests) | `final_emission_gate_fixtures.py` | Helper dataclass/tuple shape tests live in gate integration file | Move to `test_final_emission_sealed_fallback.py` / visibility owner files |
| 6 | **Gauntlet test-function import cleanup** | `test_gauntlet_regressions.py` | imports gate fixtures (fixed) but may still reuse gate test patterns | Reuse helper callables not test collection coupling | Shared helper in `final_emission_gate_fixtures.py` |
| 7 | **Inventory regeneration isolation** | Any commit touching `test_inventory.json` | `tools/test_audit.py` | 76k-line JSON diff bundles with logic changes | Pre-commit: inventory-only commit or CI job |
| 8 | **Manifest verification test** | `test_golden_replay.py`, manual manifest edits | `refresh_protected_replay_manifest.py` | Manifest drift fixed manually across docs + tests | Single test: manifest matches projection constants |

**Test files most frequently touched (30 commits):**  
`test_golden_replay.py`, `helpers/golden_replay.py`, `test_final_emission_gate.py`, `helpers/failure_dashboard_report.py`, `test_failure_classifier.py`, `test_final_emission_meta.py`, `test_failure_dashboard_controlled_failures.py`, `test_run_scenario_spine_validation.py`.

**Fixtures already extracted (do not re-do):**  
`final_emission_gate_fixtures.py`, `golden_replay_projection.py`, `failure_classification_sync.py`, `opening_fallback_evidence.py`, `runtime_lineage_reporting.py` — **extend** these rather than adding parallel helpers.

---

## Recommended Implementation Blocks

Five small blocks sized for Cycle AE. Blocks AE1–AE2 target the highest co-touch cluster; AE3–AE5 are parallel-safe test-side reductions.

### AE1 — Protected observation field registry

| Field | Value |
| --- | --- |
| **Objective** | Versioned map of protected observation fields consumed by golden replay projection, classifier sync, and manifest refresh |
| **Files likely touched** | `tests/helpers/golden_replay_projection.py`, `tests/helpers/failure_classification_sync.py`, `tools/refresh_protected_replay_manifest.py`, `tests/test_golden_replay.py` (registry contract test) |
| **Files to avoid touching** | `game/final_emission_gate.py`, `game/final_emission_meta.py`, block S/T/U tests |
| **Validation commands** | `py -m pytest tests/test_golden_replay.py tests/test_failure_classification_contract.py tests/test_failure_classifier.py -q` |
| **Risk level** | Low |
| **Parallel with** | AE3, AE4, AE5 |

### AE2 — Classifier/dashboard row facade

| Field | Value |
| --- | --- |
| **Objective** | Shared row-shape assertions so classifier and dashboard tests stop duplicating FEM column expectations |
| **Files likely touched** | `tests/helpers/failure_dashboard_report.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py` |
| **Files to avoid touching** | `tests/test_golden_replay.py` (unless adding one integration smoke), runtime modules |
| **Validation commands** | `py -m pytest tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py -q` |
| **Risk level** | Low |
| **Parallel with** | AE1 (after registry constants exist) or AE3 |

### AE3 — Downstream emission smoke facade

| Field | Value |
| --- | --- |
| **Objective** | Replace scattered exact `final_route` and FEM presence assertions in HTTP/downstream suites with route-class smoke helpers |
| **Files likely touched** | New `tests/helpers/emission_smoke_assertions.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_interaction_continuity_repair.py`, `tests/test_answer_completeness_rules.py` (max 1–2 cases each) |
| **Files to avoid touching** | `tests/test_final_emission_gate.py` orchestration tables, golden replay structural tests |
| **Validation commands** | `py -m pytest tests/test_turn_pipeline_shared.py tests/test_interaction_continuity_repair.py tests/test_answer_completeness_rules.py -q` |
| **Risk level** | Medium |
| **Parallel with** | AE1, AE5 |

### AE4 — Read-side lineage edit path lock

| Field | Value |
| --- | --- |
| **Objective** | Document and enforce that lineage/sub-kind projection changes edit only `game/final_emission_replay_projection.py` + `tests/test_final_emission_meta.py`; add ownership registry neighbor rule |
| **Files likely touched** | `game/final_emission_replay_projection.py`, `tests/test_final_emission_meta.py`, `tests/test_ownership_registry.py`, `docs/testing/protected_replay_manifest.md` |
| **Files to avoid touching** | `game/final_emission_gate.py` unless write-time stamp changes are explicitly in scope |
| **Validation commands** | `py -m pytest tests/test_final_emission_meta.py tests/test_golden_replay.py -k "subkind or lineage or projection" -q` ; `py -m pytest tests/test_ownership_registry.py -q` |
| **Risk level** | Low |
| **Parallel with** | AE2 |

### AE5 — Closure decoupling tooling

| Field | Value |
| --- | --- |
| **Objective** | Make inventory + manifest updates runnable as standalone commands; add CI check that manifest matches projection registry (AE1 output) |
| **Files likely touched** | `tools/refresh_protected_replay_manifest.py`, `tools/test_audit.py`, `tests/test_golden_replay.py` (manifest test), `docs/testing/protected_replay_manifest.md` |
| **Files to avoid touching** | Runtime `game/**` |
| **Validation commands** | `python tools/refresh_protected_replay_manifest.py --check` ; `py -m pytest tests/test_golden_replay.py -k manifest -q` |
| **Risk level** | Low |
| **Parallel with** | AE1 (depends on registry), AE3 |

**Suggested order:** AE1 → AE2 → AE5 in sequence; AE3 and AE4 parallel after AE1 merges.

**Success criterion:** Next 10 source-touching commits: source-only median ≤ **6**, no maintenance block exceeds **7 source files** unless tagged `cross-cutting`.

---

## Files to Pass Back to ChatGPT

Provide these for implementation block generation:

### Recon and prior cycle context

- `cycle_ae_change_locality_optimization_recon_2026-05-31.md` (this report)
- `docs/reports/cycle_t_maintenance_locality_reduction_recon_2026-05-30.md`
- `tests/cycle_r_test_fanout_reduction_recon_2026-05-30.md`
- `docs/reports/cycle_ab_fallback_topology_collapse_closure_2026-05-31.md`
- `audits/cycle_f_final_gate_hotspot_touch_budget_20260518.md`

### Top hotspot source files (production)

- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_visibility_fallback.py`
- `game/final_emission_opening_fallback.py`
- `game/runtime_lineage_telemetry.py`
- `game/upstream_response_repairs.py`
- `game/diegetic_fallback_narration.py`

### Key co-edited test / helper files

- `tests/test_golden_replay.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_meta.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/helpers/final_emission_gate_fixtures.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/failure_classification_contract.py`
- `tests/test_ownership_registry.py`

### Downstream fanout tests (for AE3 scoping)

- `tests/test_turn_pipeline_shared.py`
- `tests/test_answer_completeness_rules.py`
- `tests/test_response_delta_requirement.py`
- `tests/test_interaction_continuity_repair.py`
- `tests/test_broadcast_open_call_social.py`

### Fixture / manifest / tooling

- `docs/testing/protected_replay_manifest.md`
- `tools/refresh_protected_replay_manifest.py`
- `tools/run_scenario_spine_validation.py`
- `pytest.ini`
- `tests/README_TESTS.md`

### Supporting command output

```text
# Last 30 commits — source-only stats (2026-05-31)
median=8.0 mean=9.7 max=40 8+=16/30

# Top source touches (30 commits)
18 tests/test_golden_replay.py
13 tests/helpers/golden_replay.py
12 tests/test_final_emission_gate.py
11 tests/helpers/failure_dashboard_report.py
10 tests/test_failure_classifier.py
 9 game/final_emission_meta.py
 8 game/final_emission_gate.py

# Strongest prod co-edit (30 commits)
6× game/final_emission_gate.py + game/final_emission_meta.py

# Strongest test co-edit (30 commits)
13× tests/helpers/golden_replay.py + tests/test_golden_replay.py
```

---

## Validation

**Collection (2026-05-31):** `4287 tests collected` via `py -m pytest --collect-only`.

**Recommended validation commands (repo root):**

```bash
# Fast lane (day-to-day)
py -m pytest -m "not transcript and not slow" -q

# Ownership governance
py -m pytest tests/test_ownership_registry.py -q

# Golden replay protected lane
py -m pytest tests/test_golden_replay.py -q

# Failure classification cluster
py -m pytest tests/test_failure_classification_contract.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q

# Gate + meta smoke
py -m pytest tests/test_final_emission_gate.py tests/test_final_emission_meta.py -q

# Inventory audit (non-pytest)
py -3 tools/test_audit.py
```

**Recon pass verification:** `py -m pytest tests/test_ownership_registry.py -q` — **passed** (13 tests). No other tests run in this recon pass.

---

## Uncertainty / Missing Context

1. **`tests/test_inventory.json` churn** — The `b54b311` commit includes a ~76k-line inventory regen; unclear if future cycles will keep bundling inventory with logic. AE5 assumes decoupling is acceptable process-wise.
2. **60-day `data/session.json` / `session_log.jsonl` counts (89/88)** reflect test runtime writes, not maintenance fanout — excluded from hotspot analysis but may confuse raw `git log` frequency scripts.
3. **`test_inventory.json` stale snapshot** — Cycle R noted `generated_utc` 2026-04-25 vs 4287 collected tests; post-`b54b311` inventory may be fresher but was not re-audited field-by-field in this pass.
4. **Gate freeze boundary** — `docs/gate_convergence_closeout.md` marks gate orchestration frozen at AB; AE4 read-side lock aligns with freeze, but any write-time FEM stamp change still legitimately touches gate + meta.
5. **Branch context** — Analysis run on current working tree at `b54b311`; if additional unpushed commits exist locally, counts may shift slightly.

---

*Methodology: `git log --name-only --pretty=format:"COMMIT %h %s" -n 30`, source-only classification per Cycle F rules, co-edit pair analysis via `tools/_cycle_ae_git_audit.py` (ephemeral, not committed). Prior recon cross-check: Cycle T (2026-05-30), Cycle R (2026-05-30), Cycle F hotspot budget (2026-05-18).*
