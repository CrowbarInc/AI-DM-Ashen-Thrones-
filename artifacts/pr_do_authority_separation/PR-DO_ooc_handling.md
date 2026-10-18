# PR-DO OOC Handling

Three different acts stay distinct:

| Act | How it is represented | What eligibility does |
| --- | --- | --- |
| Correct a previous referent | Mode `OUT_OF_CHARACTER_CORRECTION`, subject `REFERENT` | `OUT_OF_CHARACTER`. No action, time, NPC response, or history rewrite. |
| Correct a previous intention that refers to a committed line | Mode `OUT_OF_CHARACTER_CORRECTION`, subject `COMMITTED_ACTION` | `OUT_OF_CHARACTER`. `history_disposition=ADJUDICATION_REQUIRED`. History is not rewritten. |
| Issue a new in-world action | Mode `IN_WORLD_ACTION` and an allowlisted class | May be `ELIGIBLE_FOR_VALIDATION`. Still not executed. |

DN04, "OOC: I meant the left guard, not the captain."

The leading `OOC:` prefix sets the engine channel. "Left guard" stays an unresolved reference and is not created as an entity. Disposition is `OUT_OF_CHARACTER`. `consumes_action`, `advances_time`, and `creates_npc_response` are false. Subject `REFERENT` leaves history `UNCHANGED`.

DN12, "Actually, I meant to ask the captain about patrols, not accuse him."

There is no `OOC:` prefix. The contract fixture supplies the correction mode and subject `COMMITTED_ACTION`, because the line refers to an accusation already in play. Disposition is `OUT_OF_CHARACTER`. The corrected question is a descriptive wish, not an `ASK` submission. Adjudication is required before any restatement. No rollback is performed.

A model that labels an explicit `OOC:` line as `IN_WORLD_ACTION` with class `ASK` is still out of character, because the engine channel overrides the model mode.

A model that labels DN12 as an in-world `ASK`, with no prefix and no correction subject, is eligible for validation and is not executed. The package does not guess that unmarked sentence is a correction. That remaining miss is recorded in the routing report.
