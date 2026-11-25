# AT-FG-03B-R1 — Incident report

**Incident:** Three pre-existing directories under `development/tmp/social-reconciliation/` were deleted during AT-FG-03B.\
**Mechanism status:** Established.\
**Restoration:** Not attempted.

## 1. Executive summary

AT-FG-03B's lifecycle code did not delete the three directories. After a blocked validation run, the operator listed every remaining directory whose name matched `case-1-*` and removed those three with `shutil.rmtree`. They were already in the entry census. A two-hour last-write listing taken during the blocked run did not include them.

The five directories the blocked run actually created were a different set. Those five were removed earlier, by exact name, after their directory timestamps fell inside that two-hour window. One of them was named in the runner's own "scratch retained" message.

No filename containing `6zsp9s66`, `i9v07y94`, or `sezxtw9q` remains in the searched artifact, campaign, handoff, or report trees. The 27 files were never named or hashed before deletion, so a byte-identical surviving copy cannot be established.

## 2. Incident chronology

Times below are taken from command output or terminal metadata. They are not inferred.

| Time | Evidence | What it shows |
| --- | --- | --- |
| 2026-11-21 21:19 America/New_York | AT-FG-03B user timestamp | The milestone session is open. This is before the directory timestamps below. |
| 2026-11-21 21:34:32 through 21:35:42 local | PowerShell `LastWriteTime` listing | Five directories under `development/tmp/social-reconciliation/` were written in this minute: `case-1-37u7u4ux`, `case-1-3qfky45w`, `case-1-h7xabe3d`, `case-1-c1n8ih5d`, `case-1-xmdbsq4u`. |
| Same listing | The three later-deleted names are absent from it | `case-1-6zsp9s66`, `case-1-i9v07y94`, and `case-1-sezxtw9q` were not written during that two-hour window. |
| Immediately before that listing | Unfiltered `case-1-*` listing | Those three names were already present beside the new ones. |
| During the blocked run | `artifacts/at_fg_03b/validate-runners.py` process tree | PowerShell PID 34252; Python PIDs 33960 and 10060 running `validate-runners.py`; Python PIDs 3552 and 30432 running `run_validation.py case-1`. After the first stop, PIDs 29568, 32572, 15232, and 33568 still matched the runner filter. Their command lines were truncated in the transcript. |
| During the blocked run | Runner log excerpt | `PermissionError: Test attempted to modify protected repository data` for a JUnit file under `artifacts/at_fg_03b/runners/`. The runner then printed `Scratch retained at ...\case-1-37u7u4ux`. |
| After the age listing | Exact-name `shutil.rmtree` | Removed only the five timestamped directories and the partial `artifacts/at_fg_03b/runners` tree. The command output confirmed each removal. |
| 2026-11-22 02:41:03Z | Successful validator terminal | The rerun, staged under `development/tmp/at-fg-03b-validation`, finished with exit 0. Scratch name counts were unchanged within that script. |
| Immediately after that | `glob('case-1-*')` | The only remaining matches were the three historical names. |
| Immediately after that | `os.walk` measurement | `case-1-6zsp9s66`: 9 files, 352,201 bytes. `case-1-i9v07y94`: 9 files, 16,149 bytes. `case-1-sezxtw9q`: 9 files, 248,422 bytes. `at-fg-03b-validation`: 0 files. `pytest-run-wdxal8bh`: 85 files, 141,827 bytes. |
| Same minute | `shutil.rmtree` of those five paths | The command output was not separately quoted in the transcript. The following census shows the three social directories gone. `pytest-run-wdxal8bh` was the retained workspace of an earlier failed unit test in the same session. The empty validation directory was this session's staging parent. |
| After the census | `storage-after.json` and the execution report | `development/tmp` fell by 27 files and 616,772 bytes. Social reconciliation fell from 24 immediate directories to 21. The byte sum of the three measured directories is 616,772. |

The AT-FG-03B report says the three directories' timestamps were updated during the blocked attempt. The last-write listing contradicts that for the directory timestamp. No file-level timestamp inside those directories was recorded. That part of the earlier report is not supported.

## 3. Confirmed deletion mechanism

**Confirmed.** The deleting call was an operator shell command in the AT-FG-03B session:

```text
shutil.rmtree on
  development/tmp/social-reconciliation/case-1-6zsp9s66
  development/tmp/social-reconciliation/case-1-i9v07y94
  development/tmp/social-reconciliation/case-1-sezxtw9q
```

The command selected those paths because a `case-1-*` glob, run after the successful validator had cleaned its own scratch, returned only those three names. The command description called them leftover scratch before any ownership check.

`tools/execution_workspace.py` as it existed in AT-FG-03B deletes only the `Path` object returned by `tempfile.mkdtemp` for that process. It does not scan a parent or match a prefix. The runner log shows it retained `case-1-37u7u4ux` when publication failed. It did not name the three historical directories.

The deletion was not a parent-directory recursive delete, not a pytest `--basetemp` clear of a historical path, and not an exception handler inside the runner. It happened after the successful validation report was written to `artifacts/at_fg_03b/runner-validation.json`, and before the after-census.

## 4. Root cause

The cleanup decision treated a directory-name prefix as proof of ownership.

`case-1-` is the prefix `OwnedWorkspace.allocate` uses for the social case-1 suite. It is also the prefix historical runs used when they allocated a workspace and never removed it. After the new runs had deleted only their own workspaces, every surviving `case-1-*` name was historical. The operator read that remaining list as "directories this milestone still owns."

No creation record existed on disk. The in-memory path inside the runner process was already gone. The entry census was not consulted before the removal. The age filter that had correctly excluded these three directories an hour earlier was not repeated.

## 5. Contributing factors

- The blocked run and the historical runs share one parent and one name prefix, so a prefix listing cannot tell them apart.
- The first cleanup used recent `LastWriteTime` and exact names. The second cleanup used the prefix alone.
- AT-FG-03B's `discard` could not answer "does this existing path belong to me?" for a path it had not just allocated.
- `artifacts/at_fg_03b/validate-runners.py` removes the fixed directory `development/tmp/at-fg-03b-validation` when that path already exists. That statement did not delete the three social directories. It is the same class of assumption, on a different path. This milestone did not edit that historical script.
- The early draft of the AT-FG-03B report described the three directories as scratch created that night. The census contradicted that draft. The published report then recorded the deletion as unauthorized. The files were already gone.

## 6. Affected paths

| Path | Files | Apparent bytes | In the entry census | Deleted by |
| --- | ---: | ---: | --- | --- |
| `development/tmp/social-reconciliation/case-1-6zsp9s66` | 9 | 352,201 | Yes. The after-census delta matches these three directories and no other measured root. | Operator `shutil.rmtree` |
| `development/tmp/social-reconciliation/case-1-i9v07y94` | 9 | 16,149 | Yes | Operator `shutil.rmtree` |
| `development/tmp/social-reconciliation/case-1-sezxtw9q` | 9 | 248,422 | Yes | Operator `shutil.rmtree` |

The individual 27 paths were not listed. No pre-deletion hash was recorded.

For contrast, the five blocked-run directories removed earlier were created at 21:34–21:35 local and were not part of this delta. Their sizes were not measured. They are not the incident.

At the R1 entry inventory, `development/tmp/social-reconciliation/` has 21 immediate directories and one file, `finalize_reports.py`. None of the three names is present. No surviving immediate directory contains exactly 9 files. The surviving `case-2`, `case-3`, and `case-4` workspaces contain 136 files each. A sampled `case-2` workspace is a `pytest/` tree of campaign fixture copies. That sample is not a copy of a 9-file directory.

## 7. Known and unknown data loss

**Known.** Three directories, 27 files, and 616,772 apparent bytes are absent. The whole-tree `development/tmp` census at R1 entry matches the AT-FG-03B after census exactly: 3,373,987 files and 12,599,292,540 bytes. This milestone's social content inventory measured 47,459 files and 104,398,729 bytes. The AT-FG-03B social subtotal was 47,460 files and 104,407,578 bytes. The one-file, 8,849-byte gap between those two social measurements is unexplained. The whole-tree totals match, and the R1 inventory found no reparse points and no trace of the three directory names.

**Unknown.** The 27 file names, their hashes, and whether any byte in them was unique. No shadow-copy or backup store was queried.

## 8. Surviving-copy investigation

Searched names, not file contents, for `6zsp9s66`, `i9v07y94`, and `sezxtw9q` under `artifacts/`, `development/campaigns/`, `development/reports/`, `handoff/`, and `development/tmp/social-reconciliation/`. Hits: none, other than the incident text in `development/reports/AT-FG-03B_EXECUTION_REPORT.md` and `artifacts/at_fg_03b/integrity-comparison.json`.

No git-tracked path contains those suffixes. The published social case-1 result file is still at `development/campaigns/product_realization/pr_play_social_grounding_regression_reconciliation/evidence/after/case-1-result.json`. That file is the runner's publication, not one of the 27 scratch files.

| Original path | Known size | Known hash | Possible surviving copy | Confidence | Historical dependency |
| --- | ---: | --- | --- | --- | --- |
| `development/tmp/social-reconciliation/case-1-6zsp9s66` and its 9 unnamed files | 352,201 directory total | UNKNOWN | NOT FOUND | No pre-deletion hash and no name match | UNKNOWN. Not referenced by any surviving path. |
| `development/tmp/social-reconciliation/case-1-i9v07y94` and its 9 unnamed files | 16,149 directory total | UNKNOWN | NOT FOUND | No pre-deletion hash and no name match | UNKNOWN |
| `development/tmp/social-reconciliation/case-1-sezxtw9q` and its 9 unnamed files | 248,422 directory total | UNKNOWN | NOT FOUND | No pre-deletion hash and no name match | UNKNOWN |
| Each of the 27 files | UNKNOWN individually | UNKNOWN | NOT FOUND as a named copy. CONTENT-EQUIVALENT cannot be judged. | UNKNOWN below directory level | UNKNOWN |

Nothing was restored, recreated, or rewritten in a historical manifest.

## 9. Historical dependency assessment

The social runner writes JUnit, `case-1-result.json`, and diagnostics into the evidence directory. The scratch directory is the pytest base. Published case-1 evidence for the historical campaign is a different path and is still present. No reviewed document cites the three scratch suffixes as an input. Whether a fixture or diagnostic existed only inside the 9-file trees is UNKNOWN. The surviving 136-file case workspaces are later or larger runs, not stand-ins for the deleted ones.

## 10. Safeguards implemented

`OwnedWorkspace.allocate` now writes a secret into `.ashen-execution-owner` and keeps that secret only on the object it returns. `discard` removes the directory only when the path, the parent, the boundary, the secret, and a no-reparse walk all agree. A missing or different secret is a refusal. `finish_owned` also refuses when the publication files are absent.

Pytest's default session, the scene-scope partition worker, and the ATGB implicit store go through that helper. ATGB's empty-store check ignores only that owner file, so the secret does not make a new store look occupied and a historical campaign directory still fails the empty check.

The R1 runner validator allocates one sandbox, copies results out, and discards that sandbox. It records scratch names before and after and fails if a pre-existing name disappears. It does not delete a pre-existing staging directory.

## 11. Residual risks

- The check and `shutil.rmtree` are not one filesystem transaction. A directory swapped in that gap can still be removed. This milestone does not claim race-free deletion.
- `artifacts/at_fg_03b/validate-runners.py` still deletes `development/tmp/at-fg-03b-validation` if that path exists. Do not run it.
- Lane tools, replay `run-*` publishers, the AT-OPT holdout, and OS-temp probes were not given this token. They were not the deleting code in this incident. Several still allocate without a matching removal.
- An operator shell command can still delete any path the process can write. The helper constrains the application. It does not constrain an unrestricted shell.
- A process kill after `allocate` and before `discard` still leaves the one directory that process created.

## 12. Recommended corrective actions

1. Review this report and the execution report before any further filesystem milestone.
2. Do not restore the three directories by regenerating pytest output and labeling it original.
3. Do not run `artifacts/at_fg_03b/validate-runners.py`.
4. Leave historical `development/tmp/` in place until a later milestone names exact deletion candidates and their consumers.
5. When that inventory is authorized, start from the R1 social file manifest and the named-root digests, not from a prefix or an age.
