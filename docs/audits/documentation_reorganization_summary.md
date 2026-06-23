# Documentation Reorganization Summary

Date: 2026-06-23

## Outcome

The repository-wide documentation review consolidated high-confidence audit-cycle documents into
the canonical `docs/audits/` folder structure without modifying production code or tests. Files with
generator-owned, test-owned, or otherwise ambiguous paths were left in place.

## Inventory and move totals

| Measure | Result |
|---|---:|
| Raw `.md`, `.txt`, `.rst`, `.csv`, and `.json` paths scanned | 7,315 |
| Human documentation and clearly named report/evidence records inventoried | 673 |
| Files moved | 116 |
| Tracked files moved with `git mv` | 115 |
| Pre-existing untracked CC discovery moved without content changes | 1 |
| Inventoried files left in place | 557 |
| Ambiguous/path-pinned files classified `G` | 319 |
| Active documentation files with references updated | 13 |
| Production files modified | 0 |
| Test files modified | 0 |
| Files deleted | 0 |

The complete pre/post classification is in `docs/audits/documentation_inventory.csv`.

## Move summary

- 49 discovery documents are now under `docs/audits/discovery/`.
- 56 closeout/closure/summary documents are now under `docs/audits/closeouts/`.
- 2 scaffold or Codex instruction files are now under `docs/audits/scaffolds/`.
- 8 metric/contract/regression documents are now under `docs/audits/metrics/`.
- 1 retained full-suite output is now under `docs/audits/evidence/`.
- The `ledgers/`, `archived/`, and `needs_review/` folders were established for future safe migrations.

## Items left for human review

| Area | Approximate inventory | Reason left in place |
|---|---:|---|
| Flat `docs/audits/` files | 257 classified review items | Many are generated, path-guarded, or densely cross-referenced |
| Legacy `audits/` files | 61 classified review items | Tests and report writers hard-code several paths |
| Generated `artifacts/` reports and evidence | 130 medium-confidence inventory rows | Writers and historical reports may require exact output paths |
| Remaining `docs/cycles/` block documents/data manifests | 17 plus README | Mixed implementation evidence and machine-readable cycle data |
| Audit-like documents in `docs/` | 17 | Several are active architecture, validation, or test/tool path authorities |

Five initially proposed moves were explicitly reversed after path-contract checks:

- `docs/gate_convergence_closeout.md`
- `docs/BS_semantic_replacement_attribution_discovery.md`
- `docs/BRL2_bug_fix_locality_regression_guard.md`
- `docs/reports/BR_bug_fix_locality_measurement.md`
- `docs/cycles/cycle_r_block_r4_inventory_registry_refresh_2026-05-30.md`

## Reference updates

References to moved files were updated mechanically in active documentation only. Historical
discovery/closeout contents were not rewritten. Tests, tools, scripts, workflows, and production code
were searched for old paths; no stale references to the final move set remained in those areas before
validation.

## Validation

Commands used:

```powershell
git status --short
rg --files -g '*.md' -g '*.txt' -g '*.rst' -g '*.csv' -g '*.json' ...
rg -l -F <old-path> game tests scripts tools .github docs
python tools/test_audit.py --check
```

Final validation results and warnings:

- `git status --short`: completed; changes are documentation moves/edits plus the preserved pre-existing artifact modification.
- Root audit/report filename scan: `ROOT_AUDIT_FILES=0`.
- Active code/test/CI stale-path scan: `ACTIVE_CODE_TEST_REFERENCE_HITS=0`.
- Historical reports still contain old paths by design; they were not rewritten.
- `tools/test_audit.py --check`: passed; 5,806 tests derived, 64 registry-owned files, 406 total test files.
- `tests/test_split_owner_acceptance_matrix_contract.py`: 10 passed.
- The first validation attempt could not locate `python`/`py`; validation was rerun successfully with the bundled Python runtime and `.venv` site packages.
- The pre-existing modification to `artifacts/cb6_speaker_fallback_frequency.json` was preserved.
- No feature work was started.
