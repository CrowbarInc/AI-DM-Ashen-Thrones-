# Fresh live manual review

Stamp `20261003T110414Z`. One isolated session. Three completed turns. No repair and no rerun.

## Turn 1 — FAIL

The player approached the tavern runner for stew and the missing-patrol rumor. The runner was bound canonically. Head `runner`. No incidental person.

The contract was `perceive` / `sound` because the sentence says “listen carefully.” The first reply invented a tightened curfew and a secret the serjeant lets slip. Hard validation rejected it (`consequential_invention`). The retry invented bandits and an old mill and was also rejected. The sealed line is the safe fallback: “The inspection establishes no further reliable detail about the sound.” Accepted text matches emitted text. Two generation attempts, which is the ceiling.

This is a bad answer. It is not a malformed incidental person.

## Turn 2 — PASS

The player asked the runner what people are saying about the patrol. The runner answered from the notice board, refused a solid fact, and pointed at the guard serjeant. Canonical binding. Head `runner`. Accepted text matches emitted text. The first draft was rejected; the retry was accepted.

## Turn 3 — FAIL

The player thanked the runner and asked the guard serjeant about the patrol, then looked at the serjeant’s demeanor.

Captured span: `the guard serjeant near the roster to ask`. Referential head: `serjeant`. Personhood of that head is unknown, so it was not instantiated. Catalog matching was ambiguous (`proposal:ambiguous`). Interlocutor id is null. The runner was not restored. No incidental row was stored. One interpretation call. It did not create a person.

The accepted reply is spoken by the guard captain, not the serjeant. That is a speaker mismatch. Accepted text matches emitted text. One generation attempt. Scene stayed `frontier_gate`.

## Continuation question

No fresh malformed incidental person. No place, object, or direction was stored as a person. Legitimate incidental binding was not shown to be switched off: the live player never addressed a novel role, and the deterministic controls still bind porter, woman, merchant, innkeeper, and lamplighter.

Manual gameplay: 1/3. The 2/3 bar is not met. The misses are the sound-fallback and the captain/serjeant speaker, not a new non-person NPC.
