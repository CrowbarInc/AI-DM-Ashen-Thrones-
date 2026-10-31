# 01 — Implementation Summary

ATGB-R1-02, 2026-10-18. Failure class: contract, as established by ATGB-R1-01. Implementation authority: mechanical revision routing only.

The prior investigation establishes the mechanism in the verified current source. Its S08.2 trace, mechanical counterexample, causal comparison, minimal recommendation, validation proposal and verdict were read before editing. `support/docs/NEXT_SESSION.md` is a bundle-relative path; repository orientation is `docs/NEXT_SESSION.md`. PR-EG-R6-R5 artifacts 11, 32 and 36 were reviewed. R5's bind/witness repair remains a different mechanism and was not integrated.

Production changes are limited to `game/conversational_orchestration.py`:

- `_REVISION_RE` keeps the established explicit `instead`, `make that`, and `revise` cues, recognizes `change my/the pending`, and no longer treats `i meant` or bare `change that` as sufficient by themselves.
- `_pending_revision_decision` accepts existing interpreted action components. Without an explicit cue, correction language requires both an existing intention referent (pending, clarification, or last executed) and an action component. Existing scene, status, no-pending, and executed-action checks then run unchanged.
- `_communication_decision` passes those components and reserves the set-aside/clear-context branch for WITHDRAWAL. A nonmechanical CORRECTION continues through ordinary public-evidence answering rather than clearing an intention.

The distinction uses existing state and interpretation signals. It contains no scenario IDs or calibration nouns, no new classifier, no prompt change and no new model call. Unrelated observatory/astronomer fixtures exercise the same condition; these authored variations are not independent held-out generalization.

Legitimate revisions remain pending, explicit requests with no pending action remain safeguarded, and executed actions remain immutable. A correction purpose is no longer itself authorization to control an intention.

Other authored files: `tests/test_atgb_r1_02_revision_boundary.py`; these eight reports and index; `docs/NEXT_SESSION.md`; campaign evidence scripts/JSON/logs/diff under `artifacts/atgb/atgb_r1_02/`; validation evidence packet; review configuration and generated exports. Extensive pre-existing dirty worktree changes were retained. No commit or push.
