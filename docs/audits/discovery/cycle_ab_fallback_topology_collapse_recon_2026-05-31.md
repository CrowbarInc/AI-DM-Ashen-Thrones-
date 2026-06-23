# Cycle AB — Fallback Topology Collapse Recon — 2026-05-31

**Scope:** discovery and mapping only. No runtime behavior, fixtures, tests, or code were changed for this pass.

**Prior art:** Cycle P (2026-05-28/29) collapsed fallback *family authorship* and split-owner projection. Cycle AB focuses on *topology breadth*: equivalent routes, compatibility residue, duplicate ownership projection, and dead branches.

---

## A. Executive summary

### Current topology breadth

Fallback behavior spans **three parallel vocabularies** that must not be collapsed blindly:

| Vocabulary | Examples | Primary owners |
|---|---|---|
| **Governed realization families** (9) | `upstream_prepared_emission`, `strict_social_deterministic_fallback`, `gate_terminal_repair`, `legacy_diegetic_fallback` | `game/realization_authority.py`, stamped via `game/realization_provenance.py` |
| **Diegetic dispatch families** (5) | `scene_opening`, `observe`, `action`, `social` + `temporal_frame` | `game/diegetic_fallback_narration.py` → `fallback_family_used` |
| **Runtime / replay projection kinds** | `scene_opening`, `strict_social_fallback`, `sanitizer_strict_social`, `sealed_or_global_replacement`, `upstream_fast_fallback` | `game/final_emission_replay_projection.py`, `tests/helpers/golden_replay_projection.py` |

**Runtime selection** still fans out across: upstream prepared repairs, opening adapter, strict-social emission, sealed terminal assembly, visibility replacements, sanitizer empty/strict-social, retry terminal selector, API/GM fast fallback, and fallback-behavior repair layers.

**Breadth estimate:** ~25 distinct fallback *paths* (selection + stamping + projection), backed by **9 governed families**, **8 diegetic template IDs**, and **15+ `final_emitted_source` tokens** used in FEM/replay.

### Highest-confidence collapse opportunities

1. **Dead import / retired gate-local opening composer** — `game/final_emission_gate.py` imports `_deterministic_opening_fallback_text_and_meta` but has **no call sites** in `game/` (only the import line). Opening prose composition is upstream-only (`upstream_response_repairs` → `opening_deterministic_fallback`). **Safe:** remove import + stale docs references after test audit.
2. **Compatibility-local authorship constant** — `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` is defined in `upstream_response_repairs.py` but **never assigned in production `game/` code**; only read-side mapping in `final_emission_meta` and classifier/dashboard **negative** tests. **Likely safe:** shrink to test-only fixture vocabulary or delete constant after confirming no replay rows emit it.
3. **Dual family field on replay** — golden replay prefers `fallback_family_used` then `realization_fallback_family`; opening paths often stamp **both** (`scene_opening` + `legacy_diegetic_fallback` or `upstream_prepared_emission`). **Needs replay proof** before merging fields.
4. **Legacy tuple adapters** — `SealedFallbackSelection.from_legacy_tuple` / `VisibilitySelectedFallback.from_legacy_tuple` exist solely for gate tuple compatibility. **Safe merge candidate** once gate callers use dataclass end-to-end (tests lock tuple round-trip today).

### Highest-risk areas

- **Non-strict sealed terminal tree** (`assemble_non_strict_sealed_fallback_selection` + 6 branches) — shared `gate_terminal_repair` stamp masks distinct `final_emitted_source` paths (`global_scene_fallback`, `passive_scene_pressure_fallback`, etc.).
- **Strict-social late gate patches** — `apply_strict_social_emergency_fallback_patch` and multiple accept-path layers can re-apply `minimal_social_emergency_fallback` after social emission already selected deterministic text.
- **Visibility replacement projection** — `visibility_or_scene_replacement` runtime kind can overlay opening/social/global content owners; replay protected fields include visibility buckets.
- **Protected golden replay** — 41 protected observation paths include `fallback_family`, owner buckets, and sanitizer split-owner fields (`docs/testing/protected_replay_manifest.md`).

### Is contraction safe yet?

**Partially.** Metadata/projection contraction (Cycle P-style) is safe with narrow tests. **Topology contraction** (merging selection branches or dropping diegetic vs realization dual stamps) is **not safe yet** without:

- Per-path replay fixture proof for each branch being merged
- Explicit decision on whether `fallback_family` in golden replay means diegetic, realization, or projection kind
- Confirmation that compatibility-local opening path is fully retired in production (evidence: yes for composer; constant/mapping residue remains)

---

## B. File inventory (grouped by purpose)

### Runtime fallback selection

| File | Role |
|---|---|
| `game/final_emission_gate.py` | Master orchestrator: response-type, strict-social, non-strict replace, visibility, layer repairs |
| `game/final_emission_opening_fallback.py` | Opening payload selection / fail-closed (no prose authorship) |
| `game/final_emission_sealed_fallback.py` | Non-strict terminal branch selection + sealed stamps |
| `game/final_emission_visibility_fallback.py` | Visibility/first-mention/referential clarity fallback selection |
| `game/social_exchange_emission.py` | Strict-social deterministic/emergency content + stamping |
| `game/upstream_response_repairs.py` | Upstream prepared opening/answer/action payloads |
| `game/opening_deterministic_fallback.py` | Opening prose composition |
| `game/gm_retry.py` | Retry terminal fallback selection |
| `game/api.py` | Fast fallback / budget failure attachment |
| `game/gm.py` | Provider failure fallback metadata |
| `game/output_sanitizer.py` | Empty-output and strict-social sanitizer fallbacks |
| `game/diegetic_fallback_narration.py` | Diegetic template prose + `fallback_family` classification |
| `game/fallback_provenance_debug.py` | Upstream fast fallback provenance trace |
| `game/fallback_behavior.py` | Policy contract (not selection); consumed by repairs |

### Fallback family definitions / registries

| File | Role |
|---|---|
| `game/realization_authority.py` | `FALLBACK_FAMILIES` + `AUTHORITY_PROFILES` ledger |
| `game/realization_provenance.py` | Family constants + `attach_realization_fallback_family` |
| `game/diegetic_fallback_narration.py` | Template → `fallback_family` / `temporal_frame` map |
| `game/contract_registry.py` | Emergency `final_emitted_source` / `fallback_kind` ID sets |
| `game/final_emission_boundary_contract.py` | Mutation taxonomy incl. `compose_opening_fallback_compatibility_local` |

### Ownership / provenance projection

| File | Role |
|---|---|
| `game/final_emission_meta.py` | FEM shapes, `opening_fallback_owner_bucket_from_meta`, projection field helpers |
| `game/final_emission_replay_projection.py` | `_fem_selected_fallback_projection`, `build_fem_runtime_lineage_events` |
| `game/runtime_lineage_telemetry.py` | Lineage event envelope + split-owner field vocabulary |
| `game/stage_diff_telemetry.py` | `fallback_source` / `fallback_stage` / `fallback_kind` |
| `game/realization_provenance.py` | Normalization to governed families |
| `tools/realization_provenance_audit.py` | Static provenance audit |
| `tools/final_emission_ownership_audit.py` | Ownership audit helper |

### Compatibility / legacy fallbacks

| File | Role |
|---|---|
| `game/upstream_response_repairs.py` | `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` (constant only; no production assign) |
| `game/final_emission_meta.py` | Maps compatibility-local authorship → `unknown-ambiguous` bucket |
| `game/final_emission_opening_fallback.py` | `opening_fallback_compatibility_local_disabled: True` on all active paths |
| `game/final_emission_sealed_fallback.py` | `from_legacy_tuple` / `as_legacy_tuple` |
| `game/final_emission_visibility_fallback.py` | `from_legacy_tuple` / `as_legacy_tuple` |
| `game/opening_deterministic_fallback.py` | Docstring still mentions gate compatibility re-call |
| `game/realization_authority.py` | `legacy_diegetic_fallback`, `legacy_unclassified` families |

### Tests / fixtures / replay manifests

| File | Role |
|---|---|
| `tests/test_golden_replay.py` | Protected replay scenarios (`opening_fallback_path`, strict-social, sanitizer, terminal) |
| `tests/helpers/golden_replay.py` | Observed turn assembly, fallback escalation helpers |
| `tests/helpers/golden_replay_projection.py` | `project_turn_observation`, protected field paths |
| `tests/test_final_emission_gate.py` | Largest gate fallback integration surface |
| `tests/test_opening_fallback_owner_bucket.py` | Owner bucket mapping contract |
| `tests/test_final_emission_meta.py` | FEM + runtime lineage projection |
| `tests/test_upstream_response_repairs.py` | Prepared payload + family stamps |
| `tests/test_diegetic_fallback_narration.py` | Diegetic vs realization family on opening repair |
| `tests/test_realization_authority.py` | Required family registry guard |
| `tests/test_emergency_fallback_registry_static_drift.py` | Contract registry ↔ emission literals |
| `tests/test_failure_classifier.py` | Classifier allowlists incl. compatibility-local negative cases |
| `tests/failure_classification_contract.py` | Allowed `source_family` / fallback tags |
| `docs/testing/protected_replay_manifest.md` | Governance manifest (41 protected paths) |

### Docs / audit artifacts

| File | Role |
|---|---|
| `docs/cycles/cycle_p_fallback_family_collapse_recon_2026-05-28.md` | Prior family-level recon |
| `docs/cycles/cycle_p_fallback_family_collapse_closure_2026-05-29.md` | Split-owner closure |
| `audits/cycle_e_adjacent_fallback_family_ownership_recon_2026-05-17.md` | Adjacent ownership map |
| `audits/opening_fallback_surface_inventory_2026-05-11.md` | Opening surface inventory |
| `docs/gate_cleanup_inventory.md` | Compatibility-local gate composer (may be stale vs code) |
| `docs/retry_fallback_selector_contract.md` | Retry selector contract |
| `docs/realization_provenance_audit.md` | Provenance audit spec |

---

## C. Fallback topology map

**Column notes**

- **Classification:** `runtime-active` | `compatibility-only` | `duplicate` | `dead/unknown` | `projection-only`
- **Owner/Provenance:** selection vs content where Cycle P split fields apply

| Fallback Path | File | Function/Class | Trigger Condition | Owner/Provenance | Output Effect | Tests | Classification | Notes |
|---|---|---|---|---|---|---|---|---|
| Governed family registry | `game/realization_authority.py` | `FALLBACK_FAMILIES` | Metadata stamp / audit | Authority ledger | Normalizes `realization_fallback_family` | `tests/test_realization_authority.py` | projection-only | 9 families; `legacy_unclassified` must not emit text |
| Family attach/normalize | `game/realization_provenance.py` | `attach_realization_fallback_family` | Any fallback stamp site | Normalizer → governed family | FEM/debug `realization_fallback_family` | `tests/test_realization_provenance.py` | runtime-active | Unknown → `legacy_unclassified` |
| Upstream prepared opening | `game/upstream_response_repairs.py` | `build_upstream_prepared_opening_fallback_payload` | `resolution.kind == scene_opening` + attachable facts | Content: `opening_deterministic_fallback`; package: upstream repairs | Prepared payload + `upstream_prepared_opening_fallback` authorship | `tests/test_upstream_response_repairs.py`, `tests/test_final_emission_opening_fallback.py` | runtime-active | Canonical successful opening path |
| Opening gate selection | `game/final_emission_opening_fallback.py` | opening adapter helpers | Invalid opening candidate / missing upstream | Selector: gate; content: upstream or fail-closed | Selects prepared tuple or sealed marker | `tests/test_final_emission_opening_fallback.py`, gate opening tests | runtime-active | Sets `opening_fallback_compatibility_local_disabled: True` |
| Opening fail-closed marker | `game/final_emission_opening_fallback.py` | `_opening_fail_closed_meta_*` | Unusable upstream + insufficient curated facts | `sealed-gate` bucket | Marker text, no local compose | `tests/test_final_emission_meta.py`, golden opening | runtime-active | No `_deterministic_opening` call in module |
| Gate-local opening composer | `game/final_emission_gate.py` | `_deterministic_opening_fallback_text_and_meta` (import) | *None in `game/`* | Was compatibility-local | *None* | Gate tests monkeypatch symbol | **dead/unknown** | Import only; composer runs via upstream |
| Compatibility-local authorship token | `game/upstream_response_repairs.py` | `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` | *Never assigned in `game/`* | Maps to `unknown-ambiguous` if seen | Read-side bucket only | `tests/test_opening_fallback_owner_bucket.py`, classifier negative | **compatibility-only** | Constant + meta mapper residue |
| Response-type opening repair | `game/final_emission_gate.py` | `_enforce_response_type_contract` | Opening validation failure | Upstream prepared or fail-closed | `opening_recovered_via_fallback`, diegetic `scene_opening` + often `legacy_diegetic_fallback` | `tests/test_final_emission_gate.py`, `tests/test_diegetic_fallback_narration.py` | runtime-active | Dual stamp: diegetic + realization |
| Upstream prepared answer/action | `game/upstream_response_repairs.py` | `build_upstream_prepared_emission_payload` | GPT failure / thin answer paths | `upstream_prepared_emission` | Prepared repair text | `tests/test_upstream_response_repairs.py` | runtime-active | Gate selects; lineage owner still gate |
| Strict-social build | `game/social_exchange_emission.py` | `build_final_strict_social_response` | Strict-social route active | Content: social emission; selector: gate/social | Candidate + `strict_social_deterministic_fallback` | `tests/test_social_exchange_emission.py` | runtime-active | |
| Strict-social emergency patch | `game/final_emission_gate.py` | `apply_strict_social_emergency_fallback_patch` | Post-layer legality failure on strict-social | Gate applies pre-authored emergency line | `minimal_social_emergency_fallback` source | `tests/test_strict_social_emergency_fallback_dialogue.py` | runtime-active | Multiple call sites; same line pool |
| Sanitizer strict-social | `game/output_sanitizer.py` | strict-social fallback markers | Strip empties strict-social output | Selection: sanitizer; prose: social emission | Split owner fields on trace | `tests/test_output_sanitizer.py`, golden `strict_social_sanitizer_split` | runtime-active | Model split-owner pattern |
| Sanitizer empty | `game/output_sanitizer.py` | empty fallback markers | Strip-only empty output | Sanitizer + upstream stock | `sanitizer_empty_*` fields | `tests/test_output_sanitizer.py`, golden sanitizer scenarios | runtime-active | |
| Non-strict sealed tree | `game/final_emission_sealed_fallback.py` | `assemble_non_strict_sealed_fallback_selection` | `final_route == replaced`, non-strict | Gate selector; prose via injected providers | Terminal replace + `gate_terminal_repair` | `tests/test_final_emission_gate.py` (sealed), golden terminal | runtime-active | 6 branch decision tree |
| Sealed opening branch | `game/final_emission_sealed_fallback.py` | `opening_provider` in assembly | `opening_mode_active` | Same as opening adapter | Opening safe fallback tuple | Gate + golden `opening_fallback_path` | runtime-active | |
| Sealed social interlocutor | `game/final_emission_sealed_fallback.py` | `social_interlocutor_provider` | Active interlocutor, non-opening | Diegetic `social` family | Minimal interlocutor line | Gate sealed tests | runtime-active | |
| Passive scene pressure | `game/final_emission_gate.py` + diegetic | passive candidate provider | Passive candidate available | `gate_terminal_repair` + observe/action diegetic | `passive_scene_pressure_fallback` | Gate + gauntlet | runtime-active | |
| NPC pursuit neutral | `game/diegetic_fallback_narration.py` | `npc_pursuit_neutral_nonprogress_fallback_line` | `use_neutral_nonprogress` branch | Diegetic action family | Fixed neutral line | Gate sealed tests | runtime-active | |
| Anti-reset continuation | `game/anti_reset_emission_guard.py` + gate | anti_reset provider | `suppress_intro_replace` | Gate + diegetic action | `anti_reset_local_continuation_fallback` | `tests/test_anti_reset_emission_guard.py` | runtime-active | |
| Global scene fallback | `game/diegetic_fallback_narration.py` | `render_global_scene_anchor_fallback` | Default sealed terminal branch | `gate_terminal_repair` + observe diegetic | `global_scene_fallback` | Golden frontier/long session | runtime-active | |
| Visibility replacement | `game/final_emission_visibility_fallback.py` | visibility helpers | Visibility/mention/clarity failure | `visibility_fallback_owner_bucket` | Replacement metadata; may mask underlying family | `tests/test_final_emission_visibility_fallback.py` | runtime-active | Route family ≠ content family |
| Retry terminal | `game/gm_retry.py` | `select_deterministic_retry_fallback_line` | Retry exhausted; supported failure classes | `retry_terminal_fallback` | Terminal retry line + metadata | `tests/test_gm_retry.py` | runtime-active | Many internal providers |
| API/GM fast fallback | `game/api.py`, `game/gm.py` | fast fallback paths | Provider/budget failure | `gpt_budget_or_provider_failure` / provenance trace | Sealed failure text | `tests/test_upstream_fast_fallback_block_l.py` | runtime-active | Diagnostic provenance via `fallback_provenance_debug` |
| Fallback behavior repair | `game/final_emission_repairs.py` | `_apply_fallback_behavior_layer` | Contract pressure flags | Repair layer, not family | May mutate text post-selection | `tests/test_fallback_behavior_repairs.py` | runtime-active | Not a selector; risky overlap |
| Diegetic observe fallback | `game/diegetic_fallback_narration.py` | `render_observe_perception_fallback_line` | Retry/visibility/observe paths | `legacy_diegetic_fallback` when stamped | `fallback_family_used=observe` | `tests/test_diegetic_fallback_narration.py` | runtime-active | Parallel taxonomy to realization |
| FEM replay projection | `game/final_emission_replay_projection.py` | `_fem_selected_fallback_projection` | Post-gate FEM read | `projection_owner` = this module; event `owner` = selector | `fem_runtime_lineage_events` | `tests/test_final_emission_meta.py`, `tests/test_runtime_lineage_telemetry.py` | projection-only | Split owners for opening/strict-social |
| Golden observed `fallback_family` | `tests/helpers/golden_replay_projection.py` | `_project_replay_fallback_family` | `fallback_family_used` ∥ `realization_fallback_family`; bridge for neutral reply | Read-side | Observed turn field | All golden replay | projection-only | Neutral reply bridge is narrow |
| Opening owner bucket | `game/final_emission_meta.py` | `opening_fallback_owner_bucket_from_meta` | FEM fields | `upstream-prepared` / `sealed-gate` / ambiguous | Dashboard/classifier bucket | `tests/test_opening_fallback_owner_bucket.py` | projection-only | Compatibility-local → ambiguous |
| Legacy tuple round-trip | `game/final_emission_sealed_fallback.py` | `SealedFallbackSelection` | Gate still consumes tuples | Compatibility adapter | Same tuple shape | `tests/test_final_emission_gate.py` | **compatibility-only** | Dataclass preferred end state |
| `compose_opening_fallback_compatibility_local` | `game/final_emission_boundary_contract.py` | taxonomy constant | *No production mutation kind emission found* | SEMANTIC_DISALLOWED | Classifier/mutation fence only | Gate taxonomy tests | **dead/unknown** | Docs may be stale vs retired composer |
| `legacy_unclassified` sink | `game/realization_provenance.py` | `normalize_realization_fallback_family` | Unknown family string | Sink | Non-shipping classification | `tests/test_realization_provenance.py` | compatibility-only | Prevents silent unclassified shipping |

---

## D. Collapse candidates

### Safe merge candidates (high confidence)

| Candidate | Paths involved | Evidence | Remaining differences | Tests that distinguish |
|---|---|---|---|---|
| Remove unused gate opening import | `final_emission_gate._deterministic_opening_fallback_text_and_meta` import | `rg` count = 1 line in `game/final_emission_gate.py` (import only) | Tests monkeypatch `feg._deterministic_opening_fallback_text_and_meta` | Gate opening tests (patch target may need redirect to upstream module) |
| Retire compatibility-local constant | `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` | Never assigned in `game/`; golden asserts canonical paths **never** report it | Meta mapper + classifier negative fixtures still reference token | `test_golden_*_no_compatibility_local_ownership`, `test_legacy_compatibility_local_authorship_source_maps_to_unknown_ambiguous` |
| Legacy tuple → dataclass only | `SealedFallbackSelection`, `VisibilitySelectedFallback` | `as_legacy_tuple` used at one gate callsite (`final_emission_gate.py:470`) | Tuple shape locked by tests | `test_*_from_legacy_tuple` round-trips |

### Needs fixture/replay proof

| Candidate | Why uncertain | Proof needed |
|---|---|---|
| Merge `fallback_family_used` (diegetic) with `realization_fallback_family` | Opening repair stamps `scene_opening` + `legacy_diegetic_fallback`; golden protects both via observed turn | Re-run full `tests/test_golden_replay.py` + check protected manifest rows |
| Collapse sealed terminal branches under one projection kind | All stamp `gate_terminal_repair` but differ in `final_emitted_source` | `frontier_gate_long_session`, terminal replay scenarios |
| Single strict-social emergency application helper | Gate + social + sanitizer use same line pool | Strict-social golden + `test_strict_social_emergency_fallback_dialogue.py` |
| Narrow `legacy_diegetic_fallback` stamping | Still used on opening contract repair path | `tests/test_diegetic_fallback_narration.py` asserts family on opening repair |

### Compatibility candidates (keep until proof)

| Item | Old behavior | Tests still requiring | Fixture/manifest |
|---|---|---|---|
| `legacy_diegetic_fallback` family | Classify diegetic template renderers | Diegetic + upstream opening tests | Opening golden paths |
| `legacy_unclassified` normalization | Unknown stamps → non-emitting bucket | `test_realization_provenance.py` | — |
| `compose_opening_fallback_compatibility_local` taxonomy | Fence semantic gate-local compose | Gate convergence tests | — |
| `from_legacy_tuple` adapters | Tuple-shaped gate integrations | Sealed/visibility gate tests | — |
| Compatibility-local authorship **mapping** | Detect stale replay/dashboard rows | Classifier `legacy_compatibility_local_unknown_ambiguous` | Synthetic classifier fixtures only |
| Sanitizer `legacy_sentence_rewrite` mode | Historical rewrite boundary | `tests/test_output_sanitizer.py` with legacy ctx | No production caller per audits |

### Dead-branch candidates

| Branch | Evidence | Removal needs | Risk |
|---|---|---|---|
| Gate `_deterministic_opening_fallback_text_and_meta` | Import only in `game/final_emission_gate.py` | Update tests that monkeypatch gate symbol | Low |
| Production assign of `compatibility_local_opening_deterministic` | Constant exists; no `game/` assign | Remove constant or move to test helper | Low |
| `compose_opening_fallback_compatibility_local` runtime mutation | Only in boundary contract + tests | Confirm gate never emits kind | Low |
| Stale docs: gate-local opening compose | `docs/gate_cleanup_inventory.md` describes active branch | Doc refresh only | N/A |

### Do not touch yet

- `apply_final_emission_gate` layer order and accept-path `final_emitted_source` inference
- Protected golden replay scenarios (`opening_fallback_path`, `wrong_speaker_strict_social_emission`, `frontier_gate_long_session`, …)
- `fallback_behavior` repair layer (semantic mutation after fallback selection)
- Visibility replacement tree (high coupling to referential clarity / first mention)
- Full merge of runtime lineage `owner` with `fallback_content_owner` (Cycle P explicitly kept selector owner)

---

## E. Duplicate / equivalent route analysis

### 1. Dual taxonomy: diegetic `fallback_family_used` vs `realization_fallback_family`

| Aspect | `fallback_family_used` | `realization_fallback_family` |
|---|---|---|
| Source | `diegetic_fallback_narration.fallback_template_metadata` | `realization_provenance` constants |
| Values | `scene_opening`, `observe`, `action`, `social` | 9 governed families |
| Opening success | `scene_opening` | `upstream_prepared_emission` or `legacy_diegetic_fallback` on contract repair |
| Tests | `tests/test_diegetic_fallback_narration.py` | `tests/test_realization_authority.py`, gate family tests |

**Equivalence:** Not equivalent — same turn may carry both intentionally. **Tests distinguish:** `test_diegetic_fallback_narration` vs family registry tests. **Replay:** golden prefers `fallback_family_used` first (`golden_replay_projection.py:379-381`).

### 2. Opening: upstream prepared vs gate sealed vs (retired) compatibility-local

| Path | Prose author | Authorship token | Owner bucket |
|---|---|---|---|
| Upstream prepared | `opening_deterministic_fallback` | `upstream_prepared_opening_fallback` | `upstream-prepared` |
| Fail-closed | Gate marker | *(none)* | `sealed-gate` |
| Compatibility-local | *Retired in production* | `compatibility_local_opening_deterministic` | `unknown-ambiguous` |

**Equivalence:** Upstream prepared ≠ fail-closed. Compatibility-local appears **equivalent to upstream** in intent but is **not reachable** in current `game/` code. **Tests:** golden forbids compatibility-local on canonical paths; classifier uses synthetic rows only.

### 3. Strict-social: social emission vs gate emergency patch vs sanitizer

| Path | Selector | Content | `realization_fallback_family` |
|---|---|---|---|
| `build_final_strict_social_response` | social/gate | `social_exchange_emission` | `strict_social_deterministic_fallback` |
| `apply_strict_social_emergency_fallback_patch` | gate | same emergency line pool | often still strict-social or minimal source |
| Sanitizer strict-social | `output_sanitizer` | `strict_social_emission` | split-owner fields |

**Equivalence:** Emergency line text may be **identical** across gate patch sites; ownership differs. **Tests:** sanitizer split-owner tests vs `test_strict_social_emergency_fallback_dialogue.py`. **Replay:** `wrong_speaker_strict_social_emission`, `strict_social_sanitizer_split`.

### 4. Sealed terminal branches → shared `gate_terminal_repair`

All non-strict terminal replacements stamp `gate_terminal_repair` but set different `final_emitted_source` (`global_scene_fallback`, `passive_scene_pressure_fallback`, `anti_reset_local_continuation_fallback`, etc.).

**Equivalence:** Same governed family, **not** same route/provenance. **Tests:** gate sealed branch tests + golden `gate_terminal_repair` frequency caps. **Do not merge** without per-source replay proof.

### 5. Runtime lineage `owner` vs `fallback_content_owner` / `fallback_selection_owner`

Cycle P added split fields; `owner` remains gate for gate-selected opening/strict-social.

**Equivalence:** Intentional duplication for backward-compatible recurrence keys. **Tests:** `tests/test_final_emission_meta.py` lineage projection tests.

---

## F. Historical compatibility fallbacks

| Item | Old behavior supported | Current tests require? | Legacy in fixtures/manifests? | Likely action |
|---|---|---|---|---|
| `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` | Gate-local opening compose authorship | Negative tests only (must not appear on canonical paths) | Classifier/dashboard synthetic rows | **Remove constant** after test helper extraction |
| `compose_opening_fallback_compatibility_local` | Mutation taxonomy for gate-local compose | Taxonomy fence tests only | Docs/audits reference | **Keep taxonomy** until mutation kind removed from contract tests or confirmed unused |
| `legacy_diegetic_fallback` | Diegetic renderers reading raw state | Yes — diegetic + opening repair stamps | Golden opening may show `legacy_diegetic` on repair path | **Keep**; narrow stamping scope in later cycle |
| `legacy_unclassified` | Unknown family strings | Yes — normalization tests | — | **Keep** as sink |
| `SealedFallbackSelection.from_legacy_tuple` | Tuple-based gate API | Yes — round-trip tests | — | **Merge** to dataclass-only when gate refactored |
| `opening_fallback_compatibility_local_disabled` | Flag that local compose is off | Yes — meta defaults/tests | FEM on all active opening paths = `True` | **Keep** until compatibility path fully removed from docs/tests |
| Sanitizer `SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE` | Sentence rewrite mode | Test-only | No production caller (per audits) | **Compatibility-only**; do not delete without sanitizer test refresh |

---

## G. Dead / unreachable branches

| Suspected dead branch | Evidence | Call graph / search | Test before removal? | Risk |
|---|---|---|---|---|
| `_deterministic_opening_fallback_text_and_meta` in gate | Only import in `game/final_emission_gate.py` | Composer called from `upstream_response_repairs` only | Yes — retarget monkeypatches | Low |
| Production emit of `compatibility_local_opening_deterministic` | No assign in `game/` | Constant + meta read mapper | Classifier negative tests remain | Low |
| Gate-local opening compose mutation | Taxonomy + docs; no `game/` compose call | Tests monkeypatch gate symbol but assert it does **not** run on canonical paths | Gate opening integration tests | Low |
| `legacy_unclassified` as emitted family | `may_emit_player_facing_text=False` in registry | Normalizer only | `test_realization_provenance.py` | Low (keep sink) |
| Duplicate import paths (`game\final_emission_gate.py` vs `game/final_emission_gate.py`) | Windows path duplicates in tooling | Cosmetic | No | None |

---

## H. Test / replay protection map

### Commands run (this recon)

```powershell
Set-Location "c:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm"

# Narrow registry / owner
python -m pytest tests/test_opening_fallback_owner_bucket.py tests/test_realization_provenance.py tests/test_emergency_fallback_registry_static_drift.py tests/test_fallback_shipped_contract_propagation.py -q --tb=no
# Result: 23 passed

# Projection + opening + diegetic
python -m pytest tests/test_final_emission_meta.py tests/test_opening_fallback_owner_bucket.py tests/test_upstream_response_repairs.py tests/test_diegetic_fallback_narration.py tests/test_final_emission_opening_fallback.py tests/test_runtime_lineage_telemetry.py -q --tb=line
# Result: 94 passed

# Golden opening lineage + classifier + gate fallback subset
python -m pytest tests/test_golden_replay.py::test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership tests/test_golden_replay.py::test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership tests/test_golden_replay.py::test_golden_observed_turn_projects_runtime_lineage_and_prefers_existing_events tests/test_failure_classifier.py tests/test_final_emission_gate.py -k "fallback or opening" -q --tb=line
# Result: 78 passed

# Golden replay fallback-named scenarios
python -m pytest tests/test_golden_replay.py -k "opening_fallback or strict_social or sanitizer_empty or fallback" -q --tb=no
# Result: 12 passed
```

**Not run (recommended before implementation):** full `python -m pytest tests/test_golden_replay.py -q`, `tests/test_run_scenario_spine_validation.py`, full `tests/test_final_emission_gate.py`.

### Fallback paths currently protected (by executed tests)

| Path cluster | Protecting tests (sample) |
|---|---|
| Governed `FALLBACK_FAMILIES` | `test_realization_authority.py`, `test_emergency_fallback_registry_static_drift.py` |
| Opening upstream-prepared + owner buckets | `test_opening_fallback_owner_bucket.py`, `test_upstream_response_repairs.py`, `test_final_emission_opening_fallback.py` |
| No compatibility-local on canonical opening | `test_golden_direct_seam_*`, `test_golden_canonical_opening_*` |
| Diegetic vs realization opening stamps | `test_diegetic_fallback_narration.py` |
| FEM runtime lineage + split owners | `test_final_emission_meta.py`, `test_runtime_lineage_telemetry.py` |
| Gate terminal / opening fallback integration | `test_final_emission_gate.py -k "fallback or opening"` |
| Classifier fallback tags | `test_failure_classifier.py` |
| Golden strict-social / sanitizer / terminal | `test_golden_replay.py -k "..."` (12 tests) |

### Protected replay manifest (governance)

From `docs/testing/protected_replay_manifest.md`:

- **PROTECTED scenarios (fallback-related):** `opening_fallback_path`, `wrong_speaker_strict_social_emission`, plus broader session scenarios referencing `gate_terminal_repair` / `scene_opening`
- **41 protected field paths** including `fallback_family`, `opening_fallback_*`, `sanitizer_strict_social_*`, `sealed_fallback_owner_bucket`, `visibility_fallback_*`

---

## I. Recommended implementation blocks (next phase)

| Block | Objective | Files likely touched | Tests to run | Risk | Parallel? |
|---|---|---|---|---|---|
| **AB1 — Dead import + doc sync** | Remove unused gate opening composer import; refresh stale gate-local compose docs | `game/final_emission_gate.py`, `docs/gate_cleanup_inventory.md`, `game/opening_deterministic_fallback.py` (docstring) | `tests/test_final_emission_gate.py -k opening`, opening golden trio | Low | Yes |
| **AB2 — Compatibility-local vocabulary shrink** | Move `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` to test helper or delete; keep meta mapper one release | `game/upstream_response_repairs.py`, `tests/helpers/*`, `game/final_emission_meta.py` | `test_opening_fallback_owner_bucket.py`, classifier/dashboard negatives | Low | Yes (after AB1) |
| **AB3 — Dual family field contract** | Document and test which field golden replay owns; optional single-field projection adapter (read-side only) | `tests/helpers/golden_replay_projection.py`, `docs/testing/protected_replay_manifest.md` | Full `test_golden_replay.py` | Medium | No — blocks AB4 |
| **AB4 — Diegetic stamp narrowing** | Reduce `legacy_diegetic_fallback` stamps to true diegetic paths only; opening success → `upstream_prepared_emission` only | `game/final_emission_gate.py`, `game/upstream_response_repairs.py` | `test_diegetic_fallback_narration.py`, golden opening, upstream repairs | Medium-high | After AB3 |
| **AB5 — Legacy tuple retirement** | Gate uses `SealedFallbackSelection` / `VisibilitySelectedFallback` directly; drop `as_legacy_tuple` at boundary | `game/final_emission_gate.py`, `game/final_emission_sealed_fallback.py`, `game/final_emission_visibility_fallback.py` | Sealed/visibility gate tests | Medium | Yes with AB1 |
| **AB6 — Sealed branch projection collapse** | Read-side: map `gate_terminal_repair` + `final_emitted_source` to distinct replay sub-kinds without merging selection | `game/final_emission_replay_projection.py`, `tests/helpers/golden_replay.py` | `test_golden_replay.py -k frontier`, `test_run_scenario_spine_validation.py` | Medium | After AB3 |

---

## J. Files to pass to ChatGPT for implementation planning

**Core runtime (selection + stamping)**

- `game/final_emission_gate.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_visibility_fallback.py`
- `game/social_exchange_emission.py`
- `game/upstream_response_repairs.py`
- `game/opening_deterministic_fallback.py`
- `game/diegetic_fallback_narration.py`
- `game/gm_retry.py`

**Registries + provenance**

- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `game/contract_registry.py`

**Replay / test contracts**

- `tests/helpers/golden_replay_projection.py`
- `tests/test_golden_replay.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_diegetic_fallback_narration.py`
- `tests/test_final_emission_gate.py` (opening/fallback sections only)
- `docs/testing/protected_replay_manifest.md`

**Prior recon / closure**

- `docs/cycles/cycle_p_fallback_family_collapse_recon_2026-05-28.md`
- `docs/cycles/cycle_p_fallback_family_collapse_closure_2026-05-29.md`
- This file: `cycle_ab_fallback_topology_collapse_recon_2026-05-31.md`

---

## Uncertainties (explicit)

- Whether any **non-`game/`** entry path (tools, manual gauntlets) still invokes gate-local opening compose — not exhaustively searched in this pass.
- Full golden replay suite not executed; contraction safety for all 41 protected paths is **inferred** from targeted passes.
- `docs/gate_cleanup_inventory.md` may describe pre-retirement behavior; treat as **stale** until reconciled with AB1.

---

*Recon completed 2026-05-31. No code or fixture changes.*
