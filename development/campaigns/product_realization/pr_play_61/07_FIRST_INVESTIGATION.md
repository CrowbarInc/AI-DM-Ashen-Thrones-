# 07 First investigation

Player: "I examine the notice board."

Engine: `discover_clue`, success, interactable `notice_board`, clue text exactly the authorized route. No item and no NPC change.

Provider: gpt-4.1-mini-2025-04-14. 395 input tokens, 59 output tokens, 454 total. Provider latency 3071.704 ms. Validation 27.224 ms. Integrated work 3102.425 ms. HTTP 3330.874 ms.

Validation: semantic PASS, coverage PASS, legacy hard-valid true, combined PASS.

Published sentence:

"You study the notice board more closely and uncover a crucial detail: the missing patrol was last spotted taking the northwest mud track past the crates. This new information sharpens your understanding of their last known movements amid the bustle of watchers, refugees, and the ever-watchful gate serjeant."

The player UI rendered that sentence. The clue was stored once.
