# Attribution Regression Guard Report

> BR2 repository guard — validates attribution completeness and BS3 contract scores against recorded baselines and fixed thresholds.

## Status: **PASS**

## Guarded Metrics

| Metric | Recorded baseline | Threshold | Current | Result |
|---|---:|---:|---:|---|
| `resolved_completeness_pct` | 32.65 | 32.65 | 32.65 | PASS |
| `contract_compliance_score_pct` | 100.0 | 100.0 | 100.0 | PASS |
| `taxonomy_consistency_score_pct` | 100.0 | 100.0 | 100.0 | PASS |
| `strict_completeness_pct` | 0.0 | — | 0.0 | INFO |

## Threshold Configuration

- Contract compliance minimum: **100.0%**
- Taxonomy consistency minimum: **100.0%**
- Resolved completeness minimum: **32.65%** (recorded BR2 baseline)
- Strict completeness: informational only

## Current Snapshot

- Resolved completeness: **32.65%** (16/49)
- Strict completeness: **0.0%** (0/49)
- Contract compliance: **100.0%**
- Taxonomy consistency: **100.0%**

_Recorded baseline resolved completeness: 32.65% (16/49)._

## Regression Warnings

- _none_
