# CO94 — Gate-Outcome Mutation Classification Production Audit

Audit date: 2026-06-27  
Scope: determine whether `gate_outcome` lineage events should carry `mutation_classification` at production origin.

**Note:** Target file `game/final_emission_runtime_lineage.py` does not exist. Authoritative lineage vocabulary lives in `game/runtime_lineage_telemetry.py`; FEM→lineage projection lives in `game/final_emission_replay_projection.py` (`build_fem_runtime_lineage_events`). Production writes finalized FEM; lineage events are projected read-side from FEM (not stamped at gate write time).

---

## 1. Gate-Outcome Lineage Generation Audit

### Event creation path

| Step | Location | Behavior |
|---|---|---|
| FEM finalize | Gate/sanitizer/finalize owners | Write `final_route`, repair flags, producer stamps — no lineage events |
| Lineage projection | `build_fem_runtime_lineage_events` | Derives bounded event list from finalized FEM |
| Event factory | `make_runtime_lineage_event` | Normalizes `event_kind`, optional fields |

### Where `mutation_kind` is written

| Event kind | `mutation_kind` | Primary signal |
|---|---|---|
| `mutation` | **Yes** — e.g. `visibility_replacement_mutation`, `sanitizer_mutation`, `response_type_repair_mutation` | `_append_fem_mutation_projections` from fallback kind, repair flags, sanitizer evidence |
| `fallback_selected` | **No** | `fallback_kind`, optional `repair_kind` |
| `gate_outcome` | **Intentionally absent (`None`)** | `gate_path` only (routing outcome) |
| `speaker_repair` | **No** | `repair_kind` |

### Gate_outcome creation sites (`build_fem_runtime_lineage_events`)

1. **Fallback-selected path** — when `_fem_selected_fallback_projection` returns a fallback and `gate_path != "unknown"`, emits `gate_outcome` with `gate_path` from projection tuple (e.g. `visibility_hard_replaced`, `replaced_or_sealed`, `prepared_repair`, `sanitizer_fallback`).
2. **Accept-path path** — when no fallback projection but `gate_path` inferred from FEM (`accept_unchanged`, `accept_repaired`, `strict_social_accept`, `visibility_local_repair`).

Neither path passes `mutation_kind` to `make_runtime_lineage_event`.

### Consumption

| Consumer | gate_outcome usage | mutation usage |
|---|---|---|
| Attribution inventory | Builds records per event; `mutation_classification` from `event.mutation_kind` or fallback_kind projection (fallback_selected only) | Reads `mutation_kind` directly |
| Failure classifier | `gate_path_frequency`, routing evidence | `mutation_kind_frequency`, semantic mutation evidence |
| Runtime lineage summary | `gate_path_frequency` bucket | `mutation_kind_frequency` bucket |
| Golden replay | Recurrence keys, drift observation | Separate mutation recurrence |

---

## 2. Gate_Outcome vs Mutation Comparison (Baseline Paths)

For each replacement family with a baseline `gate_outcome` gap:

| Path | gate_outcome `gate_path` | Sibling mutation `mutation_kind` | Duplication if stamped on gate_outcome? | Consumers distinguish? |
|---|---|---|---|---|
| visibility | `visibility_hard_replaced` | `visibility_replacement_mutation` | **Yes** | Yes — summary buckets split |
| first mention | `first_mention_hard_replaced` | `first_mention_replacement_mutation` | **Yes** | Yes |
| referential | `referential_clarity_hard_replaced` | `referential_clarity_replacement_mutation` | **Yes** | Yes |
| sealed (passive_scene) | `replaced_or_sealed` | `sealed_replacement_mutation` | **Yes** | Yes |
| response type | `prepared_repair` | `response_type_repair_mutation` | **Yes** | Yes |
| sanitizer | `sanitizer_fallback` | `sanitizer_mutation` | **Yes** | Yes |
| opening fallback | `opening_fallback` | `fallback_mutation` | **Yes** | Yes |
| strict social | `strict_social_fallback` | `response_type_repair_mutation` | **Yes** | Yes |

**Repair-mutation path** (passive_scene satisfier, fallback_behavior) emits `mutation` events with classification but often **no** `gate_outcome` (accept-path FEM without fallback projection) — zero gate_outcome gaps on that path.

Conclusion: every baseline `gate_outcome` gap has a sibling `mutation` event carrying the classification. Adding `mutation_kind` to `gate_outcome` would duplicate information already on the mutation event in the same lineage bundle.

---

## 3. Production Policy Decision

### **Policy A — gate_outcome should remain mutation-free**

### Rationale (production semantics, not metrics)

1. **Semantic separation** — `gate_outcome` records *routing decisions* (`gate_path`: accept, replace, prepared repair, sanitizer route). `mutation` records *text mutation classification*. These are orthogonal observability dimensions by design (Cycle H runtime lineage closure).
2. **Sibling coverage** — mutation classification is already emitted on dedicated `mutation` events derived from the same FEM evidence (`_append_fem_mutation_projections`).
3. **Downstream contract** — `summarize_runtime_lineage_events` aggregates `gate_path_frequency` and `mutation_kind_frequency` into separate buckets; collapsing them would blur dashboard semantics.
4. **No production write gap** — lineage is projected read-side from finalized FEM; there is no missing gate-time stamp. The attribution inventory gap reflects event-kind semantics, not absent production metadata.
5. **CO87–CO93 convergence** — multiple cycles explicitly lock `gate_outcome` records as missing `mutation_classification` when sibling mutations carry it (`test_co85_visibility_gate_outcome_*`, `test_co87_opening_gate_outcome_*`, etc.).

### Policy B rejected

Stamping `mutation_kind` on `gate_outcome` would:
- Duplicate sibling mutation events
- Conflate routing observability with mutation attribution
- Violate established lineage event-kind contracts
- Require reopening CO87+ intentional unresolved locks for metrics gain only (+14.3 pp resolved completeness)

---

## 4. Implementation

**No production lineage changes.**

Added/strengthened contract locks:

| Artifact | Change |
|---|---|
| `game/runtime_lineage_telemetry.py` | Module doc: gate_outcome omits `mutation_kind` by contract |
| `tests/test_replacement_attribution_inventory.py` | `test_co94_*` — gate_outcome gap intentional; 8 gaps; sibling mutation coverage |
| `tests/test_attribution_contract.py` | `test_co94_gate_outcome_and_mutation_events_are_semantically_distinct`; gate_outcome check in projection contract test |

No read-side projection added. No BS5 baseline refresh (no legitimate completeness improvement).

---

## 5. Baseline Status (unchanged from CO93)

| Metric | Value |
|---|---:|
| Resolved complete | 48/56 (85.71%) |
| Missing `mutation_classification` | 8 (all gate_outcome lineage records) |
| Missing `repair_kind` | 0 |

---

## 6. Files Modified

| File | Change |
|---|---|
| `game/runtime_lineage_telemetry.py` | Contract documentation |
| `tests/test_replacement_attribution_inventory.py` | CO94 contract lock tests |
| `tests/test_attribution_contract.py` | CO94 semantic distinction test |
| `docs/audits/CO94_gate_outcome_mutation_classification_audit.md` | This report |

---

## 7. Pytest Results

```text
tests/test_replacement_attribution_inventory.py  PASS
tests/test_attribution_contract.py               PASS
tests/test_attribution_completeness_metric.py    PASS
tests/test_failure_classifier.py                 PASS
```

(No `test_final_emission_runtime_lineage.py` — file does not exist.)

---

## 8. Remaining Intentional Attribution Gaps

| Gap | Records | Classification |
|---|---:|---|
| `gate_outcome` `mutation_classification` | 8 | **Intentional** — routing events; use sibling `mutation` event |
| Strict completeness | 0% | Requires direct stamps on all fields (projected fields excluded) |

All other BS5 fields (`repair_kind`, `owner_bucket`, `source_family`, `recurrence_key`) are at zero missing totals post-CO93.

---

## 9. Recommended CO95 Target

**CO95 — Strict-completeness policy audit (direct-stamp feasibility)**

- Target: `tests/helpers/attribution_contract.py`, `tests/helpers/replacement_attribution_inventory.py`, producer stamp governance in `game/final_emission_meta.py`
- Goal: catalog which remaining projected/inferred fields could ever become strict-direct without read-side projection, vs permanently resolved-only semantics
- Expected impact: policy clarity only; no automatic metric inflation
