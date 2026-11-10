# PR-PLAY-21 test results

All tests ran offline with repository pytest live-model guards. Read capture and
new fixtures also deny external socket connects; loopback is allowed solely for
Windows asyncio socketpair. Startup preflight is skipped. Initialization uses
the real provider request builder/parser and opening renderer with a synthetic
SDK transport; one mock dispatch, zero live-provider requests.

| Run | Passed | Failed | Errors | Skipped |
| --- | --- | --- | --- | --- |
| Pre-change relevant baseline (same 11 files as PR-PLAY-20) | 171 | 18 | 0 | 0 |
| Focused after fixture correction | 24 | 0 | 0 | 0 |
| Contract transition before expectation migration (3 relevant files) | 20 | 7 | 0 | 0 |
| Repaired broader run (baseline files plus new focused file) | 195 | 18 | 0 | 0 |
| Final focused run plus baseline I/O-case retry | 25 | 0 | 0 | 0 |
| Repaired I/O-case retry | 1 | 0 | 0 | 0 |

One Starlette/httpx deprecation warning per pytest run; it is unchanged.
Final focused total is 24 authorization cases; the 25th case is the targeted
baseline file-I/O retry. Logs and JUnit XML retain raw counts without hiding
transient failures. `failure_comparison.json` maps test identities and results.

Commands (repository .venv Python):

```
-m pytest tests/test_pr_play_21_privileged_reads.py --tb=short
-m pytest tests/test_pr_play_20_response_confidentiality.py tests/test_pr_play_18_contract_alignment.py tests/test_pr_play_13_opening_renderer.py tests/test_pr_play_04_opening_integrity.py tests/test_start_campaign_api.py tests/test_state_channels.py tests/test_ui_mode_backend_integration.py tests/test_ui_mode_policy.py tests/test_turn_pipeline_shared.py tests/test_frontend_ui_mode_hardening_objective15.py tests/test_ui_mode_regression_matrix_objective15.py --tb=short
```

The broader repaired command additionally includes the new PR-PLAY-21 file.
JUnit and text paths are `baseline_tests.*`, `repaired_tests.*`,
`focused_tests.*`, `focused_final_tests.*`, `windows_io_retry_tests.*`.
Set ASHEN_PR_PLAY_21_EVIDENCE=1 only to write initialization evidence; this
environment variable does not affect authorization.

Regression mapping:

| Requirement | Coverage |
| --- | --- |
| A/J public retrieval and compatibility | default_public_and_authority_preservation: visible fact, narration/input, exact envelope, no sentinel |
| B/C/I escalation and related endpoints | privileged_http_denied_before_data_access: author/debug x state/log/debug_trace/snapshots, 8 cases |
| D supported alternatives | body ui_mode/uiMode on campaign/scene/world, 6 cases; normalization/duplicate queries, 5 cases; query precedence retained |
| E authorized workflow | internal_projection_access_is_preserved; no authenticated HTTP workflow exists to test |
| F authoritative preservation | persisted campaign/world/scene/character/combat/session/log equal before/after reads/denials; hidden fact survives |
| G/H complete serialization/errors | response.text sentinel exclusion; exact fixed 403 body; loader/projector tripwires prove denial before access |
| K initialization/opening | offline_initialization_and_ordinary_action plus existing PR-PLAY-20/18/13/04 suites |
| L ordinary-turn isolation | initiative response succeeds, combat enters in_combat, unchanged campaign; existing shared-turn suite compared |
| Browser origin | same-origin and foreign-origin requests still denied despite wildcard CORS |
| Missing context | Request=None with privileged body selector denied, no implicit trusted path |

The actual application lifespan and ASGI serializer execute. `baseline_http.json`
and `repaired_http.json` contain complete sanitized serialized response evidence
for nine read requests. `initialization_and_action.json` includes full public
start/state/action response text, fixed denial, opening publication checks,
authoritative campaign equality and dispatch count. No production provider or
live gameplay was run. This does not verify a listening deployment.

Failure classification:

* Confirmed preexisting gameplay failures: all 17 node IDs from PR-PLAY-20 recur
  both before and after this repair (3 opening, 14 shared-turn). No repairs made.
* Pre-change additional failure: `test_chat_dialogue_lock_does_not_override_forceful_world_action`
  failed in setup at storage os.replace with WinError 5. Its targeted rerun passes.
* Repaired additional failure: `test_failed_start_campaign_does_not_mark_started`
  failed in existing rollback storage os.replace with WinError 5. It passed in
  the pre-change baseline; targeted rerun passes. Classify as an observed
  environmental I/O failure, not a confirmed new authorization regression.
  The precise external cause of Windows file denial is unresolved. No retry or
  storage workaround was introduced.
* Seven obsolete privileged-HTTP expectations: demonstrated by source trace,
  pre-change 200 disclosure, pre-implementation contract and intermediate
  seven-failure run. Their tests now require 403 while keeping pure internal
  projection assertions. These are intentional compatibility changes.
* Initial new-test iteration: three fixture/assertion mistakes (unseeded public
  visible fact, exact debug-list expectation despite existing derived traces,
  wrong combat key) and one transient WinError 5 setup error are retained in
  `focused_initial_fixture_errors.*`. Only tests were corrected; no production
  gameplay change. Subsequent focused runs pass.

New reproducible regressions: none observed in the exercised scope. Do not
interpret that as a green full suite: 17 known functional failures persist, and
the broader runs each had a separate transient file-I/O failure. HTTP
author/debug functionality is deliberately unavailable pending trusted access.
