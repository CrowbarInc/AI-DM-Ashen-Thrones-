# BR1 — Attribution Completeness Repository Metric

Metric date: 2026-06-20

Scope: metrics and reporting only. No runtime attribution behavior, producer stamps, projection, classification, or recurrence generation changes.

Implementation: `tests/helpers/attribution_completeness_metric.py`

Generator CLI: `tools/attribution_completeness_report.py`

Artifact: `artifacts/attribution_completeness_report.md`

Validation:

```powershell
pytest tests/test_attribution_completeness_metric.py tests/test_attribution_contract.py tests/test_replacement_attribution_inventory.py -q
python tools/attribution_completeness_report.py
```

---

## 1. Metric Purpose

BR1 operationalizes the BS attribution completeness cycle into a **repeatable repository metric** that future cycles can run without manual spreadsheet work.

The metric answers:

- How complete is semantic replacement attribution across the deterministic baseline corpus?
- Which replacement paths and required fields lag coverage?
- How does the current corpus compare to the frozen BS1 baseline?
- Are populated attribution values contract-compliant and taxonomy-consistent (BS3)?

Primary operational headline: **resolved completeness %**.

Secondary accountability headline: **strict completeness %** (direct producer stamps only).

---

## 2. Numerator and Denominator

### Overall completeness

| Metric | Numerator | Denominator |
|---|---|---|
| **Resolved completeness** | Records where all five required fields are present and taxonomy-valid (any `attribution_origin`) | Total attribution records in the current baseline corpus |
| **Strict completeness** | Records where all five required fields are present, taxonomy-valid, and `attribution_origin[field] == direct` for every field | Total attribution records in the current baseline corpus |

Required fields: `owner_bucket`, `source_family`, `repair_kind`, `recurrence_key`, `mutation_classification`.

Record construction reuses BS1 inventory builders (`build_baseline_attribution_corpus`).

### Field coverage

| Metric | Numerator | Denominator |
|---|---|---|
| **Field coverage %** | Records where the field is not listed in `missing_fields` | Total records in the current corpus |
| **Strict field coverage %** | Records where the field is present and `attribution_origin[field] == direct` | Total records in the current corpus |

### Path coverage

| Metric | Numerator | Denominator |
|---|---|---|
| **Path resolved completeness %** | Resolved-complete records for the replacement path | Total records for that path in the current corpus |
| **Path strict completeness %** | Strict-complete records for the replacement path | Total records for that path in the current corpus |

Nine canonical paths (same registry as BS3):

- visibility replacement
- first mention replacement
- referential replacement
- sealed replacement
- response type replacement
- sanitizer replacement
- repair mutation
- opening fallback
- strict social replacement

### Contract integration (BS3)

| Score | Numerator | Denominator |
|---|---|---|
| **Contract compliance %** | Populated required-field slots that pass canonical validators | All populated required-field slots in the corpus |
| **Taxonomy consistency %** | Structural union checks that pass (owner-bucket partition, repair-kind subsets, nine paths, emission sublayers) | Number of structural checks (5) |

These scores are computed by `calculate_attribution_maturity_scores()` — the same function used by BS3.

---

## 3. Reporting Format

The artifact is markdown with baseline / current / delta columns so trend movement can be recorded without maintaining a historical database today.

### Sections

1. **Overall Completeness** — strict and resolved completeness (percent and record counts)
2. **Contract Integration (BS3)** — contract compliance % and taxonomy consistency %
3. **Field Coverage** — per-field baseline/current/delta coverage, present/missing counts, strict coverage
4. **Path Coverage** — per-path resolved completeness trend and missing-field counts
5. **Risk Summary** — lowest coverage paths, highest coverage paths, most commonly missing fields

### Trend columns

| Column | Source |
|---|---|
| **Baseline (BS1)** | Frozen BS1 snapshot constants (`BS1_BASELINE_COMPLETENESS`, `BS1_BASELINE_MISSING_FIELD_TOTALS`, `BS1_MATURITY_SNAPSHOT`, `BR1_BASELINE_PATH_RESOLVED`) |
| **Current** | Live computation over `build_baseline_attribution_corpus()` |
| **Delta** | `current − baseline` (percentage points for rates, record counts for numerators) |

Baseline corpus size may differ from current corpus size when fixture layers change (for example BS4 producer-stamp fixtures). The report surfaces both totals explicitly.

Structured payload (`build_attribution_completeness_report()`) includes `schema_version: 1` for future JSON export or dashboard ingestion.

---

## 4. Interpretation Guidance

### Resolved vs strict

- **Resolved completeness** measures whether attribution is *operationally usable* for inventory, audits, and failure analysis. Projection and classifier backfill count.
- **Strict completeness** measures whether attribution is *write-time stamped* at producers. Use this when evaluating producer-stamp work (BS4).

Expect resolved completeness to lead strict completeness until universal direct stamps exist for `source_family`, `recurrence_key`, and `mutation_classification`.

### Contract integration

- **Contract compliance %** should approach 100% when populated values conform to locked taxonomies. Drops indicate invalid tokens entering the corpus.
- **Taxonomy consistency %** validates structural registry alignment. It should remain at 100% unless contract modules diverge.

### Field and path coverage

- High missing counts on `repair_kind` and `owner_bucket` usually indicate producer-stamp gaps.
- High missing counts on `source_family` and `mutation_classification` often reflect projection/classifier dependency.
- Path rows with 0% resolved completeness are remediation priorities; compare against BS4/BS5 cycle reports for expected movement.

### Risk summary

- **Lowest coverage paths** — prioritize producer or projection work
- **Highest coverage paths** — reference patterns for lagging paths
- **Most commonly missing fields** — rank remediation by missing-slot volume

---

## 5. Maintenance Guidance

### When attribution completeness should rise

Resolved completeness **should increase** after cycles that:

- Add or extend producer attribution stamps (BS4-class work)
- Improve read-side projection convergence (BS5-class work)
- Expand classifier backfill for previously empty fields
- Add baseline corpus fixtures for newly instrumented replacement paths

Field-level coverage for `repair_kind` and `owner_bucket` should rise with producer-stamp cycles.

Contract compliance **should rise** toward 100% as invalid legacy tokens are normalized or removed from populated slots.

### When attribution completeness should remain stable

Completeness **should remain stable** when changes are limited to:

- Runtime replacement behavior with no new attribution stamps or projection rules
- Documentation, reporting layout, or test-only fixture renames that do not alter record completeness
- Taxonomy lock edits that do not change populated corpus values

Strict completeness may remain at 0% while resolved completeness improves — that is expected until direct stamps cover all five fields.

### What constitutes regression

Treat the following as **regression** relative to the prior BR1 artifact baseline:

| Signal | Regression threshold |
|---|---|
| Resolved completeness % | Decrease of any amount without an documented corpus fixture reduction |
| Strict completeness % | Decrease when producer-stamp coverage was not intentionally removed |
| Field coverage % | Decrease for a field that previously improved in BS4/BS5 work |
| Path resolved completeness % | Decrease for a path that previously had non-zero resolved coverage |
| Contract compliance % | Drop below 100% on populated slots |
| Taxonomy consistency % | Drop below 100% |
| Path total reconciliation | Sum of path totals ≠ current corpus total (generator bug) |
| Field reconciliation | `present + missing ≠ total_records` for any field (generator bug) |

Corpus size changes alone are not regression if documented (for example consolidating duplicate fixtures). Compare path-normalized rates and field coverage, not only raw record counts.

---

## 6. Relationship to BS Cycle Artifacts

| Artifact | Role relative to BR1 |
|---|---|
| `artifacts/bs_attribution_baseline_report.md` | BS1 point-in-time inventory snapshot; BR1 baseline source |
| `artifacts/bs3_contract_compliance_report.md` | BS3 layer audit detail; BR1 embeds headline maturity scores |
| `artifacts/bs4_producer_stamp_report.md` | BS4 producer-stamp delta narrative |
| `artifacts/bs5_projection_convergence_report.md` | BS5 projection delta narrative |
| `artifacts/attribution_completeness_report.md` | **BR1 consolidated repository metric** for cycle-over-cycle tracking |

BR1 does not replace BS cycle reports. It consolidates the headline completeness metric, field/path coverage, BS3 contract scores, and risk summary into one repeatable artifact.

---

## 7. Success Criteria

- Attribution completeness is a repeatable repository metric (`tools/attribution_completeness_report.py`)
- Future cycles can measure movement via baseline / current / delta columns without historical storage
- No runtime behavior changes
- No attribution contract changes
