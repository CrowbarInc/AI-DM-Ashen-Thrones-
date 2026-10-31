# Bug-Class Recurrence History

- Generated at: `2026-10-18T16:31:34Z`
- Command: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\.venv\Lib\site-packages\pytest\__main__.py -m golden_replay -q --tb=short -o addopts=--basetemp=development/tmp/maintenance_golden --junitxml=development/tmp/github_checkpoint/golden_after.xml`
- Report only: `true`
- Advisory only: `true`
- Total recurrence keys: `5`
- Total recurrence events: `33`

## Regression Recurrence Rate

Regression Recurrence Rate: 40.0% (2 / 5 recurrence keys active by repeated observation). This is advisory/report-only and does not gate protected replay.

- Definition: Share of observed recurrence keys with occurrence_count >= 2 in the measured history window.
- Interpretation: Initial measurable proxy for recurrence keys that became active after prior observation; refine when richer state transitions exist. Advisory and report-only; does not gate protected replay.
- Report only: `true`
- Advisory only: `true`

## Scoped Recurrence Populations

### Protected Replay Recurrence

- Recurrence rate: `40.0%` (2 / 5)
- Health metric: `true`

### Session Diagnostic Recurrence

- Recurrence rate: `87.5%` (7 / 8)
- Health metric: `false`

### Synthetic/Test Artifact Recurrence

- Recurrence rate: `100.0%` (2 / 2)
- Health metric: `false`

### Legacy Unified Recurrence, compatibility only

- Recurrence rate: `81.8%` (9 / 11)
- Health metric: `false`
- Compatibility only: `true`

## Recurrence Trends

- Protected replay only: `true`
- Total protected recurrence keys: `5`
- Emerging keys: `3`
- Recurring keys: `0`
- Persistent keys: `2`
- Dormant keys: `0`
- Growth rate: `60.0%` (3 / 5 keys emerging)
- Regression recurrence rate: `40.0%` (2 / 5)

### Top Recurring Keys

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (count `21`, class `persistent`)
- `recurrence:v1:emission_drift\|validator\|response_type_candidate_ok\|game/final_emission_gate.py` (count `9`, class `persistent`)

### Newest Recurrence Keys

- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` (first seen `2026-10-18T16:31:34Z`, class `emerging`)
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py` (first seen `2026-10-09T22:38:39Z`, class `emerging`)
- `recurrence:v1:emission_drift\|validator\|response_type_candidate_ok\|game/final_emission_gate.py` (first seen `2026-10-09T22:38:39Z`, class `persistent`)
- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (first seen `2026-09-19T16:01:46Z`, class `persistent`)
- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (first seen `2026-06-04T22:31:59Z`, class `emerging`)

## Recurrence Forecast

- Protected replay only: `true`
- Forecast confidence: `high` (`1.00`)
- Stable keys: `0`
- Watch keys: `3`
- Elevated keys: `1`
- Concentrated keys: `1`
- Forecast risk score: `40.8` / 100
- Stability score: `60.0` / 100

### Concentration Metrics

- Top key share: `63.6%`
- Top three key share: `93.9%`
- Concentration ratio (HHI): `0.4821`
- Dominant recurrence key: `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`

### Key Forecasts

- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py` (forecast `watch`, trend `emerging`, share `3.0%`)
- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (forecast `concentrated`, trend `persistent`, share `63.6%`)
- `recurrence:v1:emission_drift\|validator\|response_type_candidate_ok\|game/final_emission_gate.py` (forecast `elevated`, trend `persistent`, share `27.3%`)
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py` (forecast `watch`, trend `emerging`, share `3.0%`)
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py` (forecast `watch`, trend `emerging`, share `3.0%`)

## Recurrence Portfolio

- Protected replay only: `true`
- Portfolio risk score: `43.6` / 100
- Largest risk bucket: `field_path` / `selected_speaker_id` (HHI `0.5207`)
- Forecast confidence: `1.00`

### Portfolio Metrics

- Owner concentration ratio: `0.4821`
- Category concentration ratio: `0.4821`
- Field path concentration ratio: `0.5207`
- Scenario concentration ratio: `0.4307`

### Top Owners

- `replay`, keys `1`, obs `21`, share `63.6%`, recurring `1`, elevated `1`
- `validator`, keys `1`, obs `9`, share `27.3%`, recurring `1`, elevated `1`
- `fallback`, keys `1`, obs `1`, share `3.0%`, recurring `0`, elevated `0`
- `projection`, keys `1`, obs `1`, share `3.0%`, recurring `0`, elevated `0`
- `sanitizer`, keys `1`, obs `1`, share `3.0%`, recurring `0`, elevated `0`

### Top Categories

- `replay_drift`, keys `1`, obs `21`, share `63.6%`
- `validator`, keys `1`, obs `9`, share `27.3%`
- `fallback`, keys `1`, obs `1`, share `3.0%`
- `projection`, keys `1`, obs `1`, share `3.0%`
- `sanitizer`, keys `1`, obs `1`, share `3.0%`

### Top Field Paths

- `selected_speaker_id`, keys `2`, obs `22`, share `66.7%`
- `response_type_candidate_ok`, keys `1`, obs `9`, share `27.3%`
- `final_emitted_source`, keys `1`, obs `1`, share `3.0%`
- `scaffold_leakage`, keys `1`, obs `1`, share `3.0%`

### Top Scenarios

- `writer_bridge`, keys `1`, obs `21`, share `63.6%`
- `sanitizer_scaffold_leakage`, keys `2`, obs `3`, share `9.1%`
- `vocative_override_after_prior_continuity`, keys `2`, obs `3`, share `9.1%`
- `lead_followup_with_dialogue_lock`, keys `1`, obs `2`, share `6.1%`
- `wrong_speaker_strict_social_emission`, keys `1`, obs `2`, share `6.1%`

## Recurrence Remediation Targets

- Protected replay only: `true`
- Highest leverage target: `key` / `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (priority `high`)
- Estimated portfolio reduction: `70.6`
- Remediation confidence: `1.00`

### Top Keys

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`, priority `high`, reduction `70.6`, share `63.6%`, trend `persistent`, forecast `concentrated`
- `recurrence:v1:emission_drift\|validator\|response_type_candidate_ok\|game/final_emission_gate.py`, priority `medium`, reduction `47.2`, share `27.3%`, trend `persistent`, forecast `elevated`
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, priority `low`, reduction `14.8`, share `3.0%`, trend `emerging`, forecast `watch`
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, priority `low`, reduction `14.8`, share `3.0%`, trend `emerging`, forecast `watch`
- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, priority `low`, reduction `14.8`, share `3.0%`, trend `emerging`, forecast `watch`

### Top Owners

- `replay`, priority `high`, reduction `70.6`, share `63.6%`, keys `1`
- `validator`, priority `medium`, reduction `47.2`, share `27.3%`, keys `1`
- `fallback`, priority `low`, reduction `14.8`, share `3.0%`, keys `1`
- `projection`, priority `low`, reduction `14.8`, share `3.0%`, keys `1`
- `sanitizer`, priority `low`, reduction `14.8`, share `3.0%`, keys `1`

### Top Field Paths

- `selected_speaker_id`, priority `high`, reduction `53.1`, share `66.7%`
- `response_type_candidate_ok`, priority `medium`, reduction `47.2`, share `27.3%`
- `final_emitted_source`, priority `low`, reduction `14.8`, share `3.0%`
- `scaffold_leakage`, priority `low`, reduction `14.8`, share `3.0%`

### Top Scenarios

- `writer_bridge`, priority `high`, reduction `70.6`, share `63.6%`
- `sanitizer_scaffold_leakage`, priority `medium`, reduction `36.2`, share `9.1%`
- `vocative_override_after_prior_continuity`, priority `medium`, reduction `36.2`, share `9.1%`
- `lead_followup_with_dialogue_lock`, priority `medium`, reduction `34.4`, share `6.1%`
- `wrong_speaker_strict_social_emission`, priority `medium`, reduction `34.4`, share `6.1%`

## Recurrence ROI

- Protected replay only: `true`
- Highest ROI target: `key` / `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py` (ROI `100.0`, cost `medium`)
- Portfolio ROI score: `100.0`
- Projected stability gain: `28.2`
- Projected risk reduction: `30.8`
- ROI confidence: `1.00`

### Top ROI Targets

- rank `1`, `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`, ROI `100.0`, cost `medium`, benefit `70.6`
- rank `2`, `recurrence:v1:emission_drift\|validator\|response_type_candidate_ok\|game/final_emission_gate.py`, ROI `100.0`, cost `medium`, benefit `47.2`
- rank `3`, `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, ROI `46.2`, cost `low`, benefit `14.8`
- rank `4`, `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, ROI `46.2`, cost `low`, benefit `14.8`
- rank `5`, `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, ROI `46.2`, cost `low`, benefit `14.8`

### Top ROI Owners

- rank `1`, `replay`, ROI `100.0`, cost `medium`, benefit `70.6`
- rank `2`, `validator`, ROI `100.0`, cost `medium`, benefit `47.2`
- rank `3`, `fallback`, ROI `46.2`, cost `low`, benefit `14.8`
- rank `4`, `projection`, ROI `46.2`, cost `low`, benefit `14.8`
- rank `5`, `sanitizer`, ROI `46.2`, cost `low`, benefit `14.8`

### Top ROI Field Paths

- rank `1`, `response_type_candidate_ok`, ROI `100.0`, cost `medium`, benefit `47.2`
- rank `2`, `selected_speaker_id`, ROI `99.3`, cost `medium`, benefit `53.1`
- rank `3`, `final_emitted_source`, ROI `46.2`, cost `low`, benefit `14.8`
- rank `4`, `scaffold_leakage`, ROI `46.2`, cost `low`, benefit `14.8`

### Top ROI Scenarios

- rank `1`, `writer_bridge`, ROI `100.0`, cost `medium`, benefit `70.6`
- rank `2`, `lead_followup_with_dialogue_lock`, ROI `100.0`, cost `low`, benefit `34.4`
- rank `3`, `wrong_speaker_strict_social_emission`, ROI `100.0`, cost `low`, benefit `34.4`
- rank `4`, `directed_npc_question`, ROI `100.0`, cost `low`, benefit `32.6`
- rank `5`, `sanitizer_scaffold_leakage`, ROI `90.5`, cost `medium`, benefit `36.2`

## Recurrence Governance

- Protected replay only: `true`
- Governance health score: `50.1`
- Governance confidence: `1.00`
- Watchlist size: `5`
- Prioritized targets: `1`
- Retirement opportunities: `0`

### Watchlist

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `prioritize`, action `prioritize_remediation`, ROI `100.0`, trend `persistent`, forecast `concentrated`
- `recurrence:v1:emission_drift\|validator\|response_type_candidate_ok\|game/final_emission_gate.py`, status `investigate`, action `investigate_root_cause`, ROI `100.0`, trend `persistent`, forecast `elevated`
- `recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py`, status `watch`, action `gather_more_history`, ROI `46.2`, trend `emerging`, forecast `watch`
- `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`, status `watch`, action `gather_more_history`, ROI `46.2`, trend `emerging`, forecast `watch`
- `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `watch`, action `gather_more_history`, ROI `46.2`, trend `emerging`, forecast `watch`

### Prioritized Targets

- `recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py`, status `prioritize`, action `prioritize_remediation`, ROI `100.0`, trend `persistent`, forecast `concentrated`

### Retire Candidates

No watchlist entries recorded.

### Owner Accountability

- `emission_drift`, governed `1`, watch `0`, prioritized `0`, retire `0`
- `fallback_drift`, governed `1`, watch `1`, prioritized `0`, retire `0`
- `semantic_drift`, governed `1`, watch `1`, prioritized `0`, retire `0`
- `speaker_drift`, governed `2`, watch `1`, prioritized `1`, retire `0`
- Highest governance load owner: `speaker_drift`

## Recurrence Lifecycle

- Protected replay only: `true`
- Lifecycle health score: `24.0`
- Closure rate: `0.0%`
- Average age (days): `36.5`
- Advancement rate: `0.80`

### Lifecycle Distribution

- `dormant`: `0`
- `emerging`: `3`
- `persistent`: `2`
- `recurring`: `0`
- `retired`: `0`

### Age Distribution

- Youngest key: `recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py`
- Oldest key: `recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py`
- Average age (days): `36.5`
- Median age (days): `8.7`

### Transition Summary

- Transition count: `4`
- Advancing transitions: `4`
- Retiring transitions: `0`
- Stalled keys: `2`

### Closure Effectiveness

- Active keys: `5`
- Dormant keys: `0`
- Retired keys: `0`
- Closure rate: `0.0%`

## Recurrence Program Effectiveness

- Protected replay only: `true`
- Program effectiveness score: `35.6`
- Effectiveness confidence: `1.00`
- Recurrence reduction rate: `0.0%`
- Forecast accuracy: `100.0%`
- Stability change: `-15.0`

### Governance Effectiveness

- Watchlist conversion rate: `33.3%`
- Investigate conversion rate: `100.0%`
- Prioritize conversion rate: `100.0%`
- Retirement conversion rate: `0.0%`
- Governance effectiveness: `0.58`

### Remediation Effectiveness

- Targeted keys: `5`
- Improved keys: `0`
- Unresolved keys: `5`
- Recurrence reduction rate: `0.0%`

### Forecast Effectiveness

- Forecast accuracy: `100.0%`
- Forecast confidence: `1.00`
- Predicted recurrences: `5`
- Realized recurrences: `5`
- Low confidence: `false`

### Portfolio Trajectory

- Trajectory available: `true`
- Portfolio risk change: `-0.5`
- Concentration change: `+0.0000`
- Governance health change: `-5.1`
- Lifecycle health change: `-21.0`

### Stability Trajectory

- Trajectory available: `true`
- Stability score current: `60.0`
- Stability change: `-15.0`
- Recurrence rate change: `+0.1500`

## Recurrence Maturity Assessment

- Protected replay only: `true`
- Overall maturity score: `76.8`
- Overall maturity level: `Measured`
- Highest dimension: `forecasting`
- Lowest dimension: `lifecycle`

### Dimension Scores

- Observability: `90.0`
- Governance: `62.5`
- Forecasting: `100.0`
- Remediation: `55.0`
- Lifecycle: `41.0`
- Operational Readiness: `100.0`

### Dimension Levels

- Observability: `Optimized`
- Governance: `Measured`
- Forecasting: `Optimized`
- Remediation: `Managed`
- Lifecycle: `Managed`
- Operational Readiness: `Optimized`

### Capability Gaps

- Lifecycle: current `41.0`, target `80.0`, gap `39.0`
- Remediation: current `55.0`, target `80.0`, gap `25.0`
- Governance: current `62.5`, target `80.0`, gap `17.5`
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

- Data Volume Expansion: ROI `100.0`, priority `80.0`, complexity `12.0`
- Trajectory Establishment: ROI `33.6`, priority `28.0`, complexity `27.0`
- Lifecycle Closure Tracking: ROI `27.7`, priority `37.9`, complexity `29.0`
- Remediation Feedback Loop: ROI `24.5`, priority `37.8`, complexity `42.0`
- Operationalization: ROI `23.8`, priority `40.2`, complexity `40.0`
- Forecast Validation: ROI `21.8`, priority `25.8`, complexity `38.0`

### Expected Maturity Lift

- Data Volume Expansion: projected overall `81.9` (`Optimized`)
- Trajectory Establishment: projected overall `80.2` (`Optimized`)
- Lifecycle Closure Tracking: projected overall `82.6` (`Optimized`)
- Remediation Feedback Loop: projected overall `83.8` (`Optimized`)
- Operationalization: projected overall `80.9` (`Optimized`)
- Forecast Validation: projected overall `79.3` (`Measured`)

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

- Governance / `governance_health_target_met`: current `50.1`, target `80.0`, gap `29.90`, roadmap `data_volume_expansion`

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
- Snapshot count: `43`

### Current Snapshot

- Timestamp: `2026-10-18T16:31:34Z`
- Protected observations: `33`
- Unique recurrence keys: `5`
- Portfolio risk score: `43.6`
- Governance health score: `50.1`
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

- Portfolio risk change: `-0.5`
- Governance health change: `-5.1`
- Lifecycle health change: `-21.0`
- Operational readiness change: `+0.0`
- Effectiveness change: `+0.00`
- Maturity change: `-0.9`

## Confidence Calibration Audit

- Protected replay only: `true`
- Calibration score: `65.3`
- Interpretation: `Needs monitoring`
- Largest calibration gap: `0.52`
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
- Evidence strength: `0.48`
- Calibration gap: `0.52`
- Status: `overconfident`

### Graduation Threshold Validation

- `forecast_confidence`: current `1.0`, target `0.75`, status `supported`
- `effectiveness_confidence`: current `1.0`, target `0.75`, status `optimistic`
- `operational_readiness`: current `100.0`, target `80.0`, status `optimistic`
- `trajectory_available`: current `True`, target `True`, status `supported`
- `governance_confidence`: current `1.0`, target `0.75`, status `optimistic`

| Key | Count | Owner | Status | Categories | Field Paths | Affected Scenarios | Investigate First |
|---|---:|---|---|---|---|---|---|
| recurrence:v1:speaker_drift\|replay_drift\|selected_speaker_id\|tests/helpers/golden_replay.py | 21 | replay | active | replay_drift | selected_speaker_id | writer_bridge | tests/helpers/golden_replay.py |
| recurrence:v1:emission_drift\|validator\|response_type_candidate_ok\|game/final_emission_gate.py | 9 | validator | active | validator | response_type_candidate_ok | directed_npc_question, lead_followup_with_dialogue_lock, sanitizer_scaffold_leakage, vocative_override_after_prior_continuity, wrong_speaker_strict_social_emission | game/final_emission_gate.py |
| recurrence:v1:speaker_drift\|projection\|selected_speaker_id\|tests/helpers/golden_replay.py | 1 | projection | watch | projection | selected_speaker_id | vocative_override_after_prior_continuity | tests/helpers/golden_replay.py |
| recurrence:v1:fallback_drift\|fallback\|final_emitted_source\|game/final_emission_gate.py | 1 | fallback | watch | fallback | final_emitted_source | thin_answer_action_outcome_final_emission | game/final_emission_gate.py |
| recurrence:v1:semantic_drift\|sanitizer\|scaffold_leakage\|game/output_sanitizer.py | 1 | sanitizer | watch | sanitizer | scaffold_leakage | sanitizer_scaffold_leakage | game/output_sanitizer.py |
