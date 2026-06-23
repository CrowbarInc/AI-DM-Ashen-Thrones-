# BK — Executive Summary

**Cycle:** BK (Fallback Ownership Compression) — Discovery / Audit  
**Date:** 2026-06-16  
**Status:** Recon complete. No refactors performed.

---

## Likely primary fallback owner(s)

Fallback is **not** a single module concern. The repo has a deliberate **layered ownership model** stabilized across cycles AB, AM, AP, and AU:

| Layer | Primary owner(s) |
|-------|------------------|
| **Diegetic content** | `game/diegetic_fallback_narration.py` |
| **Opening content** | `game/opening_deterministic_fallback.py` + packaging in `game/upstream_response_repairs.py` |
| **Strict-social content** | `game/social_exchange_emission.py` |
| **Retry / fast upstream content** | `game/gm_retry.py` |
| **Gate visibility selection** | `game/final_emission_visibility_fallback.py` (`standard_visibility_safe_fallback`) |
| **Opening selection** | `game/final_emission_opening_fallback.py` |
| **Sealed terminal selection** | `game/final_emission_sealed_fallback.py` |
| **FEM metadata projection** | `game/final_emission_meta.py` |
| **Runtime lineage projection** | `game/final_emission_replay_projection.py` |
| **Acceptance/replay projection** | `tests/helpers/golden_replay_projection.py` |
| **Policy contract (non-prose)** | `game/fallback_behavior.py` |

If forced to name **one coordination owner** for gate-path fallback: **`final_emission_visibility_fallback`** — it routes all visibility-family candidates despite claiming routing-only semantics.

---

## Largest ownership seam

**Owner-bucket + authorship metadata split across three projection domains:**

1. `final_emission_meta` — opening buckets  
2. `final_emission_visibility_fallback` — visibility buckets  
3. `final_emission_sealed_fallback` — sealed buckets  

…plus parallel **selection/content owner** split fields in `final_emission_replay_projection`, and **diegetic vs governed family** dual taxonomy (AB).

This seam drives the **opening authorship cluster** (7–11 files per change) and ties runtime FEM to golden-replay protected observation (41 paths).

---

## Largest touch cascade

**Gate Visibility Family** — opening + sealed + visibility runtime modules and their three direct-owner test suites move together in **6–9 files** per behavioral change.

Git co-occurrence (since 2025-10-01):
- `test_final_emission_opening_fallback` + `test_final_emission_sealed_fallback`: **7** shared commits  
- `test_final_emission_opening_fallback` + `test_final_emission_visibility_fallback`: **7** shared commits  
- `game/final_emission_sealed_fallback` + `game/final_emission_visibility_fallback`: **4** shared commits  

Cycle BJ touched all three runtime modules in a single commit — confirming the cascade is still live.

---

## Best compression opportunity

**H1 + H2 (combined): Owner-bucket consolidation + sealed consumes visibility outcomes**

| Candidate | Rationale |
|-----------|-----------|
| **H1** | Collapse three bucket classifiers into `final_emission_meta` read-side registry — highest hub fan-in (49 inbound imports) |
| **H2** | Stop `final_emission_sealed_fallback` from re-assembling provider graph already owned by `standard_visibility_safe_fallback` — eliminates largest selection duplication |

Together they attack **both** the largest ownership seam and the largest touch cascade without violating AB dual-family or AO5 projection boundaries.

---

## Estimated Files-Touched-Per-Fix improvement

| Change class | Current FTPF (est.) | Post-BK1 target | Post-BK2 target |
|--------------|---------------------|-----------------|-----------------|
| Owner bucket / authorship metadata | 7–11 | 4–6 | 3–5 |
| Visibility / sealed / opening selection | 6–9 | 4–5 | 3–4 |
| Fast-fallback provenance | 4–6 | 3–4 | 2–3 |
| Fallback-behavior policy | 4–6 | 4–6 (already tight) | — |
| Diegetic template addition | 3–5 | 3–4 | 3–4 |

**Overall:** Meaningful BK compression should yield **~30–40% FTPF reduction** on metadata/selection changes (the dominant maintenance class). Content-only changes are already relatively localized (~3–5 files).

---

## Recommended BK1 starting target

**BK1: Owner-bucket mapper consolidation in `final_emission_meta`**

| Why BK1 first | Detail |
|---------------|--------|
| Highest hub centrality | 49 inbound imports — one mapper home reduces fan-out everywhere |
| Lower behavior risk than H2 | Read-side bucket assignment; prose and selection order unchanged |
| Prior art | Cycles AJ (opening meta fields), AP (authorship resolution), AU (replay ownership) — all touched this seam |
| Clear direct-owner test | `tests/test_opening_fallback_owner_bucket.py` + `tests/failure_classification_contract.py` |
| Protected replay | Bucket **values** must stay stable; moving **code** is safe if values byte-identical |

**BK1 scope sketch (for implementation phase, not this audit):**
1. Move `classify_visibility_fallback_owner_bucket` logic behind `final_emission_meta` API  
2. Move sealed bucket assignment helpers similarly  
3. Leave call sites as thin delegates for one cycle, then remove  
4. Refresh no protected values — only import paths  

**BK2 follow-on:** H2 sealed-consumes-visibility selection consolidation (higher regression risk; requires sealed + visibility test suite alignment).

---

## Deliverables index

| # | Artifact | Path |
|---|----------|------|
| 1 | Fallback inventory | `docs/cycles/BK_fallback_inventory.md` |
| 2 | Ownership map | `docs/cycles/BK_fallback_ownership_map.md` |
| 3 | Dependency audit | `docs/cycles/BK_fallback_dependency_audit.md` |
| 4 | Touch cascades | `docs/cycles/BK_fallback_touch_cascades.md` |
| 5 | Projection audit | `docs/cycles/BK_fallback_projection_audit.md` |
| 6 | Selection audit | `docs/cycles/BK_fallback_selection_audit.md` |
| 7 | Content audit | `docs/cycles/BK_fallback_content_audit.md` |
| 8 | Compression candidates | `docs/cycles/BK_fallback_compression_candidates.md` |
| 9 | Executive summary | `docs/cycles/BK_EXECUTIVE_SUMMARY.md` |

---

## Key metrics (snapshot)

| Metric | Value |
|--------|-------|
| Runtime `game/` files matching `fallback` | 82 |
| Tier-A fallback owners | 10 runtime + 1 test projection |
| Distinct selection entry points | ~15–20 |
| Fallback dependency hub #1 | `final_emission_meta` (49 inbound) |
| Fallback selection hub #1 | `final_emission_visibility_fallback` (18 inbound) |
| Content SSOT | `diegetic_fallback_narration` (15 inbound, leaf) |
| Protected replay observation paths | 41 (`golden_replay_projection`) |
| Largest cascade FTPF | 6–9 files (visibility family) |

---

## Governance alignment

This audit confirms `docs/architecture_ownership_ledger.md` declarations for strict-social, opening, and fallback-behavior seams. The **remaining BK work** is not unresolved ownership declaration — it is **reducing distributed read-side mappers and duplicated selection graphs** that declarations already name but code still spreads across modules.

**Do not refactor in BK recon.** Proceed to BK1 implementation only with explicit cycle approval and byte-stable bucket/replay contracts.
