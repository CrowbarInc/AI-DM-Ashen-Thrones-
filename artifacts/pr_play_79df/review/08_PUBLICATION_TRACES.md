# Publication traces

Four player-facing chat turns produced four publication records. Each record’s final text matches the sentence shown in the browser.

| Turn | Owner | Category | Validation | Accepted references |
| --- | --- | --- | --- | --- |
| Step back | `completed_runtime_response` | `live_narration` | `accepted_expression` | one, equal to the published reference |
| Gate Guard question | `completed_runtime_response` | `engine_response` | `engine_or_grounded_fallback` | none |
| Examine | `completed_runtime_response` | `engine_response` | `engine_or_grounded_fallback` | none |
| Examine again | `completed_runtime_response` | `engine_response` | `engine_or_grounded_fallback` | none |

The two examination records share published reference `6ffa6d6c6ae6451cd50a20fbb624a92b40896fc75b18b021f57a1cfa61af4a5b` because the player-facing sentence is the same. They are separate turn records.

The physical record is an accepted live narration, not a fallback labeled as live. The examination records are engine recall, and they do not claim an accepted expression.

After the Gate Guard turn, `session.last_publication` still describes the earlier accepted line, “The notice board does mention a missing patrol, but I don’t have any details beyond that.” The completed publication event for that turn records the mutter that the player actually saw, with no accepted reference. The event log did not apply the stale dialogue owner to the new sentence. The session field was not refreshed. That is a trace inconsistency between the event log and `last_publication`.

No duplicate publication record was written for a turn. Player-facing text did not include a hidden route beyond the fact already disclosed before this cycle.
