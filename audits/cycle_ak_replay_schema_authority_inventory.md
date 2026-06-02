# Cycle AK0 — Replay Schema Authority Inventory

**Date:** 2026-06-02  
**Scope:** Field-level inventory for AK implementation planning. No runtime or test behavior changes.

**Machine-readable companion:** `audits/cycle_ak_schema_duplication_map.json`

---

## 1. Summary

Replay acceptance is locked by **41 protected observation paths** in `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS`, mirrored in the generated section of `docs/testing/protected_replay_manifest.md` (verified current via `refresh_protected_replay_manifest.py --check`).

Schema maintenance burden comes from **hand-maintained parallel lists** across four layers:

| Layer | Authority | Count | Co-movement risk |
|---|---|---:|---|
| Protected observation | `golden_replay_projection.py` | 41 paths | Registry + manual `project_turn_observation()` wiring + `raw_signal_presence` |
| Classifier row | `failure_classification_contract.py` | 15 required + 47 optional | TypedDict + `classify_replay_failure()` dict |
| Dashboard table | `failure_dashboard_report.py` | 17 columns | `_evidence_cell` 29-key tuple (separate from contract) |
| Manifest paths | Generated from projection registry | 41 paths | Automated (good) |

**Overlap snapshot:**

- Protected ∩ classifier optional evidence: **32**
- Protected-only (not classifier optional): **9**
- Classifier optional-only (not protected): **15**
- Dashboard evidence row keys: **29** — all ⊆ classifier optional; **9** are diagnostic-only (not protected paths)
- Dashboard evidence keys **not** in classifier contract: **0**

All validation commands passed at inventory time (59 golden + 120 diagnostic tests; manifest check OK).

---

## 2. Current replay schema authorities

| Authority | File | Symbol(s) | Role |
|---|---|---|---|
| **Protected observation (acceptance)** | `tests/helpers/golden_replay_projection.py` | `PROTECTED_OBSERVATION_FIELDS`, `protected_observation_field_registry()`, `project_turn_observation()` | 41-path registry + payload→observed-turn adapter |
| **Classifier row schema** | `tests/failure_classification_contract.py` | `REQUIRED_CLASSIFICATION_FIELDS`, `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` | Required/optional evidence field lock |
| **Classifier taxonomy** | `tests/failure_classification_contract.py` | `ALLOWED_*`, `MAJOR_OWNER_INVESTIGATION_TARGETS` | Categories, owners, tags, investigation targets |
| **Classifier runtime shape** | `tests/helpers/failure_classifier.py` | `FailureClassification`, `classify_replay_failure()` | Row construction + routing rules |
| **Contract↔classifier sync** | `tests/helpers/failure_classification_sync.py` | `assert_contract_classifier_alignment()`, `expected_failure_classification_row_fields()` | Alignment checks |
| **Dashboard rendering** | `tests/helpers/failure_dashboard_report.py` | `FAILURE_DASHBOARD_TABLE_COLUMNS`, `_evidence_cell()`, `build_failure_dashboard_rows()` | Markdown table + evidence composition |
| **Manifest governance** | `docs/testing/protected_replay_manifest.md` | Generated `protected_field_paths` section | Scenario classification + derived path table |
| **Manifest refresh** | `tools/refresh_protected_replay_manifest.py` | `render_generated_section()`, `--check` / `--write` | Keeps manifest paths aligned with registry |
| **Runtime FEM field lists** | `game/final_emission_meta.py` | `OPENING_FALLBACK_PROJECTION_FIELDS`, owner bucket frozensets | Write/read-side FEM keys (not golden authority) |
| **Runtime lineage projection** | `game/final_emission_replay_projection.py` | `build_fem_runtime_lineage_events()` | Read-side lineage (supporting, not manifest-locked) |

**Replay runner (uses authorities, does not own schema):** `tests/helpers/golden_replay.py` — drift bucketing via `protected_observation_drift_bucket()`; calls classifier on failure.

---

## 3. Protected observation fields

**Source:** `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS` (via `protected_observation_field_registry()`)

**Count:** 41 (39 structural + 2 semantic)

### Structural drift (39)

| Path | Drift bucket |
|---|---|
| `resolution_kind` | structural_drift |
| `route_kind` | structural_drift |
| `selected_speaker_id` | structural_drift |
| `final_emitted_source` | structural_drift |
| `final_emission_mutation_lineage` | structural_drift |
| `response_type_required` | structural_drift |
| `response_type_candidate_ok` | structural_drift |
| `response_type_repair_used` | structural_drift |
| `response_type_repair_kind` | structural_drift |
| `upstream_prepared_emission_used` | structural_drift |
| `upstream_prepared_emission_valid` | structural_drift |
| `upstream_prepared_emission_source` | structural_drift |
| `upstream_prepared_emission_reject_reason` | structural_drift |
| `sanitizer_empty_fallback_used` | structural_drift |
| `sanitizer_empty_fallback_source` | structural_drift |
| `sanitizer_empty_fallback_owner` | structural_drift |
| `sanitizer_lineage_mode` | structural_drift |
| `sanitizer_lineage_changed_count` | structural_drift |
| `sanitizer_lineage_dropped_count` | structural_drift |
| `sanitizer_lineage_empty_fallback_used` | structural_drift |
| `sanitizer_lineage_legacy_rewrite_active` | structural_drift |
| `sanitizer_strict_social_fallback_used` | structural_drift |
| `sanitizer_strict_social_selection_owner` | structural_drift |
| `sanitizer_strict_social_prose_owner` | structural_drift |
| `sanitizer_strict_social_source` | structural_drift |
| `opening_recovered_via_fallback` | structural_drift |
| `opening_fallback_authorship_source` | structural_drift |
| `opening_fallback_owner_bucket` | structural_drift |
| `sealed_fallback_owner_bucket` | structural_drift |
| `visibility_fallback_owner_bucket` | structural_drift |
| `visibility_replacement_applied` | structural_drift |
| `visibility_fallback_pool` | structural_drift |
| `visibility_fallback_kind` | structural_drift |
| `fallback_family` | structural_drift |
| `fallback_temporal_frame` | structural_drift |
| `trace.canonical_entry.target_actor_id` | structural_drift |
| `trace.canonical_entry.target_source` | structural_drift |
| `trace.canonical_entry.reason` | structural_drift |
| `trace.social_contract_trace.route_selected` | structural_drift |

### Semantic drift (2)

| Path | Drift bucket |
|---|---|
| `final_text` | semantic_drift |
| `scaffold_leakage` | semantic_drift |

**Related symbols:** `STRUCTURAL_DRIFT_FIELDS`, `SEMANTIC_DRIFT_FIELDS`, `_DRIFT_BUCKET_BY_PATH`, `protected_observation_drift_bucket()`, `lookup_observation_path()`.

**Manual wiring duplicate:** `project_turn_observation()` (~L433–637) extracts each field individually; `raw_signal_presence` (~L516–542) duplicates presence keys for a subset.

---

## 4. Classifier required fields

**Source:** `tests/failure_classification_contract.py::REQUIRED_CLASSIFICATION_FIELDS` (15)

| Field | Set in `classify_replay_failure()` |
|---|---|
| `scenario_id` | L829 |
| `turn_index` | L830 |
| `category` | L831 (via `classify_failure_category`) |
| `severity` | L832 (via `classify_failure_severity`) |
| `primary_owner` | L833 (via `determine_primary_owner`) |
| `source_family` | L835 |
| `replay_tags` | L836 |
| `field_path` | L837 |
| `expected` | L838 |
| `actual` | L839 |
| `reason` | L840 |
| `unavailable_fields` | L887 |
| `raw_signal_refs` | L888 (via `_raw_signal_refs`) |
| `classification_confidence` | L889 |
| `investigate_first` | L890 (via `build_investigation_target`) |

**TypedDict mirror:** `tests/helpers/failure_classifier.py::FailureClassification` (required keys + `NotRequired` optional evidence keys).

---

## 5. Classifier optional evidence fields

**Source:** `tests/failure_classification_contract.py::OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` (47)

| Field | Copied in `classify_replay_failure()` | In `FailureClassification` TypedDict |
|---|---|---|
| `secondary_owner` | L834 | yes |
| `final_text_hash` | L841 | yes |
| `route_kind` | L842 | yes |
| `selected_speaker_id` | L843 | yes |
| `canonical_target_actor_id` | L844 | yes |
| `final_emitted_source` | L845 | yes |
| `final_emission_mutation_lineage` | L846 | yes |
| `fallback_family` | L847 | yes |
| `fallback_temporal_frame` | L848 | yes |
| `opening_fallback_authorship_source` | L849 | yes |
| `opening_fallback_owner_bucket` | L850 | yes |
| `fallback_selection_owner` | L851 | yes |
| `fallback_content_owner` | L852 | yes |
| `sealed_fallback_owner_bucket` | L853 | yes |
| `visibility_fallback_owner_bucket` | L854 | yes |
| `visibility_replacement_applied` | L855 | yes |
| `visibility_fallback_pool` | L856 | yes |
| `visibility_fallback_kind` | L857 | yes |
| `upstream_prepared_emission_used` | L858 | yes |
| `upstream_prepared_emission_valid` | L859 | yes |
| `upstream_prepared_emission_source` | L860 | yes |
| `upstream_prepared_emission_reject_reason` | L861 | yes |
| `prepared_emission_owner` | L862 | yes |
| `response_type_required` | L863 | yes |
| `response_type_repair_used` | L864 | yes |
| `response_type_repair_kind` | L865 | yes |
| `post_gate_mutation_detected` | L866 | yes |
| `emission_sublayer` | L867 | yes |
| `repair_kind` | L868 | yes |
| `mutation_source` | L869 | yes |
| `missing_source_kind` | L870 | yes |
| `sanitizer_mode` | L871 | yes |
| `sanitizer_event_count` | L872 | yes |
| `sanitizer_changed_count` | L873 | yes |
| `sanitizer_rewrite_used` | L874 | yes |
| `sanitizer_empty_fallback_used` | L875 | yes |
| `sanitizer_empty_fallback_source` | L876 | yes |
| `sanitizer_empty_fallback_owner` | L877 | yes |
| `sanitizer_lineage_mode` | L878 | yes |
| `sanitizer_lineage_changed_count` | L879 | yes |
| `sanitizer_lineage_dropped_count` | L880 | yes |
| `sanitizer_lineage_empty_fallback_used` | L881 | yes |
| `sanitizer_lineage_legacy_rewrite_active` | L882 | yes |
| `sanitizer_strict_social_fallback_used` | L883 | yes |
| `sanitizer_strict_social_selection_owner` | L884 | yes |
| `sanitizer_strict_social_prose_owner` | L885 | yes |
| `sanitizer_strict_social_source` | L886 | yes |

**Flag — classifier optional NOT protected (15):**  
`canonical_target_actor_id`, `emission_sublayer`, `fallback_content_owner`, `fallback_selection_owner`, `final_text_hash`, `missing_source_kind`, `mutation_source`, `post_gate_mutation_detected`, `prepared_emission_owner`, `repair_kind`, `sanitizer_changed_count`, `sanitizer_event_count`, `sanitizer_mode`, `sanitizer_rewrite_used`, `secondary_owner`

**Flag — protected NOT classifier optional (9):**  
`final_text`, `opening_recovered_via_fallback`, `resolution_kind`, `response_type_candidate_ok`, `scaffold_leakage`, `trace.canonical_entry.reason`, `trace.canonical_entry.target_actor_id`, `trace.canonical_entry.target_source`, `trace.social_contract_trace.route_selected`

---

## 6. Dashboard table columns

**Source:** `tests/helpers/failure_dashboard_report.py::FAILURE_DASHBOARD_TABLE_COLUMNS` (17)

| # | Column header | Row key / source | Function |
|---|---|---|---|
| 1 | Scenario | `scenario_id` | `render_failure_dashboard_markdown()` L392 |
| 2 | Turn | `turn_index` | L393 |
| 3 | Category | `category` | L394 |
| 4 | Severity | `severity` | L395 |
| 5 | Primary Owner | `primary_owner` | L396 |
| 6 | Secondary Owner | `secondary_owner` | L397 |
| 7 | Investigate First | `investigate_first` | L398 |
| 8 | Evidence | `_evidence_cell(row)` composite | L399 |
| 9 | Replay Tags | `replay_tags` | L400 |
| 10 | Field | `field_path` | L401 |
| 11 | Expected | `expected` | L402 |
| 12 | Actual | `actual` | L403 |
| 13 | Unavailable | `unavailable_fields` | L404 |
| 14 | Final Source | `final_emitted_source` | L405 |
| 15 | Fallback | `fallback_family` | L406 |
| 16 | Post-Gate Mutation | `post_gate_mutation_detected` | L407 |
| 17 | Mutation Flags | filtered `replay_tags` subset | L383–387, L408 |

**Accessor:** `expected_failure_dashboard_columns()` re-exports the tuple.

**Row builder:** `build_failure_dashboard_rows()` → delegates to `classify_replay_failure()` (`failure_classifier.py`).

---

## 7. Dashboard evidence keys

**Source:** `tests/helpers/failure_dashboard_report.py::_evidence_cell()` (L184–236)

Special-case (not in `evidence_keys` tuple): prepared-emission block when `prepared_emission_owner == "upstream_prepared_emission"` (L186–193).

| Label | Row key (`classify_replay_failure` field) |
|---|---|
| sublayer | `emission_sublayer` |
| repair | `repair_kind` |
| lineage | `final_emission_mutation_lineage` |
| opening_authorship | `opening_fallback_authorship_source` |
| opening_owner | `opening_fallback_owner_bucket` |
| fallback_selection_owner | `fallback_selection_owner` |
| fallback_content_owner | `fallback_content_owner` |
| sealed_owner | `sealed_fallback_owner_bucket` |
| visibility_owner | `visibility_fallback_owner_bucket` |
| visibility_replaced | `visibility_replacement_applied` |
| visibility_pool | `visibility_fallback_pool` |
| visibility_kind | `visibility_fallback_kind` |
| mutation | `mutation_source` |
| missing | `missing_source_kind` |
| sanitizer_mode | `sanitizer_mode` |
| sanitizer_events | `sanitizer_event_count` |
| sanitizer_changed | `sanitizer_changed_count` |
| sanitizer_empty | `sanitizer_empty_fallback_used` |
| sanitizer_empty_source | `sanitizer_empty_fallback_source` |
| sanitizer_empty_owner | `sanitizer_empty_fallback_owner` |
| sanitizer_lineage_mode | `sanitizer_lineage_mode` |
| sanitizer_lineage_changed | `sanitizer_lineage_changed_count` |
| sanitizer_lineage_dropped | `sanitizer_lineage_dropped_count` |
| sanitizer_lineage_empty | `sanitizer_lineage_empty_fallback_used` |
| sanitizer_lineage_legacy | `sanitizer_lineage_legacy_rewrite_active` |
| strict_social_fallback | `sanitizer_strict_social_fallback_used` |
| strict_social_selection_owner | `sanitizer_strict_social_selection_owner` |
| strict_social_prose_owner | `sanitizer_strict_social_prose_owner` |
| strict_social_source | `sanitizer_strict_social_source` |

**Flag — dashboard evidence NOT in classifier contract:** none (all 29 row keys are in `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` or derived from `prepared_emission_owner` logic).

**Flag — dashboard evidence NOT protected paths (9 diagnostic keys):**  
`emission_sublayer`, `fallback_content_owner`, `fallback_selection_owner`, `missing_source_kind`, `mutation_source`, `repair_kind`, `sanitizer_changed_count`, `sanitizer_event_count`, `sanitizer_mode`

---

## 8. Manifest generated fields

**Source:** `docs/testing/protected_replay_manifest.md` (generated section between `<!-- BEGIN GENERATED: protected_field_paths -->` markers)

**Derived from:** `tools/refresh_protected_replay_manifest.py::render_generated_section()` → `golden_replay_projection.protected_observation_field_registry()`

**Count:** 41 paths (matches registry; manifest check passed)

**Parity lock:** `tests/test_golden_replay.py::test_protected_replay_manifest_matches_observation_registry`

Manifest also documents (manual, not generated): PROTECTED/SUPPORTING/ADVISORY scenario tables, dual fallback-family contract, metadata ownership.

---

## 9. Synthetic observed-row fields

### `tests/helpers/failure_classification_sync.py::observed_failure_row()` (L46–83)

Top-level keys: `scenario_id`, `turn_index`, `final_text`, `final_text_hash`, `route_kind`, `selected_speaker_id`, `final_emitted_source`, `fallback_family`, `fallback_temporal_frame`, `opening_fallback_owner_bucket`, `sealed_fallback_owner_bucket`, `visibility_fallback_owner_bucket`, `visibility_replacement_applied`, `visibility_fallback_pool`, `visibility_fallback_kind`, `response_type_required`, `response_type_repair_used`, `response_type_repair_kind`, `post_gate_mutation_detected`, `strict_social_active`, `speaker_contract_enforcement_reason`, `fallback_behavior_repaired`, `fallback_behavior_repair_kind`, `sanitizer_mode`, `sanitizer_event_count`, `sanitizer_changed_count`, `sanitizer_rewrite_used`, `unavailable`, `trace`

Nested `trace`: `canonical_entry.target_actor_id`, `social_contract_trace.route_selected`

**Wrappers:** `observed_opening_fallback_row`, `observed_fail_closed_opening_fallback_row`, `observed_legacy_opening_fallback_row`, `observed_global_replacement_row`, `observed_social_fallback_row`, `observed_sealed_replacement_row`, `observed_visibility_replacement_row`, `observed_sanitizer_row`, `observed_sanitizer_empty_fallback_row`

### `tests/helpers/failure_dashboard_fixtures.py::_observed()` (L15–52)

Near-duplicate of `observed_failure_row` with additions: `raw_signal_presence`, `normalized_signal_presence`; omits `fallback_behavior_repair_kind`, `speaker_contract_enforcement_reason`, `fallback_behavior_repaired`.

**Used by:** `CONTROLLED_FAILURE_CASES` → `classified_rows()` for `tests/test_failure_dashboard_controlled_failures.py`

### `project_turn_observation()` observed dict (non-protected extras)

Supporting keys not in protected registry: `player_text`, `selected_speaker_source`, `response_delta_*`, `strict_social_active`, `stage_diff`, `sanitizer_leak_terms`, `snapshot_summary`, `raw_signal_presence`, `normalized_signal_presence`, `missing_source_by_field`, `fem_raw_keys`, `fem_normalized_keys`, `emission_debug_lane_keys`, `runtime_lineage_events`, `interaction_continuity_validation`, optional `source_path`/`branch_id`/`turn_id`, `unavailable` list.

---

## 10. Field overlap matrix

### 10a. Protected observation vs classifier optional evidence

| Set | Count |
|---|---:|
| Overlap | 32 |
| Protected only | 9 |
| Classifier optional only | 15 |

**Overlap (32):** `fallback_family`, `fallback_temporal_frame`, `final_emission_mutation_lineage`, `final_emitted_source`, `opening_fallback_authorship_source`, `opening_fallback_owner_bucket`, `response_type_repair_kind`, `response_type_repair_used`, `response_type_required`, `route_kind`, all `sanitizer_*` protected fields, `sealed_fallback_owner_bucket`, `selected_speaker_id`, all `upstream_prepared_emission_*`, all `visibility_*`

### 10b. Classifier optional evidence vs dashboard evidence

| Set | Count |
|---|---:|
| Overlap | 29 |
| Classifier optional only (not in `_evidence_cell`) | 18 |
| Dashboard evidence only (not in contract) | 0 |

**Classifier optional not surfaced in Evidence column:** `canonical_target_actor_id`, `fallback_family`, `fallback_temporal_frame`, `final_emitted_source`, `final_text_hash`, `post_gate_mutation_detected`, `prepared_emission_owner`, `response_type_repair_kind`, `response_type_repair_used`, `response_type_required`, `route_kind`, `sanitizer_rewrite_used`, `secondary_owner`, `selected_speaker_id`, `upstream_prepared_emission_*` (4 fields) — these appear in dedicated table columns instead.

### 10c. Protected observation vs dashboard evidence

| Set | Count |
|---|---:|
| Overlap | 20 |
| Protected only | 21 |
| Dashboard evidence only (diagnostic, not protected) | 9 |

Protected fields with dedicated dashboard columns (not in Evidence cell): `final_emitted_source`, `fallback_family`, `route_kind`, `selected_speaker_id`, `post_gate_mutation_detected`, `upstream_prepared_emission_*`.

### 10d. Runtime FEM fields vs replay projection fields

**FEM keys read in `project_turn_observation()`** (from `read_final_emission_meta_from_turn_payload` + `_first_present(fem, ...)`):

`fallback_behavior_repair_kind`, `fallback_behavior_repair_mode`, `fallback_behavior_repaired`, `fallback_family_used`, `fallback_temporal_frame`, `final_emission_mutation_lineage`, `final_emitted_source`, `narrative_authenticity_repair_mode`, `opening_fallback_authorship_source`, `opening_recovered_via_fallback`, `post_gate_mutation_detected`, `realization_fallback_family`, `response_delta_*`, `response_type_*`, `sealed_fallback_owner_bucket`, `speaker_contract_enforcement_reason`, `strict_social_active`, `upstream_prepared_emission_*`, `visibility_*`

**`game/final_emission_meta.py::OPENING_FALLBACK_PROJECTION_FIELDS` (13 keys):**

`opening_fallback_context_source`, `opening_fallback_basis_count`, `opening_fallback_context_missing`, `opening_fallback_failed_closed`, `opening_curated_facts_present`, `opening_curated_facts_count`, `opening_curated_facts_source`, `opening_selector_source_used`, `opening_selector_selected_facts`, `opening_curated_facts`, `opening_final_fallback_basis`, `opening_final_basis_matches_selector`, `opening_fallback_authorship_source`

**Opening FEM keys NOT in protected observation (11):** all except `opening_fallback_authorship_source` — curated/selector debug telemetry not acceptance-locked.

**Dual fallback-family (AB contract):** runtime FEM carries `fallback_family_used` + `realization_fallback_family`; golden observes projected `fallback_family` only (`project_replay_fallback_family_from_fem`).

**Duplicated runtime literal:** `FINAL_EMISSION_MUTATION_LINEAGE_KEY` in both `game/final_emission_meta.py` and `game/final_emission_replay_projection.py`.

---

## 11. Duplication hotspots

| ID | Hand-maintained list | Files / symbols | AK note |
|---|---|---|---|
| D1 | Protected path registry vs extraction | `golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS` vs `project_turn_observation()` vs `raw_signal_presence` | **Primary AK1 target** |
| D2 | Classifier row schema triplication | `failure_classification_contract.py` frozensets ↔ `FailureClassification` TypedDict ↔ `classify_replay_failure()` L828–896 | AK2–AK4 |
| D3 | Dashboard evidence keys | `failure_dashboard_report.py::_evidence_cell::evidence_keys` vs contract optional fields | AK3 |
| D4 | Synthetic observed-row bases | `failure_classification_sync.observed_failure_row` vs `failure_dashboard_fixtures._observed` | Lower priority; intentional probes |
| D5 | Manifest path table | Registry ↔ generated markdown (automated) | Keep refresh workflow |
| D6 | CATEGORY_RULES field needles | `failure_classifier.py::CATEGORY_RULES` vs protected paths | Update on protected rename |
| D7 | Owner bucket constants | `final_emission_meta.py` → re-imported in contract | Good pattern |
| D8 | `FINAL_EMISSION_MUTATION_LINEAGE_KEY` | `final_emission_meta.py` + `final_emission_replay_projection.py` | Optional AK6 runtime dedup |

---

## 12. Recommended AK implementation sequence

| Block | Title | Files | Safety gates |
|---|---|---|---|
| **AK0** | Schema authority inventory (this doc) | `audits/cycle_ak_*` | All tests green |
| **AK1** | Registry-driven extractors for flat FEM/sanitizer fields in `project_turn_observation()` | `golden_replay_projection.py` | Projection adapter tests in `test_golden_replay.py`; manifest parity |
| **AK2** | Classifier evidence manifest: `PROTECTED_EVIDENCE_OVERLAP` + `CLASSIFIER_EVIDENCE_EXTENSIONS` (15 keys) | `golden_replay_projection.py` or new schema module, `failure_classifier.py` | `test_failure_classifier.py`, contract tests |
| **AK3** | Derive `_evidence_cell` keys from shared evidence manifest | `failure_dashboard_report.py` | `test_failure_dashboard_controlled_failures.py` |
| **AK4** | TypedDict ⊆ contract assertion helper | `failure_classification_sync.py` | `test_failure_classification_contract.py` |
| **AK5** | Pre-refactor sync tests: every protected path → observed dict key | `failure_classification_sync.py`, `test_golden_replay.py` | Add before AK1 lands |
| **AK6** (optional) | Import `FINAL_EMISSION_MUTATION_LINEAGE_KEY` from meta in replay_projection | `final_emission_replay_projection.py` | `test_final_emission_meta.py` |

**Do not in AK:** collapse dual fallback-family fields; move protected authority to manifest markdown; auto-derive all classifier evidence from protected paths without the 15-key extension set.

---

## 13. Files to pass back to ChatGPT

```
tests/helpers/golden_replay_projection.py
tests/helpers/golden_replay.py
tests/helpers/failure_classifier.py
tests/failure_classification_contract.py
tests/helpers/failure_classification_sync.py
tests/helpers/failure_dashboard_report.py
tests/helpers/failure_dashboard_fixtures.py
tests/test_golden_replay.py
tests/test_failure_classifier.py
tests/test_failure_classification_contract.py
tests/test_failure_dashboard_controlled_failures.py
tools/refresh_protected_replay_manifest.py
docs/testing/protected_replay_manifest.md
game/final_emission_meta.py
game/final_emission_replay_projection.py
audits/cycle_ak_replay_schema_authority_inventory.md
audits/cycle_ak_schema_duplication_map.json
```

---

## 14. Test commands

```bash
# Protected replay (59 tests at inventory time)
python -m pytest tests/test_golden_replay.py -q

# Classifier + contract + dashboard probes (120 tests)
python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py -q

# Manifest registry parity (CI)
python tools/refresh_protected_replay_manifest.py --check

# Full protected replay CI gate
python -m pytest -m golden_replay -q
```

**Inventory validation results (2026-06-02):** all three commands passed; no test failures.
