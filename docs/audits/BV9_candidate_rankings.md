# BV9 — Candidate Rankings

**Date:** 2026-06-21  
**Trigger:** Post BV2–BV8 hotspot reassessment  

---

## Top 5 next-cycle opportunities

### 1. BV10 — Meta-read & attribution read facade consolidation

- **Target:** `game.final_emission_meta_read + owner_bucket_views + ownership_schema cluster`
- **Expected ROI:** high
- **Maintenance impact:** Reduce cross-test churn on metadata reads; narrow investigation routing; continue BV2 read-side split
- **Implementation cost:** medium
- **Replay risk:** low
- **Evidence:** meta_read FI 29; bucket_views FI 22; ownership_schema FI 19; combined 70 FI read path

### 2. BV10B — Second-order smoke bridge thinning

- **Target:** `tests.helpers.replay_smoke_assertions + gate_integration_smoke`
- **Expected ROI:** medium-high
- **Maintenance impact:** Split post-BV7 bridge hubs (85 combined FI) by domain without monolith regrowth
- **Implementation cost:** medium
- **Replay risk:** low-medium
- **Evidence:** replay_smoke FI 46; gate_integration FI 39; BV7 intentional redistribution

### 3. BV10C — Terminal pipeline / gate convergence decomposition

- **Target:** `game.final_emission_gate + terminal_pipeline`
- **Expected ROI:** medium-high
- **Maintenance impact:** Split gate orchestration from terminal assembly to reduce 30+26 FI convergence edits
- **Implementation cost:** high
- **Replay risk:** medium
- **Evidence:** gate FI 30/FO 9; terminal FI 26/FO 14; 23 test importers on terminal

### 4. BV10D — Attribution completeness program (BS continuation)

- **Target:** `owner bucket strict completeness + failure classifier routing`
- **Expected ROI:** medium
- **Maintenance impact:** Close 38.78% owner-bucket gap; reduce misrouted investigations
- **Implementation cost:** medium-high
- **Replay risk:** low
- **Evidence:** ownership_schema FI 19; classifier helper FI 15; strict completeness 0%

### 5. BV10E — Residual RC observe fallback elimination

- **Target:** `referential_clarity_hard_replacement (1 event / 1.05%)`
- **Expected ROI:** medium (diminishing)
- **Maintenance impact:** Clear last measurable fallback on BV3D corpus
- **Implementation cost:** medium
- **Replay risk:** medium
- **Evidence:** BV1B 1 event; BV4B cleared PSP; RC remains sole fallback

## Priority ordering

| Rank | Cycle | Rationale |
| --- | --- | --- |
| 1 | BV10 | Highest-ROI unaddressed read/attribution cluster; BV2 continuation; low replay risk |
| 2 | BV10B | Largest test-bridge FI (85 combined) post-BV7 redistribution |
| 3 | BV10C | Gate/terminal convergence — high impact, higher cost/risk |
| 4 | BV10D | Ownership clarity — closes attribution completeness gap |
| 5 | BV10E | Last fallback event — diminishing returns |

## BV10 recommendation

**Selected cycle:** **BV10** — Meta-read & attribution read facade consolidation

After BV2–BV8, fallback incidence collapsed (69%→1%), smoke monolith FI fell 73→15 (BV7), and speaker recurrence was retired (BV8A). The largest remaining *unaddressed* maintenance cluster is the final-emission read/attribution path: meta_read (FI 29), owner_bucket_views (22), and ownership_schema (19) — 70 combined FI with low replay risk. Post-BV7 test bridge hubs (replay_smoke 46 + gate_integration 39) are intentional and governance-capped; BV10 targets production read facades first as the highest-ROI continuation of BV2.

### Projected scorecard impact

| Dimension | Projected delta |
| --- | --- |
| Maintenance Drag | +0.75 |
| Ownership Clarity | +0.5 |
| Operational Simplicity | +0.5 |
| Maintenance Economics | +0.5 |

**Alternates if blocked:** BV10B, BV10C
