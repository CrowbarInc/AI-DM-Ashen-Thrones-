# PR-CZ Implementation Changes

Changed files:
- `game/resolution_contract.py`
- `game/gm_resolution_decision.py`
- `tests/test_pr_cz_followup_reliability.py`

Implementation:
- `resolution_contract.py`: copies a validated discourse interlocutor into `interlocutor_id` for ask contracts, and handles narrow short elliptical follow-ups against active discourse focus.
- `gm_resolution_decision.py`: adds a narrow `harmless_qualified_npc_observation` classification before narrator-lead rejection.
- `tests/test_pr_cz_followup_reliability.py`: adds deterministic positive and negative controls plus PR-CY retry replay.

