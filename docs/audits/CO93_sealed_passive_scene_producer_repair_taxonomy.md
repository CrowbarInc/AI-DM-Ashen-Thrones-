# CO93 — Sealed Passive-Scene Producer Repair Taxonomy

Audit date: 2026-06-27  
Scope: production stamp for sealed `passive_scene_pressure_fallback` terminal replacements; attribution baseline refresh.

---

## 1. Sealed Passive-Scene Write-Path Audit

### Three distinct paths (must not conflate)

| Path | Trigger | Text change | `producer_repair_kind` (pre-CO93) | Owner bucket |
|---|---|---|---|---|
| **Upstream satisfier** | Observe route; pressure due; beat missing | Merge beat into upstream text | `passive_scene_concrete_beat` | Projected `sealed-gate` |
| **Sealed passive fallback** | Generic replace; `passive_scene_pressure_missing_concrete_beat` | Full terminal replace via `passive_scene_pressure_fallback` | **None** | `sealed-gate` (direct) |
| **Fail-closed / other sealed** | Opening, social minimal, global scene, etc. | Full terminal replace | Other kinds or none | Per branch |

### Sealed passive-scene flow (generic replace exit)

1. **Due-check** — `final_emission_non_strict_stack` appends `passive_scene_pressure_missing_concrete_beat` when `_passive_scene_pressure_due_for_fallback` and no concrete interaction in candidate text.
2. **Upstream satisfier (observe only)** — `apply_observe_passive_scene_concrete_beat_upstream_satisfier` may inject a beat and stamp `passive_scene_concrete_beat`, avoiding replace when successful.
3. **Selection** — `select_non_strict_replace_path_terminal_sealed_fallback_selection` → `select_non_strict_terminal_fallback_for_sealed` → passive branch when candidates exist.
4. **Candidate prose** — `_passive_scene_pressure_fallback_candidates` in `final_emission_passive_scene_pressure.py` (`final_emitted_source=passive_scene_pressure_fallback`).
5. **FEM assembly** — `run_generic_replace_exit` builds replace FEM, calls `stamp_non_strict_sealed_replacement_realization_family`.
6. **`stamp_sealed_fallback_realization_family`** — sets `realization_fallback_family=gate_terminal_repair`, `sealed_fallback_owner_bucket=sealed-gate`.
7. **Replay lineage** — `build_fem_runtime_lineage_events` emits `fallback_selected` (`sealed_passive_scene_pressure_fallback`), `mutation`, `gate_outcome`.
8. **Failure classification** — consumes FEM `producer_repair_kind` when present; split-owner matrix maps subkind → `passive_scene_pressure_fallback`.
9. **Attribution inventory** — reads `producer_repair_kind` directly from FEM for sealed path; no read-side projection added.

### Pre-CO93 gap

Generic replace stamped owner bucket and realization family but **never** stamped `producer_repair_kind` for passive-scene sealed terminal replace. Visibility hard-replace path that selects the same prose pool incorrectly retained `visibility_enforcement` (visibility-path records; out of CO93 sealed-path scope).

---

## 2. Taxonomy Decision

**Promote:** introduce `passive_scene_pressure_fallback` as a canonical producer repair kind.

### Rationale

| Alternative | Verdict |
|---|---|
| Reuse `passive_scene_concrete_beat` | **Rejected** — upstream satisfier is accept-path merge repair; sealed path is full terminal replace with different mutation semantics. |
| Reuse `visibility_enforcement` | **Rejected** — visibility enforcement owns visibility-validation hard replace; passive-scene sealed replace is gate-contract pressure enforcement on non-strict stack. |
| Taxonomy-free (intentional gap) | **Rejected** — production selects deterministic fallback prose at authoritative write site; BS4 producer-stamp policy applies. |
| **`passive_scene_pressure_fallback`** | **Selected** — aligns with `final_emitted_source`, replay subkind `sealed_passive_scene_pressure_fallback`, and failure-classifier sealed-family vocabulary. |

This is an **actual producer repair** (gate terminal text replacement), not merely a terminal realization label or fallback classification tag.

---

## 3. Production Stamp

| Component | Change |
|---|---|
| `game/final_emission_meta.py` | Added `PRODUCER_REPAIR_KIND_PASSIVE_SCENE_PRESSURE_FALLBACK` and `stamp_passive_scene_pressure_fallback_producer_metadata`. |
| `game/final_emission_sealed_fallback.py` | `stamp_non_strict_sealed_replacement_realization_family` co-stamps producer kind when `final_emitted_source=passive_scene_pressure_fallback`. |

No read-side projection helpers added. Response-type owner buckets, gate_outcome mutation_classification, and visibility-path behavior unchanged.

---

## 4. Classifier Synchronization

Updated parity surfaces:

- `tests/failure_classification_contract.py` — `ALLOWED_PRODUCER_REPAIR_KINDS`
- `game/final_emission_meta_read.py` — re-export constant
- `game/observability_attribution_read.py` — facade import, `__all__`, classifier constant registry
- BV10A parity lock (`tests/test_bv10a_read_facade_delegates.py`) — satisfied via registry sync
- Baseline fixture + CO93 tests in `tests/test_replacement_attribution_inventory.py`
- Production stamp test in `tests/test_final_emission_sealed_fallback.py`

---

## 5. Baseline Updates (BS5 only; BS1 trend preserved)

| Metric | Before (CO92) | After (CO93) |
|---|---:|---:|
| Resolved complete records | 44/56 | **48/56** |
| Resolved completeness % | 78.57 | **85.71** |
| Missing `repair_kind` | 5 | **0** |
| Sealed path complete | 0/5 | **4/5** |

`BR1_BASELINE_PATH_RESOLVED` unchanged (BS1 trend baseline).

---

## 6. Files Modified

| File | Change |
|---|---|
| `game/final_emission_meta.py` | New producer kind + stamp helper |
| `game/final_emission_sealed_fallback.py` | Co-stamp at non-strict sealed FEM assembly |
| `game/final_emission_meta_read.py` | Re-export |
| `game/observability_attribution_read.py` | Facade parity |
| `tests/failure_classification_contract.py` | `ALLOWED_PRODUCER_REPAIR_KINDS` |
| `tests/helpers/replacement_attribution_inventory.py` | Baseline fixture + BS5 snapshots |
| `tests/helpers/attribution_contract.py` | `BS5_MATURITY_SNAPSHOT` |
| `tests/test_replacement_attribution_inventory.py` | CO93 baseline + projection tests |
| `tests/test_final_emission_sealed_fallback.py` | CO93 production stamp test |

---

## 7. Remaining Intentional Attribution Gaps

| Gap | Records | Classification |
|---|---:|---|
| Sealed path `gate_outcome` `mutation_classification` | 1 | Intentionally unavailable (lineage contract) |
| Response type `gate_outcome` `mutation_classification` | 1 | Intentionally unavailable |
| Other `gate_outcome` `mutation_classification` | 6 | Intentionally unavailable |
| Strict completeness | 0% | Requires direct stamps on all projected fields |
| Lineage events without FEM co-stamp | N/A | `test_co88_sealed_passive_without_preserved_repair_stays_unresolved` guards |

---

## 8. Recommended CO94 Target

**CO94 — Gate outcome `mutation_classification` contract audit (sealed + response-type paths)**

- Target: `game/final_emission_replay_projection.py`, `tests/helpers/replacement_attribution_inventory.py`
- Goal: determine whether the remaining 8 `mutation_classification` gaps are permanently unavailable or can receive production lineage stamps without reopening CO83–CO92 convergence
- Expected impact: up to +8 resolved records if any gap is production-justified
