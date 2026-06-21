# BV17C — Repository State Classification

**Date:** 2026-06-21  
**Scope:** Post-BV17 program end state  
**Evidence:** `artifacts/bv17_hotspot_analysis.json`, `docs/audits/BV17_authority_classification.md`

---

## Selected classification

## **LEGITIMATE_AUTHORITY_DOMINANT**

---

## Rationale

### Why not CONCENTRATION_DOMINANT

Concentration-dominated repositories exhibit **high fan-in on modules without clear ownership boundaries** and **regrowth after decomposition**. This repository shows:

| Anti-pattern | Present? |
| --- | --- |
| Accidental hub in top 25 | **No** (0) |
| Top-1 FI share >10% on ungoverned module | **No** (5.1% on governed `replay_fem_read_smoke`) |
| Compat barrel regrowth | **No** — caps enforced (18 total shim FI) |
| Ungoverned import paths to retired monoliths | **No** — BV12C–BV14C guards |

Fan-in **concentrates**, but on **named authorities with locks**, not accidental routers.

### Why not MIXED

A mixed state implies **material accidental hub load coexisting with legitimate authorities**. At program end:

| Signal | Value |
| --- | --- |
| Governed + legitimate authorities in top 25 | **17 / 25** (68%) |
| Compatibility shims in top 25 | **0** |
| Accidental shim FI (repo-wide) | **18** (below contraction threshold of 25) |
| Maintenance matrix classification | **CONTRACTION_COMPLETE** |

Remaining mixed-utility helpers (8/25) are **test infrastructure**, not accidental production hubs.

### Why LEGITIMATE_AUTHORITY_DOMINANT

| Criterion | Evidence |
| --- | --- |
| Live-path sequencers centralized | Gate (30 FI, 1 prod) + terminal (11 FI) retained |
| Domain composition owned | Text formatting 51, social policy 33 — governed |
| Test smoke owned | replay_fem 56, gate_orch 39 — governed with caps |
| Fallback graph explicit | visibility/opening/sealed owners; incidence 1.05% |
| Regrowth prevented | 114 registry collectors; compat FI caps locked |

**The largest FI modules are the correct owners for their domains.**

---

## Supporting metrics

| Metric | Value | Implication |
| --- | ---: | --- |
| Top-1 FI share | 5.1% | Distributed concentration |
| Top-5 FI share | 18.9% | No monolith dominance |
| Accidental hub count | 0 | Authority-shaped |
| Governed authority count (top 25) | 9 | Intentional hubs |
| Legitimate authority count (top 25) | 8 | Production owners |
| Fallback incidence | 1.05% | Runtime drag retired |
| Recurring keys | 0 | Recurrence drag retired |

---

## Implications for future work

| Implication | Guidance |
| --- | --- |
| Hotspot retirement | **Complete** — do not schedule BV18+ without cap breach |
| New features | Route through existing domain authorities |
| New test helpers | Must not bypass compat guards — extend domain hubs |
| FI growth on capped barrels | **Regression** — fix immediately |
| FI growth on domain authorities | Evaluate — may be legitimate if domain expands |

---

## Comparison to program start (BV1)

| Shape | BV1 | BV17C |
| --- | --- | --- |
| Dominant module type | Accidental monolith / router | Governed domain authority |
| Fallback as driver | **Yes** (69%) | **No** (1.05%) |
| Hub retirement queue | Implicit / growing | **Empty** |
| Classification | CONCENTRATION_DOMINANT (implicit) | **LEGITIMATE_AUTHORITY_DOMINANT** |
