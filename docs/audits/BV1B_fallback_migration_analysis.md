# BV1B — Fallback Responsibility Migration Analysis

**Date:** 2026-06-21
**Question:** Did BI–BM remove fallback paths, or relocate them?

## Executive verdict

**Relocated, not removed.** Measured fallback incidence is unchanged (69.16%). Structural extraction (BJ/BK/BN) moved selection and content ownership into named modules while preserving trigger rates on the artifact corpus. No major path qualifies as **A. Removed**; gate monolith surface **reduced** in code but lineage packaging still defaults `event_owner` to gate.

## Migration matrix

| Path | Primary module | Status | Evidence |
|---|---|---|---|
| Final emission visibility fallback | `game/final_emission_visibility_fallback.py` | **D. Relocated** | 38 selection-owner events; observe-route referential clarity dominant. Gate label remains on lineage `event_owner` but selection routed here post-BK. |
| Terminal pipeline fallback | `game/final_emission_terminal_pipeline.py` | **D. Relocated** | BJ extracted pipeline orchestration; terminal repair family on 60/74 events (`gate_terminal_repair`). Incidence unchanged; convergence hub persists (26/13 fan-in). |
| Ownership fallback routes | meta owner buckets + BK stamp paths | **D. Relocated** | Owner buckets explicit: sealed-gate (30), upstream-prepared (30). 13 events still unbucketed — compression not elimination. |
| Replay fallback routes | `game/final_emission_replay_projection.py` + golden replay helpers | **C. Unchanged** (incidence) / **Reduced** (test projection surface) | BL simplified replay projection tests; 0 replay-subsystem bug-fix touches historically. Incidence mix unchanged on corpus. |
| Speaker-finalize fallback routes | Block T/U speaker finalize stack | **C. Unchanged** | BT audit added divergence probes; no fallback incidence shift on scanned FEM corpus (speaker touches minimal in post-BI commits). |
| Gate monolith fallback selection | `game/final_emission_gate.py` | **B. Reduced** (code) / **C. Unchanged** (lineage label) | Gate file thinned (BJ/BN); selection owner still labels 32 events while implementation moved outward. |
| Opening deterministic fallback | `game/opening_deterministic_fallback.py` | **D. Relocated** | 31 content-owner events on scene_opening route — explicit module owner post-BK. |
| Sealed fallback | `game/final_emission_sealed_fallback.py` | **D. Relocated** | 39 content-owner events; sealed-gate bucket dominant on observe route. |

## Selection vs content owner split (post-BK)

| Dimension | Owner | Events |
|---|---|---:|
| Selection | `game.final_emission_visibility_fallback` | 1 |
| Content | `game.final_emission_sealed_fallback` | 1 |

## Status legend

- **A. Removed** — path no longer appears in corpus or projection
- **B. Reduced** — fewer code touchpoints or lower structural fan-in
- **C. Unchanged** — incidence and routing behavior stable on corpus
- **D. Relocated** — behavior persists under explicit new owner module
