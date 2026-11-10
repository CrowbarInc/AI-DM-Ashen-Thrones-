# Root cause

The button path submits an action id. Availability is checked and `authored_consequences.resolve` commits the flags and trusted text.

Chat did not consult that id. `player_initiative` matched an authored verb only when the sentence started with record, report, or survey.

- "I return to report the uncertain trail to the watch." missed that matcher. Destination parsing then treated the words after "to" as a place and refused an unknown destination. The button with the same label succeeded.
- "I record the survey at the milestone." matched the unavailable follow-up `patrol_record_survey` and declined, instead of the available `patrol_survey`.
- A mixed "examine the notice board and ask the guard" split into steps whose investigation path did not call `resolve_exploration_action`, so the notice clue was not committed. A standalone examine did call it.
- An unrecognized conditional fell through to the full chat path. The lifecycle stub returns the Cinderwatch opening. That text was published while `active_scene_id` stayed `old_milestone`.

The repair does not add a second executor. `decision_for` runs before the old verb matcher. A proposal is only an id. The existing custom-action path rechecks the row and commits through the existing consequence resolver.
