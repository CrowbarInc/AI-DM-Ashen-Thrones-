# PR-CV Behavioral Authority Tests

Added deterministic PR-BT coverage:

- P2 narration-only provider request must carry `NARRATION-ONLY RESPONSE CONTRACT`.
- P2 system prompt must require the exact shape `{"narration": "player-facing response"}`.
- P2 system prompt must not expose `declared_claims`.
- P2 recipe must project `incidental_dialogue`, `reply_not_required`, and `Do not declare that reply as a world fact`.
- Smuggled narration-only output containing `declared_claims` must be rejected by `_safe_json`.
- Unauthorized declaration of `The baker prefers rye.` must be rejected by `validate_declared_claims_against_decision`.
- Valid harmless narration-only dialogue survives and normalizes to empty declarations without declaration authorship.

Focused result after reconciliation:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_bt_policy_instruction_deduplication.py tests\test_pr_bt_selective_epistemic_guidance.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cv_focused3
........
8 passed
```

Authority ownership was not changed. Validators were not weakened.
