# 10 — NPC dialogue

Bounded dynamic-NPC tests still greet, name themselves, cite a visible fact, remember what the player said, and refuse the patrol secret. Those lines in the development tests are deterministic because provider expression is disabled there.

On the live gate:

- "Hello, captain." asks which of Gate Guard, Gate Serjeant, or Tavern Runner.
- After the greeting repair, "Hello, Gate Guard." publishes `Gate Guard says, "Hello."`
- "Talk to the Gate Guard." publishes the authored mutter about captain Thoran and discovers `captain_thoran_watch`.
- "Who are you?" immediately afterward asks which available person is meant.
- "Thank you." again reaches the Gate Guard (`Thank you. Goodbye.`).

No expression audit was attached. Completed provider requests added by the two dialogue continuations: 0. Accepted live dialogue: 0. Published live dialogue: 0.

The eight-beat live conversation was not achieved. Identity is consistent on the two lines that name or thank the guard. Follow-up questions do not stay with that guard.
