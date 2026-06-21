# Fallback Incidence Anomalies

> Advisory-only anomaly detection over BP5 fallback incidence history.

## Executive Summary

- Status: `insufficient_history`
- Stability: `stable + anomaly detection suppressed`
- Highest severity: `none`
- Detected anomalies: 0

## Baseline

- Prior snapshots used: 1
- Minimum required: 5
- Rolling window: 10
- Expected band: mean +/- 2 effective standard deviations.
- Effective deviation floors: trigger/route rate 0.02; count metrics 1.
- Severity: info >=2, watch >=3, warning >=4, critical >=5 effective standard deviations.

| Metric | Mean | Median | Min | Max | Std Dev | Expected Band |
|---|---:|---:|---:|---:|---:|---:|
| _insufficient history_ | - | - | - | - | - | - |

## Current Snapshot

- Timestamp: `2026-06-21T11:37:14.736308Z`
- Fallback trigger rate: 0.6916
- Fallback turns: 74
- Fallback events: 74

## Detected Anomalies

`insufficient_history`: anomaly emission is suppressed.

## Severity

`none`

## Recommendations

- Collect at least 5 prior snapshots before interpreting anomaly signals.
