# CG-4 — Recurrence Taxonomy Registry

**Date:** 2026-06-25  
**Scope:** Documentation and import-clarity only. No recurrence behavior, key formula, classification rename, threshold, or artifact regeneration changes.

**Related:** [`CG_failure_classification_authority_registry.md`](CG_failure_classification_authority_registry.md) (CG-1 recurrence section)

## Purpose

Recurrence analytics use many overlapping status words (`watch`, `emerging`, `retired`, …) across input rows, aggregated summaries, trend buckets, governance funnels, lifecycle stages, and graduation audits. This registry records **which module owns each taxonomy**, what consumes it, and what each taxonomy is **not**.

Use this document before adding a recurrence status value, editing classifier thresholds, or importing recurrence constants.

## Authority module map

| Module | Owns | Consumes | Does not own |
|---|---|---|---|
| `replay_bug_recurrence_events.py` | Identity key, input/summary status, event source, persistence lanes | Classification row fields (`category`, `field_path`, …) | Trend, forecast, governance, lifecycle, graduation |
| `replay_bug_recurrence_history.py` | Trend, forecast, remediation cost/priority, governance, lifecycle | Events module symbols; protected event log | Program maturity, confidence calibration, outcome validation |
| `replay_bug_recurrence_statistics.py` | Program effectiveness, maturity, roadmap, completion, graduation audit builders; cross-taxonomy alignment maps | History classifiers; events aggregation | Confidence/outcome vocabularies; markdown renderers |
| `replay_bug_recurrence_serialization.py` | Confidence calibration, graduation threshold validation, blind-spot change, outcome signals, report markdown | History + statistics payloads | Trend/forecast/governance classifiers |
| `failure_dashboard_recurrence.py` | Dashboard markdown layout for recurrence sections | All analytics via `replay_bug_recurrence` facade | Any taxonomy allowed-values |
| `replay_bug_recurrence.py` | Compatibility facade (`import *` re-exports) | All four focused modules | Nothing (mirror only) |

## Taxonomy families

Columns: **Identity?** · **Dashboard render?** · **Serialized artifacts?**

### 1. Recurrence identity key

| Field | Value |
|---|---|
| **Allowed values** | `recurrence:v1:<owner_bucket>\|<category>\|<field_path>\|<investigate_first>` (formula-defined, not a closed enum) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_events.py` (`build_recurrence_key`) |
| **Purpose** | Deterministic cross-run identity for bug-class recurrence |
| **Downstream consumers** | Event log writers, history aggregation, portfolio/forecast builders, dashboard recurrence tables, trajectory snapshots |
| **Identity?** | **Yes — defines identity** |
| **Dashboard render?** | Yes (recurrence key column) |
| **Serialized artifacts?** | Yes (`bug_recurrence_history.json`, event logs, trajectory history) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` (exact-key tests), `tests/test_migrate_bug_recurrence_event_log.py` |

### 2. Input status

| Field | Value |
|---|---|
| **Allowed values** | `active`, `retired` (`ALLOWED_RECURRENCE_STATUSES`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_events.py` (`recurrence_status`, `_input_status`) |
| **Purpose** | Per-event or per-row explicit retirement signal on input classification rows |
| **Downstream consumers** | Event log persistence, lifecycle/governance classifiers (retired input → lifecycle retired / governance retire_candidate) |
| **Identity?** | No |
| **Dashboard render?** | Indirect (summary tables) |
| **Serialized artifacts?** | Yes (event log `recurrence_status` field) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 3. Summary status

| Field | Value |
|---|---|
| **Allowed values** | `active`, `retired`, `watch` (`SUMMARY_RECURRENCE_STATUSES`, `classify_recurrence_status`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_events.py` |
| **Purpose** | Aggregated history summary status after occurrence counting (first observation → watch; repeated active → active) |
| **Downstream consumers** | History markdown/json summaries, dashboard recurrence report status column, governance lifecycle inputs |
| **Identity?** | No |
| **Dashboard render?** | Yes (` | active | ` / ` | watch | ` / ` | retired | ` in recurrence history markdown) |
| **Serialized artifacts?** | Yes (`bug_recurrence_history.json` summary rows) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py`, `tests/test_failure_dashboard_report.py` |

### 4. Event source

| Field | Value |
|---|---|
| **Allowed values** | `protected_replay_failure`, `session`, `unknown` (`RECURRENCE_EVENT_SOURCE_BUCKETS`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_events.py` |
| **Purpose** | Persistence-lane routing and commit-worthiness filtering |
| **Downstream consumers** | Protected vs session-diagnostic event logs, trend timeline (protected-only), BZ movement reports |
| **Identity?** | No |
| **Dashboard render?** | No (metadata) |
| **Serialized artifacts?** | Yes (event log `event_source`) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py`, `tests/test_failure_dashboard_report.py` |

### 5. Trend classification

| Field | Value |
|---|---|
| **Allowed values** | `emerging`, `recurring`, `persistent`, `dormant` (`RECURRENCE_TREND_CLASSIFICATIONS`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_history.py` (`classify_recurrence_trend_entry`) |
| **Purpose** | Time-window observation pattern for protected keys (first seen, inactivity, active span) |
| **Downstream consumers** | Timeline, trend summary, forecast classifier inputs, governance classifier, lifecycle stage derivation, statistics alignment maps, serialization reports |
| **Identity?** | No |
| **Dashboard render?** | Yes (Recurrence Trends section) |
| **Serialized artifacts?** | Yes (`recurrence_timeline`, `recurrence_trends`) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 6. Forecast classification

| Field | Value |
|---|---|
| **Allowed values** | `stable`, `watch`, `elevated`, `concentrated` (`RECURRENCE_FORECAST_CLASSIFICATIONS`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_history.py` (`classify_recurrence_forecast`) |
| **Purpose** | Forward-looking risk bucket from trend + portfolio concentration |
| **Downstream consumers** | Forecast summary, governance classifier, program effectiveness, graduation audit, markdown forecast section |
| **Identity?** | No |
| **Dashboard render?** | Yes (Recurrence Forecast section) |
| **Serialized artifacts?** | Yes (`recurrence_forecast`) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 7. Remediation cost classification

| Field | Value |
|---|---|
| **Allowed values** | `trivial`, `low`, `medium`, `high` (`RECURRENCE_REMEDIATION_COST_CLASSIFICATIONS`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_history.py` (`classify_remediation_cost`) |
| **Purpose** | Advisory cost band from estimated remediation score thresholds |
| **Downstream consumers** | Remediation targets, ROI analysis, governance prioritize gate |
| **Identity?** | No |
| **Dashboard render?** | Yes (remediation targets section) |
| **Serialized artifacts?** | Yes |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 8. Remediation priority

| Field | Value |
|---|---|
| **Allowed values** | `critical`, `high`, `medium`, `low` (`RECURRENCE_REMEDIATION_PRIORITIES`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_history.py` |
| **Purpose** | Action ordering band from reduction potential score |
| **Downstream consumers** | Remediation targets ranking, governance investigate/prioritize thresholds |
| **Identity?** | No |
| **Dashboard render?** | Yes |
| **Serialized artifacts?** | Yes |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 9. Governance status

| Field | Value |
|---|---|
| **Allowed values** | `observe`, `watch`, `investigate`, `prioritize`, `retire_candidate` (`RECURRENCE_GOVERNANCE_STATUSES`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_history.py` (`classify_recurrence_governance_status`) |
| **Purpose** | Operator funnel stage for per-key intervention priority |
| **Downstream consumers** | Watchlist, governance summary, program effectiveness, graduation audit, dashboard governance section |
| **Identity?** | No |
| **Dashboard render?** | Yes (Recurrence Governance watchlist) |
| **Serialized artifacts?** | Yes (`recurrence_governance`, `recurrence_watchlist`) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py`, `tests/test_failure_dashboard_report.py` |

### 10. Governance action

| Field | Value |
|---|---|
| **Allowed values** | `continue_observation`, `gather_more_history`, `investigate_root_cause`, `prioritize_remediation`, `retire_tracking` (`RECURRENCE_GOVERNANCE_ACTIONS`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_history.py` (`RECURRENCE_GOVERNANCE_STATUS_TO_ACTION`) |
| **Purpose** | Display label mapping from governance status → recommended action |
| **Downstream consumers** | Governance markdown tables only |
| **Identity?** | No |
| **Dashboard render?** | Yes (derived label) |
| **Serialized artifacts?** | Yes (embedded in governance rows) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 11. Lifecycle stage

| Field | Value |
|---|---|
| **Allowed values** | `emerging`, `recurring`, `persistent`, `dormant`, `retired` (`RECURRENCE_LIFECYCLE_STAGES`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_history.py` (`classify_recurrence_lifecycle_stage`) |
| **Purpose** | Long-horizon key lifecycle including explicit retirement and extended dormancy |
| **Downstream consumers** | Lifecycle summary, program effectiveness, outcome validation, statistics alignment maps, trajectory snapshots |
| **Identity?** | No |
| **Dashboard render?** | Yes (Recurrence Lifecycle section) |
| **Serialized artifacts?** | Yes (`recurrence_lifecycle`) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py`, `tests/test_failure_dashboard_report.py` |

### 12. Maturity level

| Field | Value |
|---|---|
| **Allowed values** | `initial`, `developing`, `managed`, `measured`, `optimized` (`RECURRENCE_MATURITY_LEVEL_THRESHOLDS`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_statistics.py` |
| **Purpose** | Program-wide maturity band from weighted dimension scores |
| **Downstream consumers** | Maturity assessment markdown, roadmap target state, completion assessment |
| **Identity?** | No |
| **Dashboard render?** | Yes (Recurrence Maturity Assessment) |
| **Serialized artifacts?** | Yes (`recurrence_maturity`) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py`, `tests/test_failure_dashboard_report.py` |

### 13. Confidence calibration status

| Field | Value |
|---|---|
| **Allowed values** | `underconfident`, `calibrated`, `overconfident` (`RECURRENCE_CONFIDENCE_STATUSES`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_serialization.py` |
| **Purpose** | Compare reported confidence vs evidence strength gap per analytics component |
| **Downstream consumers** | Confidence calibration audit report, graduation threshold validation |
| **Identity?** | No |
| **Dashboard render?** | Yes (Confidence Calibration Audit section) |
| **Serialized artifacts?** | Yes (`recurrence_confidence_audit`) |
| **Tests** | `tests/test_replay_bug_class_recurrence.py`, `tests/test_failure_dashboard_report.py` |

### 14. Graduation threshold validation status

| Field | Value |
|---|---|
| **Allowed values** | `supported`, `optimistic`, `unsupported` (`RECURRENCE_GRADUATION_THRESHOLD_STATUSES`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_serialization.py` |
| **Purpose** | Per-dimension graduation readiness evidence check (forecast, effectiveness, governance, trajectory) |
| **Downstream consumers** | Graduation audit, final graduation decision builder |
| **Identity?** | No |
| **Dashboard render?** | Yes (Graduation Threshold Validation) |
| **Serialized artifacts?** | Yes |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 15. Blind-spot status change

| Field | Value |
|---|---|
| **Allowed values** | `reduced`, `partially_reduced`, `unchanged`, `escalated` (serialization module constants) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_serialization.py` |
| **Purpose** | Track whether known graduation blind spots improved between audits |
| **Downstream consumers** | Graduation audit markdown only |
| **Identity?** | No |
| **Dashboard render?** | Yes (Blind Spots section) |
| **Serialized artifacts?** | Yes |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 16. Outcome signal

| Field | Value |
|---|---|
| **Allowed values** | `retired_recurrence_key`, `dormant_recurrence_key`, `measurable_recurrence_reduction`, `confirmed_remediation_impact` (`RECURRENCE_OUTCOME_SIGNALS`) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_serialization.py` |
| **Purpose** | Evidence-backed effectiveness outcomes only (rejects synthetic/inferred success) |
| **Downstream consumers** | Outcome validation report, effectiveness evidence strength recalculation |
| **Identity?** | No |
| **Dashboard render?** | Yes (outcome validation doc sections via dashboard) |
| **Serialized artifacts?** | Yes |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 17. Outcome rejection reason

| Field | Value |
|---|---|
| **Allowed values** | `synthetic_key_rejected`, `inferred_without_evidence`, `manually_forced_status_rejected`, `insufficient_evidence` |
| **Owning file** | `tests/helpers/replay_bug_recurrence_serialization.py` |
| **Purpose** | Explain why a claimed outcome was not accepted |
| **Downstream consumers** | Outcome validation report |
| **Identity?** | No |
| **Dashboard render?** | Yes (rejection rows in audit) |
| **Serialized artifacts?** | Yes |
| **Tests** | `tests/test_replay_bug_class_recurrence.py` |

### 18. Final graduation recommendation

| Field | Value |
|---|---|
| **Allowed values** | `graduate_recurrence_program`, `one_final_targeted_validation_cycle_required`, `recurrence_program_remains_operationally_immature` |
| **Owning file** | `tests/helpers/replay_bug_recurrence_serialization.py` (`build_recurrence_final_graduation_decision`) |
| **Purpose** | Single advisory program graduation verdict |
| **Downstream consumers** | Final graduation decision markdown artifact |
| **Identity?** | No |
| **Dashboard render?** | Yes (final recommendation block) |
| **Serialized artifacts?** | Yes |
| **Tests** | `tests/test_replay_bug_class_recurrence.py`, `tests/test_failure_dashboard_report.py` |

### 19. Program completion graduation flag

| Field | Value |
|---|---|
| **Allowed values** | Boolean `program_graduated` plus requirement checklist (not a string enum) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_statistics.py` (`build_recurrence_completion_assessment`) |
| **Purpose** | Dimension-level completion scoring toward operational graduation |
| **Downstream consumers** | Completion markdown section, graduation audit inputs |
| **Identity?** | No |
| **Dashboard render?** | Yes (Recurrence Program Completion) |
| **Serialized artifacts?** | Yes |
| **Tests** | `tests/test_replay_bug_class_recurrence.py`, `tests/test_failure_dashboard_report.py` |

### 20. Trajectory snapshot schema

| Field | Value |
|---|---|
| **Allowed values** | `schema_version: 1`; numeric score fields (not categorical) |
| **Owning file** | `tests/helpers/replay_bug_recurrence_statistics.py` |
| **Purpose** | Longitudinal baseline/compare snapshots for protected replay metrics |
| **Downstream consumers** | Trajectory history JSON, trajectory summary in recurrence history |
| **Identity?** | No |
| **Dashboard render?** | Indirect (trajectory message in reports) |
| **Serialized artifacts?** | Yes (`bug_recurrence_trajectory_history.json`) |
| **Tests** | `tests/test_recurrence_trajectory_history.py` |

## Cross-taxonomy relationships

### Trend vs lifecycle

| | Trend | Lifecycle |
|---|---|---|
| **Shared labels** | `emerging`, `recurring`, `persistent`, `dormant` | Same four plus `retired` |
| **Why both exist** | Trend measures **observation pattern in a time window** for analytics dashboards. Lifecycle adds **retirement semantics** (explicit retired status or 90-day dormancy → `retired`). |
| **Not interchangeable** | Lifecycle `retired` has no trend equivalent. Trend `dormant` (30-day) ≠ lifecycle `retired` (90-day threshold). |
| **Confusion risk** | **High** — identical strings for four buckets; contributors often assume one classifier. |

### Input status vs summary status

| | Input status | Summary status |
|---|---|---|
| **Values** | `active`, `retired` | `active`, `retired`, `watch` |
| **Why both exist** | Input captures **explicit row/event retirement**. Summary derives **aggregate history posture** including first-observation `watch`. |
| **Not interchangeable** | Summary `watch` is not an input status. Input `retired` flows into summary/lifecycle but summary `active` requires occurrence_count ≥ 2. |
| **Confusion risk** | **Medium** — both appear as `status` in different JSON layers. |

### Governance status vs summary status

| | Governance | Summary status |
|---|---|---|
| **Shared label** | `watch` | `watch` |
| **Why both exist** | Governance `watch` is an **intervention funnel stage** (gather history). Summary `watch` means **single observation so far**. |
| **Not interchangeable** | Same word, different classifiers and thresholds. Governance also has `observe`, `investigate`, `prioritize`, `retire_candidate`. |
| **Confusion risk** | **High** — most common terminology collision in recurrence code. |

### Governance vs graduation

| | Governance | Graduation |
|---|---|---|
| **Nature** | Per-key operational funnel (observe → prioritize) | Program-wide readiness audit (supported/optimistic/unsupported + final recommendation) |
| **Why both exist** | Governance drives **day-to-day triage**. Graduation assesses **whether the recurrence program itself can exit advisory mode**. |
| **Not interchangeable** | `retire_candidate` governance ≠ `graduate_recurrence_program` recommendation. |
| **Confusion risk** | **Medium** — both use "retire/graduate" language about program maturity. |

### Confidence vs outcome

| | Confidence calibration | Outcome validation |
|---|---|---|
| **Values** | `underconfident`, `calibrated`, `overconfident` | `retired_recurrence_key`, `dormant_recurrence_key`, … |
| **Why both exist** | Confidence compares **reported vs evidence strength** for analytics components. Outcomes validate **concrete closure/remediation events** with evidence requirements. |
| **Not interchangeable** | High calibration does not imply validated outcomes; outcomes can exist with poor calibration. |
| **Confusion risk** | **Medium** — both appear in effectiveness/graduation audit sections. |

### Forecast vs trend

| | Forecast | Trend |
|---|---|---|
| **Overlap** | Both consume occurrence counts and timestamps | Trend is input to forecast |
| **Why both exist** | Trend describes **what happened**. Forecast estimates **future risk** including portfolio concentration (`concentrated`). |
| **Not interchangeable** | `stable` forecast exists; no trend `stable`. `concentrated` is forecast-only. |
| **Confusion risk** | **Low–medium** — distinct value sets except shared `watch`. |

### Remediation cost vs remediation priority

| | Cost | Priority |
|---|---|---|
| **Values** | `trivial`…`high` (effort estimate) | `critical`…`low` (action ordering) |
| **Why both exist** | Cost estimates **work size**; priority ranks **which keys to fix first** from reduction potential. |
| **Not interchangeable** | High cost can be low priority if reduction potential is low. |
| **Confusion risk** | **Low** — different label sets. |

## Future consolidation opportunities (not implemented)

1. **Shared emerging/recurring/persistent/dormant strings** — trend and lifecycle duplicate four labels; a single shared constant tuple with lifecycle extending it would reduce drift risk (requires careful retirement semantics).
2. **`RECURRENCE_FORECAST_LIFECYCLE_ALIGNMENT`** in statistics — alignment table duplicates relationship already documented in history classifiers; could derive from a single crosswalk module.
3. **Dual graduation recommendation constants** — `RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_*` and `BQC5_GRADUATION_RECOMMENDATION_*` mirror the same three verdicts; consolidation would reduce rename churn.
4. **Serialization markdown label mirrors** — section headers and status strings are embedded in render functions rather than a display manifest (similar to failure dashboard evidence manifest pattern).
5. **Facade `import *` chains** — four modules re-export upstream symbols; explicit `__all__` per module already partial in facade but internal wildcard imports obscure ownership at call sites.
6. **Governance `watch` rename** — highest confusion risk but would be a behavioral/display breaking change; document-only for now.

## Recurrence governance metrics (CG-4)

| Metric | Count |
|---|---:|
| Taxonomy families documented | 20 |
| Authority modules (own ≥1 taxonomy) | 4 (`events`, `history`, `statistics`, `serialization`) |
| Display-only consumer modules | 2 (`failure_dashboard_recurrence.py`, `replay_bug_recurrence.py` facade) |
| Derived consumer modules (orchestrate, do not own) | `replay_drift_reports.py`, `protected_replay_trend_movement.py`, tools/backfill scripts |
| Remaining ambiguous ownership areas | Graduation audit builder (statistics) vs graduation threshold vocabulary (serialization); maturity dimension scores (derived metrics, not closed enums) |
| Wildcard/compatibility `import *` edges | 5 (`history→events`, `statistics→events+history`, `serialization→events+history+statistics`, `facade→all four`, `failure_classification_sync` unrelated) |
| Largest recurrence governance hotspot | `replay_bug_recurrence_history.py` (~3,077 LOC — owns 6 taxonomy families plus timeline builders) |

## Change checklist

| If you change… | Edit… | Also review… |
|---|---|---|
| Recurrence key formula | `replay_bug_recurrence_events.py` | Migration tools, exact-key tests, all artifacts |
| Input/summary status | `replay_bug_recurrence_events.py` | Lifecycle/governance classifiers, dashboard status column |
| Trend thresholds | `replay_bug_recurrence_history.py` | Forecast, governance, lifecycle, statistics alignment map |
| Forecast thresholds | `replay_bug_recurrence_history.py` | Governance, program effectiveness |
| Governance funnel | `replay_bug_recurrence_history.py` | Watchlist rendering, graduation audit |
| Lifecycle retirement days | `replay_bug_recurrence_history.py` | Outcome validation, trend dormant threshold |
| Maturity levels/thresholds | `replay_bug_recurrence_statistics.py` | Roadmap, completion, graduation audit |
| Confidence/graduation/outcome vocab | `replay_bug_recurrence_serialization.py` | Audit markdown, dashboard recurrence sections |
| Dashboard section labels only | `failure_dashboard_recurrence.py` | No taxonomy authority change |

## CG-6 recurrence key stability review

**Date:** 2026-06-25  
**Change:** Design and migration audit only; no key generation, history, serialization, or artifact changes.

**Review:** [`CG_recurrence_key_stability_review.md`](CG_recurrence_key_stability_review.md)

**Summary:** `recurrence:v1` embeds two high-mutation components (`field_path`, `investigate_first`). One key producer, nine consumer modules, five persistence locations, ~15 exact-key test literals. **Recommendation:** defer v2; keep v1 for advisory report-only identity; revisit if recurrence becomes gating or refactor churn exceeds manual retirement tolerance. Hybrid v2 (Option C) preferred if migration is ever required.
