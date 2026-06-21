# BV14 — Decomposition Projection

**Date:** 2026-06-21
**Baseline:** Post-BV13 — `social_exchange_emission` FI **52** (highest production-core concentration)

---

## FI projection

| Stage | `social_exchange_emission` FI | New module FI | Top production hotspot |
| --- | --- | --- | --- |
| BV14 baseline | **52** | — | `social_exchange_emission` **52** |
| After Phase 1 (extract + re-export) | 52 | fallback ~20, policy ~12, composition ~15, validation ~6 | unchanged (compat) |
| After Phase 2 (migration) | **~6–10** | fallback ~20, policy ~12, composition ~15 | `final_emission_text_formatting` ~51 or `final_emission_gate` ~30 |
| After Phase 3 (governance lock) | **≤6** | named authorities stable | gate owner reassessment |

**Expected net:** compat FI **52 → ~6** (−46), comparable to BV13B **52 → 5**.

## Scorecard impact (projected post-Phase 2)

| Dimension | Projected delta | Rationale |
| --- | --- | --- |
| Maintenance drag | **+0.5** | Fallback sprawl localized; composition edits isolated |
| Operational simplicity | **+0.25** | Clear import routing for gate vs fallback vs composition |
| Maintenance economics | **+0.5** | Largest remaining production FI choke split into named authorities |
| Ownership clarity | **+0.5** | BN8/BJ-115 guards updated; private leak pattern eliminated |

## Replay risk assessment

| Factor | Risk | Mitigation |
| --- | --- | --- |
| Fallback phrase catalog relocation | **High** | Phase 1 re-export only; golden transcript suite before any phrase edits |
| `build_final_strict_social_response` move | **Medium** | Same function objects via compat; narration transcript regressions first |
| Policy predicate moves | **Low** | Constants/predicates only; API path selection tests |
| Telemetry projection moves | **None** | Logging side-effect only |
| Private helper promotion | **Low** | Behavior-preserving rename to public on target module |

## BV14C projection (governance)

| Item | Target | Notes |
| --- | --- | --- |
| Compat barrel FI cap | **≤6** | BD-2 legality owner + delegate tests |
| Import guard | New `test_bv14c_*` | Forbid fallback/policy via compat for new consumers |
| Encapsulation lock | Private symbol ban | Eliminate `_npc_display_name_for_emission` external imports |

## Success criteria

**Target state:** `social_exchange_emission` compat barrel **≤6 FI**; `social_exchange_composition` holds canonical terminal assembly; fallback FI (~20) is an **explicit** maintenance surface.

## BV14 executive recommendation

| Question | Answer |
| --- | --- |
| Remain centralized? | **No** for full module — **yes** for composition core |
| BV13-style decomposition? | **Yes** — parallel pattern: extract fallback/policy/validation, migrate, govern |
| Primary driver | Fallback FI sprawl (10+) + multi-concern 3881 LOC — not illegitimate composition authority |

Recommended sequence: **BV14** (this decomposition) → reassess **`final_emission_gate`** FI (~30) → evaluate **`final_emission_terminal_pipeline`** FI (~26).
