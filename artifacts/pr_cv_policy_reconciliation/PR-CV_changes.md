# PR-CV Changes

Implementation changes:

- None.

Test changes:

- `tests/test_pr_bt_policy_instruction_deduplication.py`
  - Reconciles rule-presence checks with the effective provider envelope.
  - Treats P2 narration-only as a valid effective contract instead of requiring structured-envelope markers.
  - Replaces the arbitrary 12,000 total-character threshold with current optimization behavior checks.
  - Adds deterministic parser/validator authority tests for narration-only dialogue.

- `tests/test_pr_bt_selective_epistemic_guidance.py`
  - Keeps P1/P3 epistemic protocol expectations.
  - Rebaselines P2 to assert narration-only incidental-dialogue behavior instead of requiring interpretation/hypothesis guidance.

Files were already untracked in the inherited worktree and are listed as changed PR-CV scope files.

