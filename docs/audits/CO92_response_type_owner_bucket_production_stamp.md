# CO92 — Response-Type Owner-Bucket Production Stamp

Audit date: 2026-06-27  
Scope: production stamp for prepared answer/action response-type repairs; attribution baseline refresh.

---

## 1. Response-Type Write-Path Audit

### Flow (prepared answer/action repair)

1. **Contract resolution** — `enforce_response_type_contract` resolves required type via `_resolve_response_type_contract`.
2. **Candidate validation** — `_evaluate_required_response_type_validator` for answer/action.
3. **Upstream prepared resolution** — `_resolve_upstream_prepared_answer_action_repair` reads `prepared_answer_fallback_text` or `prepared_action_fallback_text` from `upstream_prepared_emission`.
4. **Repair application** — on validator pass, sets `response_type_repair_used=True`, `response_type_repair_kind` (`answer_upstream_prepared_repair` / `action_outcome_upstream_prepared_repair`), upstream prepared debug stamps, `realization_fallback_family=upstream_prepared_emission`.
5. **Opening-only owner stamp (pre-CO92)** — `stamp_opening_fallback_owner_bucket` on opening deterministic fallback paths only.
6. **FEM merge** — `merge_gate_layer_metas_into_fem` → `merge_response_type_meta` copies RT debug into `_final_emission_meta`.
7. **Lineage projection** — `build_fem_runtime_lineage_events` emits `fallback_selected` (`response_type_prepared_emission`), `gate_outcome` (`prepared_repair`), `mutation` (`response_type_repair_mutation`); owner preserved from FEM when present.
8. **Attribution inventory** — reads `sealed_fallback_owner_bucket` directly from FEM (CO89 contract); no read-side projection added.

### Pre-CO92 gap

Prepared answer/action repairs stamped repair kind and upstream metadata but **never** stamped an owner bucket. Opening repairs used `opening_fallback_owner_bucket`; prepared non-opening repairs had no production owner field despite gate selection authority.

---

## 2. Owner-Bucket Decision

**Selected bucket:** `sealed-gate` (`SEALED_FALLBACK_OWNER_SEALED_GATE`)

**Field:** `sealed_fallback_owner_bucket` on RT debug / FEM

### Rationale

| Alternative | Verdict |
|---|---|
| `upstream-prepared` | **Rejected** — reserved for opening authorship where upstream composes opening prose. Answer/action prepared repairs are **gate-selected** via `enforce_response_type_contract`; runtime lineage owner is `game.final_emission_gate`. |
| `sealed-gate` | **Selected** — matches existing CO89 attribution contract, `sealed_fallback_owner_bucket_from_fields` default for gate-family terminal repairs, and Cycle P recon: "runtime lineage reports gate owner for selection" for upstream prepared answer/action. |
| New response-type-specific bucket | **Rejected** — would expand taxonomy without production ownership semantics. |

---

## 3. Production Stamp Location

| Component | Change |
|---|---|
| `game/final_emission_meta.py` | Added `stamp_response_type_prepared_repair_owner_bucket` — stamps `sealed-gate` when `response_type_repair_used`, `upstream_prepared_emission_used`, and repair kind is prepared answer/action. |
| `game/final_emission_response_type.py` | Calls stamp on successful prepared repair path (earliest authoritative write site). |
| `game/final_emission_validators.py` | Extended `_merge_response_type_meta` to propagate `sealed_fallback_owner_bucket` (and `opening_fallback_owner_bucket`) debug → FEM. |

No read-side projection helpers added.

---

## 4. Propagation Verification

| Surface | Verified |
|---|---|
| RT debug | `test_bj39_*`, `test_co92_*` assert `sealed_fallback_owner_bucket == sealed-gate` on debug dict |
| FEM (full gate) | `test_response_policy_contracts` integration asserts FEM carries stamp after gate accept |
| Replay lineage | Existing `_fem_preserved_repair_kind` + CO89 lineage tests; owner projected from FEM via inventory when lineage event lacks bucket |
| Failure classification | Baseline corpus + CO89 failure-classification test consume FEM/observed stamp |
| Attribution inventory | Response type path: 5/6 resolved complete (+5 records); owner_bucket missing 0 |
| Observability | `sealed_fallback_owner_bucket` already in `final_emission_meta_observability` FEM key registry |

---

## 5. Baseline Updates (BS5 only; BS1 trend preserved)

| Metric | Before (CO91) | After (CO92) |
|---|---:|---:|
| Resolved complete records | 39/56 | **44/56** |
| Resolved completeness % | 69.64 | **78.57** |
| Missing `owner_bucket` | 6 | **0** |
| Response type path complete | 0/6 | **5/6** |

`BR1_BASELINE_PATH_RESOLVED` unchanged (BS1 trend baseline).

---

## 6. Files Modified

| File | Change |
|---|---|
| `game/final_emission_meta.py` | `stamp_response_type_prepared_repair_owner_bucket` |
| `game/final_emission_response_type.py` | Call stamp on prepared repair success |
| `game/final_emission_validators.py` | Propagate owner buckets in `_merge_response_type_meta` |
| `tests/helpers/replacement_attribution_inventory.py` | Baseline fixture + BS5 snapshots |
| `tests/helpers/attribution_contract.py` | `BS5_MATURITY_SNAPSHOT` |
| `tests/test_final_emission_response_type.py` | CO92 stamp tests |
| `tests/test_replacement_attribution_inventory.py` | CO85/CO89 baseline expectations |
| `tests/test_response_policy_contracts.py` | FEM propagation assertion |

---

## 7. Pytest Results

```
tests/test_final_emission_response_type.py          PASS  (proxy for test_response_type_repairs.py — file not present)
tests/test_replacement_attribution_inventory.py     PASS
tests/test_attribution_contract.py                  PASS
tests/test_attribution_completeness_metric.py       PASS
tests/test_failure_classifier.py                    PASS
```

---

## 8. Remaining Intentional Attribution Gaps

| Gap | Records | Classification |
|---|---:|---|
| Response type `gate_outcome` `mutation_classification` | 1 | Intentionally unavailable (lineage contract) |
| Sealed passive_scene `repair_kind` | 5 | Production stamp not yet defined (CO93 target) |
| Gate_outcome `mutation_classification` (other paths) | 7 | Intentionally unavailable |
| Strict completeness | 0% | Requires direct stamps on projected fields |

---

## 9. Recommended CO93 Target

**CO93 — Sealed passive-scene pressure `producer_repair_kind` production stamp**

- Target: `game/final_emission_sealed_fallback.py`, `game/final_emission_passive_scene_pressure.py`, `tests/failure_classification_contract.py`
- Goal: define and stamp a taxonomy-valid repair kind for sealed `passive_scene_pressure_fallback` terminal replacements
- Expected impact: +5 resolved records (+8.9 pp) on sealed replacement path
