# Bug-Fix Locality Regression Guard Report

> BRL2 repository guard — validates locality economics against recorded BRL1 baselines.

## Status: **PASS**

## Guarded Metrics

| Metric | Baseline | Threshold | Current | Delta | Result |
|---|---:|---:|---:|---:|---|
| `bug_fix_median_files_touched` | 9.0 | 9.0 | 9.0 | +0.0 | PASS |
| `refactor_median_files_touched` | 16.0 | 16.0 | 16.0 | +0.0 | PASS |
| `bug_fix_maintenance_top5_share_pct` | 3.98 | 3.98 | 3.98 | +0.0 | PASS |
| `bug_fix_maintenance_top_file_share_pct` | 1.02 | 1.02 | 1.02 | +0.0 | PASS |
| `bug_fix_hotspot_top_cluster_share_pct` | 13.85 | 13.85 | 13.85 | +0.0 | PASS |

## Threshold Configuration

- Bug-fix median files touched ceiling: **9.0**
- Refactor median files touched ceiling: **16.0**
- Bug-fix maintenance top-5 share ceiling: **3.98%**
- Bug-fix maintenance top-file share ceiling: **1.02%**
- Bug-fix hotspot top-cluster share ceiling: **13.85%**

## Current Snapshot

- Bug-fix median files touched: **9.0**
- Refactor median files touched: **16.0**
- Bug-fix maintenance top-5 share: **3.98%**
- Bug-fix maintenance top-file share: **1.02%**
- Bug-fix hotspot top cluster: **`data/session.json`** (13.85%)

_Recorded baseline bug-fix median: 9.0 files._

## Regression Warnings

- _none_
