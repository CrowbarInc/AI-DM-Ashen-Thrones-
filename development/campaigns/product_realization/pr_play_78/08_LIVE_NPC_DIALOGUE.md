# Live NPC dialogue

Operation `bounded_social_line` allows ordinary wording and rejects quests, rewards, secrets, gold, hidden phrases, invented routes, identity changes, a verbatim copy of the host line, and unauthorized commitments. It is used only when `ASHEN_BOUNDED_SPEECH=1`. Withheld 3-grams from hidden facts and discoverable clues are held in a context variable, not on the player contract.

Post-fix published accepts at the gate (3), from `live_gate.json`:

- Greeting: "Hello there, just keeping an eye on things by the gate today."
- Local warning: he is an ordinary gate guard and does not know much about the warning.
- Thanks: "Thank you. Goodbye. Stay safe out there."

Those three are a multi-turn exchange with the same Gate Guard. Identity questions still clarify when more than one person matches, so "Who are you?" did not become a fourth live line.

Pre-fix extended session also published four provider lines while the Gate Guard was still addressable at the milestone:

- Greeting that added "The mud track ahead gets tricky after the stone marker."
- Uncertainty about the warning.
- Uncertainty about what concerns him, with ordinary self-description.
- Uncertainty about whether anyone passed.

The tricky-track sentence is an accepted publication that stated a road condition the host had not committed. Scene scoping stops that NPC from being greeted at the milestone. It does not rewrite the earlier transcript.

Rejected or unused: extended turn 10, "Thank the guard and look around.", requested a live line and published the deterministic "Thank you. Goodbye."

No Captain Thoran, no hidden fact, no quest, and no reward appeared in these lines. Browser dialogue is the deterministic "Hello." / "I do not know about that." because that host disabled provider calls.
