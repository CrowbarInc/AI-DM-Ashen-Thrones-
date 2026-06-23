# CA2 Path Classification Report

> CA2 Git collection and path-bucket accounting for the reviewed corrective cohort.

## Bucket definitions

### `production_runtime_source`

Executable product code under `game/` and `static/`, plus registered runtime packages.

Example paths:
- `game/api.py`
- `static/app.js`

### `tests`

Authored tests and helpers under `tests/`; excludes `codex_pytest_tmp*`.

Example paths:
- `tests/test_start_campaign_api.py`
- `tests/helpers/golden_replay.py`

### `docs_reports`

Human-authored docs under `docs/`, `audits/`, and report markdown.

Example paths:
- `docs/reports/openai_api_key_lazy_config_fix_20260520.md`
- `audits/cycle_f.md`

### `scripts_tools`

Tooling under `tools/`, `scripts/`, `.github/`, and build/CI/config files.

Example paths:
- `tools/bug_fix_locality_report.py`
- `.github/workflows/convergence-checks.yml`

### `fixtures_data`

Committed fixtures, snapshots, and scenario inputs under `data/` and `fixtures/`.

Example paths:
- `data/session.json`
- `data/scenes/frontier_gate.json`

### `generated_artifacts`

Generated output under `artifacts/`, `codex_pytest_tmp*`, caches, and coverage files.

Example paths:
- `artifacts/bug_fix_locality_report.md`
- `codex_pytest_tmp19/test_start_campaign_emits_open0/data/session.json`

### `unclassified`

Any changed path that does not match a higher-precedence bucket.

Example paths:
- `unknown.xyz`

## Cohort-wide bucket totals

- **production_runtime_source**: 36
- **tests**: 24
- **docs_reports**: 3
- **scripts_tools**: 0
- **fixtures_data**: 29
- **generated_artifacts**: 788
- **unclassified**: 0

- **Total changed paths:** 880
- **Unclassified paths:** 0

## Per-commit accounting

- **CA-01** `09863c6` — total=7, production=4, tests=0, fixtures=3, generated=0, unclassified=0
- **CA-02** `ceecc57` — total=20, production=8, tests=6, fixtures=4, generated=0, unclassified=0
- **CA-03** `6351b33` — total=16, production=9, tests=4, fixtures=3, generated=0, unclassified=0
- **CA-04** `2013258` — total=7, production=2, tests=2, fixtures=3, generated=0, unclassified=0
- **EX-01** `2b293b2` — total=3, production=0, tests=0, fixtures=3, generated=0, unclassified=0
- **CA-05** `9e83820` — total=7, production=3, tests=1, fixtures=3, generated=0, unclassified=0
- **CA-06** `1b3b3ee` — total=5, production=1, tests=1, fixtures=3, generated=0, unclassified=0
- **CA-07** `f487f4d` — total=216, production=2, tests=1, fixtures=3, generated=210, unclassified=0
- **CA-08** `f3fa4b1` — total=52, production=2, tests=2, fixtures=4, generated=44, unclassified=0
- **CA-09** `5cb8444` — total=538, production=2, tests=2, fixtures=0, generated=534, unclassified=0
- **CA-10** `6a402d2` — total=9, production=3, tests=5, fixtures=0, generated=0, unclassified=0
