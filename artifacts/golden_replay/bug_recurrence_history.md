# Bug-Class Recurrence History

- Generated at: `2026-06-28T19:49:24Z`
- Command: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\.venv\Lib\site-packages\pytest\__main__.py tests/test_migrate_bug_recurrence_event_log.py tests/test_failure_dashboard_recurrence.py tests/test_failure_dashboard_paths.py tests/test_replay_bug_class_recurrence.py -q --tb=short`
- Report only: `true`
- Advisory only: `true`
- Total recurrence keys: `1`
- Total recurrence events: `1`

## Regression Recurrence Rate

Regression Recurrence Rate: 0.0% (0 / 1 recurrence keys active by repeated observation). This is advisory/report-only and does not gate protected replay.

- Definition: Share of observed recurrence keys with occurrence_count >= 2 in the measured history window.
- Interpretation: Initial measurable proxy for recurrence keys that became active after prior observation; refine when richer state transitions exist. Advisory and report-only; does not gate protected replay.
- Report only: `true`
- Advisory only: `true`

## Scoped Recurrence Populations

### Protected Replay Recurrence

- Recurrence rate: `0.0%` (0 / 1)
- Health metric: `true`

### Session Diagnostic Recurrence

- Recurrence rate: `100.0%` (6 / 6)
- Health metric: `false`

### Synthetic/Test Artifact Recurrence

- Recurrence rate: `100.0%` (1 / 1)
- Health metric: `false`

### Legacy Unified Recurrence, compatibility only

- Recurrence rate: `85.7%` (6 / 7)
- Health metric: `false`
- Compatibility only: `true`

## Recurrence Trends

- Protected replay only: `true`
- Total protected recurrence keys: `1`
- Emerging keys: `1`
- Recurring keys: `0`
- Persistent keys: `0`
- Dormant keys: `0`
- Growth rate: `100.0%` (1 / 1 keys emerging)
- Regression recurrence rate: `0.0%` (0 / 1)

### Top Recurring Keys

No recurring protected keys yet.

### Newest Recurrence Keys

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (first seen `2026-06-04T22:31:59Z`, class `emerging`)

## Recurrence Forecast

- Protected replay only: `true`
- Forecast confidence: `low` (`0.20`)
- Stable keys: `0`
- Watch keys: `1`
- Elevated keys: `0`
- Concentrated keys: `0`
- Forecast risk score: `30.0` / 100
- Stability score: `100.0` / 100

### Concentration Metrics

- Top key share: `100.0%`
- Top three key share: `100.0%`
- Concentration ratio (HHI): `1.0000`
- Dominant recurrence key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`

### Key Forecasts

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (forecast `watch`, trend `emerging`, share `100.0%`)

## Recurrence Portfolio

- Protected replay only: `true`
- Portfolio risk score: `58.0` / 100
- Largest risk bucket: `owner` / `projection` (HHI `1.0000`)
- Forecast confidence: `0.20`

### Portfolio Metrics

- Owner concentration ratio: `1.0000`
- Category concentration ratio: `1.0000`
- Field path concentration ratio: `1.0000`
- Scenario concentration ratio: `1.0000`

### Top Owners

- `projection`, keys `1`, obs `1`, share `100.0%`, recurring `0`, elevated `0`

### Top Categories

- `projection`, keys `1`, obs `1`, share `100.0%`

### Top Field Paths

- `selected_speaker_id`, keys `1`, obs `1`, share `100.0%`

### Top Scenarios

- `vocative_override_after_prior_continuity`, keys `1`, obs `1`, share `100.0%`

## Recurrence Remediation Targets

- Protected replay only: `true`
- Highest leverage target: `key` / `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (priority `critical`)
- Estimated portfolio reduction: `3.1`
- Remediation confidence: `0.04`

### Top Keys

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, priority `critical`, reduction `78.0`, share `100.0%`, trend `emerging`, forecast `watch`

### Top Owners

- `projection`, priority `critical`, reduction `78.0`, share `100.0%`, keys `1`

### Top Field Paths

- `selected_speaker_id`, priority `critical`, reduction `78.0`, share `100.0%`

### Top Scenarios

- `vocative_override_after_prior_continuity`, priority `critical`, reduction `78.0`, share `100.0%`

## Recurrence ROI

- Protected replay only: `true`
- Highest ROI target: `key` / `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (ROI `10.5`, cost `low`)
- Portfolio ROI score: `10.5`
- Projected stability gain: `0.0`
- Projected risk reduction: `1.8`
- ROI confidence: `0.14`

### Top ROI Targets

- rank `1`, `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, ROI `10.5`, cost `low`, benefit `3.1`

### Top ROI Owners

- rank `1`, `projection`, ROI `10.5`, cost `low`, benefit `3.1`

### Top ROI Field Paths

- rank `1`, `selected_speaker_id`, ROI `10.5`, cost `low`, benefit `3.1`

### Top ROI Scenarios

- rank `1`, `vocative_override_after_prior_continuity`, ROI `10.5`, cost `low`, benefit `3.1`

## Recurrence Governance

- Protected replay only: `true`
- Governance health score: `65.5`
- Governance confidence: `0.18`
- Watchlist size: `1`
- Prioritized targets: `0`
- Retirement opportunities: `0`

### Watchlist

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `watch`, action `gather_more_history`, ROI `10.5`, trend `emerging`, forecast `watch`

### Prioritized Targets

No watchlist entries recorded.

### Retire Candidates

No watchlist entries recorded.

### Owner Accountability

- `speaker_drift`, governed `1`, watch `1`, prioritized `0`, retire `0`
- Highest governance load owner: `speaker_drift`

## Recurrence Lifecycle

- Protected replay only: `true`
- Lifecycle health score: `60.0`
- Closure rate: `0.0%`
- Average age (days): `0.0`
- Advancement rate: `0.00`

### Lifecycle Distribution

- `dormant`: `0`
- `emerging`: `1`
- `persistent`: `0`
- `recurring`: `0`
- `retired`: `0`

### Age Distribution

- Youngest key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`
- Oldest key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`
- Average age (days): `0.0`
- Median age (days): `0.0`

### Transition Summary

- Transition count: `0`
- Advancing transitions: `0`
- Retiring transitions: `0`
- Stalled keys: `0`

### Closure Effectiveness

- Active keys: `1`
- Dormant keys: `0`
- Retired keys: `0`
- Closure rate: `0.0%`

## Recurrence Program Effectiveness

- Protected replay only: `true`
- Program effectiveness score: `38.4`
- Effectiveness confidence: `0.15`
- Recurrence reduction rate: `0.0%`
- Forecast accuracy: `100.0%`
- Stability change: `+25.0`

### Governance Effectiveness

- Watchlist conversion rate: `0.0%`
- Investigate conversion rate: `0.0%`
- Prioritize conversion rate: `0.0%`
- Retirement conversion rate: `0.0%`
- Governance effectiveness: `0.00`

### Remediation Effectiveness

- Targeted keys: `1`
- Improved keys: `0`
- Unresolved keys: `1`
- Recurrence reduction rate: `0.0%`

### Forecast Effectiveness

- Forecast accuracy: `100.0%`
- Forecast confidence: `0.20`
- Predicted recurrences: `1`
- Realized recurrences: `1`
- Low confidence: `true`

### Portfolio Trajectory

- Trajectory available: `true`
- Portfolio risk change: `+13.9`
- Concentration change: `+0.0000`
- Governance health change: `+10.3`
- Lifecycle health change: `+15.0`

### Stability Trajectory

- Trajectory available: `true`
- Stability score current: `100.0`
- Stability change: `+25.0`
- Recurrence rate change: `-0.2500`

## Recurrence Maturity Assessment

- Protected replay only: `true`
- Overall maturity score: `42.6`
- Overall maturity level: `Managed`
- Highest dimension: `observability`
- Lowest dimension: `forecasting`

### Dimension Scores

- Observability: `71.3`
- Governance: `50.0`
- Forecasting: `22.5`
- Remediation: `23.8`
- Lifecycle: `50.0`
- Operational Readiness: `31.9`

### Dimension Levels

- Observability: `Measured`
- Governance: `Managed`
- Forecasting: `Developing`
- Remediation: `Developing`
- Lifecycle: `Managed`
- Operational Readiness: `Developing`

### Capability Gaps

- Forecasting: current `22.5`, target `80.0`, gap `57.5`
- Remediation: current `23.8`, target `80.0`, gap `56.2`
- Operational Readiness: current `31.9`, target `80.0`, gap `48.1`
- Governance: current `50.0`, target `80.0`, gap `30.0`
- Lifecycle: current `50.0`, target `80.0`, gap `30.0`
- Observability: current `71.3`, target `80.0`, gap `8.7`

### Improvement Priorities

- Forecasting: `critical`
- Remediation: `critical`
- Operational Readiness: `critical`
- Governance: `high`
- Lifecycle: `high`
- Observability: `low`

## Recurrence Strategic Roadmap

- Protected replay only: `true`
- Highest ROI initiative: `data_volume_expansion`
- Largest gap dimension: `forecasting`
- Estimated remaining initiatives: `5`
- Target maturity state: `Optimized`
- Roadmap priority: `Collect more protected replay observations before optimizing models.`

### Priority Initiatives

- Data Volume Expansion: ROI `100.0`, priority `79.2`, complexity `12.0`
- Trajectory Establishment: ROI `25.7`, priority `25.6`, complexity `27.0`
- Lifecycle Closure Tracking: ROI `21.1`, priority `18.6`, complexity `29.0`
- Remediation Feedback Loop: ROI `18.7`, priority `19.5`, complexity `42.0`
- Operationalization: ROI `18.1`, priority `22.9`, complexity `40.0`
- Forecast Validation: ROI `16.6`, priority `16.8`, complexity `38.0`

### Expected Maturity Lift

- Data Volume Expansion: projected overall `57.5` (`Managed`)
- Trajectory Establishment: projected overall `51.2` (`Managed`)
- Lifecycle Closure Tracking: projected overall `50.2` (`Managed`)
- Remediation Feedback Loop: projected overall `52.3` (`Managed`)
- Operationalization: projected overall `51.6` (`Managed`)
- Forecast Validation: projected overall `50.4` (`Managed`)

### Dependency Sequence

- Step `1`: `data_volume_expansion` (dependencies: none, completed: `false`)
- Step `2`: `trajectory_establishment` (dependencies: data_volume_expansion, completed: `true`)
- Step `3`: `forecast_validation` (dependencies: data_volume_expansion, trajectory_establishment, completed: `false`)
- Step `4`: `lifecycle_closure_tracking` (dependencies: trajectory_establishment, completed: `false`)
- Step `5`: `remediation_feedback_loop` (dependencies: forecast_validation, lifecycle_closure_tracking, completed: `false`)
- Step `6`: `operationalization` (dependencies: remediation_feedback_loop, completed: `false`)

### Target State

- All Dimensions Optimized: `false`
- Operational Readiness Optimized: `false`
- Forecast Confidence Target Met: `false`
- Effectiveness Confidence Target Met: `false`
- Trajectory Available: `true`
- Closure Effectiveness Measurable: `true`
- Remediation Effectiveness Measurable: `true`

## Recurrence Program Completion

- Protected replay only: `true`
- Overall completion score: `77.5`
- Completed dimensions: `3`
- Remaining dimensions: `3`
- Estimated completion distance: `22.5`
- Graduation achieved: `false`

### Dimension Completion Status

- Observability: `complete` (score `100.0`)
- Governance: `incomplete` (score `75.0`)
- Forecasting: `incomplete` (score `75.0`)
- Remediation: `complete` (score `100.0`)
- Lifecycle: `complete` (score `100.0`)
- Operational Readiness: `incomplete` (score `25.0`)

### Remaining Requirements

- `governance_health_target_met`
- `forecast_confidence_target_met`
- `operational_readiness_target_met`
- `effectiveness_confidence_target_met`
- `governance_confidence_target_met`

### Completion Gaps

- Operational Readiness / `operational_readiness_target_met`: current `31.9`, target `80.0`, gap `48.10`, roadmap `operationalization`
- Governance / `governance_health_target_met`: current `65.5`, target `80.0`, gap `14.50`, roadmap `data_volume_expansion`
- Operational Readiness / `effectiveness_confidence_target_met`: current `0.15`, target `0.75`, gap `0.60`, roadmap `operationalization`
- Operational Readiness / `governance_confidence_target_met`: current `0.18`, target `0.75`, gap `0.57`, roadmap `data_volume_expansion`
- Forecasting / `forecast_confidence_target_met`: current `0.2`, target `0.75`, gap `0.55`, roadmap `forecast_validation`

### Graduation Status

- Program graduated: `false`
- Completion criteria met: `false`

## Recurrence Graduation Audit

- Protected replay only: `true`
- Graduation readiness score: `66.8`
- Readiness level: `Moderate gaps remain`
- Critical blind spots: `1`
- Critical redundancies: `1`
- Recommended next action: Collect more protected replay observations before optimizing models.

### Capability Coverage

- Historical Persistence: implemented `true`, validated `true`, operational `false`, confidence `0.07`
- Trend Analytics: implemented `true`, validated `true`, operational `true`, confidence `0.17`
- Forecasting: implemented `true`, validated `true`, operational `true`, confidence `0.20`
- Portfolio Analytics: implemented `true`, validated `true`, operational `false`, confidence `0.13`
- Remediation Targeting: implemented `true`, validated `true`, operational `true`, confidence `0.15`
- ROI Analytics: implemented `true`, validated `true`, operational `true`, confidence `0.20`
- Governance: implemented `true`, validated `true`, operational `true`, confidence `0.18`
- Lifecycle Management: implemented `true`, validated `true`, operational `true`, confidence `0.27`
- Effectiveness Measurement: implemented `true`, validated `true`, operational `true`, confidence `0.15`
- Maturity Assessment: implemented `true`, validated `true`, operational `true`, confidence `0.43`
- Strategic Roadmap: implemented `true`, validated `true`, operational `true`, confidence `0.80`
- Completion Tracking: implemented `true`, validated `true`, operational `true`, confidence `0.78`

### Blind Spots

- `recurrence_data_quality` (critical): Protected replay observation and key volume remain below maturity confidence thresholds.
- `recurrence_confidence_decay` (medium): Confidence scores do not decay with stale observations or aging keys.
- `recurrence_auditability` (low): No immutable audit chain links recurrence analytics revisions over time.
- `recurrence_model_calibration` (high): High forecast accuracy coexists with low forecast confidence, risking over-interpretation.
- `recurrence_ownership_drift` (medium): Recurrence ownership drift across runs is not tracked as a dedicated longitudinal signal.

### Redundancies

- `maturity_vs_completion_dimensions` (medium): Use maturity scores for capability posture and completion scores for graduation gates; avoid treating both as independent KPIs in operator dashboards.
- `program_effectiveness_vs_overall_maturity` (medium): Program effectiveness measures outcomes; maturity measures capability. Report both but do not average them into a single headline metric.
- `governance_health_vs_governance_effectiveness` (high): Health score reflects posture; effectiveness reflects funnel conversion. Keep both, but label clearly to prevent duplicate escalation triggers.
- `forecast_risk_vs_portfolio_risk` (medium): Portfolio risk already blends forecast risk; prefer portfolio_risk_score for prioritization summaries unless forecast-specific drill-down is required.
- `multiple_confidence_metrics` (low): Expose a single operator-facing readiness confidence only when all component confidences exceed graduation thresholds.

### Graduation Readiness

- Operational capability ratio: `0.83`
- Validated capability ratio: `1.00`
- Average capability confidence: `0.29`
- Program graduated: `false`

## Recurrence Trajectory

- Trajectory available: `true`
- Snapshot count: `19`

### Current Snapshot

- Timestamp: `2026-06-28T19:35:14Z`
- Protected observations: `1`
- Unique recurrence keys: `1`
- Portfolio risk score: `58.0`
- Governance health score: `65.5`
- Operational readiness score: `11.7`
- Effectiveness confidence: `0.14`
- Maturity score: `36.2`

### Baseline Snapshot

- Timestamp: `2026-06-20T12:00:00Z`
- Protected observations: `11`
- Unique recurrence keys: `4`
- Portfolio risk score: `44.1`
- Governance health score: `55.2`
- Operational readiness score: `76.4`
- Effectiveness confidence: `0.82`
- Maturity score: `73.0`

### Trajectory Availability

Trajectory change detection active across baseline and current snapshots.

### Trajectory Changes

- Portfolio risk change: `+13.9`
- Governance health change: `+10.3`
- Lifecycle health change: `+15.0`
- Operational readiness change: `-64.7`
- Effectiveness change: `-0.68`
- Maturity change: `-36.8`

## Confidence Calibration Audit

- Protected replay only: `true`
- Calibration score: `64.3`
- Interpretation: `Needs monitoring`
- Largest calibration gap: `0.55`
- Graduation confidence ready: `false`

### Forecast Calibration

- Reported confidence: `0.20`
- Evidence strength: `0.43`
- Calibration gap: `-0.23`
- Status: `underconfident`

### Governance Calibration

- Reported confidence: `0.18`
- Evidence strength: `0.47`
- Calibration gap: `-0.29`
- Status: `underconfident`

### Effectiveness Calibration

- Reported confidence: `0.15`
- Evidence strength: `0.70`
- Calibration gap: `-0.55`
- Status: `underconfident`

### Graduation Threshold Validation

- `forecast_confidence`: current `0.2`, target `0.75`, status `unsupported`
- `effectiveness_confidence`: current `0.15`, target `0.75`, status `unsupported`
- `operational_readiness`: current `31.9`, target `80.0`, status `unsupported`
- `trajectory_available`: current `True`, target `True`, status `supported`
- `governance_confidence`: current `0.18`, target `0.75`, status `unsupported`

| Key | Count | Owner | Status | Categories | Field Paths | Affected Scenarios | Investigate First |
|---|---:|---|---|---|---|---|---|
| recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py | 1 | projection | watch | projection | selected_speaker_id | vocative_override_after_prior_continuity | tests/helpers/golden_replay.py |
