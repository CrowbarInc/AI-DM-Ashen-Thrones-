# 03 PR PLAY 63 REPRODUCTION

Original action: `I examine the notice board.` Resolver: `discover_clue`, success true. Mandatory discovery: “The missing patrol was last seen taking the northwest mud track past the crates.” Prior continuity: empty. Original post-resolution authority and publication are preserved in `historical_original_gameplay.json`.

Exact candidate:

> You study the notice board and learn that the missing patrol was last seen taking the northwest mud track past the crates.

Baseline complete-pipeline replay: FAIL, semantic reason `unauthorized_discovery`; mandatory coverage PASS. Legacy audit is initially valid and is then marked false by the consequential gate. Original fallback: “You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.” Exact original and reproduced traces: `historical_before.json`. No substitute narration was used.
