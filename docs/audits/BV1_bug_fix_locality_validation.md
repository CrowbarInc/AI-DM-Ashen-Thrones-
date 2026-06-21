# BV1 — Bug-Fix Locality Validation

**Date:** 2026-06-21  
**Scope:** Measurement only. No production behavior or classification methodology changes.

## Executive summary

Commits after `f7e73fb` (BI) through `22cd49a` (HEAD) were classified with the BR heuristic and measured with `git diff-tree` path inventories. **There are still zero post-BI commits classified as `bug_fix`.** Bug-fix locality after BI–BM therefore remains **not measurable**, and the valid comparison continues to be the frozen pre-BI BR baseline (median **9** files, p90 **216**) versus a post-BI corrective cohort of **N = 0**.

Program work in the same window (BJ–BU) is real and broad: **10 commits**, median **18.5** files touched (refactor + governance cohorts combined), with BJ alone at **92** files. That records migration cost, not demonstrated future fix cheapness.

**Verdict:** Bug-fix locality did **not** improve after BI–BM; it is **unchanged and unobserved** for the corrective cohort.

## Commit boundary

| Boundary | SHA | Date | Notes |
|---|---|---|---|
| BI (last pre-extraction baseline) | `f7e73fb` | 2026-06-13 | Golden Replay Ownership Isolation |
| First post-BI commit | `11ff282` | 2026-06-16 | BJ: Final Emission Gate Responsibility Extraction |
| HEAD | `22cd49a` | 2026-06-21 | BU: Post-BJ Fan-In / Fan-Out Validation |

Analyzed range: **`f7e73fb..HEAD`** (10 commits, BI exclusive).

## Post-BI classification (full cohort)

| Category | Commits | Median files | p90 files | Largest commit |
|---|---:|---:|---:|---|
| `bug_fix` | **0** | — | — | — |
| `refactor_architecture` | 5 | 18 | 92 | `11ff282` BJ (92 files) |
| `governance_observability` | 5 | 31 | 75 | `22cd49a` BU (75 files) |
| **All post-BI** | **10** | **18.5** | **75** | `11ff282` BJ (92 files) |

### Per-commit inventory

| SHA | Date | Category | Files | Prod | Tests | Docs | Subject |
|---|---|---|---:|---:|---:|---:|---|
| `22cd49a` | 2026-06-21 | governance_observability | 75 | 22 | 30 | 23 | BU: Post-BJ Fan-In / Fan-Out Validation |
| `ea80d52` | 2026-06-20 | governance_observability | 6 | 0 | 4 | 2 | BT: Speaker Finalization Divergence Audit |
| `adc374b` | 2026-06-20 | governance_observability | 50 | 9 | 18 | 23 | BS: Semantic Replacement Attribution Completeness |
| `3f5ee0c` | 2026-06-20 | governance_observability | 31 | 0 | 11 | 20 | BQ: Recurrence History Population |
| `d65a535` | 2026-06-19 | governance_observability | 59 | 0 | 13 | 46 | BP: Runtime Fallback Incidence Instrumentation |
| `b7c5b2c` | 2026-06-17 | refactor_architecture | 16 | 0 | 13 | 3 | BM: Large Test File Decomposition |
| `b88a560` | 2026-06-17 | refactor_architecture | 18 | 12 | 6 | 0 | BN — Gate Fan-Out Reduction |
| `683c8df` | 2026-06-17 | refactor_architecture | 26 | 10 | 6 | 10 | BK: Fallback Ownership Compression |
| `97b1836` | 2026-06-16 | refactor_architecture | 14 | 0 | 13 | 1 | BL: Replay Projection Simplification |
| `11ff282` | 2026-06-16 | refactor_architecture | 92 | 35 | 57 | 0 | BJ: Final Emission Gate Responsibility Extraction |

*BN is classified `refactor_architecture` here to match the BR CSV row; automated subject matching can mis-tag fan-out reduction as governance.*

## Comparison against BR baseline

| Cohort | N | Median files touched | p90 files touched | Median production files |
|---|---:|---:|---:|---:|
| Bug fixes **before BI** (BR CSV) | 11 | **9** | **216** | 5 |
| Bug fixes **after BI** | **0** | **Not measurable** | **Not measurable** | **Not measurable** |
| Refactors before BI (BR CSV) | 95 | 15 | 41 | 3 |
| BI–BM chronological range (BV) | 6 | 19 | — | — |
| Post-BI refactor only (BJ–BN–BM–BK–BL) | 5 | 18 | 92 | 10 |
| Post-BI governance (BP–BU) | 5 | 31 | 75 | 9 |

## Directory and ownership-bucket touch (refactor cohort proxy)

Because there are no bug-fix commits, directory concentration is reported for the five post-BI refactor commits as the closest maintenance-touch proxy:

| Directory cluster | Refactor touches (5 commits) | Historical bug-fix touches (11 commits, BR) |
|---|---:|---:|
| `game/final_emission_*` (aggregate) | 35+ module touches across BJ/BK/BN | 3 (`final_emission_gate.py`) |
| `tests/helpers` | 13 | varies |
| `tests/test_final_emission_gate*` | 10+ (BM decomposition) | 49 (`test_final_emission_gate.py` historical) |
| `game/final_emission_meta.py` | 2 (BK) | low in bug-fix cohort |
| `game/final_emission_replay_projection.py` | 2 (BK, BL) | — |

Ownership buckets implied by touched modules:

| Bucket | Post-BI refactor modules touched | Interpretation |
|---|---|---|
| Gate orchestration | `final_emission_gate*`, preflight modules (BN, BJ) | Gate surface split; orchestration moved outward |
| Final-emission policy/metadata | 20+ BJ-extracted modules, `final_emission_meta` (BK) | New explicit owners; meta hub reread growth |
| Fallback selection/projection | visibility, sealed, opening, deterministic (BK) | Ownership compression, not elimination |
| Replay projection | `final_emission_replay_projection`, golden replay tests (BL) | Replay read-side simplified in tests/helpers |
| Test governance | decomposed gate/golden test files (BM) | Monolith stubs replaced by focused files |

## Largest would-be maintenance events (post-BI)

| Rank | SHA | Files | Category | Primary touch surfaces |
|---:|---|---:|---|---|
| 1 | `11ff282` | 92 | refactor | BJ extraction: 35 production + 57 test modules |
| 2 | `22cd49a` | 75 | governance | BU validation sweep across audits, helpers, FEM assembly |
| 3 | `d65a535` | 59 | governance | BP incidence tooling + golden_replay artifacts |
| 4 | `adc374b` | 50 | governance | BS attribution completeness + reports |
| 5 | `683c8df` | 26 | refactor | BK fallback ownership across 10 production modules |

## Did bug-fix locality improve after BI–BM?

**No — and it still cannot be shown either way.**

- The post-BI corrective denominator remains **zero**; the 9-file BR median is unchanged because no new `bug_fix` rows exist.
- Refactor/governance commits in BJ–BU are **broader** than the pre-BI refactor median (15 files), which is expected for planned extraction but is not evidence of cheaper future fixes.
- Gate and test monolith hotspots **contracted** (BM, BN, BJ), but touches **relocated** into stack/pipeline modules and governance suites — consistent with redistribution, not demonstrated locality gain for defect repair.

## Evidence and commands

| Command | Result |
|---|---|
| `git log --format=%h|%ad|%s --date=iso-strict f7e73fb..HEAD` | 10 commits enumerated |
| Per-commit `git diff-tree --no-commit-id --name-only -r <sha>` | Path inventories for classification |
| BR methodology replay (subject + path precedence) | Matches BR CSV for BJ–BQ; adds BS/BT/BU |
| `python tools/bug_fix_locality_report.py --output artifacts/bv1_bug_fix_locality_report.md` | Frozen 235-commit inventory; bug-fix median still 9 |
| Machine-readable cohort | `artifacts/bv1_measurements.json` |

## Confidence

| Claim | Confidence | Caveat |
|---|---|---|
| Zero post-BI bug-fix commits | **High** | Heuristic matches BR; no subject claims explicit repair in BJ–BU window |
| Pre-BI median 9 files | **High** | Frozen BR/BRL1 cohort |
| Post-BI locality improved | **Not supported** | Requires non-zero corrective sample |
| Migration breadth increased | **Medium-high** | Median refactor 18 vs pre-BI 15; dominated by BJ outlier |
