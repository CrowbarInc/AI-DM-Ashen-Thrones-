# Bug-Class Recurrence History

- Generated at: `2026-05-30T00:00:00Z`
- Command: `pytest synthetic`
- Report only: `true`
- Advisory only: `true`
- Total recurrence keys: `4`
- Total recurrence events: `11`

## Regression Recurrence Rate

Regression Recurrence Rate: 25.0% (1 / 4 recurrence keys active by repeated observation). This is advisory/report-only and does not gate protected replay.

- Definition: Share of observed recurrence keys with occurrence_count >= 2 in the measured history window.
- Interpretation: Initial measurable proxy for recurrence keys that became active after prior observation; refine when richer state transitions exist. Advisory and report-only; does not gate protected replay.
- Report only: `true`
- Advisory only: `true`

## Recurrence Trends

- Protected replay only: `true`
- Total protected recurrence keys: `4`
- Emerging keys: `3`
- Recurring keys: `1`
- Persistent keys: `0`
- Dormant keys: `0`
- Growth rate: `75.0%` (3 / 4 keys emerging)
- Regression recurrence rate: `25.0%` (1 / 4)

### Top Recurring Keys

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (count `8`, class `recurring`)

### Newest Recurrence Keys

- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` (first seen `2026-06-20T12:00:00Z`, class `emerging`)
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` (first seen `2026-06-20T12:00:00Z`, class `emerging`)
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py` (first seen `2026-06-20T12:00:00Z`, class `emerging`)
- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (first seen `2026-06-04T22:31:59Z`, class `recurring`)

## Recurrence Forecast

- Protected replay only: `true`
- Forecast confidence: `high` (`1.00`)
- Stable keys: `0`
- Watch keys: `3`
- Elevated keys: `0`
- Concentrated keys: `1`
- Forecast risk score: `34.3` / 100
- Stability score: `75.0` / 100

### Concentration Metrics

- Top key share: `72.7%`
- Top three key share: `90.9%`
- Concentration ratio (HHI): `0.5537`
- Dominant recurrence key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`

### Key Forecasts

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (forecast `concentrated`, trend `recurring`, share `72.7%`)
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py` (forecast `watch`, trend `emerging`, share `9.1%`)
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` (forecast `watch`, trend `emerging`, share `9.1%`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` (forecast `watch`, trend `emerging`, share `9.1%`)

## Recurrence Portfolio

- Protected replay only: `true`
- Portfolio risk score: `44.1` / 100
- Largest risk bucket: `field_path` / `selected_speaker_id` (HHI `0.6860`)
- Forecast confidence: `1.00`

### Portfolio Metrics

- Owner concentration ratio: `0.5537`
- Category concentration ratio: `0.5537`
- Field path concentration ratio: `0.6860`
- Scenario concentration ratio: `0.5537`

### Top Owners

- `projection`, keys `1`, obs `8`, share `72.7%`, recurring `1`, elevated `1`
- `fallback`, keys `1`, obs `1`, share `9.1%`, recurring `0`, elevated `0`
- `sanitizer`, keys `1`, obs `1`, share `9.1%`, recurring `0`, elevated `0`
- `speaker`, keys `1`, obs `1`, share `9.1%`, recurring `0`, elevated `0`

### Top Categories

- `projection`, keys `1`, obs `8`, share `72.7%`
- `fallback`, keys `1`, obs `1`, share `9.1%`
- `sanitizer`, keys `1`, obs `1`, share `9.1%`
- `speaker`, keys `1`, obs `1`, share `9.1%`

### Top Field Paths

- `selected_speaker_id`, keys `2`, obs `9`, share `81.8%`
- `final_emitted_source`, keys `1`, obs `1`, share `9.1%`
- `scaffold_leakage`, keys `1`, obs `1`, share `9.1%`

### Top Scenarios

- `vocative_override_after_prior_continuity`, keys `1`, obs `8`, share `72.7%`
- `directed_npc_question`, keys `1`, obs `1`, share `9.1%`
- `sanitizer_scaffold_leakage`, keys `1`, obs `1`, share `9.1%`
- `wrong_speaker_strict_social_emission`, keys `1`, obs `1`, share `9.1%`

## Recurrence Remediation Targets

- Protected replay only: `true`
- Highest leverage target: `key` / `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (priority `high`)
- Estimated portfolio reduction: `74.2`
- Remediation confidence: `1.00`

### Top Keys

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, priority `high`, reduction `74.2`, share `72.7%`, trend `recurring`, forecast `concentrated`
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, priority `low`, reduction `18.6`, share `9.1%`, trend `emerging`, forecast `watch`
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, priority `low`, reduction `18.6`, share `9.1%`, trend `emerging`, forecast `watch`
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, priority `low`, reduction `18.6`, share `9.1%`, trend `emerging`, forecast `watch`

### Top Owners

- `projection`, priority `high`, reduction `74.2`, share `72.7%`, keys `1`
- `fallback`, priority `low`, reduction `18.6`, share `9.1%`, keys `1`
- `sanitizer`, priority `low`, reduction `18.6`, share `9.1%`, keys `1`
- `speaker`, priority `low`, reduction `18.6`, share `9.1%`, keys `1`

### Top Field Paths

- `selected_speaker_id`, priority `critical`, reduction `79.9`, share `81.8%`
- `final_emitted_source`, priority `low`, reduction `18.6`, share `9.1%`
- `scaffold_leakage`, priority `low`, reduction `18.6`, share `9.1%`

### Top Scenarios

- `vocative_override_after_prior_continuity`, priority `high`, reduction `74.2`, share `72.7%`
- `directed_npc_question`, priority `low`, reduction `18.6`, share `9.1%`
- `sanitizer_scaffold_leakage`, priority `low`, reduction `18.6`, share `9.1%`
- `wrong_speaker_strict_social_emission`, priority `low`, reduction `18.6`, share `9.1%`

## Recurrence ROI

- Protected replay only: `true`
- Highest ROI target: `key` / `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (ROI `100.0`, cost `low`)
- Portfolio ROI score: `100.0`
- Projected stability gain: `18.6`
- Projected risk reduction: `32.7`
- ROI confidence: `1.00`

### Top ROI Targets

- rank `1`, `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, ROI `100.0`, cost `low`, benefit `74.2`
- rank `2`, `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, ROI `66.0`, cost `low`, benefit `18.6`
- rank `3`, `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, ROI `66.0`, cost `low`, benefit `18.6`
- rank `4`, `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, ROI `66.0`, cost `low`, benefit `18.6`

### Top ROI Owners

- rank `1`, `projection`, ROI `100.0`, cost `low`, benefit `74.2`
- rank `2`, `fallback`, ROI `66.0`, cost `low`, benefit `18.6`
- rank `3`, `sanitizer`, ROI `66.0`, cost `low`, benefit `18.6`
- rank `4`, `speaker`, ROI `66.0`, cost `low`, benefit `18.6`

### Top ROI Field Paths

- rank `1`, `selected_speaker_id`, ROI `100.0`, cost `medium`, benefit `79.9`
- rank `2`, `final_emitted_source`, ROI `66.0`, cost `low`, benefit `18.6`
- rank `3`, `scaffold_leakage`, ROI `66.0`, cost `low`, benefit `18.6`

### Top ROI Scenarios

- rank `1`, `vocative_override_after_prior_continuity`, ROI `100.0`, cost `low`, benefit `74.2`
- rank `2`, `directed_npc_question`, ROI `66.0`, cost `low`, benefit `18.6`
- rank `3`, `sanitizer_scaffold_leakage`, ROI `66.0`, cost `low`, benefit `18.6`
- rank `4`, `wrong_speaker_strict_social_emission`, ROI `66.0`, cost `low`, benefit `18.6`

## Recurrence Governance

- Protected replay only: `true`
- Governance health score: `55.2`
- Governance confidence: `1.00`
- Watchlist size: `4`
- Prioritized targets: `1`
- Retirement opportunities: `0`

### Watchlist

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `prioritize`, action `prioritize_remediation`, ROI `100.0`, trend `recurring`, forecast `concentrated`
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, status `watch`, action `gather_more_history`, ROI `66.0`, trend `emerging`, forecast `watch`
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, status `watch`, action `gather_more_history`, ROI `66.0`, trend `emerging`, forecast `watch`
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, status `watch`, action `gather_more_history`, ROI `66.0`, trend `emerging`, forecast `watch`

### Prioritized Targets

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `prioritize`, action `prioritize_remediation`, ROI `100.0`, trend `recurring`, forecast `concentrated`

### Retire Candidates

No watchlist entries recorded.

### Owner Accountability

- `fallback_drift`, governed `1`, watch `1`, prioritized `0`, retire `0`
- `semantic_drift`, governed `1`, watch `1`, prioritized `0`, retire `0`
- `speaker_drift`, governed `2`, watch `1`, prioritized `1`, retire `0`
- Highest governance load owner: `speaker_drift`

## Recurrence Lifecycle

- Protected replay only: `true`
- Lifecycle health score: `45.0`
- Closure rate: `0.0%`
- Average age (days): `3.9`
- Advancement rate: `0.25`

### Lifecycle Distribution

- `dormant`: `0`
- `emerging`: `3`
- `persistent`: `0`
- `recurring`: `1`
- `retired`: `0`

### Age Distribution

- Youngest key: `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`
- Oldest key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`
- Average age (days): `3.9`
- Median age (days): `0.0`

### Transition Summary

- Transition count: `1`
- Advancing transitions: `1`
- Retiring transitions: `0`
- Stalled keys: `0`

### Closure Effectiveness

- Active keys: `4`
- Dormant keys: `0`
- Retired keys: `0`
- Closure rate: `0.0%`

## Recurrence Program Effectiveness

- Protected replay only: `true`
- Program effectiveness score: `41.3`
- Effectiveness confidence: `1.00`
- Recurrence reduction rate: `0.0%`
- Forecast accuracy: `100.0%`
- Stability change: `+0.0`

### Governance Effectiveness

- Watchlist conversion rate: `0.0%`
- Investigate conversion rate: `100.0%`
- Prioritize conversion rate: `100.0%`
- Retirement conversion rate: `0.0%`
- Governance effectiveness: `0.50`

### Remediation Effectiveness

- Targeted keys: `4`
- Improved keys: `0`
- Unresolved keys: `4`
- Recurrence reduction rate: `0.0%`

### Forecast Effectiveness

- Forecast accuracy: `100.0%`
- Forecast confidence: `1.00`
- Predicted recurrences: `4`
- Realized recurrences: `4`
- Low confidence: `false`

### Portfolio Trajectory

- Trajectory available: `true`
- Portfolio risk change: `+0.0`
- Concentration change: `+0.0000`
- Governance health change: `+0.0`
- Lifecycle health change: `+0.0`

### Stability Trajectory

- Trajectory available: `true`
- Stability score current: `75.0`
- Stability change: `+0.0`
- Recurrence rate change: `+0.0000`

## Recurrence Maturity Assessment

- Protected replay only: `true`
- Overall maturity score: `77.8`
- Overall maturity level: `Measured`
- Highest dimension: `forecasting`
- Lowest dimension: `lifecycle`

### Dimension Scores

- Observability: `90.0`
- Governance: `63.8`
- Forecasting: `100.0`
- Remediation: `55.0`
- Lifecycle: `46.2`
- Operational Readiness: `100.0`

### Dimension Levels

- Observability: `Optimized`
- Governance: `Measured`
- Forecasting: `Optimized`
- Remediation: `Managed`
- Lifecycle: `Managed`
- Operational Readiness: `Optimized`

### Capability Gaps

- Lifecycle: current `46.2`, target `80.0`, gap `33.8`
- Remediation: current `55.0`, target `80.0`, gap `25.0`
- Governance: current `63.8`, target `80.0`, gap `16.2`
- Observability: current `90.0`, target `80.0`, gap `0.0`
- Forecasting: current `100.0`, target `80.0`, gap `0.0`
- Operational Readiness: current `100.0`, target `80.0`, gap `0.0`

### Improvement Priorities

- Lifecycle: `high`
- Remediation: `high`
- Governance: `medium`
- Observability: `low`
- Forecasting: `low`
- Operational Readiness: `low`

## Recurrence Strategic Roadmap

- Protected replay only: `true`
- Highest ROI initiative: `data_volume_expansion`
- Largest gap dimension: `lifecycle`
- Estimated remaining initiatives: `2`
- Target maturity state: `Optimized`
- Roadmap priority: `Execute roadmap sequence in dependency order to reach optimized maturity.`

### Priority Initiatives

- Data Volume Expansion: ROI `100.0`, priority `81.3`, complexity `12.0`
- Trajectory Establishment: ROI `33.6`, priority `28.6`, complexity `27.0`
- Lifecycle Closure Tracking: ROI `27.7`, priority `39.3`, complexity `29.0`
- Remediation Feedback Loop: ROI `24.5`, priority `39.2`, complexity `42.0`
- Operationalization: ROI `23.8`, priority `41.0`, complexity `40.0`
- Forecast Validation: ROI `21.8`, priority `26.3`, complexity `38.0`

### Expected Maturity Lift

- Data Volume Expansion: projected overall `82.9` (`Optimized`)
- Trajectory Establishment: projected overall `81.2` (`Optimized`)
- Lifecycle Closure Tracking: projected overall `83.5` (`Optimized`)
- Remediation Feedback Loop: projected overall `84.8` (`Optimized`)
- Operationalization: projected overall `81.8` (`Optimized`)
- Forecast Validation: projected overall `80.2` (`Optimized`)

### Dependency Sequence

- Step `1`: `data_volume_expansion` (dependencies: none, completed: `true`)
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

- Governance / `governance_health_target_met`: current `55.2`, target `80.0`, gap `24.80`, roadmap `data_volume_expansion`

### Graduation Status

- Program graduated: `false`
- Completion criteria met: `false`

## Recurrence Graduation Audit

- Protected replay only: `true`
- Graduation readiness score: `94.7`
- Readiness level: `Ready for graduation`
- Critical blind spots: `0`
- Critical redundancies: `1`
- Recommended next action: Execute roadmap sequence in dependency order to reach optimized maturity.

### Capability Coverage

- Historical Persistence: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Trend Analytics: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Forecasting: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Portfolio Analytics: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Remediation Targeting: implemented `true`, validated `true`, operational `true`, confidence `0.90`
- ROI Analytics: implemented `true`, validated `true`, operational `true`, confidence `0.85`
- Governance: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Lifecycle Management: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Effectiveness Measurement: implemented `true`, validated `true`, operational `true`, confidence `1.00`
- Maturity Assessment: implemented `true`, validated `true`, operational `true`, confidence `0.78`
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
- Average capability confidence: `0.94`
- Program graduated: `false`

## Recurrence Trajectory

- Trajectory available: `true`
- Snapshot count: `2`

### Current Snapshot

- Timestamp: `2026-06-20T20:00:00Z`
- Protected observations: `11`
- Unique recurrence keys: `4`
- Portfolio risk score: `44.1`
- Governance health score: `55.2`
- Operational readiness score: `76.4`
- Effectiveness confidence: `0.82`
- Maturity score: `73.0`

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

- Portfolio risk change: `+0.0`
- Governance health change: `+0.0`
- Lifecycle health change: `+0.0`
- Operational readiness change: `+0.0`
- Effectiveness change: `+0.00`
- Maturity change: `+0.0`

## Confidence Calibration Audit

- Protected replay only: `true`
- Calibration score: `56.0`
- Interpretation: `Needs monitoring`
- Largest calibration gap: `0.80`
- Graduation confidence ready: `false`

### Forecast Calibration

- Reported confidence: `1.00`
- Evidence strength: `1.00`
- Calibration gap: `0.00`
- Status: `calibrated`

### Governance Calibration

- Reported confidence: `1.00`
- Evidence strength: `0.78`
- Calibration gap: `0.22`
- Status: `overconfident`

### Effectiveness Calibration

- Reported confidence: `1.00`
- Evidence strength: `0.20`
- Calibration gap: `0.80`
- Status: `overconfident`

### Graduation Threshold Validation

- `forecast_confidence`: current `1.0`, target `0.75`, status `supported`
- `effectiveness_confidence`: current `1.0`, target `0.75`, status `optimistic`
- `operational_readiness`: current `100.0`, target `80.0`, status `optimistic`
- `trajectory_available`: current `True`, target `True`, status `supported`
- `governance_confidence`: current `1.0`, target `0.75`, status `optimistic`

| Key | Count | Owner | Status | Categories | Field Paths | Affected Scenarios | Investigate First |
|---|---:|---|---|---|---|---|---|
| recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py | 8 | projection | active | projection | selected_speaker_id | vocative_override_after_prior_continuity | tests/helpers/golden_replay.py |
| recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py | 1 | speaker | watch | speaker | selected_speaker_id | wrong_speaker_strict_social_emission | game/speaker_contract_enforcement.py |
| recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py | 1 | fallback | watch | fallback | final_emitted_source | directed_npc_question | game/final_emission_gate.py |
| recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py | 1 | sanitizer | watch | sanitizer | scaffold_leakage | sanitizer_scaffold_leakage | game/output_sanitizer.py |
