# CA5 Corrective Change Candidate Inventory

> Keyword-nominated commits awaiting human corrective-fix review.

_Since date: **2026-05-20** — candidates: **26**._

## Candidate table

| Date | Commit | Subject | Files | Production | Tests | Generated | Keywords |
|---|---|---|---:|---:|---:|---:|---|
| 2026-06-22 | `0e5fe3a` | BY: First Semantic Mutation Attribution | 17 | 0 | 8 | 8 | mutation |
| 2026-06-22 | `b0803f2` | BZ: Protected Replay Trend Window #2 | 42 | 0 | 4 | 33 | replay |
| 2026-06-21 | `a31cb35` | BW: Protected Replay Trend Window | 42 | 0 | 6 | 32 | replay |
| 2026-06-19 | `d65a535` | BP: Runtime Fallback Incidence Instrumentation | 59 | 0 | 13 | 26 | fallback |
| 2026-06-17 | `683c8df` | BK: Fallback Ownership Compression | 26 | 10 | 6 | 0 | fallback |
| 2026-06-16 | `97b1836` | BL: Replay Projection Simplification | 14 | 0 | 13 | 0 | replay |
| 2026-06-13 | `f7e73fb` | BI: Golden Replay Ownership Isolation | 20 | 0 | 20 | 0 | replay |
| 2026-06-10 | `a7d6025` | AY: Bug-Class Recurrence Tracking | 5 | 0 | 4 | 0 | bug |
| 2026-06-10 | `ca830c2` | BB: Replay Surface Area Compression | 41 | 0 | 38 | 0 | replay |
| 2026-06-10 | `d067e51` | AX: Replay Harness Simplification | 13 | 0 | 13 | 0 | replay |
| 2026-06-10 | `e9263f1` | BC: Golden Replay Concentration Reduction | 8 | 0 | 6 | 2 | replay |
| 2026-06-07 | `7ed7a8b` | AU: Golden Replay Ownership Compression | 9 | 0 | 5 | 0 | replay |
| 2026-06-07 | `ef5fc34` | AV: Replay Drift Governance Promotion | 82 | 0 | 9 | 0 | replay |
| 2026-06-06 | `6210a5d` | AR: Replay Drift Classification | 35 | 0 | 17 | 8 | replay |
| 2026-06-03 | `59c14aa` | AP: Fallback Authorship Resolution | 28 | 11 | 14 | 0 | fallback |
| 2026-06-03 | `927dae2` | AO: Replay Ownership Consolidation | 23 | 1 | 10 | 0 | replay |
| 2026-06-02 | `371b38c` | AJ: Opening Fallback Metadata Consolidation | 14 | 6 | 6 | 0 | fallback |
| 2026-06-02 | `43de427` | AK: Replay Schema Maintenance Compression Recon | 11 | 0 | 8 | 0 | replay |
| 2026-06-02 | `b1c1680` | AM: Fallback Adapter Retirement | 10 | 4 | 4 | 0 | fallback |
| 2026-05-31 | `2d0ca82` | Cycle AC replay surface compression | 5 | 0 | 3 | 0 | replay |
| 2026-05-31 | `b54b311` | Close Cycle AB fallback topology collapse | 45 | 7 | 33 | 0 | fallback |
| 2026-05-31 | `c45cfe0` | Finalize strict social fallback ownership extraction | 1 | 1 | 0 | 0 | fallback |
| 2026-05-30 | `6ecb98e` | Cycle Q replay cost compression | 7 | 0 | 4 | 0 | replay |
| 2026-05-29 | `1c5b9d8` | P: Collapse fallback family ownership ambiguity | 15 | 4 | 9 | 0 | fallback |
| 2026-05-26 | `2619bb5` | K: Promote replay acceptance gate | 16 | 0 | 5 | 0 | replay |
| 2026-05-26 | `fd5f1a9` | Cycle I: Contract opening fallback authorship attribution | 16 | 2 | 10 | 0 | fallback |

## Qualification checklist

- [ ] Concrete defect response is evidenced (wrong, failing, missing, leaked, shortened, misrouted, or unsafe behavior).
- [ ] At least one production/runtime source file under game/ or static/ changes.
- [ ] Primary intent is corrective; planned architecture, extraction, or feature delivery is excluded unless the defect boundary is separable.
- [ ] Commit boundary is reviewable (not a merge; repair fanout can be attributed honestly).
- [ ] Confidence is high or medium before promotion into a future cohort.

## Exclusion checklist

- [ ] Snapshot/data-only change with no production source repair or regression lock.
- [ ] Docs-only, test-only, tooling-only, or metric-only commit.
- [ ] Feature, governance, or architecture work without a separable defect repair.
- [ ] Merge commit or unreviewably mixed intent.
- [ ] Keyword nomination alone without matching defect and repair evidence.
