# Ashen Thrones — Content lint failure investigation

Date: November 1, 2026 (America/New_York).

## A. Executive Summary

**PASS WITH CAVEATS — LOCAL REPAIR VERIFIED; REMOTE VALIDATION PENDING**

The actual failed GitHub job was retrieved through the existing signed-in Opera browser. The blocking planner convergence static audit mistook explanatory prose in a function docstring for ad-hoc opening scaffolding. The exact failure reproduced locally with exit code 1. Classification: **B — Pre-existing**. The same offending source, audit inputs, tool, registry, workflow, and dependency requirements exist at the pre-cleanup commit and at the Phase 2C parent.

A one-line docstring rewording in `game/api.py` removes the false positive. The original audit now exits 0, its existing 19 tests pass, and content lint plus its summarizer exit 0. No audit rule, exclusion, workflow gate, executable gameplay logic, or dependency was changed. The source change is uncommitted; this report is untracked. No GitHub rerun was requested or observed.

### Preflight

- Branch: `feature/product-realization`.
- HEAD: `9f6a008837438b6a9b3128b31e2cd178c7f19e90`, matching the requested starting commit; no subsequent development to reconcile.
- Initial staged and unstaged tracked diffs: empty. Initial untracked files: 22 existing storage-cleanup reports/manifests. All remain present and untracked.
- Read `artifacts/storage_cleanup_final_closeout.md` and `artifacts/storage_cleanup_development_handoff.md`. Storage cleanup remains closed.
- Inspected both files in `.github/workflows/`, lint entrypoint/runner/summarizer, planner audit, `requirements.txt`, `docs/content_lint_pipeline.md`, `docs/precommit_content_lint.md`, and relevant validation/governance documentation. No AGENTS.md was found in the repository file inventory or the checked parent directories.

### Workflow configuration at the failing commit

File: `.github/workflows/content-lint.yml`; display name: `Content lint`. Triggers: every `push` and `pull_request`, without branch/path filters. Single job: `content-lint`, on `ubuntu-latest`, with `contents: read`.

| Step | Action or command | Enforcement |
| --- | --- | --- |
| Checkout repository | `actions/checkout@v5` | Required |
| Set up Python | `actions/setup-python@v6`, Python 3.12, pip cache keyed by requirements.txt | Required |
| Install dependencies | `python -m pip install --upgrade pip`; `pip install -r requirements.txt` | Required |
| Planner convergence static audit | `python tools/planner_convergence_audit.py` | Blocking |
| Run content lint (Phase 1 — informational, non-blocking) | `python tools/ci_content_lint.py --json-out artifacts/content_lint/ci_report.json` | Existing `continue-on-error: true` |
| Summarize content lint report | `python tools/summarize_content_lint.py --input artifacts/content_lint/ci_report.json` | Required if prior required steps succeed |
| Upload content lint report | `actions/upload-artifact@v4`, artifact `content-lint-ci-report` | Existing missing-file policy: warn |
| Run content lint (Phase 2 — optional fail on warnings) | `python tools/ci_content_lint.py --fail-on-warnings` | Already disabled with `if: false` |

Requirements: `fastapi>=0.116.0`, `uvicorn>=0.35.0`, `openai>=1.100.0`, `pydantic>=2.10.0`, `python-multipart>=0.0.12`, `python-dotenv>=0.21.0`, `pytest>=8.0.0`, `httpx>=0.28.0`; pip, Python, GitHub-hosted runner, and the actions above. These are existing requirements, not upgrades performed during this investigation. Installing the OpenAI package in CI is distinct from invoking an AI provider; no provider call was made here.

## B. Failure Evidence

- Workflow run: [Content lint #161, 41305384118](https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/41305384118).
- Job: [content-lint, 124844588919](https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/41305384118/job/124844588919#step:5:1).
- Commit: `9f6a008837438b6a9b3128b31e2cd178c7f19e90`, branch `feature/product-realization`, event `push`.
- Run status: Failure; run duration 42 seconds; job duration 38 seconds.
- Failed step: `Planner convergence static audit` (step 5 in the job log, including setup).
- Checkout, Python setup, and dependency installation succeeded. Subsequent lint/report steps show 0 seconds and were not reached after the required audit failed.

Relevant GitHub log transcription, observed directly:

```text
1  Run python tools/planner_convergence_audit.py
11 planner_convergence_audit: FAILED
13 - game/api.py:4796: fallback/neutral/cinematic opener clustering — use Narrative Plan ``scene_opening`` + approved renderer seam, not ad-hoc opener scaffolding (C1-A).
14 Error: Process completed with exit code 1.
```

There was no Python stack trace in this failed audit step. Annotations: one error, `Process completed with exit code 1.`, and one notice announcing the ubuntu-latest migration to Ubuntu 26 beginning October 19, 2026 (link shown by GitHub: https://github.com/actions/runner-images/issues/14748). The notice does not explain the reproduced source-level finding.

Retrieval limitations and fallback: `gh` was unavailable on PATH and absent at the checked standard `C:\Program Files\GitHub CLI\gh.exe` location. The web tool could not access the GitHub API endpoint, and an unauthenticated shell request failed DNS resolution (`No such host is known. (api.github.com:443)`). Existing checkpoint JSON concerns Convergence checks at `588531e`, not this failure, and was not used as target evidence. The existing signed-in browser provided the actual target run and job logs without authentication changes or a workflow rerun. Browser inspection used the computer-use skill. No need remains to request missing failure logs from the user.

## C. Root-Cause Analysis

The first meaningful error is the C1-A heuristic finding above, not content validation or dependency installation. `audit_c1a_scene_opening_convergence` scans each raw source line in risk-path modules, skips lines starting with `#`, and matches `_C1A_FALLBACK_OPENER_CLUSTER_RE`. It does not distinguish function docstrings from executable strings.

The matched line is inside `_opening_response_rejection`'s explanatory docstring:

```python
    Safe fallback text is not a completed scene_opening. Structured validation
```

The negated explanation puts `fallback` and `scene_opening` on the same line within the regex distance. It constructs no opener or narration payload. The surrounding function rejects invalid opening responses; the matched prose describes that rejection. Thus the audit identifies a false positive in documentation.

Evidence for classification B:

1. The exact workflow command failed locally with the same file, line, finding, and exit code before editing.
2. Git blob comparisons show no changes in any primary audit input, discovered opening helper, the audit script, `game/contract_registry.py`, workflow, or requirements between HEAD and either `HEAD^` (`e86fd4512028af4ce698090d48c1b672dd68600c`) or the pre-cleanup commit `c16d922865b7182d47b87d27ec633f9308f1ef4c`.
3. Auditing `game/api.py` source read directly with `git show` at both earlier commits produces the same line-4796 finding, without checkout, reset, or restoration.
4. The browser workflow list independently shows failed run #160 at `e86fd45` ([41244518024](https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/41244518024)) and failed run #159 at `c16d922` ([41230228088](https://github.com/CrowbarInc/AI-DM-Ashen-Thrones-/actions/runs/41230228088)). Those ancestor job logs were not opened; the identical-input and source reproduction evidence establishes the relationship rather than the failure badges alone.
5. Phase 2C's diff consists exclusively of 2,663 deletions under `.venv-broken/`; it does not alter these inputs.

This is a static-validation documentation false positive. It is not evidence of a missing environment, bad workflow path, GitHub infrastructure failure, or cleanup-introduced gameplay defect. No second independent blocker was established.

## D. Changes

Before editing, the identified correction was restricted to `game/api.py:4796`, rewording the explanatory sentence while keeping its meaning. Expected result: the existing raw-line audit stops flagging this prose; forbidden executable opener patterns remain detected. Verification: original audit, its existing positive and negative tests, content lint/report commands, executable AST comparison, and tracked-diff inspection.

Implemented replacement:

```python
    Safe fallback text cannot complete this operation. Structured validation
```

Tracked diff: one insertion and one deletion in a docstring in `game/api.py`. This is the smallest source correction for the demonstrated false positive. The audit implementation, regex, allowlists, tests, workflow, and content data remain unchanged. The only new repository file is this investigation report. Additional generated lint JSON is outside the repository in the authorized visualization workspace.

## E. Verification

Local environment: existing `.venv/Scripts/python.exe`, Python **3.12.0**, Windows. All Python validation commands set `PYTHONDONTWRITEBYTECODE=1`; UTF-8 output was selected for the final validation commands. No dependency installation, live playtest, AI generation, paid service, or provider call was performed.

| Command/check | Result |
| --- | --- |
| `.venv/Scripts/python.exe tools/planner_convergence_audit.py`, before repair | Exit 1; exact GitHub finding reproduced |
| In-memory `audit_file('game/api.py', source=git_show_source)` on HEAD^ and c16d922 | Same finding on both |
| `.venv/Scripts/python.exe tools/planner_convergence_audit.py`, after repair | Exit 0: `planner_convergence_audit: OK (no issues)` |
| `.venv/Scripts/python.exe -m pytest tests/test_planner_convergence_static_audit.py -q -p no:cacheprovider` | Exit 0; **19 passed**, including injected forbidden fallback/opener, second-planner, raw-state shortcut, visible-facts, and import cases |
| `.venv/Scripts/python.exe tools/ci_content_lint.py --json-out <external-json-path>` | Exit 0; **62 scenes, 0 errors, 174 warnings** |
| `.venv/Scripts/python.exe tools/summarize_content_lint.py --input <external-json-path>` | Exit 0; 113 scene warnings and 61 graph warnings |
| AST comparison with HEAD, stripping function docstrings | Equal executable AST |
| `git diff --check` | Exit 0, no whitespace errors |
| `git diff --stat`, `git diff -- game/api.py`, and name/staging assertions | Only the justified one-line docstring change; staged diff empty |

`<external-json-path>` is:

```text
C:\Users\Master Mandalcio\.codex\visualizations\2026\11\01\01a19720-f79c-7540-9e54-009349e81956\content_lint_investigation_ci_report.json
```

The JSON destination differs from CI's repository artifact path to preserve existing files. All lint flags and default content inputs otherwise match the workflow. Warnings remain visible and are permitted by the existing observer policy; no content was altered to hide them.

One initial supplemental JSON-output attempt used a temporary path returned by an earlier sandboxed shell invocation. That path was inaccessible in the later invocation and produced WinError 3/5, followed by a missing-input summarizer error. This was an investigation output-destination error, distinct from the GitHub failure. Repeating both commands with the stable authorized external workspace path succeeded. No code correction was made for that path error.

Preservation: tracked diff is restricted to `game/api.py`; no historical evidence, ATGB or PR-PLAY artifact, conversational-continuity code, storage-cleanup report, or workflow was modified. The existing 22 untracked reports/manifests remain listed. No file deletion, staging, commit, push, history rewrite, cleanup, or GitHub rerun was performed. The full regression suite was outside this narrowly scoped verification and was not run.

## F. Outstanding Actions

Remote validation is pending: no successful GitHub run of this repair has been observed. The original run remains failed. Review the uncommitted source change; committing/pushing and any GitHub-hosted execution require separate user authorization and were explicitly excluded from this task. A later authorized run should verify the repaired audit on Ubuntu and the downstream report/upload steps. This investigation does not certify those hosted steps as successful.

No broader design decision is needed for this repair. An AST-aware redesign of the heuristic was deliberately left outside scope. Existing content warnings remain available for separate content work; this investigation does not authorize that work. Storage cleanup stays closed. Stop here.
