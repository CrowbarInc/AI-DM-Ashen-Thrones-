# PR-CN Persistence And Continuity

Verified path:
1. Grounded narration accepted.
2. Contextual-lead extraction generated a guard candidate.
3. Lead storage persisted subject `guard`.
4. Session reload preserved subject `guard`.
5. Next-turn provider payload included the guard lead key.
6. Next-turn provider payload did not include `as_you`.
7. Passive-pressure source selection selected `guard`, not `as you`.

No migration was added for historical saved sessions. If an existing save already contains a malformed `as you` lead, this repair does not silently rewrite it.
