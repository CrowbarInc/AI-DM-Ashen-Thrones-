# Bug-Class Recurrence History

- Generated at: `2026-06-06T00:00:00Z`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py -q --tb=no --basetemp=codex_pytest_tmp_prad_full1`
- Report only: `true`
- Advisory only: `true`
- Total recurrence keys: `2`
- Total recurrence events: `16`

## Regression Recurrence Rate

Regression Recurrence Rate: 50.0% (1 / 2 recurrence keys active by repeated observation). This is advisory/report-only and does not gate protected replay.

- Definition: Share of observed recurrence keys with occurrence_count >= 2 in the measured history window.
- Interpretation: Initial measurable proxy for recurrence keys that became active after prior observation; refine when richer state transitions exist. Advisory and report-only; does not gate protected replay.
- Report only: `true`
- Advisory only: `true`

## Scoped Recurrence Populations

### Protected Replay Recurrence

- Recurrence rate: `50.0%` (1 / 2)
- Health metric: `true`

### Session Diagnostic Recurrence

- Recurrence rate: `100.0%` (6 / 6)
- Health metric: `false`

### Synthetic/Test Artifact Recurrence

- Recurrence rate: `100.0%` (2 / 2)
- Health metric: `false`

### Legacy Unified Recurrence, compatibility only

- Recurrence rate: `87.5%` (7 / 8)
- Health metric: `false`
- Compatibility only: `true`

## Recurrence Trends

- Protected replay only: `true`
- Total protected recurrence keys: `2`
- Emerging keys: `1`
- Recurring keys: `1`
- Persistent keys: `0`
- Dormant keys: `0`
- Growth rate: `50.0%` (1 / 2 keys emerging)
- Regression recurrence rate: `50.0%` (1 / 2)

### Top Recurring Keys

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (count `15`, class `recurring`)

### Newest Recurrence Keys

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (first seen `2026-09-19T16:01:46Z`, class `recurring`)
- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (first seen `2026-06-04T22:31:59Z`, class `emerging`)

## Recurrence Forecast

- Protected replay only: `true`
- Forecast confidence: `high` (`1.00`)
- Stable keys: `0`
- Watch keys: `1`
- Elevated keys: `0`
- Concentrated keys: `1`
- Forecast risk score: `46.3` / 100
- Stability score: `50.0` / 100

### Concentration Metrics

- Top key share: `93.8%`
- Top three key share: `100.0%`
- Concentration ratio (HHI): `0.8828`
- Dominant recurrence key: `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`

### Key Forecasts

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (forecast `watch`, trend `emerging`, share `6.2%`)
- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (forecast `concentrated`, trend `recurring`, share `93.8%`)

## Recurrence Portfolio

- Protected replay only: `true`
- Portfolio risk score: `64.3` / 100
- Largest risk bucket: `field_path` / `selected_speaker_id` (HHI `1.0000`)
- Forecast confidence: `1.00`

### Portfolio Metrics

- Owner concentration ratio: `0.8828`
- Category concentration ratio: `0.8828`
- Field path concentration ratio: `1.0000`
- Scenario concentration ratio: `0.8828`

### Top Owners

- `replay`, keys `1`, obs `15`, share `93.8%`, recurring `1`, elevated `1`
- `projection`, keys `1`, obs `1`, share `6.2%`, recurring `0`, elevated `0`

### Top Categories

- `replay_drift`, keys `1`, obs `15`, share `93.8%`
- `projection`, keys `1`, obs `1`, share `6.2%`

### Top Field Paths

- `selected_speaker_id`, keys `2`, obs `16`, share `100.0%`

### Top Scenarios

- `writer_bridge`, keys `1`, obs `15`, share `93.8%`
- `vocative_override_after_prior_continuity`, keys `1`, obs `1`, share `6.2%`

## Recurrence Remediation Targets

- Protected replay only: `true`
- Highest leverage target: `key` / `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (priority `critical`)
- Estimated portfolio reduction: `90.2`
- Remediation confidence: `1.00`

### Top Keys

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`, priority `critical`, reduction `90.2`, share `93.8%`, trend `recurring`, forecast `concentrated`
- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, priority `low`, reduction `17.1`, share `6.2%`, trend `emerging`, forecast `watch`

### Top Owners

- `replay`, priority `critical`, reduction `90.2`, share `93.8%`, keys `1`
- `projection`, priority `low`, reduction `17.1`, share `6.2%`, keys `1`

### Top Field Paths

- `selected_speaker_id`, priority `critical`, reduction `78.0`, share `100.0%`

### Top Scenarios

- `writer_bridge`, priority `critical`, reduction `90.2`, share `93.8%`
- `vocative_override_after_prior_continuity`, priority `low`, reduction `17.1`, share `6.2%`

## Recurrence ROI

- Protected replay only: `true`
- Highest ROI target: `key` / `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (ROI `100.0`, cost `low`)
- Portfolio ROI score: `100.0`
- Projected stability gain: `45.1`
- Projected risk reduction: `58.0`
- ROI confidence: `1.00`

### Top ROI Targets

- rank `1`, `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`, ROI `100.0`, cost `low`, benefit `90.2`
- rank `2`, `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, ROI `85.9`, cost `trivial`, benefit `17.1`

### Top ROI Owners

- rank `1`, `replay`, ROI `100.0`, cost `low`, benefit `90.2`
- rank `2`, `projection`, ROI `85.9`, cost `trivial`, benefit `17.1`

### Top ROI Field Paths

- rank `1`, `selected_speaker_id`, ROI `100.0`, cost `medium`, benefit `78.0`

### Top ROI Scenarios

- rank `1`, `writer_bridge`, ROI `100.0`, cost `low`, benefit `90.2`
- rank `2`, `vocative_override_after_prior_continuity`, ROI `85.9`, cost `trivial`, benefit `17.1`

## Recurrence Governance

- Protected replay only: `true`
- Governance health score: `36.4`
- Governance confidence: `1.00`
- Watchlist size: `2`
- Prioritized targets: `1`
- Retirement opportunities: `0`

### Watchlist

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `prioritize`, action `prioritize_remediation`, ROI `100.0`, trend `recurring`, forecast `concentrated`
- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `watch`, action `gather_more_history`, ROI `85.9`, trend `emerging`, forecast `watch`

### Prioritized Targets

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `prioritize`, action `prioritize_remediation`, ROI `100.0`, trend `recurring`, forecast `concentrated`

### Retire Candidates

No watchlist entries recorded.

### Owner Accountability

- `speaker_drift`, governed `2`, watch `1`, prioritized `1`, retire `0`
- Highest governance load owner: `speaker_drift`

## Recurrence Lifecycle

- Protected replay only: `true`
- Lifecycle health score: `30.0`
- Closure rate: `0.0%`
- Average age (days): `53.7`
- Advancement rate: `0.50`

### Lifecycle Distribution

- `dormant`: `0`
- `emerging`: `1`
- `persistent`: `0`
- `recurring`: `1`
- `retired`: `0`

### Age Distribution

- Youngest key: `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`
- Oldest key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`
- Average age (days): `53.7`
- Median age (days): `53.7`

### Transition Summary

- Transition count: `1`
- Advancing transitions: `1`
- Retiring transitions: `0`
- Stalled keys: `1`

### Closure Effectiveness

- Active keys: `2`
- Dormant keys: `0`
- Retired keys: `0`
- Closure rate: `0.0%`

## Recurrence Program Effectiveness

- Protected replay only: `true`
- Program effectiveness score: `32.2`
- Effectiveness confidence: `0.90`
- Recurrence reduction rate: `0.0%`
- Forecast accuracy: `100.0%`
- Stability change: `-25.0`

### Governance Effectiveness

- Watchlist conversion rate: `0.0%`
- Investigate conversion rate: `100.0%`
- Prioritize conversion rate: `100.0%`
- Retirement conversion rate: `0.0%`
- Governance effectiveness: `0.50`

### Remediation Effectiveness

- Targeted keys: `2`
- Improved keys: `0`
- Unresolved keys: `2`
- Recurrence reduction rate: `0.0%`

### Forecast Effectiveness

- Forecast accuracy: `100.0%`
- Forecast confidence: `1.00`
- Predicted recurrences: `2`
- Realized recurrences: `2`
- Low confidence: `false`

### Portfolio Trajectory

- Trajectory available: `true`
- Portfolio risk change: `+20.2`
- Concentration change: `+0.0000`
- Governance health change: `-18.8`
- Lifecycle health change: `-15.0`

### Stability Trajectory

- Trajectory available: `true`
- Stability score current: `50.0`
- Stability change: `-25.0`
- Recurrence rate change: `+0.2500`

## Recurrence Maturity Assessment

- Protected replay only: `true`
- Overall maturity score: `68.5`
- Overall maturity level: `Measured`
- Highest dimension: `operational_readiness`
- Lowest dimension: `lifecycle`

### Dimension Scores

- Observability: `83.3`
- Governance: `59.1`
- Forecasting: `73.3`
- Remediation: `49.0`
- Lifecycle: `42.5`
- Operational Readiness: `91.3`

### Dimension Levels

- Observability: `Optimized`
- Governance: `Managed`
- Forecasting: `Measured`
- Remediation: `Managed`
- Lifecycle: `Managed`
- Operational Readiness: `Optimized`

### Capability Gaps

- Lifecycle: current `42.5`, target `80.0`, gap `37.5`
- Remediation: current `49.0`, target `80.0`, gap `31.0`
- Governance: current `59.1`, target `80.0`, gap `20.9`
- Forecasting: current `73.3`, target `80.0`, gap `6.7`
- Observability: current `83.3`, target `80.0`, gap `0.0`
- Operational Readiness: current `91.3`, target `80.0`, gap `0.0`

### Improvement Priorities

- Lifecycle: `high`
- Remediation: `high`
- Governance: `medium`
- Forecasting: `low`
- Observability: `low`
- Operational Readiness: `low`

## Recurrence Strategic Roadmap

- Protected replay only: `true`
- Highest ROI initiative: `data_volume_expansion`
- Largest gap dimension: `lifecycle`
- Estimated remaining initiatives: `3`
- Target maturity state: `Optimized`
- Roadmap priority: `Execute roadmap sequence in dependency order to reach optimized maturity.`

### Priority Initiatives

- Data Volume Expansion: ROI `100.0`, priority `80.2`, complexity `12.0`
- Trajectory Establishment: ROI `30.3`, priority `27.9`, complexity `27.0`
- Lifecycle Closure Tracking: ROI `24.9`, priority `35.8`, complexity `29.0`
- Remediation Feedback Loop: ROI `22.1`, priority `37.8`, complexity `42.0`
- Operationalization: ROI `21.4`, priority `38.1`, complexity `40.0`
- Forecast Validation: ROI `19.6`, priority `26.4`, complexity `38.0`

### Expected Maturity Lift

- Data Volume Expansion: projected overall `78.2` (`Measured`)
- Trajectory Establishment: projected overall `74.8` (`Measured`)
- Lifecycle Closure Tracking: projected overall `76.1` (`Measured`)
- Remediation Feedback Loop: projected overall `78.0` (`Measured`)
- Operationalization: projected overall `75.2` (`Measured`)
- Forecast Validation: projected overall `76.4` (`Measured`)

### Dependency Sequence

- Step `1`: `data_volume_expansion` (dependencies: none, completed: `false`)
- Step `2`: `trajectory_establishment` (dependencies: data_volume_expansion, completed: `true`)
- Step `3`: `forecast_validation` (dependencies: data_volume_expansion, trajectory_establishment, completed: `true`)
- Step `4`: `lifecycle_closure_tracking` (dependencies: trajectory_establishment, completed: `false`)
- Step `5`: `remediation_feedback_loop` (dependencies: forecast_validation, lifecycle_closure_tracking, completed: `false`)
- Step `6`: `operationalization` (dependencies: remediation_feedback_loop, completed: `true`)

### Target State

- All Dimensions Optimized: `false`
- Operational Readiness Optimized: `true`
- Forecast Confidence Target Met: `true`
- Effectiveness Confidence Target Met: `true`
- Trajectory Available: `true`
- Closure Effectiveness Measurable: `true`
- Remediation Effectiveness Measurable: `true`

## Recurrence Program Completion

- Protected replay only: `true`
- Overall completion score: `96.2`
- Completed dimensions: `5`
- Remaining dimensions: `1`
- Estimated completion distance: `3.8`
- Graduation achieved: `false`

### Dimension Completion Status

- Observability: `complete` (score `100.0`)
- Governance: `incomplete` (score `75.0`)
- Forecasting: `complete` (score `100.0`)
- Remediation: `complete` (score `100.0`)
- Lifecycle: `complete` (score `100.0`)
- Operational Readiness: `complete` (score `100.0`)

### Remaining Requirements

- `governance_health_target_met`

### Completion Gaps

- Governance / `governance_health_target_met`: current `36.4`, target `80.0`, gap `43.60`, roadmap `data_volume_expansion`

### Graduation Status

- Program graduated: `false`
- Completion criteria met: `false`

## Recurrence Graduation Audit

- Protected replay only: `true`
- Graduation readiness score: `93.5`
- Readiness level: `Ready for graduation`
- Critical blind spots: `0`
- Critical redundancies: `1`
- Recommended next action: Execute roadmap sequence in dependency order to reach optimized maturity.

### Capability Coverage

- Historical Persistence: implemented `true`, validated `true`, operational `true`, confidence `0.67`
- Trend Analytics: implemented `true`, validated `true`, operational `true`, confidence `0.77`
- Forecasting: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Portfolio Analytics: implemented `true`, validated `true`, operational `true`, confidence `0.97`
- Remediation Targeting: implemented `true`, validated `true`, operational `true`, confidence `0.63`
- ROI Analytics: implemented `true`, validated `true`, operational `true`, confidence `0.62`
- Governance: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Lifecycle Management: implemented `true`, validated `true`, operational `true`, confidence `0.87`
- Effectiveness Measurement: implemented `true`, validated `true`, operational `true`, confidence `0.90`
- Maturity Assessment: implemented `true`, validated `true`, operational `true`, confidence `0.69`
- Strategic Roadmap: implemented `true`, validated `true`, operational `true`, confidence `0.80`
- Completion Tracking: implemented `true`, validated `true`, operational `true`, confidence `0.96`

### Blind Spots

- `recurrence_confidence_decay` (medium): Confidence scores do not decay with stale observations or aging keys.
- `recurrence_auditability` (low): No immutable audit chain links recurrence analytics revisions over time.
- `recurrence_ownership_drift` (medium): Recurrence ownership drift across runs is not tracked as a dedicated longitudinal signal.

### Redundancies

- `maturity_vs_completion_dimensions` (medium): Use maturity scores for capability posture and completion scores for graduation gates; avoid treating both as independent KPIs in operator dashboards.
- `program_effectiveness_vs_overall_maturity` (medium): Program effectiveness measures outcomes; maturity measures capability. Report both but do not average them into a single headline metric.
- `governance_health_vs_governance_effectiveness` (high): Health score reflects posture; effectiveness reflects funnel conversion. Keep both, but label clearly to prevent duplicate escalation triggers.
- `forecast_risk_vs_portfolio_risk` (medium): Portfolio risk already blends forecast risk; prefer portfolio_risk_score for prioritization summaries unless forecast-specific drill-down is required.
- `multiple_confidence_metrics` (low): Expose a single operator-facing readiness confidence only when all component confidences exceed graduation thresholds.

### Graduation Readiness

- Operational capability ratio: `1.00`
- Validated capability ratio: `1.00`
- Average capability confidence: `0.82`
- Program graduated: `false`

## Recurrence Trajectory

- Trajectory available: `true`
- Snapshot count: `34`

### Current Snapshot

- Timestamp: `2026-09-19T23:25:45Z`
- Protected observations: `16`
- Unique recurrence keys: `2`
- Portfolio risk score: `64.3`
- Governance health score: `36.4`
- Operational readiness score: `68.9`
- Effectiveness confidence: `0.78`
- Maturity score: `64.0`

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

- Portfolio risk change: `+20.2`
- Governance health change: `-18.8`
- Lifecycle health change: `-15.0`
- Operational readiness change: `-7.5`
- Effectiveness change: `-0.04`
- Maturity change: `-9.0`

## Confidence Calibration Audit

- Protected replay only: `true`
- Calibration score: `53.0`
- Interpretation: `Needs monitoring`
- Largest calibration gap: `0.70`
- Graduation confidence ready: `false`

### Forecast Calibration

- Reported confidence: `1.00`
- Evidence strength: `0.93`
- Calibration gap: `0.07`
- Status: `calibrated`

### Governance Calibration

- Reported confidence: `1.00`
- Evidence strength: `0.66`
- Calibration gap: `0.34`
- Status: `overconfident`

### Effectiveness Calibration

- Reported confidence: `0.90`
- Evidence strength: `0.20`
- Calibration gap: `0.70`
- Status: `overconfident`

### Graduation Threshold Validation

- `forecast_confidence`: current `1.0`, target `0.75`, status `supported`
- `effectiveness_confidence`: current `0.9`, target `0.75`, status `optimistic`
- `operational_readiness`: current `91.3`, target `80.0`, status `optimistic`
- `trajectory_available`: current `True`, target `True`, status `supported`
- `governance_confidence`: current `1.0`, target `0.75`, status `optimistic`

| Key | Count | Owner | Status | Categories | Field Paths | Affected Scenarios | Investigate First |
|---|---:|---|---|---|---|---|---|
| recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py | 15 | replay | active | replay_drift | selected_speaker_id | writer_bridge | tests/helpers/golden_replay.py |
| recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py | 1 | projection | watch | projection | selected_speaker_id | vocative_override_after_prior_continuity | tests/helpers/golden_replay.py |
