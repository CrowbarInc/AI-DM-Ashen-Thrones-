# BV — Maintenance Economics Validation Closeout

Date: 2026-06-21 (BV1C final classification)  
Scope: measurement and evidence only; no production behavior or ownership changes

## A. Executive decision

**REDISTRIBUTED_COST**

BV1C integrates BV, BV1, BV1A, and BV1B into a single evidence-based verdict:

**BI–BM reduced maintenance cost in scoped structural surfaces (gate monolith, test megastructures) but did not demonstrate net maintenance-cost reduction repo-wide. Responsibility moved from implicit gate internals into explicit stack/pipeline owners, metadata readers, fallback routers, attribution surfaces, and governance test facades — with unchanged fallback incidence (69.16%) and unobserved post-BI bug-fix locality (N = 0).**

That pattern matches **REDISTRIBUTED_COST**, not **REDUCED_COST** or **MIXED_OR_INCONCLUSIVE**.

### Evidence integration summary

| Track | Finding | Classification weight |
|---|---|---|
| BV1 fallback incidence | 69.16% on 107 FEM turns; BV1B second snapshot **stable** (0.00 pp delta) | Contradicts REDUCED_COST |
| BV1 maintenance matrix | Gate improved; meta/replay/fallback/governance shifted | Supports REDISTRIBUTED_COST |
| BV1A bug-fix locality | N = 0 post-BI bug fixes; BR median **9 files** unchanged | Contradicts REDUCED_COST |
| BV1B fallback migration | Paths **relocated**, not removed; selection/content owners explicit | Supports REDISTRIBUTED_COST |
| BV1C hub migration | 4 hub classes removed; 11 relocated; 4 new BJ routing hubs | Supports REDISTRIBUTED_COST |
| BV1C burden accounting | Structural simplification **yes**; measured maintenance reduction **no** | Decisive |

### Why not REDUCED_COST

| Requirement | BV1 result |
|---|---|
| Bug-fix locality improved | **Not met** — zero post-BI `bug_fix` commits |
| Hotspot concentration reduced | **Partial only** — gate down; meta/replay/test hubs up |
| Fallback incidence reduced or stable | **Stable but high** — 69.16% unchanged across 2 snapshots; not reduced |
| No equivalent new maintenance hub | **Not met** — terminal pipeline, strict/non-strict stacks, meta, smoke assertions |

### Why not MIXED_OR_INCONCLUSIVE

Structural proxies are joined by **measured** fallback incidence (two stable snapshots), **quantified** fan-in redistribution, **reproduced** attribution completeness, and **integrated** hub migration accounting. Residual uncertainty (N = 0 bug-fix cohort; corpus not live traffic) bounds confidence but **does not overturn** the redistribution pattern — it prevents upgrading to REDUCED_COST, not withholding a verdict.

### Commit boundary used

Chronological BI–BM range: `f7e73fb^..b7c5b2c` (2026-06-13 through 2026-06-17). Post-BI measurement window for BV1: `f7e73fb..22cd49a` (10 commits, BI exclusive).

## B. Scorecard (BV1-updated)

| Metric | Current result | Prior baseline | Direction | Evidence | Risk |
|---|---|---|---|---|---|
| Bug-fix locality | Pre-BI median **9** files (11 commits). Post-BI **0** bug-fix commits | BR baseline: 9 files | **Unchanged / unobserved** | `BV1_bug_fix_locality_validation.md` | High: still no corrective cohort |
| Refactor/architecture locality | Post-BI refactor median **18** files (5 commits); governance median **31** (5 commits) | Pre-BI refactor median 15 | Migration breadth up | BV1 commit inventory | Medium: measures extraction cost |
| Recurrence history | 4 families / 11 rows; speaker projection **8** hits; 25% recurrence rate | No pre-BI protected baseline | Inconclusive longitudinal | `bug_recurrence_history.json` | High for trend; medium for concentration |
| Runtime fallback incidence | **69.16%** trigger rate; 74/107 FEM turns; **2** history snapshots (**stable**) | No prior snapshot | **Stable, high** | BV1B + BV1 incidence | Medium: corpus not live traffic |
| Fallback projection/ownership | 15/19 shapes; selection/content owners on 70/74 events; 13 missing owner bucket | BK ownership compression | **Improved legibility** | BP2/BP3 + BV1 incidence | Medium |
| Attribution owner bucket | **38.78%** (19/49) | BS1: 17.31% | **Improved** | `bv1_attribution_completeness_report.md` | High: 30/49 still missing |
| Attribution reason code | **59.18%** repair_kind | BS1: 15.38% | **Improved** | same | Medium-high |
| Speaker-finalize parity | Covered P3/P4 probes pass; named subtractive strip divergence | BT discovery | **Improved measurability** | Block T/U tests | Medium: no runtime frequency |
| Fan-in/fan-out | Gate **28/7** (prod FI **1**); meta **61/6**; replay projection **15/4**; visibility **17/17** | BU: gate 29/7; meta 57/4; replay proj 10/3 | **Shifted** | `BV1_maintenance_cost_matrix.md` | Medium-high |

## C. BV1 deliverables

| Artifact | Finding |
|---|---|
| [BV1_bug_fix_locality_validation.md](BV1_bug_fix_locality_validation.md) | 0 post-BI bug fixes; pre-BI median 9 files unchanged |
| [BV1_fallback_incidence_validation.md](BV1_fallback_incidence_validation.md) | 69.16% corpus rate; first snapshot appended; ownership splits visible |
| [BV1_maintenance_cost_matrix.md](BV1_maintenance_cost_matrix.md) | Gate improved; meta/replay/fallback/governance shifted |

## D. Hotspot analysis (BV1 refresh)

| Hotspot | Status | Owner or accidental hub? |
|---|---|---|
| `game/final_emission_gate.py` | **28/7**, prod fan-in **1**, 308 lines | Legitimate thin facade; historical git cost remains |
| `game/final_emission_meta.py` | **61/6**, 134 ownership refs | Legitimate schema owner; **growing** read-side hub |
| `game/final_emission_replay_projection.py` | **15/4**, 136 ownership refs | Legitimate projection owner; cross-surface responsibility |
| `game/final_emission_visibility_fallback.py` | **17/17** | Legitimate router; dominant fallback selection owner (38 events) |
| Strict/non-strict stacks + terminal pipeline | 22/22, 11/19, 26/13 | Legitimate BJ owners; **redistribution hubs** |
| `tests.helpers.emission_smoke_assertions` | **70** fan-in | Intentional test facade; concentration risk |
| `tests.test_ownership_registry` | **57** fan-out | Governance meta-router |
| Golden replay speaker projection | **8** recurrence rows | Legitimate replay owner; live repeat-fix signal |
| Fallback `observe` route | **95.45%** incidence | Corpus hotspot; referential clarity replacements |

## E. Final classification evidence table (BV1C)

| Evidence | Supports REDUCED_COST | Supports REDISTRIBUTED_COST | Contradicts REDISTRIBUTED_COST | Confidence |
|---|---|---|---|---|
| Gate LOC −97% (9,316 → 308); prod fan-in 1 | Partial (scoped) | ✓ (cost moved outward) | | **High** |
| Meta fan-in +4 (57→61); replay proj +5 (10→15) | | ✓ | | **High** |
| Fallback incidence 69.16% unchanged (2 snapshots) | | ✓ | ✓ (would need decrease for REDUCED) | **High** |
| Post-BI bug-fix N = 0; median 9 files unchanged | | ✓ (unobserved improvement) | | **High** |
| Attribution owner bucket +21.47 pp | Partial | ✓ (legibility) | | **High** |
| BK selection/content owners on 70/74 events | Partial | ✓ | | **High** |
| 4 monolith hubs removed; 11 roles relocated; 4 new BJ hubs | | ✓ | | **High** |
| Test smoke facade 70 fan-in (replacement hub) | | ✓ | | **High** |
| Governance BU20–BU30 CI self-maintaining | Partial | ✓ (clarity, not drag reduction) | | **Medium** |
| Speaker projection recurrence 8 protected rows | | ✓ (ongoing replay cost) | | **Medium** |
| Strict attribution completeness 0% | | ✓ (incomplete) | | **Medium** |
| Corpus-specific incidence (not live traffic) | | | Weakens all incidence claims | **Medium** |

**Selected label:** **REDISTRIBUTED_COST** — supports dominate; REDUCED_COST partial supports are scoped structural wins only; no evidence contradicts redistribution.

## F. Remaining observability gaps (non-blocking for BV closeout)

1. **Post-BI bug-fix cohort** — 8–12 corrective commits would enable locality rebaseline (future BV2+ validation, not BV blocker).
2. **Live-traffic incidence** — artifact corpus may over-represent observe/referential clarity routes.
3. **Pre-BI protected recurrence event log** — if outside Git, limits recurrence reduction claims.
4. **Speaker parity corpus measurement** — runtime frequency of divergence branches unmeasured.

BV1C explicitly closes BV: **no new measurements required** for top-level classification.

## G. Command log (BV + BV1)

| Command | Result |
|---|---|
| `git log --format=%h|%ad|%s f7e73fb..HEAD` | 10 post-BI commits |
| Post-BI BR-style classification → `artifacts/bv1_measurements.json` | 0 bug_fix; 5 refactor; 5 governance |
| Artifact scan + `build_fallback_incidence_report` | 107 turns, 69.16% rate |
| `python tools/fallback_incidence_trends.py --incidence-report artifacts/golden_replay/bv1_fallback_incidence_report.json` | Snapshot appended |
| `python tools/fallback_recurrence.py` | ok, 1 snapshot |
| `python tools/fallback_incidence_anomalies.py` | insufficient_history |
| `python scripts/bu_final_emission_coupling_discovery.py` | 623 files / 216 modules |
| `python tools/attribution_completeness_report.py` | 49-record report |
| `python tools/bug_fix_locality_report.py` | Frozen inventory; bug-fix median 9 |
| `git checkout -- docs/audits/BU_*.csv` | Restored analyzer side effects |

Prior BV command log entries remain valid; see git history for the 2026-06-21 BV discovery pass.

## H. Classification history

| Date | Label | Reason |
|---|---|---|
| 2026-06-21 (initial BV) | MIXED_OR_INCONCLUSIVE | No post-BI bug fixes; zero incidence snapshots |
| 2026-06-21 (BV1) | REDISTRIBUTED_COST (provisional) | Incidence baselined; ownership improved; hubs shifted |
| 2026-06-21 (BV1C) | **REDISTRIBUTED_COST (final)** | BV1A N=0 confirmed; BV1B stable incidence; hub migration + burden accounting integrated |

## I. BV1C deliverables (2026-06-21)

| Artifact | Finding |
|---|---|
| [BV1C_maintenance_cost_matrix.md](BV1C_maintenance_cost_matrix.md) | Seven-area integrated matrix; structural simplification vs measured reduction distinguished |
| [BV1C_hub_migration_analysis.md](BV1C_hub_migration_analysis.md) | 4 removed, 3 reduced, 11 relocated, 6 new hub roles |
| [BV1C_scorecard_recommendation.md](BV1C_scorecard_recommendation.md) | Keep ME/Drag/Simplicity; increase Ownership Clarity +1 |
| [BV_follow_on_candidates.md](BV_follow_on_candidates.md) | BV2 meta, BV3 fallback incidence, BV4 test facade decomposition |

### Sub-track confirmations (BV1A / BV1B)

| Track | Verdict | Deliverables |
|---|---|---|
| BV1A bug-fix locality | **Locality unchanged** (N = 0) | [BV1A_bug_fix_commit_inventory.md](BV1A_bug_fix_commit_inventory.md), [BV1A_bug_fix_locality_comparison.md](BV1A_bug_fix_locality_comparison.md), [BV1A_maintenance_hotspots.md](BV1A_maintenance_hotspots.md) |
| BV1B fallback incidence | **Burden relocated** (69.16% stable) | [BV1B_fallback_incidence_validation.md](BV1B_fallback_incidence_validation.md), [BV1B_fallback_baseline_comparison.md](BV1B_fallback_baseline_comparison.md), [BV1B_fallback_migration_analysis.md](BV1B_fallback_migration_analysis.md), [BV1B_fallback_maintenance_hotspots.md](BV1B_fallback_maintenance_hotspots.md) |

## J. Scorecard recommendation (BV1C)

| Dimension | Action |
|---|---|
| Maintenance Economics | **Keep** (5/10) |
| Maintenance Drag | **Keep** |
| Ownership Clarity | **Increase** (+1, 7→8/10) |
| Operational Simplicity | **Keep** |

Detail: [BV1C_scorecard_recommendation.md](BV1C_scorecard_recommendation.md).

## K. Follow-on work (REDISTRIBUTED_COST)

Top three remaining maintenance hubs for future cycles:

1. **BV2** — `final_emission_meta` read-side consolidation (FI 61/6)
2. **BV3** — Fallback observe-route incidence reduction (95.45% route rate)
3. **BV4** — Test governance facade decomposition (smoke 70 FI, registry 57 FO)

Detail: [BV_follow_on_candidates.md](BV_follow_on_candidates.md).

## I. BV1B fallback incidence recommendation (2026-06-21)

**Recommendation:** **fallback burden relocated**

BV1B re-ran BP fallback instrumentation on the current tree. On the 107-FEM artifact corpus, fallback trigger rate remains **69.16%** (74/107 turns) — **unchanged** from BP/BV1 baseline. BK/BS ownership metadata persists (70/74 selection+content owners; 61/74 owner buckets). Selection/content responsibility visibly **relocated** to visibility, sealed, and opening modules; gate monolith code **reduced** but lineage `event_owner` packaging unchanged.

Longitudinal trend: **`stable`** (2 snapshots, 0.00 pp delta); recurrence dominance is a second-snapshot artifact, not reduced incidence.

Deliverables:

- [BV1B_fallback_incidence_validation.md](BV1B_fallback_incidence_validation.md)
- [BV1B_fallback_baseline_comparison.md](BV1B_fallback_baseline_comparison.md)
- [BV1B_fallback_migration_analysis.md](BV1B_fallback_migration_analysis.md)
- [BV1B_fallback_maintenance_hotspots.md](BV1B_fallback_maintenance_hotspots.md)

_Final BV top-level classification not updated._

## L. BV5 maintenance economics revalidation (2026-06-21)

**Updated classification: REDUCED_COST** (medium-high confidence)

BV5 re-ran scorecard metrics after BV2 (meta consolidation), BV3 (RC observe-route reduction), and BV4B (concrete-beat PSP satisfier). The BV1C decisive contradictor — **unchanged 69.16% fallback incidence** — is **removed** on the active BV3D corpus (**1.05%**, 1/95 FEM). Meta core fan-in fell **61 → 24** (−64%). Residual redistribution persists on `final_emission_meta_read` (28 FI), `final_emission_owner_bucket_views` (22 FI), and `emission_smoke_assertions` (73 FI). Bug-fix locality remains **unobserved** (N = 0 post-BI).

| Track | Finding | Classification weight |
|---|---|---|
| BV2 meta | Core meta FI **−37**; read facades +50 FI | Partial redistribution |
| BV3F | Incidence **46.39% → 11.58%**; RC **−11** | Supports **REDUCED_COST** |
| BV4B | PSP **10 → 0**; incidence **1.05%**; observe **4.35%** | Supports **REDUCED_COST** |
| BV1A locality | N = 0 bug fixes | Bounds confidence |
| Test smoke facade | FI **70 → 73** | Residual drag |

**Scorecard updates (recommended):** Maintenance Economics **5 → 6**; Maintenance Drag **5–6 → 7**; Ownership Clarity **keep 8**; Operational Simplicity **keep**.

Deliverables:

- [BV5_scorecard_revalidation.md](BV5_scorecard_revalidation.md)
- [BV5_hub_comparison.md](BV5_hub_comparison.md)
- [BV5_fallback_burden_comparison.md](BV5_fallback_burden_comparison.md)
- [BV5_maintenance_cost_matrix.md](BV5_maintenance_cost_matrix.md)
- [BV5_follow_on_candidates.md](BV5_follow_on_candidates.md)

