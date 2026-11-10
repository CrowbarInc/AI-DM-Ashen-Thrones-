# 09 Repeated investigation

Player: "I examine the notice board again."

Engine: `already_searched`, success false, no new clue, `already_searched` true. The discovered-clue list stayed one entry.

Provider: 448 input, 57 output, 505 total. Provider latency 1947.887 ms. Validation 7.975 ms. HTTP 2239.977 ms.

Validation: semantic PASS, coverage PASS, legacy hard-valid true, combined PASS.

Published sentence:

"You take another careful look at the notice board, but nothing new catches your eye beyond what you already know: the missing patrol was last seen heading along the northwest mud track past the crates. The posted taxes, curfew rules, and warnings remain unchanged, offering no fresh clues."

The sentence keeps the earlier discovery and does not add a second copy of the clue.
