# CN — Final Emission Adjacency Compression Closeout

Date: 2026-06-27  
Scope: Audit-only validation after CN1–CN6 (no behavior changes in this block)

## Executive Summary

The CN cycle **materially reduced Gate Adjacency Pressure** on the primary orchestrator and improved responsibility boundaries across several former pressure magnets. `game/final_emission_gate.py` is now a thin branch orchestrator (~338 lines, **one public entrypoint**). Read-side observability, sanitizer lineage, visibility metadata stamping, repair-layer boilerplate, and protected replay ownership were extracted into focused modules without changing emitted text, FEM field names, protected replay schema, or manifest output (per CN test suites).

Pressure did not disappear—it **dispersed** into adjacent layers that were always gate-coupled: FEM write-side metadata, visibility fallback selection/enforcement, validators, terminal pipeline, and golden replay governance. That dispersion is **healthier** than pre-CN concentration because boundaries are clearer and tests pin module ownership.

**Verdict: CN complete with monitoring.**

One **new architectural friction** emerged in CN6: a test-helper import cycle `golden_replay_projection_registry ↔ golden_replay_projection_fields` (replacing the CN1-resolved `engine → facade` cycle). This does not affect runtime gate behavior but should be monitored or resolved in a small follow-up hygiene block.

**Overall readiness score: 7.8 / 10** — gate-adjacent architecture is materially improved; remaining hotspots are known, bounded, and mostly write-side policy rather than orchestration sprawl.

---

## Gate Adjacency Pressure Assessment

| Dimension | Before CN (discovery baseline) | After CN (closeout) | Assessment |
| --- | --- | --- | --- |
| Gate orchestration concentration | High; gate was historical edit magnet (69 touches / 90d) but already thinning (10 / 30d) | **Low**; single public API, delegates to stacks/exits/context | **Improved** |
| FEM metadata mixing | Very high; write + read + lineage + observability in one module | **Moderate**; write-side remains in `final_emission_meta.py`; read-side in `final_emission_meta_observability.py` | **Improved** |
| Visibility fallback mixing | High; selection + enforcement + metadata in one file | **Moderate**; metadata stamping split to `final_emission_visibility_metadata.py`; selection/enforcement still large | **Improved, incomplete** |
| Sanitizer mixing | High; text transform + lineage + attribution | **Moderate**; lineage in `output_sanitizer_lineage.py` (~140 LOC); sanitizer still ~1520 LOC | **Improved, incomplete** |
| Repair layer boilerplate | High; repeated `(text, meta, extra)` patterns | **Lower**; internal helpers in `final_emission_repairs.py` | **Improved** |
| Replay projection governance | High; ownership duplicated across fields/registry/presence/engine; **import cycle** engine→facade | **Lower duplication**; registry is canonical ownership hub; **new cycle** registry↔fields | **Mixed** |
| Validator concentration | High (~2231 LOC, 89 functions); unchanged by CN | Unchanged | **Remaining hotspot** |
| Test protection | Strong module-boundary and projection contract tests | Same suites green for CN blocks; **one import-graph test now fails** on registry↔fields cycle | **Mostly adequate** |

**Bottom line:** Gate-adjacent ownership is **clearer**, responsibility boundaries **improved**, former gate-orchestration magnets **cooled**, and pressure **dispersed** rather than eliminated. Additional extraction is **justified only for known remaining hotspots**, not for reopening completed CN blocks.

---

## 1. Gate Adjacency Scorecard

Qualitative scale: **1 = poor / highly mixed**, **5 = excellent / focused**.  
Line counts and symbol counts measured at closeout (2026-06-27).

| Module | LOC | Public-ish symbols | Before CN | After CN | Remaining extraction opportunity |
| --- | ---: | ---: | --- | --- | --- |
| **Gate** | | | | | |
| `final_emission_gate.py` | 338 | 1 func | Resp 2, Clarity 4, Coupling 3, API 5, Write 5, Extract 5 | Resp **5**, Clarity **5**, Coupling **4**, API **5**, Write **5**, Extract **5** | **Leave alone** — orchestration home is appropriately thin |
| **Metadata** | | | | | |
| `final_emission_meta.py` | 1496 | ~47 funcs | Resp 2, Clarity 2, Coupling 2, API 2, Write 3, Extract 2 | Resp **3**, Clarity **3**, Coupling **3**, API **3**, Write **4**, Extract **3** | Opening/response-type registry surfaces; owner-bucket stamp helpers |
| `final_emission_meta_observability.py` *(CN2)* | 829 | 25 funcs | *(in meta)* | Resp **4**, Clarity **4**, Coupling **3**, API **4**, Read **5**, Extract **4** | Minor: dead-turn vs stage-diff could split later |
| **Visibility** | | | | | |
| `final_emission_visibility_fallback.py` | 1655 | 30 funcs, 9 classes | Resp 2, Clarity 2, Coupling 2, API 2, Write 4, Extract 2 | Resp **3**, Clarity **3**, Coupling **3**, API **3**, Write **4**, Extract **3** | Selection candidate builders vs enforcement entrypoints |
| `final_emission_visibility_metadata.py` *(CN3)* | 558 | 26 funcs, 12 classes | *(in visibility)* | Resp **4**, Clarity **4**, Coupling **3**, API **4**, Write **4**, Extract **4** | Low priority — module is appropriately scoped |
| **Sanitizer** | | | | | |
| `output_sanitizer.py` | 1520 | 57 funcs | Resp 2, Clarity 2, Coupling 3, API 2, Write 4, Extract 2 | Resp **3**, Clarity **3**, Coupling **3**, API **3**, Write **4**, Extract **3** | Sentence rewrite modes vs strip-only path |
| `output_sanitizer_lineage.py` *(CN4)* | 140 | 6 funcs | *(in sanitizer)* | Resp **5**, Clarity **5**, Coupling **3**, API **4**, Read/Write lineage **5**, Extract **5** | **Leave alone** |
| **Repairs** | | | | | |
| `final_emission_repairs.py` | 1357 | 58 funcs | Resp 3, Clarity 3, Coupling 3, API 3, Write 4, Extract 3 | Resp **3**, Clarity **4**, Coupling **3**, API **3**, Write **4**, Extract **4** | Per-family modules only if validator/repair churn returns |
| **Replay (runtime)** | | | | | |
| `final_emission_replay_projection.py` | 892 | 25 funcs | Resp 4, Clarity 4, Coupling 3, API 4, Read **5**, Extract 4 | Unchanged — already focused | Lineage event taxonomy docs only |
| **Replay (test governance)** | | | | | |
| `golden_replay_projection_registry.py` | 551 | 16 funcs, 4 classes | Resp 3, Clarity 3, Coupling 3, API 3, Read **5**, Extract 3 | Resp **4**, Clarity **5**, Coupling **2**, API **4**, Read **5**, Extract **3** | Break registry↔fields cycle; drift buckets could move later |
| `golden_replay_projection_engine.py` | 163 | 8 funcs | Resp 3, Clarity 2, Coupling **1** (facade cycle), Extract 2 | Resp **4**, Clarity **4**, Coupling **4**, Extract **4** | **CN1 success** — no facade import |
| `golden_replay_projection_fields.py` | 156 | — | Drift bucket + defaults owner | Drift buckets still here; defaults delegate to registry | Consider drift-only module to break cycle |
| **Untouched adjacency** | | | | | |
| `final_emission_validators.py` | 2231 | 89 funcs | Resp 2, Clarity 3, Coupling 3 | Unchanged | Family split (answer/social/fallback/referent) — high value, high risk |
| `final_emission_terminal_pipeline.py` | 341 | 4 funcs | Mini-gate | Unchanged | Terminal decision object vs stamping |
| `upstream_response_repairs.py` | 606 | 21 funcs | Upstream mini-gate | Unchanged | Payload metadata vs text builders |

---

## 2. Pressure Magnet Review

| Hotspot | Classification | Why |
| --- | --- | --- |
| `final_emission_gate.py` | **Healthy** | Thin orchestrator; delegates; no longer absorbs metadata/repair logic |
| `final_emission_meta_observability.py` | **Healthy** | Read-side FEM normalization and telemetry bundles; clear docstring ownership |
| `output_sanitizer_lineage.py` | **Healthy** | Small, lineage-only; sanitizer imports it for stamping |
| `final_emission_visibility_metadata.py` | **Healthy** | Stamping/diagnostic payloads only; enforcement imports it |
| `golden_replay_projection_engine.py` | **Healthy** | Focused projection execution; acyclic w.r.t. facade (CN1) |
| `golden_replay_projection_registry.py` | **Watch** | Canonical ownership hub (good) but **imports fields for parity validation**, creating cycle with fields' lazy default import (CN6) |
| `final_emission_meta.py` | **Remaining hotspot** | Still ~1500 LOC write-side FEM: lineage, opening registry, NA packaging, owner stamps, compatibility surfaces |
| `final_emission_visibility_fallback.py` | **Remaining hotspot** | Still ~1655 LOC: candidate selection, route dispatch, three enforcement chains |
| `output_sanitizer.py` | **Remaining hotspot** | Still ~1520 LOC: text hygiene + modes + empty fallback + strict-social branches |
| `final_emission_validators.py` | **Remaining hotspot** | Largest single module in adjacency zone; CN intentionally did not touch |
| `final_emission_terminal_pipeline.py` | **Watch** | Second gate after branch choice; bounded size but high coupling |
| `upstream_response_repairs.py` | **Watch** | Upstream prepared payloads influence replace paths; moderate size |

---

## 3. Responsibility Distribution

| Concern | Primary owner (after CN) | Secondary / read-side | Evenness vs pre-CN |
| --- | --- | --- | --- |
| Gate orchestration | `final_emission_gate.py` | gate_context, stacks, generic_exit | **Much more even** — gate no longer owns details |
| FEM write / stamps | `final_emission_meta.py` | repairs, fallback modules, sanitizer_lineage | **Slightly more even** — observability extracted |
| FEM read / normalize | `final_emission_meta_observability.py` | replay_projection | **More even** |
| Runtime replay projection | `final_emission_replay_projection.py` | meta (compat re-exports) | Stable |
| Protected replay schema | `golden_replay_projection_fields.py` (drift buckets) | registry (extraction ownership) | **More even** — ownership centralized |
| Protected replay extraction | `golden_replay_projection_registry.py` | engine, presence, extractors | **More even** |
| Visibility selection/enforcement | `final_emission_visibility_fallback.py` | sealed_fallback, terminal_pipeline | **Slightly more even** — metadata split |
| Visibility FEM stamping | `final_emission_visibility_metadata.py` | meta owner-bucket views | **New clear lane** |
| Sanitizer text transform | `output_sanitizer.py` | text_formatting, social_exchange | **Slightly more even** — lineage split |
| Sanitizer lineage/attribution | `output_sanitizer_lineage.py` | meta, ownership_projection_views | **New clear lane** |
| Repair layer wiring | `final_emission_repairs.py` | validators, boundary_contract | **Slightly more even** — boilerplate helpers |
| Validation policy | `final_emission_validators.py` | domain validators | Unchanged concentration |

**Distribution verdict:** Responsibilities are **more evenly spread** across named modules. The gate is no longer the implicit owner of adjacent policy. Remaining imbalance is **intentional write-side concentration** (FEM, visibility enforcement, sanitizer modes, validators), not orchestration sprawl.

---

## 4. Boundary Review — CN Extractions

### CN1 — Replay projection import cycle removal

| Question | Answer |
| --- | --- |
| Reduced coupling? | **Yes** — `golden_replay_projection_engine.py` no longer imports the facade |
| Reduced mixed responsibilities? | **Yes** — engine is projection execution only |
| Compatibility preserved? | **Yes** — facade re-exports unchanged |
| Behavior preserved? | **Yes** — projection/metadata/registry tests pass |
| Tests adequate? | **Yes** — `test_golden_replay_projection_modules.py` (facade cycle test) was green until CN6 introduced a different cycle |

### CN2 — FEM observability extraction

| Question | Answer |
| --- | --- |
| Reduced coupling? | **Yes** — read-side bundle assembly moved out of meta write paths |
| Reduced mixed responsibilities? | **Yes** — `normalize_final_emission_meta_for_observability`, telemetry bundles, dead-turn read classifiers in observability module |
| Compatibility preserved? | **Yes** — `final_emission_meta.py` re-imports and exposes same symbols |
| Behavior preserved? | **Yes** — meta + replay metadata tests pass |
| Tests adequate? | **Yes** — `test_final_emission_meta.py`, projection metadata tests |

### CN3 — Visibility metadata separation

| Question | Answer |
| --- | --- |
| Reduced coupling? | **Moderate** — enforcement still large but stamping is delegated |
| Reduced mixed responsibilities? | **Yes** — `stamp_visibility_fallback_metadata`, payload dataclasses, diagnostic builders in metadata module |
| Compatibility preserved? | **Yes** — visibility_fallback imports metadata helpers |
| Behavior preserved? | **Yes** — visibility fallback + gate tests pass |
| Tests adequate? | **Yes** — `test_final_emission_visibility_fallback.py`, visibility integration tests |

### CN4 — Sanitizer lineage extraction

| Question | Answer |
| --- | --- |
| Reduced coupling? | **Yes** — lineage trace init/event/attribution isolated |
| Reduced mixed responsibilities? | **Yes** — `output_sanitizer_lineage.py` does not mutate player text |
| Compatibility preserved? | **Yes** — sanitizer imports lineage helpers |
| Behavior preserved? | **Yes** — sanitizer + replay metadata tests pass |
| Tests adequate? | **Yes** — `test_output_sanitizer.py`, golden replay metadata |

### CN5 — Repair layer boilerplate consolidation

| Question | Answer |
| --- | --- |
| Reduced coupling? | **Low** — internal refactor only |
| Reduced mixed responsibilities? | **Slightly** — clearer layer return/failure helpers; no new modules |
| Compatibility preserved? | **Yes** — public repair function signatures unchanged |
| Behavior preserved? | **Yes** — repairs, validators, boundary, gate tests pass |
| Tests adequate? | **Yes** — focused repair + no-semantic-repair suites |

### CN6 — Protected replay ownership registry consolidation

| Question | Answer |
| --- | --- |
| Reduced coupling? | **Mixed** — duplication reduced, but **registry↔fields import cycle introduced** |
| Reduced mixed responsibilities? | **Yes** — extraction source ownership, trace container policy, flat defaults, routing ownership in one registry |
| Compatibility preserved? | **Yes** — fields/presence/engine/routing read from registry via wrappers |
| Behavior preserved? | **Yes** — registry, manifest, metadata, golden replay tests pass |
| Tests adequate? | **Mostly** — functional parity strong; **`test_projection_module_import_graph_has_no_cycles` fails** on fields↔registry |

---

## 5. Remaining Concentration (3+ unrelated concerns)

| Module | Concerns mixed | Benefit of further extraction | Risk | Recommendation |
| --- | --- | --- | --- | --- |
| `final_emission_meta.py` | FEM lifecycle, mutation lineage, opening/response-type registries, NA packaging, producer stamps, dead-turn write hooks, compat read re-exports | Medium — smaller write-side surface | High — FEM field names are replay-protected | **Monitor** — do not split without a dedicated metadata cycle |
| `final_emission_visibility_fallback.py` | Candidate selection, route dispatch, hard replacement, three enforcement chains, first-mention/referential clarity | Medium — easier to test selection trees | High — user-visible replacement text | **Future cycle candidate** — selection vs enforcement only |
| `output_sanitizer.py` | Strip modes, rewrite modes, empty fallback, strict-social branches, sentence assembly | Medium — mode-specific modules | High — subtle text diffs | **Future cycle candidate** — after visibility/FEM stability window |
| `final_emission_validators.py` | Answer, social, fallback, referent, opening, response-type validators | High — family ownership clarity | Very high — policy duplication risk with repairs | **Future cycle candidate** — plan as validator-family split, not gate-adjacent tweak |
| `final_emission_repairs.py` | Orchestration, validator calls, metadata merges, referent minimal repair, fallback strip-only | Low — CN5 helpers already reduced boilerplate | Medium | **Leave alone** unless repair churn resumes |
| `golden_replay_projection_registry.py` + `fields.py` | Extraction ownership vs drift bucket taxonomy | Low — break cycle by moving parity check or drift paths | Low | **Monitor / small hygiene block** — break import cycle |

---

## 6. Churn Review

### Pre-CN pattern (from discovery)

- **90-day:** `final_emission_gate.py` led candidate files (69 touches).
- **30-day:** Gate had **cooled to 10 touches**; pressure had already moved to golden replay projection, FEM meta, replay projection runtime, opening/sealed/visibility fallback tests.

### Post-CN expectation

| Former hotspot | Status after CN |
| --- | --- |
| Gate orchestration | **Cooled** — stable thin surface |
| `golden_replay_projection_engine → facade` cycle | **Resolved** (CN1) |
| FEM observability in meta | **Cooled** — edits should land in observability module |
| Visibility metadata in fallback file | **Partially cooled** — stamping churn moves to metadata module |
| Sanitizer lineage in sanitizer | **Partially cooled** — lineage edits isolated |
| Repair boilerplate | **Cooled** — internal helper churn only |
| Replay ownership duplication | **Cooled functionally** — registry is hub; **new cycle** is churn risk for CN6 follow-up |
| Validators | **Unchanged** — still primary edit magnet if policy changes |

**Pressure dispersion:** Yes — edits should target **named owners** rather than the gate. **New unintentional hotspot:** test-helper **registry ↔ fields** coupling.

---

## 7. Architectural Recommendation

### **CN complete with monitoring**

CN1–CN6 achieved the stated architectural reductions without regressing replay output, manifest, or gate behavior. The gate is appropriately thin; extracted modules have clear docstring ownership; test suites for each CN block pass.

**Do not open CN7-style implementation work immediately.** The next justified work is **small and targeted**:

1. **Hygiene (recommended, low risk):** Break `golden_replay_projection_registry ↔ golden_replay_projection_fields` import cycle (e.g. move drift-path parity to a one-way validation at test collection time, or pass paths into registry validation without importing `PROTECTED_OBSERVATION_FIELDS` at module level).
2. **Future cycle (optional, medium risk):** Visibility fallback **selection vs enforcement** split — only if visibility route churn resumes.
3. **Future cycle (optional, high risk):** Validator family split — only with explicit policy ownership sign-off.

Additional broad extraction **is not justified** until one of the remaining hotspots shows renewed 30-day churn dominance comparable to pre-CN gate pressure.

---

## Completed Architectural Improvements (CN1–CN6)

| Block | Outcome |
| --- | --- |
| CN1 | Removed `engine → facade` import cycle; engine imports registry/fields directly |
| CN2 | Extracted `final_emission_meta_observability.py` (~829 LOC read-side) |
| CN3 | Extracted `final_emission_visibility_metadata.py` (~558 LOC stamping/diagnostics) |
| CN4 | Extracted `output_sanitizer_lineage.py` (~140 LOC lineage/attribution) |
| CN5 | Consolidated repair-layer `(text, meta, extra)` helpers in `final_emission_repairs.py` |
| CN6 | Centralized protected replay extraction ownership in `golden_replay_projection_registry.py` (~551 LOC) |

---

## Tests Referenced at Closeout

| Suite | Result (audit run) |
| --- | --- |
| CN5 repairs/validators/boundary/gate | Pass |
| CN6 registry/manifest/metadata/golden replay | Pass |
| `test_golden_replay_projection_modules.py` (import graph) | **Fail** — cycle `registry ↔ fields` |
| CF2 routing + CF4 trace nest contracts | Pass |

---

## Invariants Confirmed (no behavior change in CN cycle)

- Protected replay field paths and extraction specs unchanged (41 paths)
- Manifest generated section unchanged
- Replay projection representative fixtures unchanged (BL2/AK5 locks)
- Gate repair semantics and no-semantic-repair boundary unchanged
- FEM field names and sanitizer lineage keys unchanged

---

## Summary Table — Before CN vs After CN

| Metric | Before CN | After CN |
| --- | --- | --- |
| Gate public API surface | Thin but surrounded by dense adjacency | **1 function, explicit delegates** |
| Largest gate-adjacent module | `final_emission_validators.py` (~2231 LOC) | Same (untouched by design) |
| FEM read/write split | Mixed in meta | **Split** (meta + observability) |
| Visibility stamp vs select | Mixed | **Split** (fallback + metadata) |
| Sanitizer lineage | In sanitizer | **Split** (sanitizer + lineage) |
| Replay ownership sources | Duplicated across 4+ helpers | **Registry-canonical** |
| Known import cycles (tests) | engine → facade | **registry ↔ fields** (regression to fix) |
| Gate 30-day churn (discovery) | 10 touches (cooling) | Expected **stable or lower** |
| Overall adjacency pressure | Concentrated around gate + meta + projection | **Dispersed with clearer owners** |

**Final assessment:** Gate Adjacency Pressure has been **materially reduced** where CN targeted it. Remaining work is **monitoring and optional targeted cycles**, not continuation of the CN compression program as a whole.
