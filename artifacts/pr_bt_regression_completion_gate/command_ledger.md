# Command Ledger and Diagnostic Evidence

All commands were run in the repository root with zero model/API calls.
Final totals count unique cases in final_regression.xml, not repeated executions.
JUnit contains exact test IDs, failure messages, and durations.
The final command is recorded verbatim in final_command.ps1 and its console
output in final_regression.log. It ran outside the sandbox with approval.

## Completed historical commands

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_bt_policy_instruction_deduplication.py -q --tb=short --durations=10 --junitxml=artifacts\pr_bt_regression_completion_gate\stage1_pr_bt.xml --basetemp=codex_pytest_tmp_prbt_gate_stage1
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_bs_decision_facing_answer_recipe.py -q --tb=short --durations=15 --junitxml=artifacts\pr_bt_regression_completion_gate\stage2_pr_bs.xml --basetemp=codex_pytest_tmp_prbt_gate_stage2
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_br_authority_reconciliation.py tests\test_pr_br_c19_free_text_authority.py tests\test_pr_br_claim_control_regex_bound.py tests\test_pr_br_claim_control_slice1.py tests\test_pr_br_claim_control_slice2.py tests\test_pr_br_continuation12_competence.py -q --tb=short --durations=15 --junitxml=artifacts\pr_bt_regression_completion_gate\stage3_pr_br_pre_c13.xml --basetemp=codex_pytest_tmp_prbt_gate_stage3_pre_c13
$all = Get-ChildItem -LiteralPath 'tests' -Filter 'test_pr_br_*.py'; $client = Select-String -Path $all.FullName -Pattern 'TestClient\(app\)|TestClient\(' | ForEach-Object { $_.Path } | Sort-Object -Unique; $files = $all | Where-Object { $client -notcontains $_.FullName } | ForEach-Object { $_.FullName }; & '.\.venv\Scripts\python.exe' -m pytest @files -q --tb=short --durations=25 --junitxml=artifacts\pr_bt_regression_completion_gate\stage3_pr_br_non_testclient.xml --basetemp=codex_pytest_tmp_prbt_gate_stage3_nonclient
& '.\.venv\Scripts\python.exe' -m pytest tests\test_prompt_context.py tests\test_prompt_and_guard.py tests\test_prompt_compression.py tests\test_prompt_context_public_prompt_boundary.py tests\test_prompt_context_ctir_boundary.py tests\test_prompt_context_ctir_consumption.py -q --tb=short --durations=15 --junitxml=artifacts\pr_bt_regression_completion_gate\stage4_prompt_files.xml --basetemp=codex_pytest_tmp_prbt_gate_stage4_prompt
& '.\.venv\Scripts\python.exe' -m pytest tests\test_prompt_context.py tests\test_prompt_and_guard.py tests\test_prompt_compression.py tests\test_prompt_context_public_prompt_boundary.py tests\test_prompt_context_ctir_boundary.py tests\test_prompt_context_ctir_consumption.py -q --tb=short --durations=15 --junitxml=artifacts\pr_bt_regression_completion_gate\stage4_prompt_files_after_tight_repair.xml --basetemp=codex_pytest_tmp_prbt_gate_stage4_prompt_tight
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_bt_policy_instruction_deduplication.py -q --tb=short --durations=10 --junitxml=artifacts\pr_bt_regression_completion_gate\stage1_pr_bt_after_tight_repair.xml --basetemp=codex_pytest_tmp_prbt_gate_stage1_tight
& '.\.venv\Scripts\python.exe' -m pytest tests\test_realization_authority.py tests\test_realization_provenance.py tests\test_realization_provenance_audit.py tests\test_realization_layer_audit.py -q --tb=short --durations=15 --junitxml=artifacts\pr_bt_regression_completion_gate\stage4_realization_authority_provenance.xml --basetemp=codex_pytest_tmp_prbt_gate_stage4_realprov
```

The temp-permission rerun used the existing single test
`tests\test_pr_br_interpretation_proposal.py::test_persona_sessions_do_not_inherit_discourse`
after setting TMP/TEMP to the workspace. It passed, 1.878 seconds.
The exact earlier creation/rerun shell invocation was not retained.

Intermediate repair runs used the same prompt or direct PR-BT scopes.
Evidence stems: stage4_prompt_files_after_repair, after_repair2,
after_compact_repair; stage1_pr_bt_after_repair, after_compact_repair.
Their full shell strings were not retained through session compaction; the
scope, exact test IDs, counts and times remain in JUnit. This is a historical
command-logging limitation, not a claim that reconstructed commands are exact.
No test failures from these runs are omitted from the report matrix.

## Interrupted commands and diagnostic localization

```powershell
$files = Get-ChildItem -LiteralPath 'tests' -Filter 'test_pr_br_*.py' | ForEach-Object { $_.FullName }; & '.\.venv\Scripts\python.exe' -m pytest @files -q --tb=short --durations=20 --junitxml=artifacts\pr_bt_regression_completion_gate\stage3_pr_br.xml --basetemp=codex_pytest_tmp_prbt_gate_stage3
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_br_continuation13_semantic_preservation.py -vv --tb=short --durations=20 --junitxml=artifacts\pr_bt_regression_completion_gate\stage3_pr_br_c13.xml --basetemp=codex_pytest_tmp_prbt_gate_stage3_c13
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_br_continuation13_semantic_preservation.py::test_raw_chat_keeps_a_useful_inspection_and_rejects_atmospheric_avoidance -vv -s --tb=short -o faulthandler_timeout=20 -o faulthandler_exit_on_timeout=true --junitxml=artifacts\pr_bt_regression_completion_gate\stage3_pr_br_c13_stall_diagnostic.xml --basetemp=codex_pytest_tmp_prbt_gate_stage3_c13_diag
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_br_continuation14_resolution_content.py -vv -s --tb=short --durations=20 -o faulthandler_timeout=20 -o faulthandler_exit_on_timeout=true --junitxml=artifacts\pr_bt_regression_completion_gate\stage3_pr_br_c14_diagnostic.xml --basetemp=codex_pytest_tmp_prbt_gate_stage3_c14_diag
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_br_structured_chat_path.py::test_raw_chat_accepts_authorized_fact_and_seals_it -vv -s --tb=short -o faulthandler_timeout=20 -o faulthandler_exit_on_timeout=true --junitxml=artifacts\pr_bt_regression_completion_gate\c18_structured_chat_diagnostic.xml --basetemp=codex_pytest_tmp_prbt_gate_c18_structured
```

- Aggregate PR-BR: 52 progress dots, no final counts; interrupted after about
  210 seconds. A zero-test stage3 XML belongs to an earlier bad wildcard
  invocation and is not this interrupted run's result.
- C13: 8 passing cases visibly completed; raw-chat inspection case stalled.
  Interrupted after about 90 seconds. Independent diagnostic timed out at 20s.
- C14: 12 passing cases visibly completed; raw-chat procedural-answer case
  timed out at 20s.
- C18 diagnostic: 20s timeout before TestClient request handling.
- A WindowsSelectorEventLoopPolicy diagnostic attempt also stalled and was
  interrupted. Its complete shell string/runtime were not retained.
- The original broad stage4 aggregate showed prompt failures and stalled near
  99%; interrupted. The later realization/fallback/schema batch excluding the
  guarded direct-call test showed passing progress near completion and stalled
  before a summary; interrupted. No authoritative final counts or complete
  output files exist for those batches. The final approved run supersedes them.
- Two literal `tests\test_pr_br_*.py` pytest attempts failed at collection
  because the shell did not expand the wildcard; no cases executed. Their exact
  flags were not retained. A subsequent explicit file-array collection succeeded.

No incomplete batch is counted as a suite pass. Interrupted/timeout runs have
no established failed-assertion counts unless explicitly noted above.

### Diagnostic stack (recorded summary, not a raw stack dump)

Repeated timeout outputs identified this startup path:
Starlette TestClient -> AnyIO blocking portal -> asyncio Windows event-loop
construction -> _make_self_pipe -> socket.socketpair -> socket.accept.
The test body waited for portal startup. No production request or model call was
executing at the stall. Original timeout output was displayed in the session;
this file preserves its substantive stack locations. Those forcibly exited
processes did not produce normal JUnit summaries.

## Approved environment verification

Exact C18 command, outside sandbox:
```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests\test_pr_br_structured_chat_path.py::test_raw_chat_accepts_authorized_fact_and_seals_it -vv -s --tb=short -o faulthandler_timeout=20 -o faulthandler_exit_on_timeout=true --junitxml=artifacts\pr_bt_regression_completion_gate\c18_outside_sandbox.xml --basetemp=codex_pytest_tmp_prbt_gate_c18_outside
```

1 passed, 0 failed/skipped/xfailed, normal exit, 1.501s JUnit / 1.65s pytest.
Full relevant rerun: final_command.ps1; 913 passed, 1 failed, 1 deselected,
0 skipped/xfailed, normal process exit code 1, 36.251 seconds JUnit.

Measurement command:
```powershell
& '.\.venv\Scripts\python.exe' tools\measure_pr_bt_policy_instruction_payloads.py
```
Normal exit 0, approximately 1.71s shell time, zero calls. Probe rule-presence
JSON and provider requests are included. Earlier measurement commands used the
same script; their exact times were not retained.

## Live-call exclusion

The provenance provider-failure case uses a RaisingOpenAI fake but calls the
guarded gm.call_gpt wrapper. The autouse guard raises before any API interaction.
It was run initially, failed with that guard error, then explicitly deselected.
No production fallback was exercised by that case. Other provider routes use
test-local deterministic generation stubs. tests/conftest.py disables preflight
and live interpretation and installs tests/helpers/live_model_guard.py.

