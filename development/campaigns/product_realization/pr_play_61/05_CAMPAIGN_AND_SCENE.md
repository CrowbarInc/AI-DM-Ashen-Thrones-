# 05 Campaign and scene

Fixture: `data/scenes/frontier_gate.json`, copied into an isolated session directory. The canonical file was not edited.

Scene: `frontier_gate`, Cinderwatch Gate District.

Player: Galinor, the default wizard sheet. HP 8/8.

Investigable element: `notice_board`, clue `notice_patrol_route`.

Authorized discovery: "The missing patrol was last seen taking the northwest mud track past the crates."

Follow-up: "I examine the rain barrel." The engine treats this as an investigation of a visible feature and discovers no new clue.

Repeat: "I examine the notice board again." The engine returns `already_searched` and does not add the clue a second time.

Continuation: "I look around the gate." The engine returns an observation and no new clue.

Hidden facts and the canary clue added by the isolated seed stayed undisclosed.
