# BV11 — Next Candidate Rankings

**Date:** 2026-06-21  
**Trigger:** Post-BV10 hotspot reassessment  

---

## Top 5 next-cycle opportunities

### 1. BV12 — Smoke bridge domain decomposition (BV10B continuation)

- **Target:** `tests.helpers.replay_smoke_assertions + gate_integration_smoke`
- **Projected FI reduction:** 25–35 (split domain-specific bridges; cap monolith regrowth)
- **Implementation risk:** medium
- **Replay risk:** low-medium
- **Maintenance impact:** Highest current FI cluster (95 combined, +10 post-BV10); reduces cross-domain test churn
- **Evidence:** replay_smoke FI 56 (#1 repo-wide); gate_integration FI 39; BV10C added intentional bridge load

### 2. BV12B — Gate / terminal pipeline convergence split

- **Target:** `game.final_emission_gate + final_emission_terminal_pipeline`
- **Projected FI reduction:** 15–22 (orchestration vs assembly boundary)
- **Implementation risk:** high
- **Replay risk:** medium
- **Maintenance impact:** Second-largest production convergence hub (56 combined FI); 23+ test importers on terminal
- **Evidence:** gate FI 30/FO 9; terminal FI 26/FO 14; unchanged since BV9

### 3. BV12C — Terminal text / social emission surface thinning

- **Target:** `game.final_emission_text + social_exchange_emission`
- **Projected FI reduction:** 20–30 (extract read-only views and policy slices)
- **Implementation risk:** high
- **Replay risk:** medium-high
- **Maintenance impact:** Largest production-core concentration (104 FI) but touches live composition path
- **Evidence:** text FI 52; social FI 52; tied #2–#3 rank unchanged since BV9

### 4. BV12D — Attribution completeness & classifier routing (BS continuation)

- **Target:** `failure_classifier + attribution completeness metrics`
- **Projected FI reduction:** 8–12 (narrow misrouted investigations)
- **Implementation risk:** medium
- **Replay risk:** low
- **Maintenance impact:** Closes owner-bucket strict completeness gap; adjacent to closed BV10 read cluster
- **Evidence:** failure_classifier FI 13; strict completeness 0%; facades now govern read path

### 5. BV12E — Residual RC observe fallback elimination

- **Target:** `referential_clarity_hard_replacement (1 event / 1.05%)`
- **Projected FI reduction:** 1 incidence event (not FI)
- **Implementation risk:** medium
- **Replay risk:** medium
- **Maintenance impact:** Clears last measurable fallback; diminishing structural returns
- **Evidence:** BV1B 1 event unchanged; gate_terminal_repair family

## Priority ordering

| Rank | Cycle | Projected FI ↓ | Replay risk | Rationale |
| --- | --- | --- | --- | --- |
| 1 | BV12 | 25–35 | low-medium | Largest addressable FI cluster (95); grew post-BV10 |
| 2 | BV12B | 15–22 | medium | Gate/terminal convergence — high impact, higher cost |
| 3 | BV12C | 20–30 | medium-high | Production-core text/social — largest FI but highest touch risk |
| 4 | BV12D | 8–12 | low | Attribution completeness — adjacent to closed BV10 cluster |
| 5 | BV12E | 1 event | medium | Last fallback — diminishing structural returns |

## BV12 recommendation

**Selected cycle:** **BV12** — Smoke bridge domain decomposition (BV10B continuation)

BV10 closed the read-side attribution cluster (authority FI 70→19, governance locked) without changing runtime behavior. Post-closeout measurement shows maintenance cost **redistributed**, not eliminated: replay_smoke_assertions is now the **#1 module** (FI 56, +10 from BV10C routing), and the smoke bridge cluster (replay_smoke + gate_integration) totals **95 FI** — up from 85 at BV9. Production-core text/social (52 each) and gate/terminal (56 combined) remain large but higher-risk targets. BV12 addresses the largest **addressable** concentration with BV7/BV10 lineage and bounded replay risk.

### Projected scorecard impact

| Dimension | Projected delta |
| --- | --- |
| Maintenance Drag | +0.5 |
| Ownership Clarity | +0.25 |
| Operational Simplicity | +0.5 |
| Maintenance Economics | +0.5 |

**Alternates if blocked:** BV12B, BV12C
