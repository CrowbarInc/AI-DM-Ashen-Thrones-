# Bug-Class Recurrence History

- Generated at: `2026-06-22T21:39:03Z`
- Command: `C:\Users\Master Mandalcio\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pytest\__main__.py tests/test_bx_speaker_identity_end_to_end_parity.py tests/test_bx_speaker_identity_golden_replay.py tests/test_golden_replay.py tests/test_golden_replay_projection.py tests/test_golden_replay_trend.py tests/test_golden_replay_structural_invariants.py tests/test_speaker_contract_risk.py tests/test_social_interaction_authority.py -q --tb=line`
- Report only: `true`
- Advisory only: `true`
- Total recurrence keys: `6`
- Total recurrence events: `17`

## Regression Recurrence Rate

Regression Recurrence Rate: 50.0% (3 / 6 recurrence keys active by repeated observation). This is advisory/report-only and does not gate protected replay.

- Definition: Share of observed recurrence keys with occurrence_count >= 2 in the measured history window.
- Interpretation: Initial measurable proxy for recurrence keys that became active after prior observation; refine when richer state transitions exist. Advisory and report-only; does not gate protected replay.
- Report only: `true`
- Advisory only: `true`

## Recurrence Trends

- Protected replay only: `true`
- Total protected recurrence keys: `6`
- Emerging keys: `3`
- Recurring keys: `3`
- Persistent keys: `0`
- Dormant keys: `0`
- Growth rate: `50.0%` (3 / 6 keys emerging)
- Regression recurrence rate: `50.0%` (3 / 6)

### Top Recurring Keys

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (count `8`, class `recurring`)
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py` (count `4`, class `recurring`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` (count `2`, class `recurring`)

### Newest Recurrence Keys

- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py` (first seen `2026-06-22T21:39:03Z`, class `emerging`)
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py` (first seen `2026-06-22T21:38:39Z`, class `recurring`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` (first seen `2026-06-20T12:00:00Z`, class `recurring`)
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` (first seen `2026-06-20T12:00:00Z`, class `emerging`)
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py` (first seen `2026-06-20T12:00:00Z`, class `emerging`)

## Recurrence Forecast

- Protected replay only: `true`
- Forecast confidence: `high` (`1.00`)
- Stable keys: `0`
- Watch keys: `3`
- Elevated keys: `3`
- Concentrated keys: `0`
- Forecast risk score: `45.5` / 100
- Stability score: `50.0` / 100

### Concentration Metrics

- Top key share: `47.1%`
- Top three key share: `82.3%`
- Concentration ratio (HHI): `0.3010`
- Dominant recurrence key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`

### Key Forecasts

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (forecast `elevated`, trend `recurring`, share `47.1%`)
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py` (forecast `watch`, trend `emerging`, share `5.9%`)
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` (forecast `watch`, trend `emerging`, share `5.9%`)
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py` (forecast `elevated`, trend `recurring`, share `11.8%`)
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py` (forecast `elevated`, trend `recurring`, share `23.5%`)

## Recurrence Portfolio

- Protected replay only: `true`
- Portfolio risk score: `44.9` / 100
- Largest risk bucket: `owner` / `projection` (HHI `0.5363`)
- Forecast confidence: `1.00`

### Portfolio Metrics

- Owner concentration ratio: `0.5363`
- Category concentration ratio: `0.5363`
- Field path concentration ratio: `0.4118`
- Scenario concentration ratio: `0.2734`

### Top Owners

- `projection`, keys `2`, obs `12`, share `70.6%`, recurring `2`, elevated `2`
- `speaker`, keys `2`, obs `3`, share `17.6%`, recurring `1`, elevated `1`
- `fallback`, keys `1`, obs `1`, share `5.9%`, recurring `0`, elevated `0`
- `sanitizer`, keys `1`, obs `1`, share `5.9%`, recurring `0`, elevated `0`

### Top Categories

- `projection`, keys `2`, obs `12`, share `70.6%`
- `speaker`, keys `2`, obs `3`, share `17.6%`
- `fallback`, keys `1`, obs `1`, share `5.9%`
- `sanitizer`, keys `1`, obs `1`, share `5.9%`

### Top Field Paths

- `selected_speaker_id`, keys `2`, obs `10`, share `58.8%`
- `response_type_candidate_ok`, keys `1`, obs `4`, share `23.5%`
- `final_emitted_source`, keys `1`, obs `1`, share `5.9%`
- `scaffold_leakage`, keys `1`, obs `1`, share `5.9%`
- `selected_speaker_source`, keys `1`, obs `1`, share `5.9%`

### Top Scenarios

- `vocative_override_after_prior_continuity`, keys `1`, obs `8`, share `47.1%`
- `bx5_guard_ambiguous_multi_guard`, keys `3`, obs `3`, share `17.6%`
- `bx5_guard_canonical_guard_captain`, keys `1`, obs `1`, share `5.9%`
- `bx5_guard_gate_guard_distinct`, keys `1`, obs `1`, share `5.9%`
- `bx5_guard_role_alias_guard_captain`, keys `1`, obs `1`, share `5.9%`

## Recurrence Remediation Targets

- Protected replay only: `true`
- Highest leverage target: `key` / `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (priority `high`)
- Estimated portfolio reduction: `56.2`
- Remediation confidence: `1.00`

### Top Keys

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, priority `high`, reduction `56.2`, share `47.1%`, trend `recurring`, forecast `elevated`
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py`, priority `medium`, reduction `42.0`, share `23.5%`, trend `recurring`, forecast `elevated`
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, priority `medium`, reduction `34.9`, share `11.8%`, trend `recurring`, forecast `elevated`
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, priority `low`, reduction `16.6`, share `5.9%`, trend `emerging`, forecast `watch`
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, priority `low`, reduction `16.6`, share `5.9%`, trend `emerging`, forecast `watch`

### Top Owners

- `projection`, priority `high`, reduction `70.4`, share `70.6%`, keys `2`
- `speaker`, priority `medium`, reduction `38.4`, share `17.6%`, keys `2`
- `fallback`, priority `low`, reduction `16.5`, share `5.9%`, keys `1`
- `sanitizer`, priority `low`, reduction `16.5`, share `5.9%`, keys `1`

### Top Field Paths

- `selected_speaker_id`, priority `high`, reduction `63.3`, share `58.8%`
- `response_type_candidate_ok`, priority `medium`, reduction `42.0`, share `23.5%`
- `final_emitted_source`, priority `low`, reduction `16.5`, share `5.9%`
- `scaffold_leakage`, priority `low`, reduction `16.5`, share `5.9%`
- `selected_speaker_source`, priority `low`, reduction `16.5`, share `5.9%`

### Top Scenarios

- `vocative_override_after_prior_continuity`, priority `high`, reduction `56.2`, share `47.1%`
- `bx5_guard_ambiguous_multi_guard`, priority `medium`, reduction `38.4`, share `17.6%`
- `bx5_guard_canonical_guard_captain`, priority `medium`, reduction `31.3`, share `5.9%`
- `bx5_guard_gate_guard_distinct`, priority `medium`, reduction `31.3`, share `5.9%`
- `bx5_guard_role_alias_guard_captain`, priority `medium`, reduction `31.3`, share `5.9%`

## Recurrence ROI

- Protected replay only: `true`
- Highest ROI target: `key` / `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (ROI `100.0`, cost `medium`)
- Portfolio ROI score: `100.0`
- Projected stability gain: `28.1`
- Projected risk reduction: `25.2`
- ROI confidence: `1.00`

### Top ROI Targets

- rank `1`, `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, ROI `100.0`, cost `medium`, benefit `56.2`
- rank `2`, `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py`, ROI `100.0`, cost `low`, benefit `42.0`
- rank `3`, `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, ROI `100.0`, cost `low`, benefit `34.9`
- rank `4`, `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, ROI `51.9`, cost `low`, benefit `16.6`
- rank `5`, `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, ROI `51.9`, cost `low`, benefit `16.6`

### Top ROI Owners

- rank `1`, `projection`, ROI `100.0`, cost `medium`, benefit `70.4`
- rank `2`, `speaker`, ROI `91.0`, cost `medium`, benefit `38.4`
- rank `3`, `fallback`, ROI `51.6`, cost `low`, benefit `16.5`
- rank `4`, `sanitizer`, ROI `51.6`, cost `low`, benefit `16.5`

### Top ROI Field Paths

- rank `1`, `selected_speaker_id`, ROI `100.0`, cost `medium`, benefit `63.3`
- rank `2`, `response_type_candidate_ok`, ROI `100.0`, cost `low`, benefit `42.0`
- rank `3`, `final_emitted_source`, ROI `51.6`, cost `low`, benefit `16.5`
- rank `4`, `scaffold_leakage`, ROI `51.6`, cost `low`, benefit `16.5`
- rank `5`, `selected_speaker_source`, ROI `51.6`, cost `low`, benefit `16.5`

### Top ROI Scenarios

- rank `1`, `vocative_override_after_prior_continuity`, ROI `100.0`, cost `medium`, benefit `56.2`
- rank `2`, `bx5_guard_canonical_guard_captain`, ROI `97.8`, cost `low`, benefit `31.3`
- rank `3`, `bx5_guard_gate_guard_distinct`, ROI `97.8`, cost `low`, benefit `31.3`
- rank `4`, `bx5_guard_role_alias_guard_captain`, ROI `97.8`, cost `low`, benefit `31.3`
- rank `5`, `wrong_speaker_strict_social_emission`, ROI `97.8`, cost `low`, benefit `31.3`

## Recurrence Governance

- Protected replay only: `true`
- Governance health score: `46.3`
- Governance confidence: `1.00`
- Watchlist size: `6`
- Prioritized targets: `1`
- Retirement opportunities: `0`

### Watchlist

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `prioritize`, action `prioritize_remediation`, ROI `100.0`, trend `recurring`, forecast `elevated`
- `recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py`, status `investigate`, action `investigate_root_cause`, ROI `100.0`, trend `recurring`, forecast `elevated`
- `recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py`, status `investigate`, action `investigate_root_cause`, ROI `100.0`, trend `recurring`, forecast `elevated`
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, status `watch`, action `gather_more_history`, ROI `51.9`, trend `emerging`, forecast `watch`
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, status `watch`, action `gather_more_history`, ROI `51.9`, trend `emerging`, forecast `watch`

### Prioritized Targets

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `prioritize`, action `prioritize_remediation`, ROI `100.0`, trend `recurring`, forecast `elevated`

### Retire Candidates

No watchlist entries recorded.

### Owner Accountability

- `emission_drift`, governed `1`, watch `0`, prioritized `0`, retire `0`
- `fallback_drift`, governed `1`, watch `1`, prioritized `0`, retire `0`
- `semantic_drift`, governed `1`, watch `1`, prioritized `0`, retire `0`
- `speaker_drift`, governed `3`, watch `1`, prioritized `1`, retire `0`
- Highest governance load owner: `speaker_drift`

## Recurrence Lifecycle

- Protected replay only: `true`
- Lifecycle health score: `30.0`
- Closure rate: `0.0%`
- Average age (days): `4.2`
- Advancement rate: `0.50`

### Lifecycle Distribution

- `dormant`: `0`
- `emerging`: `3`
- `persistent`: `0`
- `recurring`: `3`
- `retired`: `0`

### Age Distribution

- Youngest key: `recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py`
- Oldest key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`
- Average age (days): `4.2`
- Median age (days): `2.4`

### Transition Summary

- Transition count: `3`
- Advancing transitions: `3`
- Retiring transitions: `0`
- Stalled keys: `0`

### Closure Effectiveness

- Active keys: `6`
- Dormant keys: `0`
- Retired keys: `0`
- Closure rate: `0.0%`

## Recurrence Program Effectiveness

- Protected replay only: `true`
- Program effectiveness score: `33.2`
- Effectiveness confidence: `1.00`
- Recurrence reduction rate: `0.0%`
- Forecast accuracy: `100.0%`
- Stability change: `-25.0`

### Governance Effectiveness

- Watchlist conversion rate: `66.7%`
- Investigate conversion rate: `50.0%`
- Prioritize conversion rate: `100.0%`
- Retirement conversion rate: `0.0%`
- Governance effectiveness: `0.54`

### Remediation Effectiveness

- Targeted keys: `6`
- Improved keys: `0`
- Unresolved keys: `6`
- Recurrence reduction rate: `0.0%`

### Forecast Effectiveness

- Forecast accuracy: `100.0%`
- Forecast confidence: `1.00`
- Predicted recurrences: `6`
- Realized recurrences: `6`
- Low confidence: `false`

### Portfolio Trajectory

- Trajectory available: `true`
- Portfolio risk change: `+0.8`
- Concentration change: `+0.0000`
- Governance health change: `-8.9`
- Lifecycle health change: `-15.0`

### Stability Trajectory

- Trajectory available: `true`
- Stability score current: `50.0`
- Stability change: `-25.0`
- Recurrence rate change: `+0.2500`

## Recurrence Maturity Assessment

- Protected replay only: `true`
- Overall maturity score: `76.9`
- Overall maturity level: `Measured`
- Highest dimension: `forecasting`
- Lowest dimension: `lifecycle`

### Dimension Scores

- Observability: `90.0`
- Governance: `61.6`
- Forecasting: `100.0`
- Remediation: `55.0`
- Lifecycle: `42.5`
- Operational Readiness: `100.0`

### Dimension Levels

- Observability: `Optimized`
- Governance: `Measured`
- Forecasting: `Optimized`
- Remediation: `Managed`
- Lifecycle: `Managed`
- Operational Readiness: `Optimized`

### Capability Gaps

- Lifecycle: current `42.5`, target `80.0`, gap `37.5`
- Remediation: current `55.0`, target `80.0`, gap `25.0`
- Governance: current `61.6`, target `80.0`, gap `18.4`
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

- Data Volume Expansion: ROI `100.0`, priority `80.1`, complexity `12.0`
- Trajectory Establishment: ROI `33.6`, priority `28.0`, complexity `27.0`
- Lifecycle Closure Tracking: ROI `27.7`, priority `38.0`, complexity `29.0`
- Remediation Feedback Loop: ROI `24.5`, priority `37.9`, complexity `42.0`
- Operationalization: ROI `23.8`, priority `40.2`, complexity `40.0`
- Forecast Validation: ROI `21.8`, priority `25.9`, complexity `38.0`

### Expected Maturity Lift

- Data Volume Expansion: projected overall `82.0` (`Optimized`)
- Trajectory Establishment: projected overall `80.3` (`Optimized`)
- Lifecycle Closure Tracking: projected overall `82.7` (`Optimized`)
- Remediation Feedback Loop: projected overall `83.9` (`Optimized`)
- Operationalization: projected overall `81.0` (`Optimized`)
- Forecast Validation: projected overall `79.4` (`Measured`)

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

- Governance / `governance_health_target_met`: current `46.3`, target `80.0`, gap `33.70`, roadmap `data_volume_expansion`

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
- Maturity Assessment: implemented `true`, validated `true`, operational `true`, confidence `0.77`
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
- Snapshot count: `5`

### Current Snapshot

- Timestamp: `2026-06-22T21:39:03Z`
- Protected observations: `17`
- Unique recurrence keys: `6`
- Portfolio risk score: `44.9`
- Governance health score: `46.3`
- Operational readiness score: `76.4`
- Effectiveness confidence: `0.82`
- Maturity score: `72.1`

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

- Portfolio risk change: `+0.8`
- Governance health change: `-8.9`
- Lifecycle health change: `-15.0`
- Operational readiness change: `+0.0`
- Effectiveness change: `+0.00`
- Maturity change: `-0.9`

## Confidence Calibration Audit

- Protected replay only: `true`
- Calibration score: `55.3`
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
- Evidence strength: `0.76`
- Calibration gap: `0.24`
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
| recurrence:v1:emission_drift\|projection\|response_type_candidate_ok\|tests/helpers/golden_replay.py | 4 | projection | active | projection | response_type_candidate_ok | bx5_guard_ambiguous_multi_guard, bx5_guard_canonical_guard_captain, bx5_guard_gate_guard_distinct, bx5_guard_role_alias_guard_captain | tests/helpers/golden_replay.py |
| recurrence:v1:speaker_drift\|speaker\|selected_speaker_id\|game/speaker_contract_enforcement.py | 2 | speaker | active | speaker | selected_speaker_id | bx5_guard_ambiguous_multi_guard, wrong_speaker_strict_social_emission | game/speaker_contract_enforcement.py |
| recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py | 1 | fallback | watch | fallback | final_emitted_source | directed_npc_question | game/final_emission_gate.py |
| recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py | 1 | sanitizer | watch | sanitizer | scaffold_leakage | sanitizer_scaffold_leakage | game/output_sanitizer.py |
| recurrence:v1:speaker_drift\|speaker\|selected_speaker_source\|game/speaker_contract_enforcement.py | 1 | speaker | watch | speaker | selected_speaker_source | bx5_guard_ambiguous_multi_guard | game/speaker_contract_enforcement.py |
