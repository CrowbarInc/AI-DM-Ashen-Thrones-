# PR-BR Claim Control Slice 1 Test Results

All commands used the bundled local Python runtime with `PYTHONPATH=.\\.venv\\Lib\\site-packages`.

## Passed

- `python -m pytest tests\\test_pr_br_claim_control_slice1.py -q --tb=short --basetemp=codex_pytest_tmp_claim3`
- `python -m pytest tests\\test_pr_br_gm_resolution_decision.py -q --tb=short --basetemp=codex_pytest_tmp_claim6`
- `python -m pytest tests\\test_pr_br_decision_ownership_slice2.py -q --tb=short --basetemp=codex_pytest_tmp_claim9`
- `python -m pytest tests\\test_pr_br_qualifier_movement_mixed_intent.py -q --tb=short --basetemp=codex_pytest_tmp_claim11`
- `python -m pytest tests\\test_pr_br_continuation18_immutable_boundary.py -q --tb=short -k "not raw_chat" --basetemp=codex_pytest_tmp_claim14`
- `python -m pytest tests\\test_pr_br_continuation19_hard_authority.py -q --tb=short -k "not raw_chat" --basetemp=codex_pytest_tmp_claim15`
- `python -m pytest tests\\test_pr_br_continuation20_incidental_entity.py -q --tb=short -k "not raw_chat" --basetemp=codex_pytest_tmp_claim16`
- `python -m pytest tests\\test_pr_br_claim_control_slice1.py tests\\test_pr_br_gm_resolution_decision.py tests\\test_pr_br_decision_ownership_slice2.py tests\\test_pr_br_decision_semantic_fidelity_slice3.py tests\\test_pr_br_qualifier_movement_mixed_intent.py -q --tb=short --basetemp=codex_pytest_tmp_claim17`

## Interrupted

- Combined broad run including raw-chat API stub tests stalled and was interrupted.
- Full C18/C19 raw-chat files also stalled after their non-API tests had progressed and were interrupted.

## Model/gameplay API calls

0.
