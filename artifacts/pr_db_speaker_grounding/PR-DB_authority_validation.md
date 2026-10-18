# PR-DB Authority Validation

`tests/test_pr_cx_authority_assurance.py`: 9 passed / 0 failed / 0 skipped.

Rejected, with and without projection enabled:

- Invented biography: the captain born in Blackharbor and serving twenty years.
- Invented geography: the old milestone east beyond the trading crossroads.
- Hidden information: a secret tunnel beneath the gate.
- Consequential NPC action: the captain unlocks the gate and lets the player pass.
- Unauthorized discovery: a hidden map under the notice board.

Each rejection kept `hard_valid` false, reason `unauthorized_resolution_decision_fact`, and a player-facing text different from the candidate. Projection on and off produced the same audit and the same text.

Accepted:

- Harmless preference.
- Ordinary opinion.
- Incidental characterization.
- A grounded observation already on the notice board.

`tests/test_bounded_improvisation_authority.py`: 5 passed / 0 failed.

`tests/test_pr_br_continuation18_immutable_boundary.py`: 21 passed / 0 failed.

`tests/test_pr_br_continuation19_hard_authority.py`: 11 passed / 0 failed.

`tests/test_pr_br_c19_free_text_authority.py`: 5 passed / 0 failed.

No authority predicate was weakened. The follow-up reply plan remains `genuine_uncertainty`, so this turn does not receive harmless-subjective speech authority.
