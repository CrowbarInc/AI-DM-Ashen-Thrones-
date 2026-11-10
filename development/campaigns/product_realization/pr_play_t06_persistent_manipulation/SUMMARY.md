# PR-PLAY T06 Persistent Physical Manipulation

Milestone: `pr_play_t06_persistent_manipulation`. Predecessor: `pr_play_t04_local_action`. Cycle verdict: **BLOCKED**. Primary failure class: **architectural**.

Original HTTP T06 reproduces. Parsing recovers a physical interaction but calls its verb `try` and leaves the entire copy clause as an unbound target. `_unbound_physical_decline` selects `unsupported_physical_manipulation`; `_chat_turn` returns before any physical resolver or prerequisite checks. The refusal is truthful but generic.

The known clue is present; an equipped sleeve identity, access, suitability and usable mud supply are not established. More fundamentally, inventory dictionaries can persist JSON but there is no existing item-instance modification validator/application owner, equipment binding, or later item-inspection projection for this action. Adding fields to character inventory alone would not satisfy the authority contract. The experimental physical owner has its own scene-object/posture ledger and no carried-item binding; enabling or repurposing it here would create a parallel authority.

No production files changed. No successful controlled-fixture modification is claimed. The stop conditions in sections 8 and 17 of the request apply; no fabricated A/PASS or B/PARTIAL implementation.

Original and final T06: “That part is not supported here. It was not carried out.” Character, world, scene and knowledge are unchanged. Refusal text is hard-valid and immutable; the completed-publication pointer still references T05, accurately not recording a completed inscription.

Fresh baseline: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). Final same selection: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failure identities: 0. New diagnostic controls: 6 passed / 0 failed / 0 errors / 0 skipped (6 tests). Existing physical/persistence/state-authority controls: 93 passed / 0 failed / 0 errors / 0 skipped (93 tests). Historical 408/17 is reference only; exact fresh identities are in REGRESSION_RESULTS and test_results.json. No causal repair claim for fluctuating failures.

All twelve published turns and compared authority/state fields are unchanged. T04 contact, T05 disclosure, T09 recall and T11 travel remain. T01/T07 narration, T02 NPC usefulness, T08 acknowledgment, T10 trading and T12 refusal remain deferred. Zero live provider calls; no commits/pushes.

Exactly one proposed next action: Conduct one bounded architecture review to assign item-instance modification ownership and define its validated mutation and inspection contract within existing character persistence.
