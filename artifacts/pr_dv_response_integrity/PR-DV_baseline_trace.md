PR-DV Baseline Trace

Baseline reproduced from PR-DU focused production-function harness before repair:

1. Lantern inspection executed through `game.api.chat`, resolver `investigate`, final text could remain generic when the narrator emitted generic text.
2. OOC correction returned non-mutating text and did not invoke gameplay execution.
3. Sergeant Mara question executed through social resolver and could preserve the authored `north road` topic when model text included it.
4. Courtyard gate transition mutated state to `waystation_street`, but generic final text could obscure the destination.
5. Notice-board inspection resolved `street_notice`, but generic final text could obscure the authored notice text.

Observed baseline red tests:
- `test_pr_dv_structured_resolution_facts_survive_generic_final_text` failed on lantern text: final output was `The action resolves.`
- `test_pr_dv_rejected_and_ambiguous_stored_interpretations_do_not_fallback_execute` failed because a rejected stored interpretation fell through to the parser and executed as `investigate`.
