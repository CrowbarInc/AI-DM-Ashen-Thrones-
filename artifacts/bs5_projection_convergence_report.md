# BS5 Projection Convergence Report

> Read-side attribution completeness before (BS1 baseline) vs after BS5 projection convergence.

## Summary

| Metric | Before (BS1) | After (BS5) | Delta |
|---|---:|---:|---:|
| Strict completeness | 0.0% | 0.0% | 0.0 |
| Resolved completeness | 5.77% | 32.65% | 26.88 |
| Strict complete records | 0/52 | 0/49 | +0 |
| Resolved complete records | 3/52 | 16/49 | +13 |

## Field-Level Improvements

| Field | Missing before | Missing after | Slots recovered |
|---|---:|---:|---:|
| `owner_bucket` | 43 | 30 | +13 |
| `source_family` | 8 | 8 | +0 |
| `repair_kind` | 44 | 20 | +24 |
| `recurrence_key` | 5 | 0 | +5 |
| `mutation_classification` | 16 | 8 | +8 |

## Path-Level Improvements (resolved complete)

| Replacement path | Before complete | After complete | Delta |
|---|---:|---:|---:|
| visibility replacement | 0 | 3 | +3 |
| first mention replacement | 0 | 3 | +3 |
| referential replacement | 0 | 3 | +3 |
| sealed replacement | 0 | 0 | +0 |
| response type replacement | 0 | 0 | +0 |
| sanitizer replacement | 0 | 1 | +1 |
| repair mutation | 0 | 0 | +0 |
| opening fallback | 3 | 5 | +2 |
| strict social replacement | 0 | 1 | +1 |
