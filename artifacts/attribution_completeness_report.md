# Attribution Completeness Report

> BR1 repository metric — read-side attribution completeness over the deterministic baseline corpus.

## Overall Completeness

| Metric | Baseline (BS1) | Current | Delta |
|---|---:|---:|---:|
| Strict completeness % | 0.0 | 0.0 | +0.0 |
| Resolved completeness % | 5.77 | 32.65 | +26.88 |
| Strict complete records | 0/52 | 0/49 | +0 |
| Resolved complete records | 3/52 | 16/49 | +13 |

_Corpus size: baseline 52 records, current 49 records._

## Contract Integration (BS3)

| Score | Baseline (BS1) | Current | Delta |
|---|---:|---:|---:|
| Contract compliance % | 40.3 | 100.0 | +59.7 |
| Taxonomy consistency % | 72.0 | 100.0 | +28.0 |

## Field Coverage

| Field | Baseline coverage | Current coverage | Delta | Present | Missing | Strict coverage |
|---|---:|---:|---:|---:|---:|---:|
| `owner_bucket` | 17.31% | 38.78% | +21.47 | 19 | 30 | 34.69% |
| `source_family` | 84.62% | 83.67% | -0.95 | 41 | 8 | 10.2% |
| `repair_kind` | 15.38% | 59.18% | +43.8 | 29 | 20 | 53.06% |
| `recurrence_key` | 90.38% | 100.0% | +9.62 | 49 | 0 | 51.02% |
| `mutation_classification` | 69.23% | 83.67% | +14.44 | 41 | 8 | 18.37% |

## Path Coverage

| Replacement path | Baseline resolved | Current resolved | Delta | Total | Strict % | Missing owner | Missing source | Missing repair | Missing recurrence | Missing mutation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| visibility replacement | 0.0% (0/5) | 60.0% (3/5) | +60.0 | 5 | 0.0% | 2 | 1 | 2 | 0 | 1 |
| first mention replacement | 0.0% (0/5) | 60.0% (3/5) | +60.0 | 5 | 0.0% | 2 | 1 | 2 | 0 | 1 |
| referential replacement | 0.0% (0/5) | 60.0% (3/5) | +60.0 | 5 | 0.0% | 2 | 1 | 2 | 0 | 1 |
| sealed replacement | 0.0% (0/5) | 0.0% (0/5) | +0.0 | 5 | 0.0% | 2 | 1 | 5 | 0 | 1 |
| response type replacement | 0.0% (0/7) | 0.0% (0/6) | +0.0 | 6 | 0.0% | 6 | 1 | 2 | 0 | 1 |
| sanitizer replacement | 0.0% (0/7) | 16.67% (1/6) | +16.67 | 6 | 0.0% | 5 | 1 | 2 | 0 | 1 |
| repair mutation | 0.0% (0/4) | 0.0% (0/4) | +0.0 | 4 | 0.0% | 4 | 0 | 1 | 0 | 0 |
| opening fallback | 42.86% (3/7) | 71.43% (5/7) | +28.57 | 7 | 0.0% | 2 | 1 | 2 | 0 | 1 |
| strict social replacement | 0.0% (0/7) | 16.67% (1/6) | +16.67 | 6 | 0.0% | 5 | 1 | 2 | 0 | 1 |

## Risk Summary

### Lowest Coverage Paths

- repair mutation: 0.0% resolved complete
- response type replacement: 0.0% resolved complete
- sealed replacement: 0.0% resolved complete
- sanitizer replacement: 16.67% resolved complete
- strict social replacement: 16.67% resolved complete

### Highest Coverage Paths

- opening fallback: 71.43% resolved complete
- visibility replacement: 60.0% resolved complete
- referential replacement: 60.0% resolved complete
- first mention replacement: 60.0% resolved complete
- strict social replacement: 16.67% resolved complete

### Most Commonly Missing Fields

- `owner_bucket`: 30 record(s)
- `repair_kind`: 20 record(s)
- `mutation_classification`: 8 record(s)
- `source_family`: 8 record(s)
