# Cycle AR — Block AR5: Drift Hotspot Analysis Summary

**Date:** 2026-06-06  
**Prerequisites:** AR2 (`owner_drift_bucket`), AR3 (reporting), AR4 (longitudinal)

---

## Objective

Identify replay surfaces generating the most owner drift so operators can quickly see where instability originates — advisory only, using existing classification metadata.

---

## Files modified

| File | Change |
| --- | --- |
| `tests/helpers/replay_drift_hotspots.py` | **New.** Field/target/bucket aggregations, rankings, markdown renderer |
| `tests/helpers/failure_dashboard_report.py` | Hotspot artifact paths; `collected_hotspot_classifications`; `write_owner_drift_hotspot_artifacts`; integration on protected failure + scorecard writes |
| `tests/test_replay_drift_hotspots.py` | **New.** 7 tests |

**Not modified:** `game/**`, replay assertions, protected scenarios, pass/fail logic, existing report section renderers.

---

## Aggregation model

### Inputs

Failure classification rows with:

- `field_path`
- `owner_drift_bucket`
- `category`
- `investigate_first`

Optional expansion: rerun scorecard `owner_drift_classifications` mapped to field paths via `RERUN_DELTA_KEY_FIELD_PATHS` (e.g. `speaker` → `selected_speaker_id`).

### Helpers

| Function | Output |
| --- | --- |
| `aggregate_field_drift_counts(classifications)` | `{"route_kind": 14, "selected_speaker_id": 11, ...}` |
| `aggregate_investigation_target_counts(classifications)` | `{"game/interaction_context.py": 18, ...}` |
| `aggregate_owner_bucket_by_field(classifications)` | `[{field, owner_drift_bucket, count}, ...]` |
| `aggregate_owner_drift_bucket_counts(classifications)` | `{route_drift: 20, speaker_drift: 15, ...}` |
| `build_hotspot_rankings(classifications)` | Full payload + ranked lists |
| `render_owner_drift_hotspot_report(hotspots)` | Advisory markdown |

### Ranking rules

- Sort by count descending; ties broken alphabetically by name
- Ranks assigned 1..N within each top list

---

## Artifact outputs

| Artifact | Path |
| --- | --- |
| Hotspot JSON | `artifacts/golden_replay/owner_drift_hotspots.json` |
| Hotspot markdown | `artifacts/golden_replay/owner_drift_hotspots.md` |

Written by `write_owner_drift_hotspot_artifacts()` when:

- Protected replay failure report is written (`write_protected_replay_failure_report_if_present`)
- Rerun scorecard artifacts are written (`write_rerun_drift_scorecard_artifacts`)

JSON includes `schema_version`, `report_only`, `advisory_only`, counts, pairings, and ranked top lists.

---

## Sample markdown output

```markdown
# Owner Drift Hotspot Report

- Advisory only: `true`
- Report only: `true`
- Total classifications: `3`

## Top Drift Fields

1. selected_speaker_id (2)
2. route_kind (1)

## Top Investigation Targets

1. game/speaker_contract_enforcement.py (2)
2. game/interaction_context.py (1)

## Top Owner Drift Buckets

1. speaker_drift (2)
2. route_drift (1)

## Owner Drift Buckets By Field

| Field | Owner Drift Bucket | Count |
|---|---|---:|
| `route_kind` | `route_drift` | `1` |
| `selected_speaker_id` | `speaker_drift` | `2` |
```

---

## Test coverage

**`tests/test_replay_drift_hotspots.py`** — 7 tests:

- Empty inputs
- Field + investigation target aggregation
- Owner bucket by field pairings
- Ranking with ties
- Markdown rendering (populated + empty)
- Artifact generation

**Regression:** hotspot + longitudinal + taxonomy + golden replay — all green.

---

## Compatibility verification

| Check | Result |
| --- | --- |
| Pass/fail unchanged | Pass |
| Existing reports unchanged (standalone hotspot artifacts) | Pass |
| No new telemetry | Pass — reads existing classification fields only |
| Scorecard `report_only` preserved | Pass |

---

## Governance verification

| Constraint | Status |
| --- | --- |
| No replay expansion | Pass |
| No runtime changes | Pass |
| No new acceptance gates | Pass — `advisory_only: true` |
| No assertion changes | Pass |

---

## Acceptance

**PASS** — hotspot rankings generated; fields, investigation targets, and owner drift buckets ranked; artifacts written; advisory only.
