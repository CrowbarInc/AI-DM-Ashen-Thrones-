# BS4 Producer Stamp Report

> Producer-side attribution stamps (repair_kind, owner_bucket) compared against BS1 baseline and BS5 projection convergence.

## Summary

| Metric | BS1 | BS5 | BS4 | BS4 vs BS1 | BS4 vs BS5 |
|---|---:|---:|---:|---:|---:|
| Strict completeness % | 0.0 | 0.0 | 0.0 | +0.0 | +0.0 |
| Resolved completeness % | 5.36 | 85.71 | 85.71 | +80.35 | +0.0 |
| Strict complete records | 0 | 0 | 0 | +0 | +0 |
| Resolved complete records | 3 | 48 | 48 | +45 | +0 |

## Field-Level Missing Slots

| Field | BS1 missing | BS5 missing | BS4 missing | BS4 vs BS1 | BS4 vs BS5 |
|---|---:|---:|---:|---:|---:|
| `owner_bucket` | 44 | 0 | 0 | +44 | +0 |
| `source_family` | 8 | 0 | 0 | +8 | +0 |
| `repair_kind` | 45 | 0 | 0 | +45 | +0 |
| `recurrence_key` | 5 | 0 | 0 | +5 | +0 |
| `mutation_classification` | 16 | 8 | 8 | +8 | +0 |

## Path-Level Resolved Complete

| Replacement path | BS1 | BS5 | BS4 | BS4 vs BS1 | BS4 vs BS5 |
|---|---:|---:|---:|---:|---:|
| visibility replacement | 4 | 4 | 4 | +0 | +0 |
| first mention replacement | 4 | 4 | 4 | +0 | +0 |
| referential replacement | 4 | 4 | 4 | +0 | +0 |
| sealed replacement | 0 | 0 | 4 | +4 | +4 |
| response type replacement | 5 | 5 | 5 | +0 | +0 |
| sanitizer replacement | 9 | 9 | 9 | +0 | +0 |
| repair mutation | 0 | 0 | 7 | +7 | +7 |
| opening fallback | 6 | 6 | 6 | +0 | +0 |
| strict social replacement | 5 | 5 | 5 | +0 | +0 |
