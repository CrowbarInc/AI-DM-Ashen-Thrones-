# Repository Organization — Runtime / Development / Archive Boundaries

Date: 2026-09-20

This is a housekeeping report. It does not change Product Realization gameplay
priority.

## Before-state summary

Repository root mixed runtime entry points, standing governance, 123 campaign
reports (`AR-*`, `PR-*`, `CD`–`CX`), stale `scorecard.*` files, and 69 leftover
`codex_pytest_tmp*` directories. `pytest.ini` wrote `--basetemp=codex_pytest_tmp`
at root. The worktree was already dirty from Product Realization and earlier
validation work.

## Classification method

Classification used startup/import path resolution (`run.py`, `game/config.py`,
`game/storage.py`, `game/api.py`), test/tool path contracts, Constitution and
`NEXT_SESSION` live pointers, and a reference search before any move. Files
were not deleted. Historical prose mentions were not rewritten.

## Final directory structure

```text
repository root
├── run.py, requirements.txt, pytest.ini, Makefile, .env.example
├── game/                     runtime application
├── data/                     canonical + playthrough state; data/validation/ stays
├── static/                   frontend
├── tests/, tools/, scripts/  active engineering
├── docs/                     standing governance
├── artifacts/                generated evidence (unmoved)
├── audits/, handoff/, history/  existing contract/history owners (unmoved)
├── development/
│   ├── campaigns/
│   │   ├── reconciliation/        AR-* (36)
│   │   ├── product_realization/   PR-* (18)
│   │   └── foundation/            CD–CX (68)
│   ├── reports/                   this report
│   ├── archive/                   stale root scorecard.*
│   └── tmp/                       disposable pytest/agent output
└── leftover root codex_pytest_tmp*  already Git-ignored, not deleted
```

## Minimum runnable product

- Entry: `run.py` → `game.api:app`
- Python: entire `game/` package
- Data: `data/{campaign,character,conditions,world,session,combat}.json`,
  `data/session_log.jsonl`, `data/scenes/*.json`
- Frontend: `static/{index.html,app.js,styles.css}`
- Config: repo-root `.env` / `.env.example`, `requirements.txt`
- Not required to launch: `tests/`, `tools/`, `docs/`, `development/`,
  `artifacts/`, `data/validation/`

## Active engineering surface

`tests/`, `tools/`, `scripts/`, `docs/` (especially Constitution and
`NEXT_SESSION`), `data/validation/`, `.github/`, `pytest.ini`, `Makefile`,
`.cursor/rules/`.

## Historical archive

- Campaign reports: `development/campaigns/`
- Stray root scorecards: `development/archive/`
- Existing trees left in place: `audits/`, `docs/audits/`, `history/`,
  `handoff/history/`

## Temporary-output policy

New disposable pytest/agent output: `development/tmp/`
(`pytest.ini --basetemp=development/tmp/pytest`).

Git-ignored:

- `development/tmp/`
- `codex_pytest_tmp*/` (legacy leftovers)
- `artifacts/*pytest_tmp*/`, `artifacts/*pytest_reg*/`, `artifacts/*pytest_verify*/`
- `.venv-broken/`

Existing leftover temp dirs were not deleted.

## Constitution changes

Added:

- **Agent Working Set**
- **Repository File Placement and Generated Artifacts**
- session-exit generated-file placement sentence

Updated specialized-authority paths for `AR-AD` and `PR-AA`.

## Moved files / directories

| From root | To | Count |
|---|---|---|
| `AR-*.md` | `development/campaigns/reconciliation/` | 36 |
| `PR-*.md` | `development/campaigns/product_realization/` | 18 |
| `CD_*`–`CX_*` | `development/campaigns/foundation/` | 68 |
| `scorecard.md`, `scorecard.json` | `development/archive/` | 2 |

New: `development/README.md`, this report.

## Deliberately unmoved

| Path | Why |
|---|---|
| `game/`, `data/`, `static/`, `run.py` | Runtime owners |
| `tests/`, `tools/`, `scripts/`, `docs/` | Active engineering / governance |
| `artifacts/` | Established generated-evidence sink; moving it would break many live paths |
| `data/validation/` | Active validation inputs; tests/tools depend on the path |
| `audits/` | Test/tool path contracts (`audits/failure_dashboard_latest.md`, etc.) |
| `handoff/` | Constitution review-export owner |
| `history/` | Already a named historical owner |
| Root `codex_pytest_tmp*` | Disposable leftovers; already ignored; not unique committed evidence |
| `artifacts/*pytest_*` leftovers | Same; now ignored going forward |

## `.gitignore` changes

Added `development/tmp/`, `artifacts/*pytest_{tmp,reg,verify}*/`, and
`.venv-broken/`. Kept `codex_pytest_tmp*/`.

## Path / reference updates

Operational paths updated in Constitution, `NEXT_SESSION`, `docs/README.md`,
`docs/audits/documentation_governance.md`, `tests/README_TESTS.md`,
`pytest.ini`, hotspot/recurrence helpers, locality classifiers,
`docs/processes/hotspot_compression_measurement_standard.md`,
`docs/runbooks/protected_replay_observation_collection.md`, and
`artifacts/policy_resolution/policy_evidence_manifest.json`.

Historical campaign-report prose still mentions old filenames. Those are
historical statements, not live open paths.

## Verification

- Runtime import: `from game.api import app` succeeded; `ROOT_DIR` / `DATA_DIR` /
  `static/index.html` / `run.py` resolve at repo root. Live server was not
  bound; startup path and imports were checked instead.
- Focused pytest: passed
  `tests/test_perception_narration_authority_audible_non_invention.py`,
  `tests/test_corrective_change_locality_classifier.py`,
  `tests/test_replay_bug_class_recurrence.py`,
  `tests/test_ck_hotspot_compression_report.py`.
- Tools: `tools/run_prar_freeform_probe.py` and
  `tools/run_playability_validation.py` compile.
- `docs/NEXT_SESSION.md` named paths: all exist.
- Broken-reference search: live operational paths in `docs/`, `tests/`,
  `tools/`, `scripts/`, and `.github/` now use `development/campaigns/...`.
  Remaining filename mentions are historical prose inside archived campaign
  reports.
- Git: one repository at root; no nested `.git` under `development/`, `game/`,
  `data/`, or `artifacts/`. Relocations are present as Git renames. Previously
  untracked `PR-AC`–`PR-AR` remain untracked in the new Product Realization
  campaign directory. `development/tmp/` is Git-ignored.

## Remaining risks

- Git may record many foundation/AR moves as add+delete rather than rename
  depending on index state; files themselves are preserved.
- Leftover root `codex_pytest_tmp*` dirs still exist until a later cleanup
  chooses to delete them.
- `handoff/CURRENT_REVIEW.*` remains a stale generated review export (pre-existing).
- Dirty worktree from Product Realization and earlier campaigns remains.
