# Disclosed-fact recall

The campaign already knew clue `notice_patrol_route`: “The missing patrol was last seen taking the northwest mud track past the crates.”

Typed twice, not through the Examine button:

1. `I examine the notice board.`
2. `I examine the notice board again.`

Both player-facing replies were:

`You examine the notice board again. Previously disclosed here: The missing patrol was last seen taking the northwest mud track past the crates. The examination adds nothing new to what you already know.`

Each reply used one interpretation request and no expression request. The two publication records share the same published-text reference. Position stayed `back` from the notice board. The patrol clue was not replaced and no additional discovery sentence was published. The social lead created on the dialogue turn remained, and the examinations did not add another clue.

The repeat is source-bound recall of a fact disclosed before this cycle. It spent a live interpretation request because the browser sequence required the repeat. It did not spend an expression request to restate the clue.

Deterministic snapshot recall in `test_snapshot_restores_disclosed_fact` also passed on this fingerprint.
