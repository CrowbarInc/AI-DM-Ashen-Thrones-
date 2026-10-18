# PR-CX Implementation Changes

Changed production files:

- `game/proposition_authority.py`
- `game/gm_resolution_decision.py`

Changed tests:

- `tests/test_pr_cw_social_context_projection.py`
- `tests/test_pr_cx_authority_assurance.py`

Implementation summary:

- Added five narrow consequential proposition families: `biography`, `geography`, `hidden_information`, `npc_action`, and `discovery`.
- Added grounding checks so authored exact/corpus-covered statements can still be authoritative.
- Kept hearsay/speculative frames as NPC claims instead of world truth.
- Narrowed geography matching after C18 replay showed false positives on ordinary proximity/body language.
- Extended GM decision structural detection for present-tense consequential actions, hidden objects, and discovery statements.
- Updated PR-CW adversarial expectations from inherited acceptance to PR-CX rejection.
- Added PR-CX focused tests proving full/reduced equivalence for the repaired categories and preservation for harmless dialogue.

