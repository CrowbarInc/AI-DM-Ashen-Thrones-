# 08 Follow-up investigation

Player: "I examine the rain barrel."

Engine: `investigate`, success, no discovered clue, no item, no NPC change. The earlier route remained the only discovered clue.

Provider: 410 input, 69 output, 479 total. Provider latency 1972.176 ms. Validation 16.549 ms. HTTP 2266.065 ms.

Validation: semantic FAIL, coverage REVIEW_REQUIRED, legacy hard-valid false, combined FAIL.

Rejected candidate, retained only in the diagnostic record:

"You take a careful look at the rain barrel, noting its worn surface and the faint scent of damp wood. Aside from what you already knew about the missing patrol last seen heading northwest past the crates, this close inspection reveals nothing new or unusual. The bustle around the barrel continues, with the tavern runner nearby trading hot stew and rumors."

The original live response showed the provider-disabled stub because ordinary narration was intentionally disabled. The replay of this same candidate publishes the engine sentence instead: no new clue, the known route, and the visible gate facts. The rejected candidate is not the player text.
