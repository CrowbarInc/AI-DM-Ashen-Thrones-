# Ashen Thrones — Combined repair integration report

Date: November 1, 2026 (America/New_York).

## A. Executive Summary

**PASS — INTEGRATED, PUSHED, AND CI VERIFIED**

Both narrowly scoped repairs passed combined local validation, were committed together, and were pushed as a normal fast-forward to `origin/feature/product-realization`.

- Commit: `d40f1ed198236c604085f1c842ead267a8104ce2`.
- Message: `fix: restore clarification recency and resolve planner audit false positive`.
- Parent: `9f6a008837438b6a9b3128b31e2cd178c7f19e90`.
- Push: successful; local HEAD, remote-tracking HEAD, and GitHub's advertised branch SHA agree; ahead/behind 0/0.
- Local tests: **278 passed** across the requested 19 + 106 + 153 selections.
- Local lint: **62 scenes, 0 errors, 174 warnings**, matching the established baseline.
- Resulting [Content lint #162](https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/41309527714): **Success**, 36 seconds total; job `content-lint` succeeded in 33 seconds.

The tracked working tree is clean. Existing untracked reports/manifests and the separately observed `artifacts.zip` were preserved and excluded from the commit. This report remains untracked. Storage cleanup remains closed.

## B. Starting Repository State

Verified branch: `feature/product-realization`. Initial HEAD exactly matched the required `9f6a008837438b6a9b3128b31e2cd178c7f19e90`; there was no advanced HEAD to reconcile. The index was empty. The only tracked modifications were:

```text
game/api.py
game/conversational_continuity.py
tests/test_pr_eg_r2c_r2_reference_eligibility.py
```

Reviewed the required storage-cleanup closeout and development handoff, content-lint investigation, and C01–C03 repair report. The investigation reports' original statements that changes were uncommitted remain historical records; neither was edited to describe this later integration.

Initial status listed the 22 cleanup reports/manifests and the two repair reports. A subsequent explicit untracked inventory also found repository-root `artifacts.zip`, 391,594,375 bytes. Its creation was not part of this operation. It was preserved, excluded from staging, and checked by metadata rather than rehashing this large unrelated archive. The preflight inventory therefore recorded 25 untracked files before this new report.

No reset, restore, stash, checkout, automatic reconciliation, or unrelated source edit was performed.

## C. Integrated Changes

### Content lint correction

`game/api.py` changes exactly one explanatory docstring line:

```diff
-    Safe fallback text is not a completed scene_opening. Structured validation
+    Safe fallback text cannot complete this operation. Structured validation
```

The full file matches HEAD with only that replacement. An AST comparison with function docstrings removed confirmed unchanged executable code. No planner rule, allowlist, workflow, dependency, or validation threshold changed.

### Conversational-continuity correction

`game/conversational_continuity.py` changes only the recency selection and its explanatory comments:

```python
# Conversational recency includes GM questions that are not NPC disclosures.
# Keep the filtered rows for historical recall below.
latest = last_delivered_exchange(session) or {}
```

The actual delivered order now determines whether the current matching GM clarification is repeated. Historical-disclosure filtering remains intact for later NPC/history selection. Clarification category, scene, matching response, ownership, and explicit reference guards remain intact. Absent-NPC branches, persistent state, and provider behavior are unchanged.

### Regression tests and committed inventory

The existing test module adds two parametrized tests containing 3 positive clarification cases and 12 selection-boundary controls. Removing those two added functions from its AST reproduces the original module AST exactly. All original test bodies, decorators, assertions, and frozen fixtures therefore remain unchanged, including C01–C03.

Complete committed file list:

```text
game/api.py
game/conversational_continuity.py
tests/test_pr_eg_r2c_r2_reference_eligibility.py
```

Commit statistics: **3 files, 69 insertions, 2 deletions**. No report, manifest, generated output, archive, CI configuration, or protected evidence was committed.

## D. Local Verification

Used the existing `.venv/Scripts/python.exe`: Python 3.12.0, pytest 9.1.1, pluggy 1.6.0, anyio 4.14.2. No dependency was installed or upgraded locally.

Environment:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONIOENCODING=utf-8
ASHEN_DISABLE_PROVIDER_CALLS=1
ASHEN_DISABLE_LIVE_INTERPRETATION=1
ASHEN_DISABLE_EXPRESSION_GENERATION=1
ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1
ASHEN_PROVIDER_REQUEST_LIMIT=0
```

Commands/results:

| Validation | Result |
| --- | --- |
| `.venv/Scripts/python.exe tools/planner_convergence_audit.py` | Exit 0; `planner_convergence_audit: OK (no issues)` |
| Planner static-audit test module | **19 passed**, exit 0 |
| Content lint with external JSON destination | Exit 0; **62 scenes, 0 errors, 174 warnings** |
| Existing summarizer against that JSON | Exit 0; 113 scene warnings, 61 graph warnings |
| Requested adjacent continuity selection | **106 passed**, exit 0, including unchanged C01–C03 and existing HTTP clarification controls |
| Requested historical-disclosure regression selection | **153 passed**, exit 0 |
| `git diff --check` and staged whitespace check | Passed |
| Exact source replacement/AST checks | Passed; API executable AST unchanged, original tests unchanged, expected 15 new cases |
| Preflight hashes and verified diff after validation | Unchanged |

Lint commands:

```text
.venv/Scripts/python.exe tools/ci_content_lint.py --json-out <external-workspace>/combined_integration_ci_report.json
.venv/Scripts/python.exe tools/summarize_content_lint.py --input <external-workspace>/combined_integration_ci_report.json
```

Pytest selections:

```text
tests/test_planner_convergence_static_audit.py
```

```text
tests/test_pr_eg_r2c_r2_reference_eligibility.py
tests/test_pr_eg_r1_continuity.py
tests/test_pr_eb_conversational_continuity.py
```

```text
tests/test_pr_eg_r2c_speech_adoption.py
tests/test_pr_eg_r6_r1_disclosure_boundary.py
tests/test_pr_eg_r6_r1_r1_provenance.py
```

Each selection ran in a fresh Python process with `pytest.main`, arguments `-q -o addopts= -p no:cacheprovider --basetemp <unique-temporary-parent>/pytest`, and its own unused basetemp. Complete expanded argument lists are retained in external logs. This preserves the documented safeguards and avoids reusing historical/locked test stores.

The preceding investigation had established that sandboxed Windows socketpair creation could block Starlette/AnyIO before application handling. Accordingly, these tests used approved execution outside the restricted sandbox with a process-local loopback-only guard on socket connect, connect_ex, create_connection, and getaddrinfo. The project's live-model guard remained active. **Each process recorded zero external network attempts**. Test-controlled interpretation/model stubs did not invoke a provider. No application code or OS setting was altered to accommodate the environment.

The adjacent and disclosure selections each emitted the existing Starlette/httpx deprecation warning. It did not fail tests; no dependency change was attempted. No full-repository suite, live campaign, or paid provider call was run.

External evidence workspace:

```text
C:\Users\Master Mandalcio\.codex\visualizations\2026\11\01\01a19720-f79c-7540-9e54-009349e81956\
```

Integration evidence files: `combined_integration_preflight.json`, `combined_integration_ci_report.json`, `combined_planner_audit.txt`, `combined_content_lint.txt`, `combined_summarizer.txt`, `combined_planner_tests.txt`, `combined_adjacent_tests.txt`, `combined_disclosure_tests.txt`, `combined_lint_results.json`, and `combined_test_results.json`.

## E. Git Verification

All required local gate criteria passed before staging. Staged exactly the three named files using an explicit path list. Inspected the complete staged diff, staged file list/statistics, and whitespace results. Its binary diff SHA-256 matched the preflight verified diff, with no unstaged tracked changes.

Created the single requested ordinary commit:

```text
d40f1ed198236c604085f1c842ead267a8104ce2
parent 9f6a008837438b6a9b3128b31e2cd178c7f19e90
fix: restore clarification recency and resolve planner audit false positive
```

Then fetched only the target branch without tags:

```text
git fetch --no-tags origin refs/heads/feature/product-realization:refs/remotes/origin/feature/product-realization
```

The fetched branch remained at the expected parent `9f6a0088`. The ancestry check succeeded; remote/local comparison was 0 remote-only and 1 local-only commit. No remote advance or divergence was present.

Pushed only the target branch:

```text
git push origin HEAD:refs/heads/feature/product-realization
```

Result: successful fast-forward `9f6a0088..d40f1ed1`. `git ls-remote --heads origin refs/heads/feature/product-realization` advertised the exact new SHA. Both `git rev-parse HEAD` and `git rev-parse origin/feature/product-realization` returned that SHA; ahead/behind was **0/0**. Staged and unstaged tracked diffs were empty. No force, amend, merge, rebase, other branch/tag push, or history rewrite occurred.

## F. GitHub Actions Verification

Observed through the existing signed-in browser using the computer-use skill; no authentication setting was changed and no workflow was manually triggered or rerun.

- Workflow: **Content lint**, `.github/workflows/content-lint.yml`.
- Run: **#162**, ID **41309527714**.
- [Run URL](https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/41309527714).
- Commit: `d40f1ed198236c604085f1c842ead267a8104ce2`, branch `feature/product-realization`, event `push`.
- Job: **content-lint**, ID **124856801066**; [job log](https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/41309527714/job/124856801066).
- Final run status: **Success**, 36 seconds. Final job status: **succeeded**, 33 seconds.

| Step | Observed result |
| --- | --- |
| Checkout, Python setup, dependency installation | Completed; job proceeded through all required steps |
| Planner convergence static audit | Passed; log explicitly reports `planner_convergence_audit: OK (no issues)` |
| Content lint Phase 1 | Executed; log reports **62 scenes, 0 errors, 174 warnings** |
| Summarize content lint report | Executed successfully; **0 errors / 174 warnings**, 113 scene and 61 graph warnings |
| Upload content lint report | Upload finalized successfully; one file, 2,725-byte artifact archive |
| Optional Phase 2 warning gate | Remained disabled by existing `if: false`; no configuration change |
| Post-job cleanup | Completed; final job succeeded |

Upload confirmation:

- Artifact name: `content-lint-ci-report`.
- Artifact ID: `13084253030`.
- [Artifact URL](https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/41309527714/artifacts/13084253030).
- SHA-256 reported by upload and run summary: `855b831a4b1738b0792a9346318becdcfd8f0442d7cb5366a74d75c0b60672ef`.

Annotations: **one warning and one notice; no failure annotation**. The warning says Node.js 20 is deprecated and `actions/upload-artifact@v4` is being forced to Node.js 24. The notice concerns the ubuntu-latest migration to Ubuntu 26 beginning October 19, 2026. The upload log also contains Node deprecation messages for `punycode` and `url.parse()`. These did not prevent successful upload or workflow completion. No action/runtime upgrade was introduced in this task.

This confirms the previously failing workflow and its previously unreached downstream steps. It does not claim a result for the separate Convergence checks workflow, which was outside this requested verification and was not inspected.

## G. Preservation

Preservation checks used the prior reports and narrow comparisons rather than a full repository rehash:

- Required source/content/tool directories `game`, `data`, `tests`, `tools`, `scripts`, `static`, and `experiments` remain present. Only the three approved tracked paths changed relative to the parent.
- Active `.venv` and separate `venv` remain present; no environment was installed, upgraded, removed, or reorganized.
- ATGB baselines/evidence, golden replay, PR-PLAY 10/11/12 and their historical packages, history, and retained snapshots remain present and absent from the committed diff.
- `handoff/CURRENT_REVIEW.zip` remains present at the closeout's recorded 3,796,976 bytes.
- All 22 cleanup reports/manifests and both repair reports match their integration-preflight hashes and remain untracked. Frozen clarification and R1 continuity fixtures match both HEAD content at preflight and their saved hashes afterward.
- All four external recovery archives were read-only checked against the development handoff's exact byte sizes and SHA-256 values; all matched. They remain in `ashen_thrones_storage_archives` beside the repository.
- Repository-root untracked `artifacts.zip` was preserved and never staged. No historical evidence was deleted or regenerated in place.
- Validation introduced no unexpected tracked modification. Generated lint/test logs are outside the repository; this final report is intentionally untracked.

## H. Remaining Issues

**Resolved:** planner audit docstring false positive; C01–C03 clarification recency regression. The repaired Content lint workflow was observed passing on the pushed commit.

**Known nonblocking warnings:** 174 authored-content warnings (61 graph-unreachable, 57 sensory-grounding, 56 player-anchor); local Starlette/httpx deprecation; GitHub action Node deprecations and runner migration notice. Their thresholds and handling were not changed.

**Unverified:** full regression suite, separate Convergence checks workflow, live/provider performance, and gameplay quality. Selected deterministic checks and passing Content lint do not certify those outcomes. No new assertion failure or unresolved integration conflict was found in scope.

## I. Recommendation

The integrated branch is ready to return to separately authorized ATGB and Product Realization development: the two repairs are validated, committed, pushed, and the target Content lint workflow is confirmed successful. This is development-validation readiness, not gameplay certification. Storage cleanup stays closed. No further development, rerun, or repair is initiated by this report.
