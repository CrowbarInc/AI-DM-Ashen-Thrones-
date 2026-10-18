# PR-DQ IC/OOC Safety

OOC messages must not execute authoritative gameplay actions.

`execution_permitted` is true only for an uncommitted IC message whose destination is IC_ACTION or IC_DIALOGUE and whose status is still CLASSIFIED. OOC, MIXED, UNRESOLVED, rejected, and clarification messages fail that gate. The resolver wrapper raises if a non-IC message reaches it.

A message that does not execute is compared to the authoritative snapshot taken before dispatch. The snapshot covers scene, visited scenes, clocks, turn counter, NPC runtime, scene state, resolved interactables, flags, inventory, HP, combat action use, and world flags. A difference raises `OOCSafetyError`.

An OOC path does not:

- advance world time
- consume a combat action
- move a character
- change inventory
- change HP
- call a social or exploration resolver
- establish a world fact
- roll gameplay dice
- rewrite an earlier message or its result

An OOC correction with subject COMMITTED_ACTION returns a non-mutating adjudication notice. It does not undo the committed turn.

An IC override does not authorize an unsupported mechanic. The adapter rejects that class before any resolver call and restores nothing because it did not call.

An accepted IC result may keep session changes made by the existing resolver, then apply only the slice's own scene, clock, clue, and turn-counter updates. Character, combat, and the world document are restored from the pre-call copies even on acceptance, so this slice does not take HP, inventory, or world-flag changes from the resolver. An unaccepted resolver result restores the session copy as well. That discard happens before commit. It is not a rollback of committed history, and this cycle does not implement one.

No provider is called. Production `data/session.json`, `data/world.json`, `data/combat.json`, and `data/session_log.jsonl` are not the slice's store.
