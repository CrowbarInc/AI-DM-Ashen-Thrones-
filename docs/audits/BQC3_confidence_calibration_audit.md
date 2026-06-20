# BQ-C3 Confidence Calibration Audit

**Date:** 2026-06-20T18:10:17Z
**Protected replay only:** true

## Summary

- Calibration score: `84.0`
- Interpretation: `Acceptable`
- Largest calibration gap: `0.29`
- Graduation confidence ready: `false`

# Forecast Confidence

- Reported confidence: `0.20`
- Evidence strength: `0.28`
- Calibration gap: `-0.08`
- Status: `calibrated`
- Forecast accuracy: `1.00`
- Observations: `1`
- Keys: `1`
- Trajectory available: `false`

# Governance Confidence

- Reported confidence: `0.18`
- Evidence strength: `0.47`
- Calibration gap: `-0.29`
- Status: `underconfident`
- Watchlist size: `1`
- Governance health: `65.5`

# Effectiveness Confidence

- Reported confidence: `0.14`
- Evidence strength: `0.25`
- Calibration gap: `-0.11`
- Status: `underconfident`
- Trajectory available: `false`
- Remediation effectiveness: `0.00`
- Closure rate: `0.00`

# Graduation Threshold Validation

- `forecast_confidence`: current `0.2`, target `0.75`, status `unsupported` — Forecast confidence remains below graduation threshold.
- `effectiveness_confidence`: current `0.14`, target `0.75`, status `unsupported` — Effectiveness confidence remains below graduation threshold.
- `operational_readiness`: current `11.7`, target `80.0`, status `unsupported` — Operational readiness remains materially below graduation threshold.
- `trajectory_available`: current `False`, target `True`, status `optimistic` — Trajectory baseline exists but trajectory_available remains false until snapshot #2 is captured.
- `governance_confidence`: current `0.18`, target `0.75`, status `unsupported` — Governance confidence remains below graduation threshold.

# Blind Spot Reassessment

- **recurrence_data_quality** (BQ16 `critical`, now `critical`): `unchanged` — Protected replay volume remains below maturity confidence thresholds.
- **recurrence_trajectory_history** (BQ16 `critical`, now `high`): `partially_reduced` — Trajectory infrastructure and baseline snapshot exist; trajectory_available remains false until snapshot #2.
- **recurrence_model_calibration** (BQ16 `high`, now `low`): `reduced` — Forecast confidence aligns with evidence strength.
- **recurrence_ownership_drift** (BQ16 `medium`, now `medium`): `unchanged` — Recurrence ownership drift is still not tracked as a dedicated longitudinal signal.
- **recurrence_confidence_decay** (BQ16 `medium`, now `medium`): `unchanged` — Confidence scores still do not decay with stale observations or aging keys.
- **recurrence_auditability** (BQ16 `low`, now `low`): `partially_reduced` — Trajectory history artifacts provide versioned snapshots, but no immutable audit chain exists.

# Recommended Actions

1. Capture snapshot #2 to activate trajectory_available before final graduation audit.
2. Resolve unsupported graduation thresholds before closing the BQ recurrence program.
3. Continue protected replay observation collection.
4. Monitor owner_drift_bucket transitions separately from recurrence lifecycle.
5. Consider temporal decay modeling if history spans long idle periods.
