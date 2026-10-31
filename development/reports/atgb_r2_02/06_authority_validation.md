# 06 — Authority Validation

Grounding success, conversational success, and authority success are separate.

## Grounding success

S03.3 and S05.3 identify `tavern_runner` with provenance `established_interlocutor`. That does not by itself answer the player.

## Conversational success

The decision category becomes EXECUTE with an empty player-facing string. The existing resolver then returns `genuine_uncertainty` and does not reveal a topic, because the rumor is already in `revealed_topics`. This is not a claim that the reply is a good answer to "tell me more", and it is not a claim that the future-promise question was answered in natural language.

## Authorization checks

- Presence: a runner moved off the scene is not selected. An authorized bridge target that is no longer visible is still `target_not_visible`.
- Identity: explicit names override the old focus. A mismatched provider candidate on a bare "you" does not become the target.
- Disclosure: the resolver blob for both historical lines contains none of the hidden noble-house, Ash Cowl, signal, paid-list, northwest-mud-track, Thoran, or route-change strings. No topic text is attached.
- Pending actions: the repaired decisions do not create an ambiguous-addressee pending record. They also do not clear an existing pending record; that remains the caller's existing behavior.
- State: grounding and `decision_from_interpretation_record` left the session and world-state copies unchanged. The resolver comparison left clocks, turn counter, world flags, and factions unchanged.
- Speech-role ASK and an explicit "I ask Porter Hale..." ASK share `operation_eligibility=executable`, `mutation_eligibility=true`, and `allowed_operation=ask`. The repair does not grant a wider operation than naming the person.
- The same uncertainty plan is returned for "Tell me more about that." and for "I ask the Tavern Runner to tell me more about that." The speech-role path does not disclose more than the explicit path.

## Unresolved authority concerns

`mutation_eligibility` remains true for an executable ASK, as it already was for an explicit address. A later tick can still advance time under the existing social rules. This pass did not execute a tick. Combat, faction, and event owners were not modified and were not separately exercised beyond the unchanged world/faction snapshots above.
