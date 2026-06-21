# BQ-C3 Confidence Calibration Audit

**Date:** 2026-06-12T00:00:00Z
**Protected replay only:** true

## Summary

- Calibration score: `66.0`
- Interpretation: `Needs monitoring`
- Largest calibration gap: `0.47`
- Graduation confidence ready: `false`

# Forecast Confidence

- Reported confidence: `0.00`
- Evidence strength: `0.10`
- Calibration gap: `-0.10`
- Status: `calibrated`
- Forecast accuracy: `0.00`
- Observations: `0`
- Keys: `0`
- Trajectory available: `false`

# Governance Confidence

- Reported confidence: `0.00`
- Evidence strength: `0.45`
- Calibration gap: `-0.45`
- Status: `underconfident`
- Watchlist size: `0`
- Governance health: `100.0`

# Effectiveness Confidence

- Reported confidence: `0.00`
- Evidence strength: `0.47`
- Calibration gap: `-0.47`
- Status: `underconfident`
- Trajectory available: `false`
- Remediation effectiveness: `0.50`
- Closure rate: `0.00`

# Graduation Threshold Validation

- `forecast_confidence`: current `0.0`, target `0.75`, status `unsupported` — Forecast confidence remains below graduation threshold.
- `effectiveness_confidence`: current `0.0`, target `0.75`, status `unsupported` — Effectiveness confidence remains below graduation threshold.
- `operational_readiness`: current `0.0`, target `80.0`, status `unsupported` — Operational readiness remains materially below graduation threshold.
- `trajectory_available`: current `False`, target `True`, status `optimistic` — Trajectory baseline exists but trajectory_available remains false until snapshot #2 is captured.
- `governance_confidence`: current `0.0`, target `0.75`, status `unsupported` — Governance confidence remains below graduation threshold.

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
