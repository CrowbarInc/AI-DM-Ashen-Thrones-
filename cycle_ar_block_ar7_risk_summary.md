# Cycle AR — Block AR7: Drift Risk Prioritization Summary

**Date:** 2026-06-06  
**Prerequisites:** AR4 (longitudinal), AR5 (hotspots), AR6 (trends)

---

## Objective

Convert owner drift observations into prioritized replay risk signals so operators can distinguish high-impact replay instability from low-impact noise — advisory only, without changing existing drift counts.

---

## Risk model

### Inputs

Each risk signal consumes existing classification metadata:

| Input | Source |
| --- | --- |
| `owner_drift_bucket` | AR2 classification / scorecard rows |
| `field_path` | Failure classifier / rerun delta mapping |
| `category` | Failure classifier |
| `severity` | Failure classifier |
| `field_source` | Protected manifest vs classifier extension vs advisory |
| `longitudinal_frequency` | Hotspot counts / scorecard history |
| `trend_direction` | AR6 field or bucket trends (`up` / `down` / `stable`) |

### Output

`risk_level`: `low` | `medium` | `high`

### Deterministic scoring rules

| Risk | Rule |
| --- | --- |
| **High** | Protected source + worsening trend (`up`) + repeated occurrence (frequency ≥ 2) |
| **Medium** | Protected source + stable trend |
| **Medium** | Supporting-only source + frequent occurrence (frequency ≥ 2) |
| **Low** | Advisory-only source |
| **Low** | Rare occurrence (frequency ≤ 1, not worsening) |
| **Low** | Improving trend (`down`) |

Protected field paths derive from `protected_observation_field_paths()`. Supporting paths derive from `CLASSIFIER_EVIDENCE_EXTENSION_FIELDS`. Owner buckets map to protected/supporting tiers for bucket-level ranking.

---

## Files modified

| File | Change |
| --- | --- |
| `tests/helpers/replay_drift_risk.py` | **New.** Risk scoring, rankings, markdown renderer |
| `tests/helpers/failure_dashboard_report.py` | Risk artifact paths; `write_owner_drift_risk_artifacts`; scorecard + protected failure integration |
| `tests/test_replay_drift_risk.py` | **New.** Classification, ranking, rendering, artifact tests |
| `artifacts/golden_replay/owner_drift_risk.json` | **New.** Baseline advisory payload |
| `artifacts/golden_replay/owner_drift_risk.md` | **New.** Baseline advisory report |

**Not modified:** `game/**`, replay assertions, protected scenarios, pass/fail logic, acceptance gates.

---

## Rankings

`build_risk_rankings()` produces:

| Ranking | Example |
| --- | --- |
| Top Risk Fields | `route_kind` → `high` |
| Top Risk Owners | `route_drift` → `high` |
| Top Risk Investigation Targets | `game/interaction_context.py` → `high` |
| Recommended Investigation Order | Targets ranked by risk, then frequency |

Table format:

```markdown
| Rank | Item | Risk |
|---:|---|---|
| 1 | `route_kind` | `high` |
```

---

## Artifact outputs

| Artifact | Path |
| --- | --- |
| Risk JSON | `artifacts/golden_replay/owner_drift_risk.json` |
| Risk markdown | `artifacts/golden_replay/owner_drift_risk.md` |

Written by `write_owner_drift_risk_artifacts()` when:

- Protected replay failure report is written
- Rerun scorecard artifacts are written

JSON payload includes: `risk_signals`, `risk_by_level`, ranked top lists, `recommended_investigation_order`, `advisory_only: true`.

---

## Report sections

`render_owner_drift_risk_report()` renders:

- `## High Risk Drift`
- `## Medium Risk Drift`
- `## Low Risk Drift`
- `## Recommended Investigation Order`

Plus ranked tables for fields, owners, and investigation targets.

---

## Test coverage

**`tests/test_replay_drift_risk.py`** — 10 tests:

- High / medium / low risk classification
- Protected field source detection
- Ranking order (high before low)
- Report rendering (all required sections)
- Artifact generation

---

## Compatibility verification

| Check | Result |
| --- | --- |
| Pass/fail unchanged | Pass |
| Assertions unchanged | Pass |
| Existing drift counts unchanged | Pass — risk reads counts, does not recompute taxonomy |
| Advisory only | Pass |

---

## Governance verification

| Constraint | Status |
| --- | --- |
| No replay expansion | Pass |
| No runtime changes | Pass |
| No assertion changes | Pass |
| No acceptance gate changes | Pass |
| Advisory only | Pass |

---

## Acceptance

**PASS** — risk levels generated; rankings and investigation order produced; artifacts and tests in place; replay behavior unchanged.

**Operator command** (unchanged):

```powershell
python -m pytest -m golden_replay -q --write-rerun-drift-scorecard
```

Produces scorecard, longitudinal, hotspot, trend, and risk artifacts under `artifacts/golden_replay/`.
