# State integrity

Canonical `data/` hashes were identical before and after the experiment. `.env` was unchanged. No campaign fixture was rewritten.

## Live versus no-provider baseline

A1, B1, and C1 matched their baselines on player-facing text, mechanical outcome, inventory, conditions, combat, and the scrubbed world slice. The prelude did not appear in the player-facing text or in that authority slice. Baseline turns made zero provider calls.

B1's second turn is `already_searched`, success false, on both the live run and the baseline. C1 is `investigate`, success true, no clue, on both.

## D1

The in-process D baseline did not match. Its player-facing text was the playtest stop message, and its mechanical kind was `interpretation_rejected`. That turn ran after six expression requests had already been counted against `ASHEN_PROVIDER_REQUEST_LIMIT=6`. The chat gate refused it before resolution. The difference is the experiment ceiling, not the prelude.

A fresh process then resolved "I examine the footprints." with provider calls disabled and no request ceiling. It made no provider call. It matched live D1:

- Player-facing text identical, including the authorized print sentence.
- Kind `discover_clue`, same clue id and clue text.
- Inventory still the starting spellbook.
- Event log length 2.
- The same three faction progress and pressure values.

Those faction and event-log changes are produced by deterministic clue resolution. They appear with the provider off. The prelude did not cause them. Evidence: `supplemental_d_baseline.json`. The original mismatched pair is preserved in `scenario_results.json` and was not edited to hide it.

## Quarantine

The live hook does not write the prelude back onto the resolution. Player-facing text for the successful discoveries stayed on the deterministic sentence. No experimental narration was stored as the authoritative player response.

Offline invariant checks, with no provider call, confirmed that a silver-key find is not a pass, that an unfamiliar mark is `REVIEW_REQUIRED`, that the gate blocks review, and that the validator reports zero provider requests. Those checks did not change the validator bytes.
