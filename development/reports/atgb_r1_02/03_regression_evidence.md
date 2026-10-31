# 03 — Regression Evidence

No live provider calls. All tests use the repository's autouse live-model guard, which blocks OpenAI constructors and known model entry points. Existing tests install deterministic stubs. Local socket access was required only for Starlette TestClient.

| Run | Tests | Passed | Failed | Exit |
| --- | ---: | ---: | ---: | ---: |
| New boundary tests + frozen PR-EF-R4 authorization suite | 133 | 133 | 0 | 0 |
| Final relevant slice | 452 | 443 | 9 | 1 |
| Matched existing slice, saved pre-repair source loaded in memory | 347 | 338 | 9 | 1 |

New tests: 105 passing. Existing focused authorization tests: 28 passing, including correction_pending, correction_already_executed, correction_nothing_pending. The broad existing outcome set matches the pre-repair run exactly. Full suite not run; no full-suite-green claim.

Coverage includes all requested correction and ambiguous wordings, DESCRIPTION/CORRECTION labels, absent/pending/executed contexts, movement and attack revisions, implicit action revisions, pending_clarification fallback, stale-scene rejection, nonexecution, selected public evidence, original S08.2 context and direct API gameplay-state integrity. Related observatory/astronomer vocabulary is authored scenario-independent coverage, not unseen evaluation.

Nine pre-existing failures are in test_pr_eg_r6_r2_r1_referents: eight test_untrusted_operations_fail_closed_without_losing_focus parameters expect clarification but get unknown, and test_unqualified_historical_id_cannot_override_focus lacks bound_referent_id. Both runs have precisely these IDs. No production change was made to repair them. `test_summary.json` retains every failure ID; XML and text logs retain exact assertions.

Initial sandbox focused and broader runs were interrupted (exit 1, incomplete counts) because Python's socket._fallback_socketpair blocked on accept during TestClient loop initialization. `diagnose.txt` preserves the 15-second faulthandler stack. The outside-sandbox rerun completed. The first completed run had three new-test assertion failures from requiring the entire session to remain equal: normal delivered-history/save metadata changed. Assertions were corrected to check gameplay stores and pending/executed records explicitly. That run remains preserved as verified.txt/xml (440 pass, 12 fail).

One existing Starlette/httpx deprecation warning. No test expectation in an existing test or frozen fixture was changed.

## Exact commands

Commands below use the repository cwd and bundled runtime. Their exit codes are pytest exits, retained in *_exit.txt; the enclosing PowerShell command can itself exit 0 after recording a failed pytest exit.

### targeted

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_atgb_r1_02_revision_boundary.py tests/test_pr_ef_r4_authorization.py -q --tb=short --basetemp=development/tmp/atgb_r1_02_targeted --junitxml=artifacts/atgb/atgb_r1_02/targeted.xml *> artifacts/atgb/atgb_r1_02/targeted.txt; $code=$LASTEXITCODE; $code | Set-Content artifacts/atgb/atgb_r1_02/targeted_exit.txt
```

Exit 0; 133 passed, 0 failed.

### final

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_atgb_r1_02_revision_boundary.py tests/test_pr_ef_r4_authorization.py tests/test_pr_ea_conversational_orchestration.py tests/test_pr_ef_gm_authority.py tests/test_pr_ef_r1_semantic_handoff.py tests/test_pr_ef_r2_social_authority.py tests/test_state_authority.py tests/test_pr_eg_r1_continuity.py tests/test_pr_eg_r6_r1_disclosure_boundary.py tests/test_pr_eg_r6_r1_r1_provenance.py tests/test_pr_eg_r6_r2_r1_referents.py tests/test_pr_eg_r6_r2_r2_operations.py tests/test_pr_eg_r6_r5_diagnostic.py -q --tb=short --basetemp=development/tmp/atgb_r1_02_final --junitxml=artifacts/atgb/atgb_r1_02/final.xml *> artifacts/atgb/atgb_r1_02/final.txt; $code=$LASTEXITCODE; $code | Set-Content artifacts/atgb/atgb_r1_02/final_exit.txt
```

Exit 1; 443 passed, 9 failed.

### pre_repair

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' artifacts/atgb/atgb_r1_02/run_pre_repair_regression.py tests/test_pr_ef_r4_authorization.py tests/test_pr_ea_conversational_orchestration.py tests/test_pr_ef_gm_authority.py tests/test_pr_ef_r1_semantic_handoff.py tests/test_pr_ef_r2_social_authority.py tests/test_state_authority.py tests/test_pr_eg_r1_continuity.py tests/test_pr_eg_r6_r1_disclosure_boundary.py tests/test_pr_eg_r6_r1_r1_provenance.py tests/test_pr_eg_r6_r2_r1_referents.py tests/test_pr_eg_r6_r2_r2_operations.py tests/test_pr_eg_r6_r5_diagnostic.py -q --tb=short --basetemp=development/tmp/atgb_r1_02_pre_repair --junitxml=artifacts/atgb/atgb_r1_02/pre_repair.xml *> artifacts/atgb/atgb_r1_02/pre_repair.txt; $code=$LASTEXITCODE; $code | Set-Content artifacts/atgb/atgb_r1_02/pre_repair_exit.txt
```

Exit 1; 338 passed, 9 failed.
