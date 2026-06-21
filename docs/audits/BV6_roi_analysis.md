# BV6 — Residual Referential-Clarity ROI Analysis

**Date:** 2026-06-21  
**Baseline:** BV3D corpus post-BV4B — 95 FEM, 1 fallback event (1.05% incidence)

---

## Current state

| Metric | Value |
|---|---:|
| Total fallback events | 1 |
| `referential_clarity_hard_replacement` | 1 |
| `sealed_passive_scene_pressure_fallback` | 0 |
| Observe route fallback rate | 4.35% (1/23) |
| Replay-only RC events | **0** |

The single event is the negative-control fixture OBS-M002, not a replay turn.

---

## Option comparison

### 1. Retain (status quo)

| Dimension | Estimate |
|---|---|
| Expected incidence reduction | **0** — metric stays 1/95 (1.05%) |
| Replay risk | **None** — replay already at 0 RC |
| Speaker risk | **None** — fail-closed preserved |
| Ownership risk | **None** |
| Maintenance cost | **Low** — one frozen fixture row |
| Test coverage value | **High** — proves ineligible path still hard-replaces |

### 2. Measurement split (exclude negative controls from incidence)

| Dimension | Estimate |
|---|---|
| Expected incidence reduction | **−1 event** → 0/94 replay turns (0% replay incidence) |
| Reported BV3D incidence | **0%** if fixtures excluded from numerator/denominator |
| Replay risk | **None** — read-side filter only |
| Speaker risk | **None** |
| Ownership risk | **None** |
| Maintenance cost | **Low** — ~20 lines in metrics tooling + doc update |
| Downside | Loses "single fallback event" alarm unless dual metrics reported |

### 3. EC-M01 contract expansion (repair the shape)

| Dimension | Estimate |
|---|---|
| Expected incidence reduction | **−1** on current corpus; **−2 to −5 pp** observe rate if applied to ~30 archive OBS-001 shapes (BV4B-RC projection) |
| Replay risk | **Medium-high** — golden replay + speaker contract suites must gate |
| Speaker risk | **High** — deterministic guess between co-present named NPCs |
| Ownership risk | **Low-medium** — repair entity selection becomes new write surface |
| Maintenance cost | **Medium** — new eligibility predicates, tests, recurrence monitoring |
| False repair rate (estimated) | **15–40%** on 2-entity named-anchor shapes without salience signal |

### 4. Remove negative control fixture

| Dimension | Estimate |
|---|---|
| Expected incidence reduction | **−1** (metric only) |
| Replay risk | **Low** |
| Speaker risk | **None** |
| Test coverage loss | **High** — no measurement proof that ineligible shapes hard-replace |
| Maintenance cost | **Negative ROI** — reintroduces BV3C-style activation blind spot |

---

## Cost / benefit summary

| Option | Incidence Δ | Safety | Maintenance ROI |
|---|---|---|---|
| Retain | 0 | Best | Coverage > metric cosmetics |
| Measurement split | −1 (reported) | Best | **Best cost/benefit for metric target** |
| EC-M01 expansion | −1 to −30+ shapes | Poor | Poor unless salience signal added |
| Remove fixture | −1 (reported) | Neutral | Worst — loses negative control |

---

## Projected scorecard impact (BV5 framing)

| Action | Fallback incidence | Maintenance economics | Risk posture |
|---|---|---|---|
| Retain | 1.05% (unchanged) | Stable | Safest |
| Measurement split | **0% replay** | +0.5 (cleaner signal) | Safest |
| EC-M01 expansion | **0% combined** | +0.5 then −0.5 if speaker regressions | Elevated |

---

## Key insight

The **marginal benefit of eliminating this one event via repair is near zero** on replay behavior (already eliminated) while **marginal risk of EC-M01 expansion is non-zero**.

The **highest ROI action** is dual reporting:

- `referential_clarity_hard_replacement_replay` = **0** (graduation metric)
- `referential_clarity_hard_replacement_negative_control` = **1** (regression guard)

This preserves both **zero replay fallback** claim and **negative-control coverage**.

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/bv3a_referential_clarity_metrics.json` | Current incidence |
| `docs/audits/BV4B_concrete_beat_report.md` | PSP eliminated; RC residual noted |
| `docs/audits/BV3E_eligibility_candidates.md` | EC-M01 risk classification |
| `docs/audits/BV4_candidate_recommendation.md` | BV4B-RC projection (−2 to −5 pp) |
