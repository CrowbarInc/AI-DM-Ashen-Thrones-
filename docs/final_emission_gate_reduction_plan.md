# Final emission gate — branch reduction map (pre-refactor)

Branch context: `feature/failure-locality`

**Prepared / sealed branch reduction phase (Blocks AF–AI):** **complete** for inventory, selector extraction, and **contract tests** in `tests/test_final_emission_gate.py` (Block AI: importability, non-mutation expectations for selector helpers, assembly-without-line-selection, upstream opening preference, and Block AG snapshot entrypoints). Runtime gate behavior is intentionally unchanged by that phase; remaining risks are listed below.

**Helper groups (`game/final_emission_gate.py` + upstream merge):**

| Group | Role | Key symbols |
| --- | --- | --- |
| Upstream prepared selection | Merge/inject upstream-prepared answer/action and opening payloads before layers | `merge_upstream_prepared_emission_into_gm_output`, `maybe_attach_upstream_prepared_opening_fallback_payload`, `_upstream_prepared_opening_fallback_payload_if_usable` (used inside `_opening_scene_safe_fallback_tuple`) |
| Compatibility opening selection | Shared deterministic composer when upstream opening snapshot is absent/unusable | `_deterministic_opening_fallback_text_and_meta`, `_opening_scene_safe_fallback_tuple` compatibility branch |
| Sealed replacement selector helpers | Branch routing only (no FEM packaging here) | `_route_visibility_enforcement_after_failed_validation`, `_select_acceptance_quality_n4_sealed_fallback_line`, `_scene_opening_rt_contract_accept_path_promotes_candidate`, `_select_non_strict_replace_path_terminal_sealed_fallback` |
| Sealed replacement metadata helpers | FEM route/source keys **after** text is already chosen | `_prepare_sealed_replacement_route_meta`, `_finalize_n4_sealed_replace_fem_route_meta` |
| Provenance stamping helper | `realization_fallback_family` only from emitted source id + route | `_stamp_sealed_fallback_realization_family` |

**Remaining final gate risks not solved by this phase:**

- Strict-social terminal pool / `build_final_strict_social_response` churn (speaker binding, route-illegal intercept).
- Layer repair precedence stacks (`final_emitted_source` overrides from NA/NAA/ARR/CSS/etc.) vs downstream terminal stamps.
- Compatibility opening byte-stable parity vs upstream snapshots in production-adjacent harnesses.
- Scene-emit integrity / travelish descriptor regressions on global tuples.
- Narrative-mode contract + N4 interaction when planner bundles are partial or legacy harnesses omit `prompt_context.narrative_plan`.

---

**Objective:** Inventory `apply_final_emission_gate` fallback and replacement routes before extracting or thinning gate-local authorship. This document is static observability for Cursor-led branch-by-branch reduction; it is **not** a refactor specification.

**Hard constraints for subsequent work (unchanged here):**

- Do not remove **compatibility opening** fallback (shared composer when upstream prepared opening snapshot is absent/unusable).
- Do not touch **retry fallback**, **prompt construction**, broad gate rewrites, emitted prose, or fallback selection order.

**Canonical ordering reference** (non–strict-social trunk): module docstring near `apply_final_emission_gate` — response-type and upstream merge happen first; visibility and acceptance-quality floors run late; `_finalize_emission_output` performs packaging/strip only.

### Replacement provenance policy (`realization_fallback_family`, Block AE)

Sealed **hard-replace** paths (visibility, first-mention, referential-clarity, N4 floor fail, and the generic terminal-replace trunk) stamp metadata via `_stamp_sealed_fallback_realization_family` in `game/final_emission_gate.py`:

| Situation | `realization_fallback_family` |
| --- | --- |
| `final_emitted_source == minimal_social_emergency_fallback` **and** the route is strict-social (`strict_social_active` / `strict_social_path` as applicable) | `strict_social_deterministic_fallback` |
| Any other sealed tuple selected (global scene, opening id, npc pursuit, anti-reset, visibility-safe pool, non-strict N4 global scene, etc.) | `gate_terminal_repair` |

**Unchanged by this policy:** `player_facing_text` bytes, `final_emitted_source` string ids, `final_route` semantics, tags, and which tuple wins — metadata only.

**Not covered here (no family on acceptance):** layer repair “win” ids (`anti_railroading_repair`, …) where the candidate remains author-selected prose unless a terminal path later stamps; upstream prepared / opening RT repairs continue to use `upstream_prepared_emission` / `legacy_diegetic_fallback` via `_enforce_response_type_contract` as before.

**Assembly helpers (Block AF, metadata only):**

- `_prepare_sealed_replacement_route_meta` — shared FEM keys (`final_route`, `final_emitted_source`, stamp, preview, optional diegetic `fallback_*` from `composition_meta`) after sealed text is written; **visibility** passes `composition_meta=None` so `fallback_family_used` / `fallback_temporal_frame` are not set here (historical shape).
- `_finalize_n4_sealed_replace_fem_route_meta` — N4 hard-replace branch route + source ids + family stamp (no change to fallback line selection).

**Selector/order snapshots (Block AG, tests only):**

- `tests/test_final_emission_gate.py` pins discriminators between visibility vs generic terminal replace, N4 vs generic terminal, opening RT repair vs generic terminal family, strict-social sealed minimal vs non–strict gate-terminal family, accept-path ordering (`visibility` seam before N4 seam), replace-path ordering the same, and valid-candidate bypass — before extracting branch selectors.

**Selector extraction (Block AH, helpers only — behavior unchanged):**

- Completed: sealed-branch **selection predicates / tuple routing** for the AG-snapshotted paths are extracted in `game/final_emission_gate.py` without reordering orchestration, changing prose, FEM ids, or fallback authorship.
- Helpers added:
  - `_route_visibility_enforcement_after_failed_validation` — visibility illegality → continuity-lead exemption vs concrete-interaction bypass vs sealed `_standard_visibility_safe_fallback` hard replace (order preserved).
  - `_select_acceptance_quality_n4_sealed_fallback_line` — N4 floor failure: strict-social minimal line vs non–strict global sealed tuple head (same logic as inline ternary; wires `_finalize_n4_sealed_replace_fem_route_meta` unchanged downstream).
  - `_scene_opening_rt_contract_accept_path_promotes_candidate` — scene-opening accept-path promotion after `_enforce_response_type_contract` (same conjunction as before).
  - `_select_non_strict_replace_path_terminal_sealed_fallback` — non–strict **candidate-rejection** terminal replace trunk (opening tuple → social interlocutor minimal → passive pressure → NPC pursuit neutral → anti-reset continuation → global integrity tuple); opening composition meta returned only on opening branch for `response_type_debug.update`.
- Still inline (not part of this extraction): strict-social trunk emission (`build_final_strict_social_response`) selector/details; layer repair `final_emitted_source` precedence inside accept/replace strict-social branches; first-mention / referential-clarity sealed enforcement orchestration; upstream prepared emission RT repairs; compatibility opening author inside `_opening_scene_safe_fallback_tuple` / `opening_deterministic_fallback` (authorship boundaries untouched).

**Contract guards (Block AI, tests only):**

- `test_block_ai_sealed_selector_helpers_importable_and_callable`, `test_block_ai_route_visibility_and_opening_rt_selectors_do_not_mutate_inputs`, `test_block_ai_n4_sealed_line_selector_preserves_copied_input_dicts`, `test_block_ai_non_strict_terminal_selector_does_not_mutate_gm_output_when_opening_branch`, `test_block_ai_assembly_helpers_stamp_meta_without_selecting_fallback_lines`, `test_block_ai_opening_upstream_prepared_snapshot_remains_preferred_over_compatibility_local`, `test_block_ai_block_ag_selector_order_snapshots_remain_entrypoints`.

---

## 1. Merge / preflight (not prose branches, but feed prepared payloads)

| Area | Owner | Role |
| --- | --- | --- |
| `merge_upstream_prepared_emission_into_gm_output` | `game.upstream_response_repairs` | Injects `upstream_prepared_emission` fields before gate layers. |
| `maybe_attach_upstream_prepared_opening_fallback_payload` | `game.upstream_response_repairs` | Attaches prepared opening snapshot when attach rules pass. |
| `maybe_attach_upstream_prepared_opening_fallback_payload` failure locality | Gate caller chain | When curated facts are empty, snapshot may be skipped; downstream routes must remain deterministic (see opening / N4 interactions in tests). |

**Recommended reduction action:** Keep merge hooks stable; any move is upstream-only with identical payload shapes.

**Risk:** LOW (behavior already covered by upstream provenance tests).

---

## 2. `_enforce_response_type_contract` — prepared / sealed repairs

Invoked for both strict-social and non–strict-social paths. Primary prose-selection branches:

### 2a. Upstream prepared emission (answer / action_outcome)

| Field | Provenance | Author vs select | `final_emitted_source` (via RT repair kind) | `realization_fallback_family` |
| --- | --- | --- | --- | --- |
| `prepared_answer_fallback_text` | Upstream payload | **Select** prepared string | `answer_upstream_prepared_repair` | `upstream_prepared_emission` |
| `prepared_action_fallback_text` | Upstream payload | **Select** prepared string | `action_outcome_upstream_prepared_repair` | `upstream_prepared_emission` |

**Test coverage:** `test_final_gate_upstream_prepared_emission_branch_records_upstream_family` (`tests/test_final_emission_gate.py`); upstream module tests.

**Recommended reduction action:** Keep gate as selector only; reject/regress upstream merge behavior via existing attribution keys.

**Risk:** LOW–MODERATE (contract-shaped text must stay byte-stable).

### 2b. Upstream prepared opening fallback

| Path | Owner | Author vs select | `final_emitted_source` | Family |
| --- | --- | --- | --- | --- |
| Snapshot usable (`upstream_prepared_opening_fallback`) | `upstream_response_repairs` + gate | **Select** `prepared_opening_fallback_text` | `opening_deterministic_fallback` (repair kind; stable id) | `legacy_diegetic_fallback` + opening classification meta |

### 2c. Compatibility opening (shared composer)

| Path | Owner | Author vs select | Same IDs as 2b |
| --- | --- | --- | --- |
| Snapshot missing/unusable | `game.opening_deterministic_fallback` via `_deterministic_opening_fallback_text_and_meta` | **Author** (bounded library); gate composes only when snapshot incomplete | `opening_deterministic_fallback` |

**Test coverage:** Opening tuples, `_enforce_response_type_contract`, FEM snapshots with `opening_fallback_authorship_source` (`upstream_prepared` vs `compatibility_local`).

**Recommended reduction action:** Prefer upstream snapshot everywhere production touches opening; keep compatibility path until telemetry proves parity (per `realization_cursor_handoff.md`).

**Risk:** MODERATE for compatibility path (exact text pinned).

### 2d. Dialogue strict-social terminal / minimal repairs

| Branch | Owner | Select vs author | Repair kind / source ids | Family |
| --- | --- | --- | --- | --- |
| Strict-social terminal pool | `social_exchange_emission` / strict-social builders | **Select** sealed dialogue-class lines | `strict_social_dialogue_repair`, pool-backed details → `final_emitted_source` from `build_final_strict_social_response` details | `strict_social_deterministic_fallback` when stamped |
| Non–strict-social dialogue minimal | `minimal_social_emergency_fallback_line` | **Select** sealed minimal line | `dialogue_minimal_repair` | `strict_social_deterministic_fallback` when stamped |

**Test coverage:** Strict-social FEM snapshots (`test_strict_social_narrative_mode_output_enforcement_terminal_fallback`, emergency source lists).

**Recommended reduction action:** Defer extraction until strict-social terminal pools remain stable under planner/API churn.

**Risk:** HIGH.

---

## 3. Non–strict-social **candidate rejection** replace tree (`reasons` non-empty)

When validation layers accumulate reasons, the gate hard-replaces text **before** `_finalize_emission_output`. Branch selection (opening mode vs social interlocutor vs passive pressure vs anti-reset vs global):

### 3a. Opening-mode replace (`_opening_scene_safe_fallback_tuple`)

Same prepared/compatibility opening semantics as §2b–2c; `final_emitted_source` remains `opening_deterministic_fallback`; FEM carries opening telemetry (`opening_*` keys).

**Risk:** MODERATE.

### 3b. Social active interlocutor minimal (`minimal_social_emergency_fallback_line` on synthetic mini-resolution)

| Item | Value |
| --- | --- |
| Owner | Gate orchestration + `minimal_social_emergency_fallback_line` |
| Author vs select | **Select** sealed minimal social line |
| `final_emitted_source` | `social_interlocutor_minimal_fallback` |
| FEM `realization_fallback_family` | `gate_terminal_repair` (set on this replace-path FEM dict) |

**Test coverage:** Indirect via scene integrity / visibility suites; **no** dedicated `apply_final_emission_gate` snapshot in `test_final_emission_gate.py` (candidate for future narrow test if orchestration changes).

**Risk:** MODERATE.

### 3c. Passive scene pressure candidates (`_passive_scene_pressure_fallback_candidates`)

Diegetic classified templates; first tuple wins in gate replace ordering.

| Author vs select | **Select** template line + composition meta |
| `final_emitted_source` | From candidate tuple (variable by scene/session pressure) |
| Family | `gate_terminal_repair` on FEM for this replace trunk |

**Risk:** MODERATE.

### 3d. NPC pursuit neutral non-progress (`_should_use_neutral_nonprogress_fallback_instead_of_global_stock`)

| Item | Value |
| --- | --- |
| Owner | Gate policy |
| Author vs select | **Select** fixed sealed sentence (single stock line in gate) |
| `final_emitted_source` | `npc_pursuit_neutral_fallback` |

**Risk:** MODERATE.

### 3e. Anti-reset continuation (`local_exchange_continuation_fallback_line`)

| Item | Value |
| --- | --- |
| Owner | Gate + localized continuation helper |
| Author vs select | **Select** bounded continuation text |
| `final_emitted_source` | `anti_reset_local_continuation_fallback` |

**Risk:** MODERATE.

### 3f. Global scene / scene-emit integrity (`_scene_emit_integrity_global_fallback_tuple`)

| Situation | `final_emitted_source` |
| --- | --- |
| Non-travelish or integrity passes | `global_scene_fallback` |
| Travelish + integrity failures | `scene_emit_integrity_safe_fallback` |

**Test coverage:** `tests/test_final_emission_scene_integrity.py`; `test_final_gate_terminal_repair_branch_records_gate_terminal_family`.

**Risk:** MODERATE–HIGH for travel/descriptor correctness.

---

## 4. Strict-social trunk — sealed terminal / minimal paths

Handled **before** the generic trunk; layers mutate strict-social text then compute `final_emitted_source` from `details` + layer repair precedence.

### 4a. Response-type social emergency (`minimal_social_emergency_fallback_line`)

Hard swap when response-type repair fails; stamps:

- `final_emitted_source`: `minimal_social_emergency_fallback`
- `realization_fallback_family`: `strict_social_deterministic_fallback`

### 4b. Dialogue-plan subtractive strip collapse / bare strip edge cases

Emergency branch resets to `minimal_social_emergency_fallback` when strip removes all usable diegetic text.

### 4c. Interaction continuity validation-only strict path (`ic_strict_fb`)

May patch FEM to `minimal_social_emergency_fallback` + strict-social family.

### 4d. Narrative mode output (C4) strict-social failure

Replaces with minimal social emergency line; tags `final_emission_gate:narrative_mode_output`; FEM matches §4a semantics.

**Test coverage:** `test_strict_social_narrative_mode_output_enforcement_terminal_fallback`.

### 4e. Strict-social replaced route (`used_internal_fallback`)

Fem carries `realization_fallback_family` normalized from `details` (defaults strict-social deterministic).

**Risk:** HIGH for speaker-binding regressions.

---

## 5. Layer repairs — anti-railroading / context separation / narration purity / answer-shape / …

These layers **mutate or validate** text before finalize. When a layer performs the winning repair, `apply_final_emission_gate` **overrides** `final_emitted_source` with that layer’s repair mode string (e.g. `anti_railroading_repair`, `context_separation_repair`, `player_facing_narration_purity_repair`, `answer_shape_primacy_repair`, narrative authenticity/authority/tone modes, fast-fallback neutral composition repair modes).

| Family | Usually **none** on FEM (`realization_fallback_family` omitted) unless a downstream terminal path stamps it. |

**Test coverage:** Layer-specific tests in `test_final_emission_gate.py` (anti-railroading, context separation, answer-shape, purity stacks).

**Recommended reduction action:** Split helpers without reordering layers; keep repair-mode strings stable for telemetry.

**Risk:** MODERATE per layer (ordering-sensitive).

---

## 6. Visibility safe fallback (`_apply_visibility_enforcement`)

When visibility validation fails, the gate replaces text via `_standard_visibility_safe_fallback` (same sealed tuple machinery as §3, plus visibility-specific tagging).

| Item | Behavior |
| --- | --- |
| `final_emitted_source` | Resolved from selected visibility-safe tuple (often `global_scene_fallback` for stock/global branch; strict-social minimal uses `minimal_social_emergency_fallback` when that tuple wins) |
| `final_route` | `replaced` |
| `realization_fallback_family` | Stamped per **Replacement provenance policy** (above): `gate_terminal_repair` for generic sealed lines; `strict_social_deterministic_fallback` when source id is `minimal_social_emergency_fallback` on a strict-social route |

**Test coverage:** Pipeline suite (`tests/test_final_emission_visibility.py`); **narrow FEM snapshot:** `test_visibility_safe_fallback_final_emitted_source_snapshot` in `test_final_emission_gate.py`.

**Risk:** MODERATE.

---

## 7. Acceptance quality N4 floor (`_apply_acceptance_quality_n4_floor_seam`)

| Pass | Candidate repaired subtractively; FEM merged trace; **no** terminal swap |
| Fail | Hard replace with sealed fallback line then second validate pass |

**Replace branch:**

| Path | `final_emitted_source` | `realization_fallback_family` |
| --- | --- | --- |
| Strict-social | `minimal_social_emergency_fallback` | `strict_social_deterministic_fallback` |
| Non–strict | `acceptance_quality_global_scene_fallback` | `gate_terminal_repair` |

**Test coverage:** N4 suite in `test_final_emission_gate.py` (`test_acceptance_quality_n4_replace_path_reruns_seam_on_fallback_and_fem_terminal` asserts non-strict family); opening empty-curatedFacts paths combine AQ with terminal replace semantics.

**Risk:** MODERATE (floor toggled by narrative plan presence).

---

## 8. Narrative mode output (non–strict-social) — reasons append

When shipped narrative-mode contract exists and output fails validation, `_narrative_mode_output_legality_assessment` contributes reason codes → generic trunk **hard replace** via §3 (not a distinct `final_emitted_source` string by itself).

**Risk:** MODERATE–HIGH.

---

## 9. Referential clarity / first-mention enforcement

Replace paths (`first_mention_enforcement_replaced`, `referential_clarity_enforcement_replaced`) set `final_emitted_source` from `_standard_visibility_safe_fallback`-shaped tuples and stamp `realization_fallback_family` with the same sealed-replace policy as §6 (strict-social minimal vs `gate_terminal_repair`).

**Risk:** MODERATE.

---

## Summary — reduction priority (aligned with handoff)

1. **Prepared/sealed-only branches first:** upstream prepared emission + upstream prepared opening selection (already mostly selector-shaped).
2. **Compatibility opening:** narrow once upstream snapshot coverage proves parity.
3. **Terminal replace pool alignment:** global scene, passive pressure, anti-reset, NPC pursuit — extract tuple builders only with snapshots frozen.
4. **Family/FEM consistency:** sealed-replace paths stamp `realization_fallback_family` intentionally (Block AE); layer-only repairs remain family-unclassified unless a terminal stamp applies later.
5. **Defer:** strict-social speaker emergencies, retry-adjacent behaviors, API narration hub.

---

## Related docs

- `docs/realization_cursor_handoff.md` — Cursor-required seams and ordering.
- `docs/realization_triage_ledger.md` — Risk classification snapshot.
- `docs/realization_seam_inventory.md` — Static seam table including gate rows.
