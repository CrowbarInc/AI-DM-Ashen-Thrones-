# Continuation 10 temporary compatibility bridges

Continuation 11 must replace both of these. Neither one turns an abstention back into a confident malformed target.

## 1. Unscoped player nominal

`construct_resolution_contract` does not load a scene catalog. When `canonical_referents` is omitted (`None`), a short determiner or verb nominal may still become an explicit target. That keeps existing lines such as "posted sheet" and "canvas awning" on the live `/api/chat` path.

The bridge does not apply to:

- a bare preposition capture with no determiner (`on duty` -> `duty`)
- a clause-sized span
- a compound with two speech-act families

An empty catalog is a supplied index. Unknown nominals abstain. Tests that pass `canonical_referents=[]` or a real index do not use the bridge.

## 2. Abstention reuses the clarification obligation

Hard abstention (`target_not_canonical`, `malformed_target_span`, `unresolved_compound_intent`, `conflicting_operations`, invalid model fields) sets `operation` to `unresolved`, clears the target, and blocks discourse commit. Generation already uses the existing clarification constraint. There is no new player-facing fallback line.

`insufficient_discourse_context` does not wipe a lexical operation the older contract already chose (`act`, `perceive`). It still blocks discourse commit, so an unresolved anaphor cannot create `object:it`.

## Not migrated

Sessions that already stored a malformed `active_inspected` value are not scrubbed. New commits cannot add one.
