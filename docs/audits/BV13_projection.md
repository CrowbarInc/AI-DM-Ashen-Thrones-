# BV13 — Decomposition Projection

**Date:** 2026-06-21 (updated post-BV13B)  
**Baseline:** BV11/BV12 post-closeout — `final_emission_text` FI **52** (tied #1 production hotspot)

---

## FI projection

| Stage | `final_emission_text` FI | `formatting` FI | `policy` FI | Top production hotspot |
| --- | --- | --- | --- | --- |
| BV13 baseline | **52** | — | — | tied 52 (`social_exchange_emission`) |
| After BV13A (extract + re-export) | 52 | 2 (internal) | 1 (internal) | unchanged (compat) |
| **After BV13B (migration)** | **5** | **52** | **8** | `social_exchange_emission` **52** (text hub demoted) |
| After BV13C (compat cap + governance) | **≤5** | **52** | **8** | formatting primitive (legitimate) |

**BV13B actuals:** compat FI **52 → 5** (−47). Formatting absorbed **52** direct importers; policy **8**.

## Scorecard impact (actual post-BV13B)

| Dimension | Projected delta | Rationale |
| --- | --- | --- |
| Maintenance drag | **+0.5** | Mixed hub eliminated; formatting/policy edits localize |
| Operational simplicity | **+0.25** | Clear import routing for gate vs validator changes |
| Maintenance economics | **+0.5** | Largest production FI choke split into named authorities |
| Ownership clarity | **+0.5** | BN9/BJ-129 guards updated; gate routes pregate text via BN9 helper |

## Replay risk assessment

| Factor | Risk | BV13B outcome |
| --- | --- | --- |
| `_normalize_text` behavior change | **Low** | Same function objects; import path only |
| Fallback stock line relocation | **None** | Remains on compat barrel (3 consumers) |
| Policy tuple moves | **Low** | Constants-only; validator suites green |
| Legacy repair isolation | **None** | Test-only via legacy module |
| Gate preflight import churn | **Low** | Gate uses `resolve_gate_preflight_pregate_text` (BJ-129 green) |

## BV13C projection

| Item | Target | Notes |
| --- | --- | --- |
| Compat barrel FI cap | **≤5** | Already at **5** — delegate test + 3 fallback wrapper + governance strings |
| Import guard | New `test_bv13c_*` | Forbid formatting/policy imports via compat barrel for new consumers |
| Fallback wrapper migration | Optional BV13D | Move `_global_narrative_fallback_stock_line` to diegetic facade (−3 compat FI) |
| Remaining migration count | **0 mechanical** | Phase 2 consumer migration complete |

## Success criteria

**Achieved:** `final_emission_text` is no longer a mixed utility hub. Formatting (**FI 52**) and policy (**FI 8**) are canonical authorities; compat barrel (**FI 5**) is compatibility-only.

Recommended sequence: **BV13C** (governance lock) → **BV14** (`social_exchange_emission`) → reassess gate owner FI (30).
