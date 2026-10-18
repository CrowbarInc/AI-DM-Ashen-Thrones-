# PR-CC Implementation Report

Mode: Incidental social reply planning reconciliation.

Live provider calls: 0.

Inherited PR-CB decision: F - multiple coupled causes.

Implemented repair:
- Added bounded social reply-plan kinds for unauthored social turns:
  - `authoritative_answer_available`
  - `harmless_subjective_response_permitted`
  - `genuine_uncertainty`
  - `genuine_refusal`
  - `consequential_information_request`
- Changed the missing-topic branch in `resolve_social_action` so absence of an authored topic no longer automatically projects refusal.
- Harmless subjective requests now receive `reply_kind=answer`, `incidental_subjective_allowed=true`, `npc_speech_authority=claim_only`, and no objective fact or mutation authority.
- Consequential/restricted requests remain outside the subjective lane and keep `objective_world_fact_authority=authored_context_required`.
- Projected the same bounded codes through `noncombat.narration_constraints` and `dialogue_social_plan`.
- Added provider guidance that permits only attributed, low-consequence NPC speech and explicitly preserves consequential/refusal/uncertainty limits.

Files changed for PR-CC:
- `game/social.py`
- `game/noncombat_resolution.py`
- `game/dialogue_social_plan.py`
- `game/prompt_context.py`
- `tests/test_social.py`
- `tests/test_pr_cc_social_reply_reconciliation.py`

Worktree note: these files had pre-existing unrelated dirty changes. This report records only the PR-CC scoped additions above.

Decision: B - partial repair.

Reason: The corrected refusal mechanism and focused positive/negative/authority controls pass. Broad deterministic regression and one adjacent social relevance file were interrupted after long quiet periods in this already-dirty worktree, so PR-CC is not marked ready for live comparison.
