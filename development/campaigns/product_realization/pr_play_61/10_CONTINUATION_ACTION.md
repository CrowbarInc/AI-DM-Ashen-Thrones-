# 10 Continuation

Player: "I look around the gate."

Engine: `observe`, no new clue, same scene.

Provider: 410 input, 78 output, 488 total. Provider latency 2187.42 ms. Validation 17.023 ms. HTTP 2568.62 ms.

Validation: semantic PASS, coverage REVIEW_REQUIRED, legacy hard-valid true, combined REVIEW_REQUIRED. The candidate was not published.

Rejected candidate:

"You take in the scene around the gate once more, noting the familiar bustle: the serjeant watching the crowd, the tavern runner hawking stew and gossip, and the weary watchers and refugees lining the muddy queue. The notice board still displays the same warnings, including the missing patrol last seen heading northwest past the crates—information you already knew, with nothing new to add."

The replay publishes the engine fallback. The session accepted the action and remained on `frontier_gate` with the same single clue.

The player UI then accepted another "I examine the notice board again." The input cleared and stayed enabled. That browser action ran with the experimental flag off and provider calls disabled, so its sentence was the ordinary disabled-provider line, not a fifth live narration.
