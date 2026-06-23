# BS4 — Producer Attribution Stamp Audit

Audit date: 2026-06-20

Scope: producer metadata stamps only. No replacement selection, content, fallback routing, recurrence generation, or runtime behavior changes.

Ground truth: BS5 reporting (`artifacts/bs5_projection_convergence_report.md`) + post-BS4 corpus (`artifacts/bs4_producer_stamp_report.md`).

Validation:

```powershell
pytest tests/test_replacement_attribution_inventory.py tests/test_final_emission_meta.py tests/test_failure_classifier.py tests/test_runtime_lineage_telemetry.py -q
```

---

## 1. Pre-BS4 Producer Gaps (BS5 Ground Truth)

| Replacement path | Missing owner_bucket (BS5) | Missing repair_kind (BS5) | Root cause |
|---|---:|---:|---|
| visibility replacement | 3 | 5 | Owner stamped on hard replace; repair kind absent |
| first mention replacement | 5 | 5 | No visibility/sealed owner inherit; no repair kind |
| referential replacement | 5 | 5 | Same as first-mention; local sub unstamped |
| sealed replacement | 3 | 5 | Sealed owner present; repair kind absent |
| response type replacement | 7 | 4 | Repair kind present; owner bucket projected only |
| sanitizer replacement | 7 | 7 | Trace owners only; no taxonomy bucket or repair kind |
| repair mutation | 4 | 4 | Layer flags only; no repair kind mapping |
| opening fallback | 2 | 3 | Owner projected from meta; repair kind on response-type branch |
| strict social replacement | 7 | 6 | Partial sealed owner; repair kind on response-type branch only |

BS5 recovered projection-accessible fields (recurrence_key, mutation_classification, partial owner/repair via lineage). Remaining gaps were producer-side.

---

## 2. BS4 Producer Stamps Applied

### Repair kind taxonomy (contract-locked)

Added to `tests/failure_classification_contract.py` → `ALLOWED_PRODUCER_REPAIR_KINDS`:

| Token | Producer site |
|---|---|
| `visibility_enforcement` | `apply_visibility_enforcement` hard replace |
| `first_mention_enforcement` | `apply_first_mention_enforcement` hard replace |
| `referential_clarity_enforcement` | `apply_referential_clarity_enforcement` hard replace |
| `referential_clarity_local_substitution` | referential local pronoun sub branch |
| `sanitizer_empty_output` | `_mark_sanitizer_empty_fallback(used=True)`, strict-social empty |
| `sanitizer_strip_only` | strip-only path when output mutates |
| `strict_social_repair` | strict-social replace stack + emergency patch |
| `fallback_behavior_repair` | `repair_fallback_behavior` when text changes |

Stamp field: `producer_repair_kind` on FEM (sanitizer: trace → FEM via finalize merge).

### Owner bucket stamps

| Path | Field stamped | Helper |
|---|---|---|
| visibility hard replace | `visibility_fallback_owner_bucket` | existing + `stamp_visibility_fallback_owner_bucket_from_fields` |
| first mention hard replace | `visibility_fallback_owner_bucket` | `stamp_visibility_fallback_owner_bucket_from_fields` |
| referential hard replace | `visibility_fallback_owner_bucket` | same |
| referential local sub | `visibility_fallback_owner_bucket` | inherit from existing FEM fields |
| sealed / strict social | `sealed_fallback_owner_bucket` | `stamp_sealed_fallback_realization_family` |
| opening fallback | `opening_fallback_owner_bucket` | `stamp_opening_fallback_owner_bucket` |
| sanitizer empty / strip | `sealed_fallback_owner_bucket` | sanitizer trace → FEM merge |

---

## 3. Canonical Producer Metadata Matrix

| Producer | Previously stamped | Newly stamped (BS4) | Remaining gaps |
|---|---|---|---|
| **visibility** | `visibility_replacement_applied`, pool/kind, `visibility_fallback_owner_bucket` | `producer_repair_kind=visibility_enforcement` | `source_family`, `recurrence_key`, `mutation_classification` (projection) |
| **first mention** | `first_mention_replacement_applied`, composition layers | `producer_repair_kind`, `visibility_fallback_owner_bucket` | projection fields above |
| **referential** | hard: replacement flag; local: substitution tokens | `producer_repair_kind`, `visibility_fallback_owner_bucket` | projection fields above |
| **sealed** | `sealed_fallback_owner_bucket`, route/source | _(inherits path-specific repair kind when chained)_ | standalone sealed terminal repair kind |
| **opening** | authorship, `response_type_repair_kind` | `opening_fallback_owner_bucket` (direct) | non-opening response-type owner bucket |
| **sanitizer** | trace empty/strict-social flags | `producer_repair_kind`, `sealed_fallback_owner_bucket` | projection fields above |
| **response type** | `response_type_repair_kind`, upstream flags | opening owner bucket direct stamp | universal owner bucket on non-opening repairs |
| **strict social** | route/source, realization family | `producer_repair_kind`, `sealed_fallback_owner_bucket` | projection fields above |
| **repair mutation** | `fallback_behavior_repaired`, mode string | `producer_repair_kind`, `fallback_behavior_repair_kind` | owner bucket for non-fallback-behavior layers |

---

## 4. Read-Side Convergence (unchanged routing)

- `game/final_emission_replay_projection._fem_preserved_repair_kind` now prefers `producer_repair_kind`
- `tests/helpers/replacement_attribution_inventory._repair_kind_from_fem` reads producer field first
- `tests/helpers/failure_classifier._repair_kind` reads `producer_repair_kind`
- `game/final_emission_finalize._refresh_output_mutation_lineage` merges sanitizer trace stamps into FEM

Recurrence keys unchanged (BS5 algorithm preserved).

---

## 5. Completeness Impact

See `artifacts/bs4_producer_stamp_report.md`.

| Metric | BS1 | BS5 | BS4 | BS4 vs BS1 | BS4 vs BS5 |
|---|---:|---:|---:|---:|---:|
| Resolved completeness | 5.77% | 10.2% | **32.65%** | +26.88 pp | +22.45 pp |
| Resolved complete records | 3/52 | 5/49 | **16/49** | +13 | +11 |
| Strict completeness | 0% | 0% | 0% | — | — |

### Field-level slots recovered (BS4 vs BS5)

| Field | BS5 missing | BS4 missing | Recovered |
|---|---:|---:|---:|
| `repair_kind` | 37 | 20 | **17** |
| `owner_bucket` | 38 | 30 | **8** |
| `recurrence_key` | 0 | 0 | 0 |
| `mutation_classification` | 8 | 8 | 0 |
| `source_family` | 8 | 8 | 0 |

Strict completeness remains 0% until `source_family`, `recurrence_key`, and `mutation_classification` gain direct producer stamps (future block).
