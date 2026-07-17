# CO91 — Attribution Maturity Plateau Audit

Audit date: 2026-06-27  
Scope: read-side attribution inventory only (BS1 corpus, BS3 contract, BS5 projection convergence, BR1 metric). No production changes.

Ground truth: live `build_baseline_attribution_corpus()` (56 records).

---

## 1. Replacement-Path Completeness Matrix

### 1a. Canonical replacement paths (9 paths, 56 records)

| Replacement path | Total | Resolved complete | Unresolved | Completeness % | Missing owner | Missing source | Missing repair | Missing recurrence | Missing mutation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| visibility replacement | 5 | 4 | 1 | 80.00 | 0 | 0 | 0 | 0 | 1 |
| first mention replacement | 5 | 4 | 1 | 80.00 | 0 | 0 | 0 | 0 | 1 |
| referential replacement | 5 | 4 | 1 | 80.00 | 0 | 0 | 0 | 0 | 1 |
| sealed replacement | 5 | 0 | 5 | 0.00 | 0 | 0 | 5 | 0 | 1 |
| response type replacement | 6 | 0 | 6 | 0.00 | 6 | 0 | 0 | 0 | 1 |
| sanitizer replacement | 10 | 9 | 1 | 90.00 | 0 | 0 | 0 | 0 | 1 |
| repair mutation | 7 | 7 | 0 | 100.00 | 0 | 0 | 0 | 0 | 0 |
| opening fallback | 7 | 6 | 1 | 85.71 | 0 | 0 | 0 | 0 | 1 |
| strict social replacement | 6 | 5 | 1 | 83.33 | 0 | 0 | 0 | 0 | 1 |
| **Overall** | **56** | **39** | **17** | **69.64** | **6** | **0** | **5** | **0** | **8** |

### 1b. Producer repair-kind sub-paths (requested minimum set)

| Sub-path | Corpus records | Resolved complete | Unresolved | Completeness % | Primary missing fields |
|---|---:|---:|---:|---:|---|
| `sanitizer_empty_output` | 6 | 5 | 1 | 83.33 | `mutation_classification` (gate_outcome) |
| `sanitizer_strip_only` | 4 | 4 | 0 | 100.00 | — |
| `passive_scene_concrete_beat` | 3 | 3 | 0 | 100.00 | — |
| `repair_mutation` (fallback_behavior_repair) | 4 | 4 | 0 | 100.00 | — |
| `opening_fallback` (success) | 6 | 5 | 1 | 83.33 | `mutation_classification` (gate_outcome) |
| `opening_failed_closed` | 1 | 1 | 0 | 100.00 | — |
| `visibility` | 5 | 4 | 1 | 80.00 | `mutation_classification` (gate_outcome) |
| `first_mention` | 5 | 4 | 1 | 80.00 | `mutation_classification` (gate_outcome) |
| `referential_clarity` | 5 | 4 | 1 | 80.00 | `mutation_classification` (gate_outcome) |
| `referential_local_substitution` | 0 | — | — | — | **Not in baseline corpus** |
| `strict_social` | 6 | 5 | 1 | 83.33 | `mutation_classification` (gate_outcome) |
| `sealed` (passive_scene_pressure) | 5 | 0 | 5 | 0.00 | `repair_kind` (all layers); `mutation_classification` (gate_outcome) |
| `response_type` | 6 | 0 | 6 | 0.00 | `owner_bucket` (all layers); `mutation_classification` (gate_outcome) |

---

## 2. Unresolved-Field Classification (17 unresolved record slots)

Every remaining gap is on a **gate_outcome lineage record**, a **sealed passive-scene terminal**, or a **response-type repair without owner stamp**. Classifications are grounded in production FEM/lineage evidence and CO87–CO90 lock tests.

| # | Path | Source kind | Missing field(s) | Classification | Production evidence |
|---|---|---|---|---|---|
| 1 | visibility | runtime_lineage_event (gate_outcome) | `mutation_classification` | **Intentionally unavailable in production** | `build_fem_runtime_lineage_events` emits `gate_outcome` with `mutation_kind=None`; sibling `mutation` event carries classification. CO87 locks gate_outcome as unresolved (`test_co87_opening_gate_outcome_projects_repair_and_owner`). |
| 2 | first mention | runtime_lineage_event (gate_outcome) | `mutation_classification` | **Intentionally unavailable in production** | Same gate_outcome contract as visibility. |
| 3 | referential | runtime_lineage_event (gate_outcome) | `mutation_classification` | **Intentionally unavailable in production** | Same gate_outcome contract. |
| 4 | sealed | fem_metadata | `repair_kind` | **Intentionally unavailable in production** | Baseline FEM: `passive_scene_pressure_fallback` with `sealed_fallback_owner_bucket` only; no `producer_repair_kind`. Not in `ALLOWED_PRODUCER_REPAIR_KINDS`. CO88 locks baseline unresolved. |
| 5 | sealed | runtime_lineage_event (fallback_selected) | `repair_kind` | **Intentionally unavailable in production** | Lineage `fallback_selected` has no repair_kind; FEM lacks producer stamp. |
| 6 | sealed | runtime_lineage_event (gate_outcome) | `repair_kind`, `mutation_classification` | **Intentionally unavailable in production** | Gate_outcome lacks both fields by lineage design; FEM lacks producer stamp. |
| 7 | sealed | runtime_lineage_event (mutation) | `repair_kind` | **Intentionally unavailable in production** | Mutation has `mutation_kind=sealed_replacement_mutation` but FEM has no `producer_repair_kind`. Projection requires preserved FEM stamp (CO88 positive test). |
| 8 | sealed | replay_projection | `repair_kind` | **Intentionally unavailable in production** | Same FEM evidence gap as above. |
| 9 | response type | fem_metadata | `owner_bucket` | **Intentionally unavailable in production** | Baseline FEM lacks `sealed_fallback_owner_bucket`. `final_emission_response_type.py` stamps `opening_fallback_owner_bucket` only for opening repairs, not `answer_upstream_prepared_repair`. CO89 locks unresolved without bucket. |
| 10 | response type | runtime_lineage_event (fallback_selected) | `owner_bucket` | **Intentionally unavailable in production** | `_fem_preserved_fallback_owner_bucket` returns None when FEM lacks bucket. |
| 11 | response type | runtime_lineage_event (gate_outcome) | `owner_bucket`, `mutation_classification` | **Intentionally unavailable in production** | Gate_outcome + no owner stamp on FEM. |
| 12 | response type | runtime_lineage_event (mutation) | `owner_bucket` | **Intentionally unavailable in production** | CO89: without `sealed_fallback_owner_bucket` on FEM, mutation lineage stays unresolved. |
| 13 | response type | replay_projection | `owner_bucket` | **Intentionally unavailable in production** | Same FEM gap. |
| 14 | response type | failure_classification | `owner_bucket` | **Intentionally unavailable in production** | Classifier row lacks bucket; observed turn in baseline also lacks stamp. |
| 15 | sanitizer (empty_output) | runtime_lineage_event (gate_outcome) | `mutation_classification` | **Intentionally unavailable in production** | Gate_outcome at sanitizer stage; `mutation_kind=None` by lineage contract. |
| 16 | opening fallback | runtime_lineage_event (gate_outcome) | `mutation_classification` | **Intentionally unavailable in production** | CO87 gate_outcome lock. |
| 17 | strict social | runtime_lineage_event (gate_outcome) | `mutation_classification` | **Intentionally unavailable in production** | Gate_outcome contract. |

**Summary by classification**

| Classification | Count |
|---|---:|
| Intentionally unavailable in production | 17 |
| Production evidence exists (projection candidate) | 0 |
| Production evidence exists but projection helper missing | 0 |
| Runtime behavior required | 0 |
| Historical baseline artifact | 0 |

---

## 3. BS5 Maturity Validation

| Snapshot constant | Expected | Live | Status |
|---|---|---|---|
| `BS5_BASELINE_COMPLETENESS.total_records` | 56 | 56 | OK |
| `BS5_BASELINE_COMPLETENESS.resolved_complete_records` | 39 | 39 | OK |
| `BS5_BASELINE_COMPLETENESS.resolved_completeness_pct` | 69.64 | 69.64 | OK |
| `BS5_BASELINE_MISSING_FIELD_TOTALS.repair_kind` | 5 | 5 | OK |
| `BS5_BASELINE_MISSING_FIELD_TOTALS.owner_bucket` | 6 | 6 | OK |
| `BS5_BASELINE_MISSING_FIELD_TOTALS.mutation_classification` | 8 | 8 | OK |
| `BS5_BASELINE_MISSING_FIELD_TOTALS.source_family` | 0 | 0 | OK |
| `BS5_BASELINE_MISSING_FIELD_TOTALS.recurrence_key` | 0 | 0 | OK |
| `BS5_MATURITY_SNAPSHOT.coverage_score_pct` | 69.64 | 69.64 | OK |
| `BS5_MATURITY_SNAPSHOT.contract_compliance_score_pct` | 100.0 | 100.0 | OK |
| `BS5_MATURITY_SNAPSHOT.taxonomy_consistency_score_pct` | 100.0 | 100.0 | OK |
| `BS5_MATURITY_SNAPSHOT.resolved_complete_records` | 39 | 39 | OK |
| `BR1_BASELINE_PATH_RESOLVED` path totals | 56 | 56 | OK (BS1 resolved counts frozen for trend baseline) |
| Embedded `bs5_path_complete` (write_bs4) | per-path | per-path | OK (all 9 paths match live) |

**No snapshot updates required.**

---

## 4. Remaining Read-Side Projection Opportunities

After CO83–CO90 convergence, **no legitimate read-side projection opportunities remain** on the deterministic baseline corpus without violating locked governance tests or inventing metadata.

| Hypothetical opportunity | Affected path | Est. improvement | Complexity | Semantic risk | Verdict |
|---|---|---:|---|---|---|
| Project `mutation_classification` onto `gate_outcome` from sibling FEM mutation events | 8 gate_outcome records across 8 paths | +14.3 pp overall (8/56) | Medium | **High** — conflates gate observability with mutation attribution; violates CO87+ intentional unresolved locks | **Reject** |
| Project `repair_kind` for sealed passive_scene from `fallback_kind` | sealed (5 records) | +8.9 pp (5/56) | Low | **High** — no producer repair kind in taxonomy; would invent `repair_kind` | **Reject** |
| Project `owner_bucket` for response_type from `source_family=upstream_prepared_emission` | response type (6 records) | +10.7 pp (6/56) | Low | **High** — source family ≠ owner bucket; not in production stamps | **Reject** |
| Add `referential_local_substitution` baseline fixture | referential sub-path | N/A (0 records today) | Low | Low | **Out of scope** — corpus expansion, not projection |

**Plateau declaration:** The attribution inventory has reached a **read-side projection plateau** at **69.64% resolved completeness** (39/56). All projection-accessible fields recoverable from existing production FEM/lineage evidence without semantic invention have been consumed through BS5 and CO83–CO90.

Remaining 30.36% requires **production-side metadata stamps** or acceptance of intentional lineage-shape gaps.

---

## 5. Plateau Recommendation

**Recommendation: Transition to production-stamp improvements**

### Rationale

1. **Read-side convergence is complete.** `source_family` and `recurrence_key` are at 100% corpus coverage. Repair mutation path is 100% resolved. Sanitizer strip-only is 100% resolved. CO90 closed repair-mutation owner projection.

2. **All 17 remaining gaps classify as production-intentional**, not missing projection helpers. CO87–CO90 tests explicitly lock gate_outcome `mutation_classification`, sealed passive-scene `repair_kind`, and response-type `owner_bucket` as unresolved when producer stamps are absent.

3. **BS5 snapshots are stable** — no drift detected; thresholds should not be relaxed.

4. **Strict completeness remains 0%** by design (projected/inferred fields excluded). Further strict gains also require direct producer stamps, not read-side work.

### Recommended production-stamp targets (CO92+)

| Priority | Path | Field | Producer action |
|---|---|---|---|
| P1 | response type replacement | `owner_bucket` | Stamp `sealed_fallback_owner_bucket` (or dedicated response-type bucket) on non-opening `answer_upstream_prepared_repair` turns |
| P2 | sealed replacement (passive_scene_pressure) | `repair_kind` | Add sealed-terminal producer repair kind to taxonomy and stamp at `stamp_sealed_fallback_realization_family` |
| P3 | gate_outcome lineage (optional) | `mutation_classification` | Either accept intentional gap or add direct `mutation_kind` to gate_outcome events in lineage projection (production lineage change) |

### Not recommended

- **Continue read-side attribution convergence** — no verified omissions remain.
- **Close the attribution convergence program** — 30% unresolved slots and 0% strict completeness still block graduation; production stamps are the next lever.

---

## 6. Validation

```text
python -m pytest tests/test_replacement_attribution_inventory.py -q  PASS
python -m pytest tests/test_attribution_contract.py -q               PASS
python -m pytest tests/test_attribution_completeness_metric.py -q    PASS
python -m pytest tests/test_failure_classifier.py -q                 PASS
```

---

## 7. Files Modified

| File | Change |
|---|---|
| `docs/audits/CO91_attribution_maturity_plateau_audit.md` | **Added** — this audit report |

No production code, snapshot constants, classifier vocabulary, or projection helpers modified.

---

## 8. Recommended CO92 Target

**CO92 — Production-stamp closure for response-type owner bucket**

- Target: `game/final_emission_response_type.py`, `tests/failure_classification_contract.py` (if new bucket needed), baseline corpus fixture in `replacement_attribution_inventory.py`
- Goal: stamp and validate `owner_bucket` on `answer_upstream_prepared_repair` path; expect +6 resolved records (+10.7 pp) without read-side projection
- Success gate: response type path resolved completeness > 0%; no regression on CO89 negative tests for unstamped turns
