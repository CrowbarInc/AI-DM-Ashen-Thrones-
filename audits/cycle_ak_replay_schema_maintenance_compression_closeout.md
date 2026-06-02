# Cycle AK Closeout — Replay Schema Maintenance Compression

**Date:** 2026-06-02  
**Status:** Complete (AK0–AK5). No runtime or replay acceptance behavior changed.  
**Companion artifacts:** `audits/cycle_ak_replay_schema_authority_inventory.md`, `audits/cycle_ak_schema_duplication_map.json`

---

## 1. Executive summary

Cycle AK reduced **hand-maintained parallel schema lists** across golden replay projection, failure classification rows, and failure dashboard evidence rendering. Protection is unchanged: **41 protected observation paths**, golden replay drift buckets, classifier taxonomy, and dashboard markdown output all remain contract-locked with expanded sync tests.

**Before AK (AK0 inventory):** four layers maintained overlapping field names independently (protected registry + manual extraction, classifier TypedDict + 47 manual `observed_turn.get(...)` copies, dashboard `_evidence_cell` tuple, generated manifest).

**After AK:** each layer has a named authority, cross-layer subset assertions, and registry-driven or manifest-driven copying where safe. Drift is caught at import time or via `assert_contract_classifier_alignment()`.

---

## 2. Block-by-block summary (AK0–AK5)

| Block | Title | Primary deliverable | Protection preserved |
|---|---|---|---|
| **AK0** | Schema authority inventory | `audits/cycle_ak_replay_schema_authority_inventory.md`, `audits/cycle_ak_schema_duplication_map.json` | Inventory only; no code changes |
| **AK1** | Registry-driven projection extractors | `_FEM_FLAT_OBSERVED_EXTRACTORS`, `_SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS`, `_SANITIZER_LINEAGE_OBSERVED_EXTRACTORS` in `tests/helpers/golden_replay_projection.py` | Same observed-turn values; 28 flat FEM/sanitizer fields centralized |
| **AK2** | Classifier evidence manifest | `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS` (32), `CLASSIFIER_EVIDENCE_EXTENSION_FIELDS` (15), `CLASSIFIER_EVIDENCE_FIELDS` in `tests/failure_classification_contract.py`; `_copy_manifest_observed_evidence()` in `failure_classifier.py` | Same `classify_replay_failure()` row values; computed fields unchanged |
| **AK3** | Dashboard evidence manifest | `FAILURE_DASHBOARD_EVIDENCE_MANIFEST`, `FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS` in `tests/helpers/failure_dashboard_report.py` | Same evidence labels and `_evidence_cell` output (21 controlled probes locked) |
| **AK4** | Row contract sync | `failure_classification_row_contract_fields()`, `failure_classification_typeddict_field_sets()`, `ALLOWED_CLASSIFICATION_ROW_FIELDS`; `validate_failure_classification_row()` uses shared allowlist | Same validation messages; TypedDict ↔ contract exact match |
| **AK5** | Protected-path projection locks | `protected_path_representation_errors()`, `test_ak5_every_protected_path_is_projected_or_marked_unavailable` in `tests/test_golden_replay.py` | Every registry path projected or listed `unavailable` |

---

## 3. Final schema authorities

| Concern | Authority file | Symbol(s) | Role |
|---|---|---|---|
| **Protected observation (acceptance)** | `tests/helpers/golden_replay_projection.py` | `PROTECTED_OBSERVATION_FIELDS`, `protected_observation_field_registry()`, `project_turn_observation()` | 41 paths (39 structural + 2 semantic); drift bucketing |
| **Classifier evidence manifest** | `tests/failure_classification_contract.py` | `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS`, `CLASSIFIER_EVIDENCE_EXTENSION_FIELDS`, `CLASSIFIER_EVIDENCE_FIELDS` (= `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS`) | 32 protected overlap + 15 classifier-only extensions |
| **Classifier row schema** | `tests/failure_classification_contract.py` | `REQUIRED_CLASSIFICATION_FIELDS` (15), `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` (47), `ALLOWED_CLASSIFICATION_ROW_FIELDS` | Full row allowlist for validation |
| **Classifier runtime** | `tests/helpers/failure_classifier.py` | `FailureClassification`, `classify_replay_failure()`, `validate_failure_classification_row()` | Row construction + routing (unchanged semantics) |
| **Dashboard evidence manifest** | `tests/helpers/failure_dashboard_report.py` | `FAILURE_DASHBOARD_EVIDENCE_MANIFEST`, `FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS`, `FAILURE_DASHBOARD_EVIDENCE_LABELS` | 29 curated evidence keys ⊆ classifier evidence |
| **Row contract helper** | `tests/helpers/failure_classification_sync.py` | `failure_classification_row_contract_fields()`, `failure_classification_typeddict_field_sets()`, `assert_failure_classification_row_contract_locked()` | Single accessor for required / optional / allowed |
| **Contract ↔ classifier ↔ dashboard sync** | `tests/helpers/failure_classification_sync.py` | `assert_contract_classifier_alignment()`, `classifier_evidence_manifest_misalignments()`, `dashboard_evidence_manifest_misalignments()` | Central drift detection |
| **Protected replay manifest (generated)** | `docs/testing/protected_replay_manifest.md` | Generated `protected_field_paths` section | Governance doc derived from registry |
| **Manifest refresh tool** | `tools/refresh_protected_replay_manifest.py` | `render_generated_section()`, `--check` / `--write` | Registry → markdown parity |

**Replay runner (consumer, not owner):** `tests/helpers/golden_replay.py` — uses projection + classifier on failure.

---

## 4. Duplication reduced

| Hotspot (AK0 ID) | What changed | Maintenance win |
|---|---|---|
| **D1** Protected registry vs flat extraction | AK1 extractor registries drive FEM/sanitizer flat field projection; AK5 asserts every path is represented | Adding a flat protected field → add extractor entry + registry row; AK5 catches omissions |
| **D2** Classifier row triplication | AK2 manifest + `_copy_manifest_observed_evidence()`; AK4 `ALLOWED_CLASSIFICATION_ROW_FIELDS` + TypedDict sync | Optional evidence copied from one table; unknown-field check uses one allowlist |
| **D3** Dashboard evidence keys | AK3 `FAILURE_DASHBOARD_EVIDENCE_MANIFEST`; import-time ⊆ `CLASSIFIER_EVIDENCE_FIELDS` | No parallel 29-key tuple; labels locked in sync |
| **D5** Manifest path table | Unchanged automation via `refresh_protected_replay_manifest.py --check` | Still generated from registry (good) |

**Counts unchanged (protection proof):**

- Protected observation paths: **41**
- Classifier required fields: **15**
- Classifier optional evidence: **47**
- Protected ∩ classifier optional overlap: **32**
- Classifier-only extensions: **15**
- Dashboard evidence row keys: **29** (all ⊆ classifier evidence)

---

## 5. Intentionally explicit (not collapsed)

These remain hand-authored because behavior or read-side semantics must stay visible and reviewable:

| Area | Location | Why explicit |
|---|---|---|
| **Dual fallback-family projection** | `project_replay_fallback_family_from_fem()` in `golden_replay_projection.py` | Runtime FEM carries `fallback_family_used` and `realization_fallback_family`; golden observes single `fallback_family` via read-side preference (AB contract). Not collapsed at write time. |
| **Trace dotted paths** | `trace.canonical_entry.*`, `trace.social_contract_trace.route_selected` in `PROTECTED_OBSERVATION_FIELDS` | Nested observation paths; `lookup_observation_path()` + AK5 unavailable-parent rules |
| **Semantic drift** | `final_text`, `scaffold_leakage` | Semantic buckets; hash/scaffold logic separate from structural extractors |
| **Opening owner bucket logic** | `_opening_fallback_owner_bucket()` in `failure_classifier.py` | Maps/authorship composition; not a flat `observed_turn.get` |
| **Unavailable / raw_signal_presence** | `project_turn_observation()`, `_missing_source_kind()` | Projection gaps vs normalization; classifier missing-source routing |
| **Classifier computed evidence** (11 fields) | `_CLASSIFIER_COMPUTED_EVIDENCE_FIELDS` in `failure_classifier.py` | `canonical_target_actor_id`, `emission_sublayer`, `fallback_*_owner`, `prepared_emission_owner`, etc. |
| **Prepared-emission evidence block** | `_prepared_emission_evidence_parts()` in `failure_dashboard_report.py` | Special-cased dashboard prefix before manifest iteration |
| **CATEGORY_RULES / owner routing** | `failure_classifier.py` | Taxonomy and `investigate_first` policy (out of AK scope) |
| **Synthetic observed-row bases** | `failure_classification_sync.observed_failure_row` vs `failure_dashboard_fixtures._observed` | Intentional probe locality (optional dedup only) |

---

## 6. Tests run and results (closeout verification)

Commands (2026-06-02):

```bash
python -m pytest tests/test_golden_replay.py -q
python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py -q
python tools/refresh_protected_replay_manifest.py --check
```

| Suite | Result |
|---|---|
| `tests/test_golden_replay.py` | **65 passed** |
| `tests/test_failure_classifier.py` + `tests/test_failure_classification_contract.py` + `tests/test_failure_dashboard_controlled_failures.py` | **148 passed** |
| `tools/refresh_protected_replay_manifest.py --check` | **OK** (manifest matches registry) |

**AK-specific locks added during cycle:**

- `test_ak5_every_protected_path_is_projected_or_marked_unavailable`
- `test_classifier_evidence_manifest_matches_optional_contract_fields`
- `test_dashboard_evidence_row_keys_are_classifier_contract_backed`
- `test_controlled_probe_evidence_cells_unchanged` (21 probes)
- `test_failure_classification_typeddict_matches_row_contract`
- `test_unknown_classification_field_validation_message_unchanged`

---

## 7. Remaining optional follow-up

| Item | Priority | Notes |
|---|---|---|
| **Synthetic observed-row deduplication** | Low | Merge `observed_failure_row` and `failure_dashboard_fixtures._observed` only if probe locality tradeoff is acceptable |
| **`FINAL_EMISSION_MUTATION_LINEAGE_KEY` dedup** | Optional (AK6) | Single import in `final_emission_replay_projection.py` from `final_emission_meta.py` |
| **CATEGORY_RULES vs protected path renames** | Ongoing | Update needles when protected paths change (D6 in AK0) |

**Not recommended without new replay proof:** collapsing dual fallback-family FEM fields; auto-deriving all 47 classifier optional fields from protected paths without the 15-key extension set.

---

## 8. Commit readiness

| Criterion | Status |
|---|---|
| All closeout verification commands green | Yes |
| No runtime (`game/`) behavior changes in AK | Yes (test/helpers/tools/audits only) |
| Protected path count and drift buckets unchanged | Yes (41 paths) |
| Classifier/dashboard output unchanged (locked tests) | Yes |
| Manifest generator in sync | Yes |

**AK is ready to commit** as a test-side schema maintenance compression cycle, provided this closeout doc and the AK code changes are included in the same commit series. Reviewers should treat the four authorities above as the co-movement checklist for any future schema edit.
