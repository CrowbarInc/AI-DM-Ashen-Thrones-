# Cycle AB — Fallback Topology Collapse — Closure — 2026-05-31

**Status:** Closed. Topology contraction is complete at maintenance grade; runtime fallback **selection** and **emitted text** are unchanged.

**Recon:** `cycle_ab_fallback_topology_collapse_recon_2026-05-31.md` (discovery-only baseline).

**Related freeze:** Gate convergence initiative ends at Block AB in `docs/gate_convergence_closeout.md`. Cycle AB is the **fallback-topology** closeout companion to that gate freeze—not a reopening of gate orchestration refactors.

---

## 1. Executive Summary

Cycle AB reduced fallback **topology breadth** without altering player-facing output or fallback precedence. Work spanned six blocks: dead import and doc sync (AB1), shrinking compatibility-local vocabulary to test helpers (AB2), documenting and locking the dual FEM fallback-family contract for golden replay (AB3), narrowing diegetic provenance stamps on canonical opening success (AB4), retiring legacy tuple adapters at the gate sealed-selection boundary while keeping test-round-trip shims (AB5), and collapsing the read-side `sealed_or_global_replacement` lineage bucket into stable sealed sub-kinds keyed off `final_emitted_source` (AB6).

Protected golden replay, dual-family projection tests, sealed sub-kind projection tests, and the gate convergence closeout snapshot test all pass. **No further runtime fallback topology work is recommended** unless a new audit or defect identifies a specific seam.

---

## 2. Blocks Completed

### AB1 — Dead import + doc sync

- Removed the unused `_deterministic_opening_fallback_text_and_meta` import from `game/final_emission_gate.py` (opening prose authorship remains upstream-only via `game/upstream_response_repairs` → `game/opening_deterministic_fallback`).
- Refreshed opening ownership docstrings in `game/opening_deterministic_fallback.py` and reconciled stale gate-local compose references in `docs/gate_cleanup_inventory.md`.

### AB2 — Compatibility-local vocabulary shrink

- Retired `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` from production `game/` modules.
- Centralized the legacy token in `tests/helpers/opening_fallback_evidence.py` for classifier/owner-bucket negative fixtures and compatibility-local negative assertions.
- `game/final_emission_meta.py` retains read-side mapping for `compatibility_local` / `compatibility_local_opening_deterministic` strings if synthetic telemetry ever surfaces them.

### AB3 — Dual family field contract

- Documented the **diegetic** (`fallback_family_used`) vs **governed provenance** (`realization_fallback_family`) contract in `docs/testing/protected_replay_manifest.md` and `tests/helpers/golden_replay_projection.py`.
- Added golden replay projection tests that prefer diegetic first, fall back to realization when diegetic is absent, and assert raw FEM fields are not rewritten by projection.
- Added `tests/test_final_emission_meta.py::test_normalize_fem_preserves_dual_fallback_family_fields_without_collapse`.

### AB4 — Diegetic stamp narrowing

- Canonical successful opening fallback now stamps `realization_fallback_family=upstream_prepared_emission` alongside diegetic `fallback_family_used=scene_opening`; `legacy_diegetic_fallback` is no longer the success-path provenance stamp on opening.
- Locked by `tests/test_diegetic_fallback_narration.py::test_opening_dual_family_stamps_are_intentionally_distinct` and opening golden replay invariants (`realization_fallback_family != legacy_diegetic_fallback` on canonical paths).

### AB5 — Legacy tuple retirement

- Non-strict sealed terminal selection in the gate uses `SealedFallbackSelection` end-to-end via `_select_non_strict_replace_path_terminal_sealed_fallback_selection`; `as_legacy_tuple()` remains only on the backward-compatible private tuple adapter for historical tests/imports.
- Visibility paths still use `VisibilitySelectedFallback.from_legacy_tuple` at tuple-shaped candidate boundaries (intentional compatibility edge).
- Round-trip and dataclass selection contracts remain in `tests/test_final_emission_gate.py` (`-k sealed_fallback_selection or legacy_tuple`).

### AB6 — Sealed branch projection collapse

- Added read-side `SEALED_REPLACEMENT_SUBKIND_*` constants and `project_sealed_replacement_subkind_from_fem` in `game/final_emission_replay_projection.py`.
- Runtime FEM keeps `final_route`, `final_emitted_source`, `fallback_pool`, and `fallback_kind` unchanged; lineage `fallback_kind` on `fem_runtime_lineage_events` refines the former catch-all `sealed_or_global_replacement` bucket.
- Documented in `docs/testing/protected_replay_manifest.md` (Cycle AB6 section).
- Golden replay recurrence-key allowlist extended to accept per-subkind `fallback_selected:gate:...` keys.

---

## 3. Runtime Behavior Statement

| Surface | Changed? |
|---|---|
| Emitted player-facing text | **No** |
| Fallback selection order / precedence | **No** |
| Write-time FEM stamps (`final_emitted_source`, `final_route`, selection metadata) | **No** (AB4 narrows which provenance family is stamped on canonical opening success; text and route unchanged) |
| Protected golden replay structural observations | **No** (41 protected paths; projected `fallback_family` still prefers diegetic) |
| Read-side lineage / replay projection | **Yes** — narrower vocabulary only; no selection side effects |

---

## 4. Metric Movement

| Metric | Direction | Evidence |
|---|---|---|
| **Fallback Surface** | Improved | Dead gate import removed; compatibility-local constant removed from `game/`; sealed lineage catch-all split into seven stable sub-kinds; duplicate topology paths documented rather than silently merged. |
| **Ownership Clarity** | Improved | Dual-family contract explicit in manifest + projection helper; opening success provenance=`upstream_prepared_emission` vs diegetic=`scene_opening`; sealed branches distinguishable in lineage despite shared `gate_terminal_repair`. |
| **Fix Persistence** | Improved | Dedicated dual-family and sealed-sub-kind tests; golden replay locks canonical opening authorship and recurrence keys; gate closeout snapshot test guards doc/taxonomy drift. |

---

## 5. Remaining Intentional Seams

- **Dual family fields remain distinct** on runtime FEM (`fallback_family_used` diegetic, `realization_fallback_family` governed). Golden replay observes a single projected `fallback_family` with diegetic-first preference only.
- **Tuple wrappers remain at compatibility/test edges** — `SealedFallbackSelection.as_legacy_tuple` / `from_legacy_tuple`, `VisibilitySelectedFallback.from_legacy_tuple`, and `_select_non_strict_replace_path_terminal_sealed_fallback` tuple adapter for private historical imports.
- **Sealed sub-kinds are read-side lineage only** — they appear on projected `fem_runtime_lineage_events[*].fallback_kind`, not as protected golden replay observation fields or runtime FEM rewrites.
- **Compatibility-local opening authorship** — helper/tests may still synthesize `compatibility_local_opening_deterministic`; canonical production paths must not emit it (negative tests and golden replay guards).

---

## 6. Test Evidence

### Gate convergence closeout (Block AB freeze doc)

```text
python -m pytest tests/test_gate_convergence_closeout.py -q --tb=line
22 passed
```

### AB6 + dual-family focused regressions

```text
python -m pytest \
  tests/test_final_emission_meta.py::test_project_sealed_replacement_subkind_maps_terminal_replace_sources \
  tests/test_final_emission_meta.py::test_build_fem_runtime_lineage_events_sealed_branches_remain_distinct_read_side \
  tests/test_golden_replay.py::test_golden_replay_dual_family_projection_prefers_diegetic_fallback_family_used \
  tests/test_golden_replay.py::test_golden_replay_dual_family_projection_falls_back_to_realization_when_diegetic_absent \
  tests/test_golden_replay.py::test_golden_replay_dual_family_projection_does_not_rewrite_raw_fem_fields \
  tests/test_diegetic_fallback_narration.py::test_opening_dual_family_stamps_are_intentionally_distinct \
  -q --tb=line
6 passed
```

### AB5 tuple / sealed selection

```text
python -m pytest tests/test_final_emission_gate.py -k "sealed_fallback_selection or legacy_tuple" -q --tb=line
2 passed
```

### Full protected golden replay

```text
python -m pytest tests/test_golden_replay.py -q --tb=line
58 passed
```

*Note:* One initial golden replay run hit a transient Windows `PermissionError` on `codex_pytest_tmp` atomic rename; immediate retry was green. Treat as environmental, not assertion drift.

---

## 7. Recommendation

**Cycle AB is closed.** Do not schedule further runtime fallback topology contraction unless:

- A new topology audit identifies an equivalent route or compatibility residue worth merging, or
- A bug report shows incorrect selection, stamping, or protected replay drift.

Future work on fallbacks should be **bug-driven** (incorrect text, wrong branch, missing stamp) or **product-driven** (new fallback family), not broad topology thinning.

---

## Files Touched (Cycle AB scope)

**Runtime / projection**

- `game/final_emission_gate.py`
- `game/final_emission_replay_projection.py`
- `game/final_emission_meta.py`
- `game/final_emission_sealed_fallback.py`
- `game/upstream_response_repairs.py`
- `game/opening_deterministic_fallback.py`

**Tests / helpers**

- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_golden_replay.py`
- `tests/test_final_emission_meta.py`
- `tests/test_diegetic_fallback_narration.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_final_emission_gate.py`

**Governance docs**

- `docs/testing/protected_replay_manifest.md`
- `docs/gate_cleanup_inventory.md`
- `docs/gate_convergence_closeout.md` (AB6 lineage note)
- `cycle_ab_fallback_topology_collapse_recon_2026-05-31.md` (recon baseline; unchanged by closure pass)
