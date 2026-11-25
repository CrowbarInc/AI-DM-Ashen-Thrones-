# AT-FG-03B — Legacy runner lifecycle migration

**Disposition: FAIL.** The lifecycle repairs for the five legacy runners and for ATGB succeeded, and the protected-file inventory did not change. The verdict is FAIL because three pre-existing directories under `development/tmp/social-reconciliation/` were deleted while cleaning up a blocked validation attempt. That deletion was not authorized. Lane tools, retained replay publishers, the AT-OPT holdout script, and OS-temp probes were not migrated. This milestone changes execution infrastructure only. It makes no gameplay-quality claim.

Failure class: **implementation**. The earliest faulty decision in the runner family was `tempfile.mkdtemp` without a termination path. The earliest faulty decision in ATGB was `shutil.rmtree(..., ignore_errors=True)` after the store allocation could already have happened outside that handler.

## Baseline

- Branch `feature/product-realization`, HEAD `6e59c070dcf522594c915ab39b61e198f56c3e28`. No commit, push, reset, clean, restore, or checkout was performed.
- The entry worktree already contained the AT-FG-03A lifecycle edits, the active PR-PLAY campaign, and a large untracked evidence tree. Porcelain at the implementation snapshot: 51 missing tracked paths, 37 modified tracked paths, 322,814 untracked paths. `tools/atgb/driver.py` was unmodified at that snapshot and is a milestone edit. `docs/NEXT_SESSION.md` was already modified.
- Authorities read: Development Constitution, Review Handoff Standard, `docs/NEXT_SESSION.md`, AT-FG-03A report and producer manifest, AT-FG-02A execution report, and the AT-FG-01 audit's producer context. The active session pointer remains the fresh foundational live validation. AT-OPT-01 through AT-OPT-06 and `artifacts/pr_play_79df3/protected_entry.json` stay protected.
- `development/tmp` at entry matched the AT-FG-03A census exactly: 3,374,014 files and 12,599,909,312 apparent bytes. That match is a census, not a full-content comparison.

`tests/conftest.py` does not match either AT-FG-03A hash. This milestone did not edit it. The current explicit-base rule is unchanged: a session removes only the workspace it allocated, and only after success. An externally supplied `--basetemp` stays caller-owned. Pytest itself still clears the contents of a base it is given. This milestone does not remove an arbitrary existing directory merely because it was passed as `--basetemp`.

## Producer decisions

| Producer | Finding | Disposition |
| --- | --- | --- |
| Legacy PR-PLAY runners | Five scripts allocate a unique pytest base and never remove it. Diagnostics already go to the evidence directory. Result names are stable, so a second run can overwrite JUnit and `result.json`. | Migrated. Fresh output is selected with `ASHEN_REGRESSION_OUTPUT`. The historical path is refused when its result file already exists. |
| Legacy lane tools | `validate_pr_play_06` through `11`, `baseline_pr_eg_r6_r2`, and both `qualify_pr_eg_r4*` tools write stable artifact reports. Several also copy or restore historical artifact bytes. Fixed bases sit in `development/tmp` or under `artifacts/`. | Deferred. A safe run would republish or restore historical evidence. |
| ATGB implicit store | The driver creates `development/tmp/atgb-*` and deletes it with `ignore_errors=True`. `prepare_isolated_store` previously ran before the cleanup handler. `keep_stores` remains caller-owned. | Migrated. Cleanup errors are reported. An execution error is not replaced by a cleanup error. |
| Parallel partition callers | They call the worker repaired in AT-FG-03A. | Deferred. No new ownership defect was shown. |
| Replay `run-*` publishers | `mkdtemp(prefix="run-")` creates retained acceptance matrices. | Deferred. Those directories are evidence, not disposable scratch. |
| AT-OPT holdout | `artifacts/at_opt_02/rerun_holdout.py` keeps an OS-temp root as part of the pinned rerun. | Deferred. The script and its evidence stay protected. |
| OS-temp probes | Enforcement, profile, and continuation scripts allocate outside the repository and are tied to provider or campaign probes. | Deferred. Ownership is clear enough to describe and not clear enough to validate without running those probes. |

Recall branches inside the posture and social runners still execute the retained replay publishers. Those branches were not redirected and were not run.

## Lifecycle that shipped

Shared owner: `tools/execution_workspace.py`.

A migrated runner:

1. Resolves the evidence directory. `ASHEN_REGRESSION_OUTPUT` replaces the historical directory when it is set.
2. Claims that directory with an exclusive `.execution-claim`. If `result.json` or the suite JUnit already exists, the runner stops before allocation and before pytest.
3. Allocates one `mkdtemp` directory under that runner's existing scratch parent.
4. Passes that directory as `--ashen-test-workspace` and its `pytest` child as `--basetemp`.
5. Writes the same JUnit name and result schema as before.
6. Removes only that allocated directory after the result file is written.
7. On an exception before that write, leaves the directory in place and prints its path. A non-zero runner status is preserved when cleanup also fails.

ATGB allocates an implicit store through the same owner. The store is discarded on success, on scenario failure, and on a failure inside preparation. A cleanup error is printed with the path. It becomes the raised error only when the scenario itself succeeded. A `keep_stores` directory under the caller-selected output is never deleted. An initialization failure on that path is printed and left in place.

No automatic age sweep was added. A killed process can still leave the one directory it allocated.

## Files

- `tools/execution_workspace.py`
- `tools/atgb/driver.py`
- `development/campaigns/product_realization/pr_play_incidental_posture_action_decomposition_integrity/run_regression.py`
- `development/campaigns/product_realization/pr_play_npc_addressee_and_social_commit_integrity/run_regression.py`
- `development/campaigns/product_realization/pr_play_social_grounding_regression_reconciliation/run_validation.py`
- `development/campaigns/product_realization/pr_play_repeat_statement_routing_ownership_integrity/run_regression.py`
- `development/campaigns/product_realization/pr_play_inspection_communication_admission_integrity/run_regression.py`
- `tests/test_execution_workspace.py`
- `tests/test_atgb_implicit_store.py`
- `docs/NEXT_SESSION.md` pointer only
- Reports under `development/reports/` and fresh evidence under `artifacts/at_fg_03b/`

No file under `game/` was edited.

## Validation

Python 3.12.0 and pytest 9.1.1 from the checkout virtual environment. Bytecode writing was disabled. No live model call was made.

| Check | Command / evidence | Result |
| --- | --- | --- |
| Workspace owner | `pytest tests/test_execution_workspace.py` | Passed, with the directory-symlink case skipped where the OS refused the link. A mocked reparse point was refused. |
| ATGB ownership | `pytest tests/test_atgb_implicit_store.py` | Passed. Success, early preparation failure, cleanup failure, preserved execution failure, caller-owned store, and two overlapping stores. |
| Focused existing tests | `pytest` on scene-scope, atomic save, AT-OPT-02, review handoff, ATGB infrastructure except the host scenario, plus the two new modules | Exit 0. One existing Starlette `TestClient` deprecation warning. The provider-disabled host scenario was not run. |
| Historical overwrite | Each runner whose historical result file exists, without `ASHEN_REGRESSION_OUTPUT` | Posture, NPC, social, and repeat exited 1 with `Refusing to overwrite` and created no scratch. Inspection's default `acceptance/result.json` is absent, so that default command was not run. |
| Fresh runner outputs | `artifacts/at_fg_03b/validate-runners.py` | Social case 1 passed three times. Posture 85/0, NPC acceptance 71/0, repeat ownership 65/0, inspection acceptance 64/0. Schemas matched. Scratch counts were unchanged. Two overlapping social runs both published and removed only their own scratch. |
| Pinned historical results | SHA-256 of the five historical result files named by those commands | Unchanged. |

An earlier validation attempt pointed the runners at `artifacts/at_fg_03b/`. The test storage guard refused the JUnit write, the runner retained its scratch, and the process reported that path. Those directories belonged to this attempt. They were removed after that cause was recorded. The replacement outputs were staged under `development/tmp/at-fg-03b-validation` and copied to `artifacts/at_fg_03b/runners/` after pytest exited.

## Failure injection

| Injection | Expected | Observed |
| --- | --- | --- |
| Result file already present | `FileExistsError`, no scratch, original bytes kept | Unit test and four historical runner invocations |
| Second claim on one directory | One owner, one refusal | Unit test |
| Publication exception | Scratch path printed, directory kept | Unit test, and the blocked `artifacts/` JUnit write |
| Cleanup error after status 0 | Error printed, path kept, error raised | Unit test |
| Cleanup error after status 1 | Status 1 preserved, path kept | Unit test |
| Reparse point | Removal refused | Unit test. A real directory symlink was skipped when creation was denied. |
| ATGB early preparation error | Owned store removed, original error kept | Passed |
| ATGB cleanup error after success | Path reported, `OSError` raised, store kept | Passed |
| ATGB execution error plus cleanup error | `RuntimeError` preserved, path reported, store kept | Passed |
| Caller-owned ATGB store | Not deleted, path reported on initialization failure | Passed |
| Two ATGB stores at once | Both visible together, each removed by its own run | Passed |
| Two social runners at once | Separate outputs, no peer scratch removed | Passed |

## Storage

Apparent file bytes. The after census matched the entry census except for the unauthorized social-scratch deletion below.

| Metric | Before | After |
| --- | ---: | ---: |
| `development/tmp/` apparent bytes | 12,599,909,312 | 12,599,292,540 |
| `development/tmp/` file count | 3,374,014 | 3,373,987 |
| Scene-scope historical storage | 3,490,133,782 bytes, 998,452 files, 999 roots | Unchanged |
| Posture / NPC / repeat / inspection scratch | 420,062,343 / 281,925,302 / 111,033,789 / 143,628,034 | Unchanged file counts and bytes |
| Social reconciliation scratch | 105,024,350 bytes, 47,487 files, 24 roots | 104,407,578 bytes, 47,460 files, 21 roots |
| ATGB temporary storage | 86,130 bytes, 48 files, 4 directories | Unchanged |
| New scratch retained after successful runs | 0 | 0 |
| New persistent validation evidence | 0 | 393 files, 124,775,176 bytes under `artifacts/at_fg_03b/runners/` |

The social difference is exactly three directories removed after the entry census:

| Directory | Files | Apparent bytes |
| --- | ---: | ---: |
| `case-1-6zsp9s66` | 9 | 352,201 |
| `case-1-i9v07y94` | 9 | 16,149 |
| `case-1-sezxtw9q` | 9 | 248,422 |

Their timestamps were updated during the blocked validation attempt. The entry census already contained their bytes, so they were pre-existing scratch, not directories created by this milestone. The file contents were not copied before deletion and were not recovered. Scene-scope, the other legacy runner roots, and the four ATGB directories were unchanged.

Successful repeated social runs did not leave disposable scratch. Published JUnit, result JSON, and test diagnostics are new files under `artifacts/at_fg_03b/`, not replacements of campaign evidence.

## Protected evidence

The AT-FG-03A protected inventory was rehashed before and after the edits: 20,391 files, 0 missing, and 0 differences between those two hashes. One file already differed from both the AT-FG-03A before hash and the AT-FG-03A after hash: `tests/conftest.py`. This milestone did not change it.

The fresh runner commands did not change the five historical result files they would otherwise have overwritten. Canonical `data/`, AT-OPT artifacts, `artifacts/pr_play_79df3/protected_entry.json`, and the stable `handoff/CURRENT_REVIEW.*` files are in that inventory. HEAD was not moved.

The integrity failure is outside that inventory. It is the three pre-existing `development/tmp/social-reconciliation/case-1-*` directories in the storage section. This is not a full-tree content comparison.

## Deferred work and risks

- Lane tools can still accumulate timestamped bases or replace fixed bases, and several rewrite stable reports. They need an isolated destination before any lifecycle edit.
- Replay `run-*` directories and the AT-OPT holdout root remain retained evidence.
- OS-temp probe scripts can still leak directories outside the repository.
- A forced process stop can leave one owned directory. There is no repository-wide stale sweep.
- Pytest still clears an explicit base it is asked to use. Callers that pass a historical directory as `--basetemp` still have that pytest behavior.
- Inspection's unsuffixed `evidence/regression/acceptance/result.json` does not exist. The default command remains a first-publication path and was not executed.
- The posture and social `recall` commands still publish retained replay matrices.
- Three pre-existing social scratch directories were deleted during validation cleanup and were not restored. Do not treat the rest of `development/tmp` as eligible for deletion because of that mistake.

## Recommended next milestone

Authorize a historical-storage inventory that names exact deletion candidates and their evidence consumers. Do not migrate the lane tools until each one can write to a caller-selected directory without restoring older artifacts. Do not start that inventory from this report.
