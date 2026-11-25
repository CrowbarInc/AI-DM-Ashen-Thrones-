# AT-FG-03B-R1 — Ownership safeguards

**Disposition: PASS.** The deletion mechanism is established. Cleanup of the repaired lifecycle paths now requires a creation secret from the allocating execution. Uncertain ownership is refused. The pre-existing `development/tmp/social-reconciliation/` tree matches its entry manifest file for file. No historical review package, AT-OPT tree, or active PR-PLAY campaign tree changed. This milestone does not recover storage and does not restore the deleted files.

## Repository baseline

- Branch `feature/product-realization`. HEAD `6e59c070dcf522594c915ab39b61e198f56c3e28`. Index tree `fc777dc562a98f64acbaf1b2abc7bd7a5319aecb`. Both were the same after validation. No commit, push, reset, clean, or checkout.
- Entry porcelain, collapsed untracked directories: 38 modified tracked paths, 51 missing tracked paths, 270 untracked status lines. Those modifications were already present. `tools/atgb/isolation.py` was not in that modified set and is a milestone edit.
- `development/tmp` census during preflight: 3,373,987 files, 12,599,292,540 bytes, 272,601 directories. That matches the AT-FG-03B after census exactly. `artifacts/` at the same census: 418,190 files, 11,523,779,833 bytes.
- One Python process was running at preflight: the baseline capture itself.
- Authorities read: Development Constitution, Review Handoff Standard, `docs/NEXT_SESSION.md`, AT-FG-01 audit, AT-FG-02A execution report, AT-FG-03A execution report and producer manifest, AT-FG-03B execution report, producer manifest, storage censuses, and integrity comparison. A separate AT-FG-02A verification report was not found. The execution report contains the verification record. The active session pointer remains the fresh foundational live validation.

## Files changed

- `tools/execution_workspace.py` — creation secret and fail-closed `discard`.
- `tools/atgb/isolation.py` — a new store may contain only the owner file; any other existing name still refuses the store.
- `tests/conftest.py` — the default session discards through the helper.
- `tests/test_execution_workspace.py` — adversarial ownership tests.
- `development/campaigns/product_realization/pr_play_current_scene_evidence_scope_integrity/run_regression_partitions.py` — partition cleanup goes through the helper.
- `docs/NEXT_SESSION.md` — pointer only, added after the source comparison below.
- Reports under `development/reports/AT-FG-03B-R1_*`. Evidence under `artifacts/at_fg_03b_r1/`. Review under `handoff/history/at_fg_03b_r1/`.

The five migrated runners and `tools/atgb/driver.py` already called the helper. Their sources were not edited. No file under `game/` was edited.

## Ownership safeguards

A directory is removed only when this execution allocated it, still holds the secret written into `.ashen-execution-owner`, the path still resolves to that directory inside the allowed root, the parent is unchanged, and the tree contains no reparse point. A prefix, a glob, an age, or a location under `development/tmp/` is not ownership.

`finish_owned` refuses removal when the publication files are absent, prints the path, and preserves a non-zero status. `discard` raises `WorkspaceOwnershipError` and leaves the directory when the secret does not match.

The check and `shutil.rmtree` are not one transaction. A replacement in that gap is not prevented. The tests cover a replacement that happens before the check.

## Validation commands

Python 3.12.0 and pytest 9.1.1 from `.venv`. Bytecode writing was disabled. No live model call was made.

| Check | Command | Result |
| --- | --- | --- |
| Ownership and ATGB store | `pytest tests/test_execution_workspace.py tests/test_atgb_implicit_store.py -p no:cacheprovider --tb=short` | 24 passed, 1 skipped, 14.64s |
| Focused regressions | `pytest` on scene-scope, atomic save, AT-OPT-02, review handoff, and ATGB infrastructure except the host scenario | 136 passed, 1 deselected, 43.35s. One existing Starlette `TestClient` deprecation warning |
| Fresh runners | `artifacts/at_fg_03b_r1/validate-runners.py` | Exit 0. See below |
| Scene-scope worker | `run_regression_partitions.py posture 0 --output-dir <fresh sandbox>` | 17 passed, 68 deselected. Immediate scene-scope names unchanged |

## Adversarial tests

All of these ran inside the pytest session workspace or read the entry inventory. None deleted a path that existed before the milestone.

| Test | Expected | Observed |
| --- | --- | --- |
| Pre-existing `case-1-*` directory | The new workspace is removed. The pre-existing directory remains. | Passed |
| Neighbor beside the new workspace | Only the new workspace is removed. | Passed |
| `mkdtemp` raises | The guessed pre-existing path remains. | Passed |
| Published non-zero status | The result file remains and the owned workspace is removed. | Passed |
| Publication files absent | The workspace remains and the path is printed. A non-zero status is returned when the run already failed. | Passed |
| Injected `rmtree` failure | The error is printed, the workspace remains, and a failed status stays 1. | Passed |
| Two workers | One cannot discard the other's path. Each removes only its own. | Passed |
| Directory replaced after allocation | Removal is refused. The replacement's file remains. | Passed |
| Directory junction inside the workspace | Removal is refused. The protected marker remains. | Passed. A pure directory symlink was unavailable, so the older symlink-only test skipped. The junction fallback ran. |
| Historical social inventory | Every immediate directory fails the ownership check. Nothing is deleted. | Passed. 21 directories checked, including `__pycache__`. |

## PR-PLAY revalidation

Fresh outputs under `artifacts/at_fg_03b_r1/runners/`. Historical result files were not overwritten.

| Runner | Result | Scratch names |
| --- | --- | --- |
| Posture | 85 passed, 0 failed | Unchanged |
| NPC acceptance | 71 passed, 0 failed | Unchanged |
| Social case 1 | 1 passed, 0 failed | Unchanged |
| Repeat ownership | 65 passed, 0 failed | Unchanged |
| Inspection acceptance | 64 passed, 0 failed | Unchanged |
| Two overlapping social case-1 runs | Both exit 0, both published | No name added or removed |

Posture, NPC, social, and repeat each refused to overwrite their historical result and created no scratch. Inspection's unsuffixed acceptance result is still absent, so that default command was not run. Recall branches were not run.

## ATGB revalidation

`tests/test_atgb_implicit_store.py` passed as part of the 24-test run. That module covers a successful simulated store, early preparation failure, cleanup failure, an execution failure preserved when cleanup also fails, a caller-owned store, and two overlapping stores. No live provider benchmark was run. The four pre-existing `atgb-S06-*` directories are still the only `atgb-*` directories.

## Pytest revalidation

A child pytest process with no `--basetemp` removed only the `pytest-run-*` directory it created. A child process given a fresh `--basetemp` left the neighboring marker in place and did not remove any pre-existing `pytest-run-*` name. Pytest can still clear the contents of a base it is given. This run did not pass a historical path as that base.

## Cleanup failure behavior

An injected `OSError` from `shutil.rmtree` is printed with the workspace path. The directory stays. `finish_owned` returns the original non-zero status when the run had already failed, and raises when the run had succeeded. A missing publication file is refused before `rmtree`.

## Concurrency

Two social runners overlapped and each published its own result. The social name set was unchanged afterward. The unit test ran two allocators together. Discarding one left the other's marker readable. A second object constructed on the peer path, with a different secret, was refused.

## Storage measurements

| Metric | Entry | After validation |
| --- | ---: | --- |
| `development/tmp` files / bytes | 3,373,987 / 12,599,292,540 | Full tree not walked again. Named roots below were. |
| Social reconciliation files / bytes / content SHA-256 | 47,459 / 104,398,729 / `58e431f95175ce350d055fd9196b158189736ea9f74c7165dde2de3e815b7fc9` | Identical. 0 missing, 0 added, 0 changed. |
| Scene-scope, posture, NPC, repeat, inspection | Per-child content digests in `artifacts/at_fg_03b_r1/baseline/named-tmp-roots.json` | No child digest changed. |
| New evidence under `artifacts/at_fg_03b_r1/` before the review bundle | 0 | 415 files, 130,144,088 bytes |
| `pytest-run-*` or `at-fg-03b-r1-*` left behind | — | None |

The social figure is 1 file and 8,849 bytes below the AT-FG-03B social subtotal, while the whole-tree census matches that milestone's after census exactly. The R1 comparison uses the R1 content manifest, not the earlier subtotal.

## Historical integrity comparison

Compared after the runner, pytest, ATGB, and scene-scope runs, and before the session-pointer edit:

1. HEAD unchanged.
2. Index tree unchanged.
3. Pre-existing tracked modifications were not reverted. The milestone added `tools/atgb/isolation.py` and further edits to `tests/conftest.py`.
4. The 51 missing tracked paths were not restored.
5. Social file membership: 47,459 paths before and after.
6. Social file hashes: exact match.
7. Other named temporary roots: per-child content digests unchanged. This is every immediate child, not a sample.
8. `handoff/history/at_fg_03a` and `handoff/history/at_fg_03b` content hashes unchanged.
9. `artifacts/at_opt_01` through `artifacts/at_opt_06` content hashes unchanged.
10. `development/campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation` content hash unchanged.

Stable `handoff/CURRENT_REVIEW.md`, `CURRENT_REVIEW.zip`, and `REVIEW_MANIFEST.json` were hashed at entry. The review for this milestone was generated with `--no-history` into `artifacts/at_fg_03b_r1/review-stage/` and copied only to `handoff/history/at_fg_03b_r1/`. The stable trio was hashed again after that copy.

Coverage limit: `development/tmp` as a whole was not content-hashed again after validation. The exact comparison is the social tree. The other runner roots and scene-scope are covered by a content digest of each immediate child. A file outside those named roots could change without appearing in this comparison. The only `atgb-*` names present after validation are the four that were already there.

`docs/NEXT_SESSION.md` was edited after that source comparison. Its entry hash was `22837b421fb2d68a98c88d05bab2294cbce087ccdbf0d833c3cf999e4c376c83`.

## Remaining limitations

- Check-then-delete is not atomic.
- `artifacts/at_fg_03b/validate-runners.py` still removes a fixed staging path if it exists. It was not run and was not edited.
- Lane tools, replay publishers, the AT-OPT holdout, and OS-temp probes do not use the creation secret.
- A killed process can leave the one directory it allocated.
- The 27 deleted files have no names and no hashes. They were not restored.
- Directory symlink creation was denied. Junction refusal was tested.
- Only posture partition 0 of the scene-scope worker was re-run.

## Recommended next milestone

Review this PASS and the incident report. Do not start historical cleanup, restoration, or another governance milestone from this report. When a cleanup inventory is explicitly authorized, name exact paths and their consumers from the R1 manifests. Do not select them by prefix or age.
