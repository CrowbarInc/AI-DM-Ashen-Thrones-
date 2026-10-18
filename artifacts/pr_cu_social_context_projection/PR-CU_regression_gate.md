# PR-CU Regression Gate

Mode: resolver-specific context projection.

Live provider calls: 0.

Git HEAD recorded before PR-CU work: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`.

Worktree safety:
- The repository was already dirty before PR-CU.
- No reset, checkout, or production-save restoration was performed.
- PR-CU did not modify runtime code or production save data.

Pre-implementation gate results:

| Suite | Command | Result |
|---|---|---|
| PR-CT prompt-contract tests | `.\.venv\Scripts\python.exe -m pytest tests\test_pr_ct_safe_prompt_deduplication.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cu_gate_ct` | 3 passed |
| PR-BT policy-instruction tests plus selective guidance check | `.\.venv\Scripts\python.exe -m pytest tests\test_pr_bt_policy_instruction_deduplication.py tests\test_pr_bt_selective_epistemic_guidance.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cu_gate_bt` | 3 passed, 3 failed |
| Authored-knowledge realization | `.\.venv\Scripts\python.exe -m pytest tests\test_authored_knowledge_realization.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cu_gate_authored` | 14 passed, 2 failed |
| PR-CP authorized finalization | `.\.venv\Scripts\python.exe -m pytest tests\test_pr_cp_authorized_finalization.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cu_gate_cp` | 9 passed |
| PR-CR authored retry recovery focus | `.\.venv\Scripts\python.exe -m pytest tests\test_pr_by_narration_only_retry_contract.py tests\test_pr_br_continuation18_immutable_boundary.py tests\test_pr_br_continuation19_hard_authority.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cu_gate_cr` | 54 passed |
| Shared turn pipeline | `.\.venv\Scripts\python.exe -m pytest tests\test_turn_pipeline_shared.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cu_gate_shared` | 41 passed, 24 failed |

PR-BT failure investigation:

1. `test_pr_bt_reconstructed_provider_requests_keep_required_rule_presence`
   - Failing probe: P2.
   - Missing provider-visible rules:
     - `authority_generated_prose_not_authoritative`
     - `npc_incidental_bounded`
     - `declaration_lane_visible`
     - `ordinary_narration_need_not_be_declared`
     - `structured_envelope_explicit`
     - `raw_internal_json_no_player_leak`
   - Assessment: required policy is genuinely missing from the effective reconstructed provider request for that probe according to the PR-BT detector.
   - PR-CT relation: the missing strings are not the three exact duplicate instruction strings removed by PR-CT. This does not appear to be caused by PR-CU, and available PR-CT artifacts already recorded PR-BT failures as inherited/unrelated.

2. `test_pr_bt_provider_requests_remove_at_least_12000_chars_each`
   - Failing assertion: P3 reduction was `110665 - 99094 = 11571`, below the older 12000-character threshold.
   - Assessment: this is an obsolete/over-specific savings threshold relative to PR-CT's measured limited savings, not an authority expansion by itself.

3. `test_p2_mundane_npc_path_stays_incidental_dialogue`
   - Missing system-prompt phrase: `On an interpretation, or when the player offers a hypothesis`.
   - Assessment: the P2 narration-only route does not carry the same epistemic protocol phrase expected by the selective-guidance test.

Authored-knowledge failure investigation:

- Current failures:
  - `test_http_notice_question_communicates_patrol_fact`
  - `test_http_read_notice_board_speaks_written_clue`
- Both expected the authored notice fact containing `northwest`.
- Actual outputs:
  - `gate guard says, "i do not know enough to answer that."`
  - `a gate serjeant manages the crowd and keeps one eye on the roster board.`
- Assessment: inherited authored-realization gap. PR-CT artifacts reported authored-knowledge failures in this area before PR-CU. PR-CU made no code changes, so these are not new PR-CU regressions.

Gate decision:

The gate is blocked for PR-CU implementation. The current provider request already fails a prompt-contract/policy-surface check for ordinary NPC dialogue. Even if this appears inherited rather than introduced by PR-CT's exact deduplication, the requested optimization requires the existing authority and prompt contracts to support reducing context. They do not.

Decision: C - REGRESSION GATE BLOCKED.
