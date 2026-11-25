# Limitations

The repair withholds a negated or conditional player act. It does not interpret every negation.

- "I approach the guard but do not speak." still uses the provider-disabled narration path and advances the turn. The approach clause is affirmative, so the new gate does not take it.
- "Tell me the hidden motives of the threadbare watcher." and "Tell me about the patrol." still ask "Which person do you mean: Guard Captain or Tavern Runner?" Nothing is attempted, and no motive is invented. The clarification set is still wrong.
- "I examine the book." still does not bind the spellbook, and the turn still advances.
- "I look around the gate district." still hits the provider-disabled stub and advances the turn.
- A committed social check is still final for that kind and NPC. A failed check does not roll again. That behavior was not changed.
- "I ask the guard captain about the patrol" can still change trust through the legacy dialogue path. That path was not changed. The paused milestone remains paused.
- Putting a coat on a table, taking a rope, and casting a spell remain capability gaps. They were not given new mechanics.
- Live model understanding was not measured. Every score here is deterministic HTTP with providers disabled.
- The broad sample does not contain the repaired sentences. A change in the historical 12/40 score is not claimed from this repair. The replay comparison is the authority for whether any frozen line changed.
