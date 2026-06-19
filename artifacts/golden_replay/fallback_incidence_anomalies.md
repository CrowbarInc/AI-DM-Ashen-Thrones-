# Fallback Incidence Anomalies

> Advisory-only anomaly detection over BP5 fallback incidence history.

## Executive Summary

- Status: `insufficient_history`
- Stability: `insufficient_history + anomaly detection suppressed`
- Highest severity: `none`
- Detected anomalies: 0

## Baseline

- Prior snapshots used: 0
- Minimum required: 5
- Rolling window: 10
- Expected band: mean +/- 2 effective standard deviations.
- Effective deviation floors: trigger/route rate 0.02; count metrics 1.
- Severity: info >=2, watch >=3, warning >=4, critical >=5 effective standard deviations.

| Metric | Mean | Median | Min | Max | Std Dev | Expected Band |
|---|---:|---:|---:|---:|---:|---:|
| _insufficient history_ | - | - | - | - | - | - |

## Current Snapshot

No current snapshot is available.

## Detected Anomalies

`insufficient_history`: anomaly emission is suppressed.

## Severity

`none`

## Recommendations

- Collect at least 5 prior snapshots before interpreting anomaly signals.
