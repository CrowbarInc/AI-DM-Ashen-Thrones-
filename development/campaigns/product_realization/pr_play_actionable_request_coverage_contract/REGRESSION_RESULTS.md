# Regression

Same combined selection as the predecessor (`artifacts/pr_play_inventory_object_reference_binding/combined_before_command.txt`), same environment: live interpretation, expression, and provider retries disabled, upstream preflight skipped, `ASHEN_DISABLE_PROVIDER_CALLS` unset, experimental physical adjudication unset, external sockets blocked.

Final run: `artifacts/pr_play_actionable_request_coverage_contract/combined_after_local_result.json`.

| | Tests | Passed | Failed | New identities | Provider records | External sockets |
|---|---:|---:|---:|---:|---:|---:|
| Predecessor saved after | 425 | 408 | 17 | 0 | 0 | 0 |
| This milestone | 425 | 408 | 17 | 0 | 0 | 0 |

Failure identities match `artifacts/pr_play_compound_action_admission_guard/regression_comparison.json` exactly. None resolved, none added.

An earlier combined run, taken before admission deferred to the existing local-action owner, failed three additional tests: `test_recorded_handoff_leaves_the_previous_npc_line`, `test_a_original_t04_http_completes_without_mutation`, and `test_e_compound_outcome_authorizes_both_parts`. Those are superseded. After the deferral, that file's HTTP checks pass, and the 425-test run is 408/17.

Focused checks run directly:

- `tests/test_compound_action_admission.py` passed with the local-action and handoff checks (44 passed).
- `tests/test_ordinary_semantic_admission.py` still fails `negated_travel` / "Instead of entering the gate, I wait beside the rain barrel." on `addresses_request` only. Authority, duplicate, and non-execution checks on that case stayed true. The predecessor already recorded this wording failure. The assertion was not weakened or removed.
- Durable reload: eight checks true (`durable_reload.json`).

The historical 611-test focused bundle was not repeated as its own process. Modules that sit inside the 425-test selection did not add failure identities.
