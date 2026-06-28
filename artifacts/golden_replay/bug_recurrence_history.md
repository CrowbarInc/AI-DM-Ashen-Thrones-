# Bug-Class Recurrence History

- Generated at: `2026-06-28T22:00:00Z`
- Command: `python tools/capture_recurrence_trajectory_activation.py`
- Report only: `true`
- Advisory only: `true`
- Total recurrence keys: `7`
- Total recurrence events: `19`

## Regression Recurrence Rate

Regression Recurrence Rate: 57.1% (4 / 7 recurrence keys active by repeated observation). This is advisory/report-only and does not gate protected replay.

- Definition: Share of observed recurrence keys with occurrence_count >= 2 in the measured history window.
- Interpretation: Initial measurable proxy for recurrence keys that became active after prior observation; refine when richer state transitions exist. Advisory and report-only; does not gate protected replay.
- Report only: `true`
- Advisory only: `true`

## Recurrence Trends

- Protected replay only: `true`
- Total protected recurrence keys: `7`
- Emerging keys: `3`
- Recurring keys: `4`
- Persistent keys: `0`
- Dormant keys: `0`
- Growth rate: `42.9%` (3 / 7 keys emerging)
- Regression recurrence rate: `57.1%` (4 / 7)

### Top Recurring Keys

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (count `8`, class `recurring`)
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py` (count `4`, class `recurring`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` (count `2`, class `recurring`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py` (count `2`, class `recurring`)

### Newest Recurrence Keys

- `recurrence:v1:fallback_drift\|projection\|fallback_family\|tests/helpers/golden_replay.py` (first seen `2026-06-28T10:45:45Z`, class `emerging`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py` (first seen `2026-06-22T21:39:03Z`, class `recurring`)
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py` (first seen `2026-06-22T21:38:39Z`, class `recurring`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` (first seen `2026-06-20T12:00:00Z`, class `recurring`)
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` (first seen `2026-06-20T12:00:00Z`, class `emerging`)

## Recurrence Forecast

- Protected replay only: `true`
- Forecast confidence: `high` (`1.00`)
- Stable keys: `0`
- Watch keys: `3`
- Elevated keys: `4`
- Concentrated keys: `0`
- Forecast risk score: `48.2` / 100
- Stability score: `42.9` / 100

### Concentration Metrics

- Top key share: `42.1%`
- Top three key share: `73.7%`
- Concentration ratio (HHI): `0.2521`
- Dominant recurrence key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`

### Key Forecasts

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (forecast `elevated`, trend `recurring`, share `42.1%`)
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py` (forecast `watch`, trend `emerging`, share `5.3%`)
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` (forecast `watch`, trend `emerging`, share `5.3%`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` (forecast `elevated`, trend `recurring`, share `10.5%`)
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py` (forecast `elevated`, trend `recurring`, share `21.1%`)

## Recurrence Portfolio

- Protected replay only: `true`
- Portfolio risk score: `45.2` / 100
- Largest risk bucket: `owner` / `projection` (HHI `0.5180`)
- Forecast confidence: `1.00`

### Portfolio Metrics

- Owner concentration ratio: `0.5180`
- Category concentration ratio: `0.5180`
- Field path concentration ratio: `0.3407`
- Scenario concentration ratio: `0.2465`

### Top Owners

- `projection`, keys `3`, obs `13`, share `68.4%`, recurring `2`, elevated `2`
- `speaker`, keys `2`, obs `4`, share `21.1%`, recurring `2`, elevated `2`
- `fallback`, keys `1`, obs `1`, share `5.3%`, recurring `0`, elevated `0`
- `sanitizer`, keys `1`, obs `1`, share `5.3%`, recurring `0`, elevated `0`

### Top Categories

- `projection`, keys `3`, obs `13`, share `68.4%`
- `speaker`, keys `2`, obs `4`, share `21.1%`
- `fallback`, keys `1`, obs `1`, share `5.3%`
- `sanitizer`, keys `1`, obs `1`, share `5.3%`

### Top Field Paths

- `selected_speaker_id`, keys `2`, obs `10`, share `52.6%`
- `response_type_candidate_ok`, keys `1`, obs `4`, share `21.1%`
- `selected_speaker_source`, keys `1`, obs `2`, share `10.5%`
- `fallback_family`, keys `1`, obs `1`, share `5.3%`
- `final_emitted_source`, keys `1`, obs `1`, share `5.3%`

### Top Scenarios

- `vocative_override_after_prior_continuity`, keys `1`, obs `8`, share `42.1%`
- `bx5_guard_ambiguous_multi_guard`, keys `3`, obs `4`, share `21.1%`
- `wrong_speaker_strict_social_emission`, keys `2`, obs `2`, share `10.5%`
- `bx5_guard_canonical_guard_captain`, keys `1`, obs `1`, share `5.3%`
- `bx5_guard_gate_guard_distinct`, keys `1`, obs `1`, share `5.3%`

## Recurrence Remediation Targets

- Protected replay only: `true`
- Highest leverage target: `key` / `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (priority `high`)
- Estimated portfolio reduction: `53.1`
- Remediation confidence: `1.00`

### Top Keys

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, priority `high`, reduction `53.1`, share `42.1%`, trend `recurring`, forecast `elevated`
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py`, priority `medium`, reduction `40.4`, share `21.1%`, trend `recurring`, forecast `elevated`
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, priority `medium`, reduction `34.1`, share `10.5%`, trend `recurring`, forecast `elevated`
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py`, priority `medium`, reduction `34.1`, share `10.5%`, trend `recurring`, forecast `elevated`
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, priority `low`, reduction `16.2`, share `5.3%`, trend `emerging`, forecast `watch`

### Top Owners

- `projection`, priority `high`, reduction `68.9`, share `68.4%`, keys `3`
- `speaker`, priority `medium`, reduction `40.4`, share `21.1%`, keys `2`
- `fallback`, priority `low`, reduction `16.2`, share `5.3%`, keys `1`
- `sanitizer`, priority `low`, reduction `16.2`, share `5.3%`, keys `1`

### Top Field Paths

- `selected_speaker_id`, priority `high`, reduction `59.4`, share `52.6%`
- `response_type_candidate_ok`, priority `medium`, reduction `40.4`, share `21.1%`
- `selected_speaker_source`, priority `medium`, reduction `34.1`, share `10.5%`
- `fallback_family`, priority `low`, reduction `16.2`, share `5.3%`
- `final_emitted_source`, priority `low`, reduction `16.2`, share `5.3%`

### Top Scenarios

- `vocative_override_after_prior_continuity`, priority `high`, reduction `53.1`, share `42.1%`
- `bx5_guard_ambiguous_multi_guard`, priority `medium`, reduction `40.4`, share `21.1%`
- `bx5_guard_canonical_guard_captain`, priority `medium`, reduction `30.9`, share `5.3%`
- `bx5_guard_gate_guard_distinct`, priority `medium`, reduction `30.9`, share `5.3%`
- `bx5_guard_role_alias_guard_captain`, priority `medium`, reduction `30.9`, share `5.3%`

## Recurrence ROI

- Protected replay only: `true`
- Highest ROI target: `key` / `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (ROI `100.0`, cost `medium`)
- Portfolio ROI score: `100.0`
- Projected stability gain: `30.3`
- Projected risk reduction: `24.0`
- ROI confidence: `1.00`

### Top ROI Targets

- rank `1`, `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, ROI `100.0`, cost `medium`, benefit `53.1`
- rank `2`, `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py`, ROI `100.0`, cost `low`, benefit `40.4`
- rank `3`, `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, ROI `98.0`, cost `low`, benefit `34.1`
- rank `4`, `recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py`, ROI `98.0`, cost `low`, benefit `34.1`
- rank `5`, `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, ROI `48.6`, cost `low`, benefit `16.2`

### Top ROI Owners

- rank `1`, `projection`, ROI `100.0`, cost `medium`, benefit `68.9`
- rank `2`, `speaker`, ROI `91.0`, cost `medium`, benefit `40.4`
- rank `3`, `fallback`, ROI `48.6`, cost `low`, benefit `16.2`
- rank `4`, `sanitizer`, ROI `48.6`, cost `low`, benefit `16.2`

### Top ROI Field Paths

- rank `1`, `selected_speaker_id`, ROI `100.0`, cost `medium`, benefit `59.4`
- rank `2`, `response_type_candidate_ok`, ROI `100.0`, cost `low`, benefit `40.4`
- rank `3`, `selected_speaker_source`, ROI `98.0`, cost `low`, benefit `34.1`
- rank `4`, `fallback_family`, ROI `48.6`, cost `low`, benefit `16.2`
- rank `5`, `final_emitted_source`, ROI `48.6`, cost `low`, benefit `16.2`

### Top ROI Scenarios

- rank `1`, `vocative_override_after_prior_continuity`, ROI `100.0`, cost `medium`, benefit `53.1`
- rank `2`, `bx5_guard_canonical_guard_captain`, ROI `92.8`, cost `low`, benefit `30.9`
- rank `3`, `bx5_guard_gate_guard_distinct`, ROI `92.8`, cost `low`, benefit `30.9`
- rank `4`, `bx5_guard_role_alias_guard_captain`, ROI `92.8`, cost `low`, benefit `30.9`
- rank `5`, `bx5_guard_ambiguous_multi_guard`, ROI `89.8`, cost `medium`, benefit `40.4`

## Recurrence Governance

- Protected replay only: `true`
- Governance health score: `45.9`
- Governance confidence: `1.00`
- Watchlist size: `7`
- Prioritized targets: `0`
- Retirement opportunities: `2`

### Watchlist

- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, status `investigate`, action `investigate_root_cause`, ROI `98.0`, trend `recurring`, forecast `elevated`
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py`, status `investigate`, action `investigate_root_cause`, ROI `98.0`, trend `recurring`, forecast `elevated`
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, status `watch`, action `gather_more_history`, ROI `48.6`, trend `emerging`, forecast `watch`
- `recurrence:v1:fallback_drift\|projection\|fallback_family\|tests/helpers/golden_replay.py`, status `watch`, action `gather_more_history`, ROI `48.6`, trend `emerging`, forecast `watch`
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, status `watch`, action `gather_more_history`, ROI `48.6`, trend `emerging`, forecast `watch`

### Prioritized Targets

No watchlist entries recorded.

### Retire Candidates

- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py`, status `retire_candidate`, action `retire_tracking`, ROI `100.0`, trend `recurring`, forecast `elevated`
- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `retire_candidate`, action `retire_tracking`, ROI `100.0`, trend `recurring`, forecast `elevated`

### Owner Accountability

- `emission_drift`, governed `1`, watch `0`, prioritized `0`, retire `1`
- `fallback_drift`, governed `2`, watch `2`, prioritized `0`, retire `0`
- `semantic_drift`, governed `1`, watch `1`, prioritized `0`, retire `0`
- `speaker_drift`, governed `3`, watch `0`, prioritized `0`, retire `1`
- Highest governance load owner: `fallback_drift`

## Recurrence Lifecycle

- Protected replay only: `true`
- Lifecycle health score: `35.7`
- Closure rate: `28.6%`
- Average age (days): `8.3`
- Advancement rate: `0.57`

### Lifecycle Distribution

- `dormant`: `0`
- `emerging`: `3`
- `persistent`: `0`
- `recurring`: `2`
- `retired`: `2`

### Age Distribution

- Youngest key: `recurrence:v1:fallback_drift\|projection\|fallback_family\|tests/helpers/golden_replay.py`
- Oldest key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`
- Average age (days): `8.3`
- Median age (days): `7.9`

### Transition Summary

- Transition count: `8`
- Advancing transitions: `4`
- Retiring transitions: `4`
- Stalled keys: `2`

### Closure Effectiveness

- Active keys: `5`
- Dormant keys: `0`
- Retired keys: `2`
- Closure rate: `28.6%`

## Recurrence Program Effectiveness

- Protected replay only: `true`
- Program effectiveness score: `31.8`
- Effectiveness confidence: `1.00`
- Recurrence reduction rate: `28.6%`
- Forecast accuracy: `71.4%`
- Stability change: `-32.1`

### Governance Effectiveness

- Watchlist conversion rate: `66.7%`
- Investigate conversion rate: `0.0%`
- Prioritize conversion rate: `0.0%`
- Retirement conversion rate: `57.1%`
- Governance effectiveness: `0.31`

### Remediation Effectiveness

- Targeted keys: `7`
- Improved keys: `2`
- Unresolved keys: `5`
- Recurrence reduction rate: `28.6%`

### Forecast Effectiveness

- Forecast accuracy: `71.4%`
- Forecast confidence: `1.00`
- Predicted recurrences: `7`
- Realized recurrences: `5`
- Low confidence: `false`

### Portfolio Trajectory

- Trajectory available: `true`
- Portfolio risk change: `+1.1`
- Concentration change: `+0.0000`
- Governance health change: `-9.3`
- Lifecycle health change: `-9.3`

### Stability Trajectory

- Trajectory available: `true`
- Stability score current: `42.9`
- Stability change: `-32.1`
- Recurrence rate change: `+0.3214`

## Recurrence Maturity Assessment

- Protected replay only: `true`
- Overall maturity score: `79.0`
- Overall maturity level: `Measured`
- Highest dimension: `operational_readiness`
- Lowest dimension: `lifecycle`

### Dimension Scores

- Observability: `90.0`
- Governance: `61.5`
- Forecasting: `98.6`
- Remediation: `69.3`
- Lifecycle: `43.9`
- Operational Readiness: `100.0`

### Dimension Levels

- Observability: `Optimized`
- Governance: `Measured`
- Forecasting: `Optimized`
- Remediation: `Measured`
- Lifecycle: `Managed`
- Operational Readiness: `Optimized`

### Capability Gaps

- Lifecycle: current `43.9`, target `80.0`, gap `36.1`
- Governance: current `61.5`, target `80.0`, gap `18.5`
- Remediation: current `69.3`, target `80.0`, gap `10.7`
- Observability: current `90.0`, target `80.0`, gap `0.0`
- Forecasting: current `98.6`, target `80.0`, gap `0.0`
- Operational Readiness: current `100.0`, target `80.0`, gap `0.0`

### Improvement Priorities

- Lifecycle: `high`
- Governance: `medium`
- Remediation: `low`
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

- Data Volume Expansion: ROI `100.0`, priority `81.5`, complexity `12.0`
- Trajectory Establishment: ROI `33.6`, priority `29.7`, complexity `27.0`
- Lifecycle Closure Tracking: ROI `27.7`, priority `41.8`, complexity `29.0`
- Remediation Feedback Loop: ROI `24.5`, priority `34.3`, complexity `42.0`
- Operationalization: ROI `23.8`, priority `42.5`, complexity `40.0`
- Forecast Validation: ROI `21.8`, priority `27.3`, complexity `38.0`

### Expected Maturity Lift

- Data Volume Expansion: projected overall `84.3` (`Optimized`)
- Trajectory Establishment: projected overall `82.6` (`Optimized`)
- Lifecycle Closure Tracking: projected overall `85.0` (`Optimized`)
- Remediation Feedback Loop: projected overall `86.2` (`Optimized`)
- Operationalization: projected overall `83.3` (`Optimized`)
- Forecast Validation: projected overall `81.7` (`Optimized`)

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

- Governance / `governance_health_target_met`: current `45.9`, target `80.0`, gap `34.10`, roadmap `data_volume_expansion`

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
- Maturity Assessment: implemented `true`, validated `true`, operational `true`, confidence `0.79`
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
- Snapshot count: `18`

### Current Snapshot

- Timestamp: `2026-06-28T22:00:00Z`
- Protected observations: `19`
- Unique recurrence keys: `7`
- Portfolio risk score: `45.2`
- Governance health score: `45.9`
- Operational readiness score: `76.4`
- Effectiveness confidence: `0.82`
- Maturity score: `74.3`

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

- Portfolio risk change: `+1.1`
- Governance health change: `-9.3`
- Lifecycle health change: `-9.3`
- Operational readiness change: `+0.0`
- Effectiveness change: `+0.00`
- Maturity change: `+1.3`

## Confidence Calibration Audit

- Protected replay only: `true`
- Calibration score: `66.3`
- Interpretation: `Needs monitoring`
- Largest calibration gap: `0.40`
- Graduation confidence ready: `false`

### Forecast Calibration

- Reported confidence: `1.00`
- Evidence strength: `0.93`
- Calibration gap: `0.07`
- Status: `calibrated`

### Governance Calibration

- Reported confidence: `1.00`
- Evidence strength: `0.76`
- Calibration gap: `0.24`
- Status: `overconfident`

### Effectiveness Calibration

- Reported confidence: `1.00`
- Evidence strength: `0.60`
- Calibration gap: `0.40`
- Status: `overconfident`

### Graduation Threshold Validation

- `forecast_confidence`: current `1.0`, target `0.75`, status `supported`
- `effectiveness_confidence`: current `1.0`, target `0.75`, status `optimistic`
- `operational_readiness`: current `100.0`, target `80.0`, status `optimistic`
- `trajectory_available`: current `True`, target `True`, status `supported`
- `governance_confidence`: current `1.0`, target `0.75`, status `optimistic`

| Key | Count | Owner | Status | Categories | Field Paths | Affected Scenarios | Investigate First |
|---|---:|---|---|---|---|---|---|
| recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py | 8 | projection | retired | projection | selected_speaker_id | vocative_override_after_prior_continuity | tests/helpers/golden_replay.py |
| recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py | 4 | projection | retired | projection | response_type_candidate_ok | bx5_guard_ambiguous_multi_guard, bx5_guard_canonical_guard_captain, bx5_guard_gate_guard_distinct, bx5_guard_role_alias_guard_captain | tests/helpers/golden_replay.py |
| recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py | 2 | speaker | active | speaker | selected_speaker_id | bx5_guard_ambiguous_multi_guard, wrong_speaker_strict_social_emission | game/speaker_contract_enforcement.py |
| recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py | 2 | speaker | active | speaker | selected_speaker_source | bx5_guard_ambiguous_multi_guard | game/speaker_contract_enforcement.py |
| recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py | 1 | fallback | watch | fallback | final_emitted_source | directed_npc_question | game/final_emission_gate.py |
| recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py | 1 | sanitizer | watch | sanitizer | scaffold_leakage | sanitizer_scaffold_leakage | game/output_sanitizer.py |
| recurrence:v1:fallback_drift\|projection\|fallback_family\|tests/helpers/golden_replay.py | 1 | projection | watch | projection | fallback_family | wrong_speaker_strict_social_emission | tests/helpers/golden_replay.py |
