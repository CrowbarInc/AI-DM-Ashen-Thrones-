# BS4 Producer Stamp Report

> Producer-side attribution stamps (repair_kind, owner_bucket) compared against BS1 baseline and BS5 projection convergence.

## Summary

| Metric | BS1 | BS5 | BS4 | BS4 vs BS1 | BS4 vs BS5 |
|---|---:|---:|---:|---:|---:|
| Strict completeness % | 0.0 | 0.0 | 0.0 | +0.0 | +0.0 |
| Resolved completeness % | 5.77 | 10.2 | 32.65 | +26.88 | +22.45 |
| Strict complete records | 0 | 0 | 0 | +0 | +0 |
| Resolved complete records | 3 | 5 | 16 | +13 | +11 |

## Field-Level Missing Slots

| Field | BS1 missing | BS5 missing | BS4 missing | BS4 vs BS1 | BS4 vs BS5 |
|---|---:|---:|---:|---:|---:|
| `owner_bucket` | 43 | 38 | 30 | +13 | +8 |
| `source_family` | 8 | 8 | 8 | +0 | +0 |
| `repair_kind` | 44 | 37 | 20 | +24 | +17 |
| `recurrence_key` | 5 | 0 | 0 | +5 | +0 |
| `mutation_classification` | 16 | 8 | 8 | +8 | +0 |

## Path-Level Resolved Complete

| Replacement path | BS1 | BS5 | BS4 | BS4 vs BS1 | BS4 vs BS5 |
|---|---:|---:|---:|---:|---:|
| visibility replacement | 0 | 0 | 3 | +3 | +3 |
| first mention replacement | 0 | 0 | 3 | +3 | +3 |
| referential replacement | 0 | 0 | 3 | +3 | +3 |
| sealed replacement | 0 | 0 | 0 | +0 | +0 |
| response type replacement | 0 | 0 | 0 | +0 | +0 |
| sanitizer replacement | 0 | 0 | 1 | +1 | +1 |
| repair mutation | 0 | 0 | 0 | +0 | +0 |
| opening fallback | 5 | 5 | 5 | +0 | +0 |
| strict social replacement | 0 | 0 | 1 | +1 | +1 |
