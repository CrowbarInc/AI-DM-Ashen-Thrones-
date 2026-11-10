# Mixed-action integration

`integrated_play` asks `authored_examination` before the generic investigation step. That helper runs only when one current interactable with `reveals_clue` is named by examine, read, inspect, check, study, or look at. It calls `resolve_exploration_action`. On `discover_clue` it commits through `apply_authoritative_clue_discovery` and `mark_interactable_resolved`. Later steps in the same turn see that clue.

Browser report, first typed turn: "Examine the notice board and ask the guard about the warning." Published text contained the northwest-mud clue and then "Gate Guard says, \"I do not know about that.\"" The discovery committed. The guard did not invent knowledge of the warning.

"I look at the weathered milestone and the tracks." published the overlapping-prints clue and then said a further part was not supported. The clue was not fabricated by narration alone.
