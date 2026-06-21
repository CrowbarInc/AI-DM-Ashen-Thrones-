# BV15 — Decomposition Candidates

**Date:** 2026-06-21

---

## Executive framing

Unlike BV13/BV14, the gate module is **already decomposed internally** (BN1–BN11). BV15 decomposition targets are **namespace cleanup** and **FI governance**, not stack extraction.

## Candidate modules

| Candidate | Extract / action | Est. FI absorbed | Consumers | Migration cost | Replay risk |
| --- | --- | --- | --- | --- | --- |
| **`final_emission_gate_policy`** | Move eligibility/routing predicates if any remain re-exported | **0** (already in gate_context/preflight) | preflight modules | **N/A** — already extracted | **Low** |
| **`final_emission_gate_validation`** | Validator imports (none external today) | **0** | validators module | **N/A** | **Low** |
| **`final_emission_gate_projection`** | FEM/replay owner strings referencing `game.final_emission_gate` | **0 import FI** | replay_projection, ownership_schema | **Low** — string owner migration | **Medium** — attribution labels |
| **`terminal_gate_adapter`** | Consolidate `final_emission_runtime` + document API→gate seam | **1** production | api_turn_support | **Low** | **Low** |
| **Namespace re-export retirement** | Remove 13 stack/compat re-exports from gate namespace | **−0 module FI** | governance tests update imports | **Low-medium** | **Low** |
| **Governance introspection migration** | Point `feg` tests at stack owners directly | **−18 AST module FI** | 18 test modules | **Medium** — large test diff | **Low** |

## Not recommended

| Candidate | Reason |
| --- | --- |
| Split `apply_final_emission_gate` across modules | Would fracture orchestration authority — stacks already own behavior |
| Merge gate into terminal_pipeline | Inverts dependency direction; gate must remain upstream router |
| Full module elimination | Legitimate orchestration owner — API path depends on it |

## Projected FI reduction (module-level)

| Stage | `final_emission_gate` BU FI | Notes |
| --- | --- | --- |
| Current | **30** | 17 orchestration + 13 governance/introspection |
| After re-export retirement | **~28–30** | BU FI unchanged — re-exports have 0 external imports |
| After governance import migration | **~14–17** | Module-level `feg` imports eliminated; orchestration FI remains |
| After BV15C governance cap | **≤12** | Orchestration + runtime adapter + ownership tests only |

**Primary win is clarity**, not massive FI drop — gate is already thin post-BN.
