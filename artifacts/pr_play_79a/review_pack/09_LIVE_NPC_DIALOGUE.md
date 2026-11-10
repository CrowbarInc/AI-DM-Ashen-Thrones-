# Live NPC dialogue

Provider was enabled. Expression generation used `bounded_social_line`. Counts below require the turn's interlocutor `last_player_utterance` to match the input, `dialogue_adopted` true, and the player text not to be a refusal or a clarification.

Published in the conversation campaign:

1. Hello, Gate Guard. — provider greeting, then a narration wrapper.
2. Who are you? — provider identity line, then a narration wrapper.
3. When did you last hear about them? — the guard is not sure when.
4. Do you think something happened? — the guard is unsure whether anything occurred.
5. What is this place like? — the guard cites the visible notice and the muddy gate line.
6. Who are you? (after the failed beats) — provider identity line.
7. Who are you? (after snapshot resume) — provider identity line.

Not published as dialogue:

- "What do you know about the missing patrol?" — "Nothing was attempted. That is not available here yet."
- "What about the patrol again?" — the same refusal.
- "Look around the gate." — "Which person do you mean: Gate Guard or Gate Serjeant?"

Longest stretch without a clarification or refusal: three turns (when / think / place). That misses the five-consecutive gate. The six-line gate is met only if the interrupted lines are counted; they are not one continuous sequence. Deterministic host lines are not counted.
