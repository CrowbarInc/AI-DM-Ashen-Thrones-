# CA3 Corrective Change Locality Report

> First repository-authoritative measurement of corrective change locality.

_Primary metric: **files_touched_per_fix** — source `docs/audits/CA_corrective_change_locality_cohort.csv`._

## 1. Executive Summary

This cohort measures what a genuine corrective fix costs to modify in this repository.

- **Qualifying fixes:** 10
- **Median files touched per fix (raw):** 12.5
- **Median files touched per fix (effective):** 7.0
- **Median production files touched:** 2.5
- **Median test files touched:** 2.0
- **Largest repair family:** opening_fallback (6 fixes)

## 2. Cohort Composition

- **Qualifying fixes:** 10
- **Exclusion controls:** 1
- **Excluded cohort IDs:** EX-01
- **Date range:** 2026-03-21 through 2026-05-20

### Confidence distribution

- **high:** 8
- **medium:** 2

## 3. Files Touched Per Fix

| Metric | Value |
|---|---:|
| Cohort size | 10 |
| Median | 12.5 |
| Mean | 87.7 |
| Minimum | 5 |
| Maximum | 538 |
| P75 | 44.0 |
| P90 | 248.2 |

## 4. Production Locality

| Metric | Value |
|---|---:|
| Median production files touched | 2.5 |
| Mean production files touched | 3.6 |
| Minimum | 1 |
| Maximum | 9 |

## 5. Test Locality

| Metric | Value |
|---|---:|
| Median test files touched | 2.0 |
| Mean test files touched | 2.4 |

## 6. Generated Artifact Distortion

- **Raw median files touched:** 12.5
- **Effective median files touched:** 7.0
- **Median distortion percentage:** 44.0%
- **Fixes with generated-artifact pollution:** 3 (30.0%)

### Distortion by commit

| Cohort ID | Total | Generated | Effective | Distortion % |
|---|---:|---:|---:|---:|
| CA-01 | 7 | 0 | 7 | 0.0 |
| CA-02 | 20 | 0 | 20 | 0.0 |
| CA-03 | 16 | 0 | 16 | 0.0 |
| CA-04 | 7 | 0 | 7 | 0.0 |
| CA-05 | 7 | 0 | 7 | 0.0 |
| CA-06 | 5 | 0 | 5 | 0.0 |
| CA-07 | 216 | 210 | 6 | 97.22 |
| CA-08 | 52 | 44 | 8 | 84.62 |
| CA-09 | 538 | 534 | 4 | 99.26 |
| CA-10 | 9 | 0 | 9 | 0.0 |

## 7. Repair Family Concentration

- **Largest repair family:** opening_fallback
- **Largest family count:** 6
- **Concentration ratio:** 0.6

| Repair family | Count | Percentage |
|---|---:|---:|
| ci_import | 1 | 10.0% |
| dialogue_routing | 1 | 10.0% |
| opening_fallback | 6 | 60.0% |
| replay_log | 1 | 10.0% |
| routing | 1 | 10.0% |

## 8. Full Cohort Table

| Cohort ID | Commit | Title | Confidence | Repair family | Total | Production | Tests | Generated | Effective |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| CA-01 | `09863c6` | Fix dialogue/adjudication routing and remove scaffold text leakage; improve follow-up response handling | medium | dialogue_routing | 7 | 4 | 0 | 0 | 7 |
| CA-02 | `ceecc57` | Opening Scene Repair | medium | opening_fallback | 20 | 8 | 6 | 0 | 20 |
| CA-03 | `6351b33` | Preserve curated opening facts through fallback | high | opening_fallback | 16 | 9 | 4 | 0 | 16 |
| CA-04 | `2013258` | Restrict journal seed facts to perceptual opening content | high | opening_fallback | 7 | 2 | 2 | 0 | 7 |
| CA-05 | `9e83820` | Preserve journal openings through selector fallback | high | opening_fallback | 7 | 3 | 1 | 0 | 7 |
| CA-06 | `1b3b3ee` | Preserve valid scene openings before deterministic fallback | high | opening_fallback | 5 | 1 | 1 | 0 | 5 |
| CA-07 | `f487f4d` | Guard rich scene openings from post-gate shortening | high | opening_fallback | 216 | 2 | 1 | 210 | 6 |
| CA-08 | `f3fa4b1` | Preserve player chat in replayed logs | high | replay_log | 52 | 2 | 2 | 44 | 8 |
| CA-09 | `5cb8444` | Recover mixed investigation question routing | high | routing | 538 | 2 | 2 | 534 | 4 |
| CA-10 | `6a402d2` | config: lazy-load OpenAI API key for import-safe tests | high | ci_import | 9 | 3 | 5 | 0 | 9 |
