# Structural Fallback Risk Report

> Advisory-only maintenance risk scoring. Scores do not affect runtime or replay acceptance.

## Executive Summary

- Status: `no_history`
- Snapshots analyzed: 0
- Highest-risk contributor: none
- Source signals: BP5 `insufficient_history`, BP6 `insufficient_history`, BP7 `no_history`.

## Risk Model

Score = frequency contribution (20) + recurrence strength (25) + anomaly participation (15) + anomaly severity (20) + trend direction (20).

- Frequency: within-dimension cumulative incidence share, scaled to 20 points.
- Recurrence: transient 0, recurring 8, persistent 16, dominant 25.
- Anomaly participation: 5 points per matching named anomaly, capped at 15.
- Anomaly severity: none 0, info 4, watch 8, warning 14, critical 20.
- Trend: insufficient/improving 0, stable 5, worsening 20.
- Classes: negligible <10; low <25; moderate <40; elevated <60; high <80; critical >=80.
- Maximum score: 100.0.

## Ranked Hotspots

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| - | _none_ | 0 | - | - | 0.0% | - | 0 | - | - |

## Highest-Risk Kinds

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| - | _none_ | 0 | - | - | 0.0% | - | 0 | - | - |

## Highest-Risk Owners

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| - | _none_ | 0 | - | - | 0.0% | - | 0 | - | - |

## Highest-Risk Routes

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| - | _none_ | 0 | - | - | 0.0% | - | 0 | - | - |

## Highest-Risk Families

| Rank | Risk | Score | Dimension | Contributor | Frequency | Recurrence | Anomalies | Severity | Trend |
|---:|---|---:|---|---|---:|---|---:|---|---|
| - | _none_ | 0 | - | - | 0.0% | - | 0 | - | - |

## Recommendations

- Collect fallback-incidence history before interpreting structural risk.
