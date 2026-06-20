# Bug-Fix Locality Report

> BRL1 repository metric — commit cohort locality over the BR classification inventory.

_Source: `docs\reports\BR_commit_classification.csv` (235 commits)._

## Bug-Fix Locality

| Metric | Baseline | Current | Delta |
|---|---:|---:|---:|
| Median files touched | 9.0 | 9.0 | +0.0 |
| P75 files touched | 36.0 | 36.0 | +0.0 |
| P90 files touched | 216.0 | 216.0 | +0.0 |
| Max files touched | 538 | 538 | +0.0 |

_Commits in cohort: 11 (baseline snapshot: 11)._

## Refactor Locality

| Metric | Baseline | Current | Delta |
|---|---:|---:|---:|
| Median files touched | 16.0 | 16.0 | +0.0 |
| P75 files touched | 23.0 | 23.0 | +0.0 |
| P90 files touched | 41.0 | 41.0 | +0.0 |
| Max files touched | 1407 | 1407 | +0.0 |

_Commits in cohort: 101 (baseline snapshot: 101)._

## Governance Locality

| Metric | Baseline | Current | Delta |
|---|---:|---:|---:|
| Median files touched | 16.0 | 16.0 | +0.0 |

_Commits in cohort: 36 (baseline snapshot: 36)._

## Feature Locality

| Metric | Baseline | Current | Delta |
|---|---:|---:|---:|
| Median files touched | 14.0 | 14.0 | +0.0 |

_Commits in cohort: 44 (baseline snapshot: 44)._

## Repository Economics Summary

| Score | Baseline | Current | Delta | Interpretation |
|---|---:|---:|---:|---|
| Bug-fix locality score | 11.11 | 11.11 | +0.0 | Higher is more local (fewer median files touched). |
| Refactor locality score | 6.25 | 6.25 | +0.0 | Higher is more local (fewer median files touched). |

### Maintenance Concentration Indicators

- Bug-fix top-5 file touch share: **3.98%**
- Bug-fix top-file touch share: **1.02%**
- Refactor top-5 file touch share: **4.57%**
- Distinct bug-fix paths touched: **835**
- Distinct refactor paths touched: **2059**

## Hotspot Reporting

### Most Frequently Touched Files

- `data/session.json`: 88 commit(s)
- `data/session_log.jsonl`: 87 commit(s)
- `game/final_emission_gate.py`: 64 commit(s)
- `game/prompt_context.py`: 57 commit(s)
- `data/scenes/frontier_gate.json`: 54 commit(s)
- `game/api.py`: 53 commit(s)
- `data/world.json`: 49 commit(s)
- `tests/test_final_emission_gate.py`: 49 commit(s)
- `game/gm.py`: 35 commit(s)
- `tests/test_golden_replay.py`: 34 commit(s)

### Most Common Bug-Fix Clusters

- `data/session.json`: 9 production touch(es)
- `data/session_log.jsonl`: 9 production touch(es)
- `data/combat.json`: 7 production touch(es)
- `game/api.py`: 5 production touch(es)
- `game/prompt_context.py`: 4 production touch(es)
- `game/gm.py`: 3 production touch(es)
- `game/final_emission_gate.py`: 3 production touch(es)
- `data/scenes`: 2 production touch(es)
- `data/world.json`: 2 production touch(es)
- `game/api_upstream_preflight.py`: 2 production touch(es)

### Most Common Refactor Clusters

- `data/scenes`: 44 production touch(es)
- `data/session.json`: 36 production touch(es)
- `data/session_log.jsonl`: 35 production touch(es)
- `game/final_emission_gate.py`: 35 production touch(es)
- `game/api.py`: 27 production touch(es)
- `game/prompt_context.py`: 24 production touch(es)
- `game/final_emission_meta.py`: 23 production touch(es)
- `game/gm.py`: 21 production touch(es)
- `data/combat.json`: 17 production touch(es)
- `data/world.json`: 16 production touch(es)
