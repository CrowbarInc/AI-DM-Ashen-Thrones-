# BK — Fallback Compression Candidates

**Cycle:** BK — Discovery / Audit  
**Date:** 2026-06-16  

Evidence basis: `BK_fallback_inventory.md`, `BK_fallback_ownership_map.md`, `BK_fallback_dependency_audit.md`, `BK_fallback_touch_cascades.md`, `BK_fallback_projection_audit.md`, `BK_fallback_selection_audit.md`, `BK_fallback_content_audit.md`, git co-occurrence since 2025-10-01, prior cycles AP/AB/AM/AU/BL.

---

## HIGH VALUE

### H1 — Owner-bucket mapper consolidation

| Field | Value |
|-------|-------|
| **Files involved** | `game/final_emission_meta.py`, `game/final_emission_visibility_fallback.py`, `game/final_emission_sealed_fallback.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/failure_classification_contract.py`, `tests/helpers/golden_replay_projection.py` |
| **Ownership issue** | Three parallel bucket classifiers with overlapping `UNKNOWN_*` / `SEALED_*` vocabulary |
| **Expected touch reduction** | Bucket policy changes: **7–11 → 3–5 FTPF** |
| **Risk level** | **Medium** — golden-replay protected bucket values must remain byte-stable |

---

### H2 — Sealed selection consumes visibility outcomes (stop re-assembling providers)

| Field | Value |
|-------|-------|
| **Files involved** | `game/final_emission_sealed_fallback.py`, `game/final_emission_visibility_fallback.py`, `tests/test_final_emission_sealed_fallback.py`, `tests/test_final_emission_visibility_fallback.py` |
| **Ownership issue** | `assemble_non_strict_sealed_fallback_selection` duplicates sub-selector provider graph already inside `standard_visibility_safe_fallback` |
| **Expected touch reduction** | Sealed/visibility behavior changes: **6–9 → 3–5 FTPF** |
| **Risk level** | **Medium-high** — sealed terminal path is regression-heavy |

---

### H3 — Opening metadata field registry single re-export surface

| Field | Value |
|-------|-------|
| **Files involved** | `game/final_emission_meta.py`, `game/final_emission_opening_fallback.py`, `game/opening_deterministic_fallback.py`, `tests/helpers/opening_fallback_evidence.py`, `tools/refresh_protected_replay_manifest.py` |
| **Ownership issue** | Field lists split across meta constants, opening_fallback factory, and test re-exports (`OPENING_FALLBACK_RESULT_META_FIELD_NAMES`) |
| **Expected touch reduction** | New opening meta field: **7–11 → 4–6 FTPF** |
| **Risk level** | **Low-medium** — additive fields already follow AJ1 pattern |

---

### H4 — Provenance debug promotion or absorption into meta

| Field | Value |
|-------|-------|
| **Files involved** | `game/fallback_provenance_debug.py`, `game/final_emission_meta.py`, `game/api.py`, `game/gm_retry.py`, `tests/test_fallback_overwrite_containment.py`, `tests/test_upstream_fast_fallback_block_l.py` |
| **Ownership issue** | Documented "temporary" module owns fast-fallback trace packaging; crosses API/gate boundary |
| **Expected touch reduction** | Fast-fallback provenance changes: **4–6 → 2–3 FTPF** |
| **Risk level** | **Medium** — overwrite containment tests lock behavior |

---

### H5 — Social fallback selection surface unification (visibility vs sanitizer)

| Field | Value |
|-------|-------|
| **Files involved** | `game/final_emission_visibility_fallback.py`, `game/output_sanitizer.py`, `game/social_exchange_emission.py`, `tests/test_strict_social_emergency_fallback_dialogue.py`, `tests/test_output_sanitizer.py` |
| **Ownership issue** | Same `minimal_social_emergency_fallback_line` content selected in visibility candidate list AND sanitizer empty-output path with separate trace owners |
| **Expected touch reduction** | Social emergency path changes: **3–5 → 2–3 FTPF** |
| **Risk level** | **Medium** — sanitizer is hot path |

---

### H6 — Opening dual-entry selector convergence (RT contract vs visibility opening-mode)

| Field | Value |
|-------|-------|
| **Files involved** | `game/final_emission_opening_fallback.py`, `game/final_emission_visibility_fallback.py`, `game/final_emission_response_type.py`, `tests/test_final_emission_opening_fallback.py` |
| **Ownership issue** | Two authoritative entry points call `opening_scene_safe_fallback_selection` with different orchestration wrappers |
| **Expected touch reduction** | Opening selection policy: **6–9 → 4–5 FTPF** |
| **Risk level** | **Medium** |

---

## MEDIUM VALUE

### M1 — Retire compatibility-local test vocabulary residue

| Field | Value |
|-------|-------|
| **Files involved** | `tests/helpers/opening_fallback_evidence.py`, `game/final_emission_meta.py` (`OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`) |
| **Ownership issue** | `compatibility_local_opening_deterministic` never written in prod; still in mapper + negative golden tests |
| **Expected touch reduction** | Authorship cleanup: **-1 to -2 files** per pass |
| **Risk level** | **Low** — AP already scoped this |

---

### M2 — Consolidate opening test evidence with golden_replay_projection row builders

| Field | Value |
|-------|-------|
| **Files involved** | `tests/helpers/opening_fallback_evidence.py`, `tests/helpers/replay_observed_row_fixtures.py`, `tests/helpers/failure_classification_sync.py` |
| **Ownership issue** | Parallel FEM-slice builders for classifier/dashboard vs opening direct-owner tests |
| **Expected touch reduction** | Fixture changes: **4–5 → 2–3 FTPF** |
| **Risk level** | **Low** |

---

### M3 — `visibility_selected_fallback_candidate` inlined at call sites

| Field | Value |
|-------|-------|
| **Files involved** | `game/final_emission_visibility_fallback.py`, `game/final_emission_first_mention_composition.py` |
| **Ownership issue** | Pure wrapper factory adds indirection without boundary value |
| **Expected touch reduction** | Minimal — cosmetic API surface |
| **Risk level** | **Low** |

---

### M4 — Gate thin-boundary lock updates after selection consolidation

| Field | Value |
|-------|-------|
| **Files involved** | `tests/helpers/gate_thin_boundary_locks.py`, `tests/test_ownership_registry.py` |
| **Ownership issue** | Static import fences lag behind actual consolidation |
| **Expected touch reduction** | Indirect — prevents false-positive touch cascades in future cycles |
| **Risk level** | **Low** |

---

### M5 — Historical tuple adapters (`from_legacy_tuple` / `as_legacy_tuple`)

| Field | Value |
|-------|-------|
| **Files involved** | `game/final_emission_sealed_fallback.py`, `game/final_emission_visibility_fallback.py` |
| **Ownership issue** | AM retired most adapters; tuple paths may remain for compatibility |
| **Expected touch reduction** | Small maintenance win |
| **Risk level** | **Low-medium** — verify zero prod callers before removal |

---

## LOW VALUE

### L1 — Module docstring ownership comment alignment

Align `final_emission_visibility_fallback` doc ("must not author prose") with its coordinator role — documentation only.

### L2 — Rename `_global_narrative_fallback_stock_line` visibility

Already delegated to diegetic; rename is cosmetic.

### L3 — `fallback_behavior` hedge form list extraction

Policy constants — no touch cascade impact.

### L4 — Test file naming normalization (`test_diegetic_fallback_block4.py`)

Historical block naming — no ownership impact.

---

## Compression priority matrix

| ID | Candidate | FTPF delta | Risk | BK phase fit |
|----|-----------|------------|------|--------------|
| **H1** | Owner-bucket consolidation | High | Medium | BK1 |
| **H2** | Sealed consumes visibility | High | Medium-high | BK1–BK2 |
| **H3** | Opening meta registry | Medium | Low-medium | BK1 |
| **H4** | Provenance absorption | Medium | Medium | BK2 |
| **H5** | Social selection unify | Medium | Medium | BK2 |
| **H6** | Opening dual-entry | Medium | Medium | BK2 |
| M1–M5 | Various | Low | Low | BK3+ |

---

## Explicit non-candidates (do not compress in BK)

| Target | Reason |
|--------|--------|
| Merge `golden_replay_projection` + `final_emission_replay_projection` | AO5 boundary — explicitly forbidden |
| Collapse `fallback_family_used` + `realization_fallback_family` at write time | AB dual-family contract |
| Move diegetic prose into visibility_fallback | Violates content/selection split |
| Merge `social_exchange_emission` content into gate | Governance-aligned owner — keep |
| Consolidate `fallback_behavior` into gate | Already isolated policy contract |
