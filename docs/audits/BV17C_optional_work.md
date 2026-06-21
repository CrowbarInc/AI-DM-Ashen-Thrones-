# BV17C — Optional Work Register

**Date:** 2026-06-21  
**Context:** Post-contraction program closeout — no standing hotspot-retirement queue  
**Source:** [BV17_candidate_rankings.md](BV17_candidate_rankings.md)

---

## Register

| ID | Work item | Classification | Maintenance impact | Replay risk | Trigger to pursue |
| --- | --- | --- | --- | --- | --- |
| **BV18A** | Visibility fallback test-seam migration (`game.final_emission_visibility_fallback`) | **optional** | **maintenance-positive** (FI ↓ 8–14 on test coupling) | **replay-risky** (medium-high) | Visibility test churn causes repeated gate/fallback suite edits |
| **BV18E** | Residual RC observe fallback elimination (1 event / 1.05%) | **optional** | **maintenance-neutral** (1 incidence event, not FI) | **replay-risky** (medium) | Product priority to reach 0% fallback on FEM corpus |
| **GOV-1** | BV15 gate marker consolidation in ownership registry | **optional** | **maintenance-neutral** | low | Registry readability only |
| **GOV-2** | Attribution strict-completeness gap (38.78% owner bucket) | **optional** | **maintenance-positive** if pursued | low–medium | BS program restart — not contraction |
| **DEFER-B** | Strict/non-strict stack FO thinning | **defer** | **maintenance-negative** if forced | **replay-risky** (high) | Do not pursue under contraction framing |
| **DEFER-C** | Ownership registry FO split | **defer** | **maintenance-negative** | low | Do not pursue — guard fragmentation risk |
| **DEFER-D** | Further smoke/text/social domain hub split | **defer** | **maintenance-negative** | medium | Regrowth guards make this negative ROI |

---

## Detail: active optional items

### BV18A — Visibility fallback test-coupling governance

| Field | Value |
| --- | --- |
| **Target** | `game.final_emission_visibility_fallback` (FI 31, FO 20) |
| **Method** | Mirror BV16C — migrate test monkeypatches to owner modules |
| **Projected FI reduction** | 8–14 (test-side; production coupling unchanged) |
| **Classification** | optional / maintenance-positive / replay-risky |
| **Pursue when** | Test maintenance on visibility suites exceeds product feature work |

### BV18E — Residual RC fallback elimination

| Field | Value |
| --- | --- |
| **Target** | Single `referential_clarity_hard_replacement` event |
| **Method** | Upstream RC repair before fallback path (BV3 pattern continuation) |
| **Projected impact** | 1 incidence event → 0 |
| **Classification** | optional / maintenance-neutral / replay-risky |
| **Pursue when** | Zero-fallback corpus is an explicit product milestone |

### GOV-1 — Registry polish

| Field | Value |
| --- | --- |
| **Target** | `tests/test_ownership_registry.py` BV15 marker gap (0 markers vs BV12C–BV16) |
| **Classification** | optional / maintenance-neutral / low replay risk |
| **Pursue when** | Documentation pass on governance inventory |

### GOV-2 — Attribution completeness

| Field | Value |
| --- | --- |
| **Target** | Owner-bucket strict completeness (0% at BS baseline) |
| **Classification** | optional / maintenance-positive / low–medium replay risk |
| **Pursue when** | New BS cycle — **not** contraction-driven |

---

## Items explicitly not registered

| Former candidate | Reason excluded |
| --- | --- |
| BV12–BV16 decomposition | **Closed** — governed authorities installed |
| Smoke/text/social hub split (BV18D) | **Negative ROI** — would undo BV12–BV14 |
| Gate/terminal body split | **Validated deferred** — BV15/BV16 |
| Meta read cluster work | **Closed** — BV10 |

---

## How to use this register

1. **Do not** auto-schedule BV18 — items are **opportunistic**, not queued.
2. **Do** investigate if compat barrel FI caps fail in CI — that is **regression**, not optional work.
3. **Prefer** new functionality and isolated ROI over structural contraction unless caps breach.

---

## Evidence

| Source | Role |
| --- | --- |
| `docs/audits/BV17_candidate_rankings.md` | Candidate provenance |
| `docs/audits/BV17_retirement_analysis.md` | Defer / leave-intact decisions |
