# PR-DB Authority Contract

An inherited interlocutor may be used for speaker grounding only when all of the following already hold:

1. Discourse focus has one interlocutor referent for the current scene.
2. The current resolution contract names that same interlocutor.
3. The referent is one NPC id, not a group or an unresolved nominal.
4. That NPC is in the current scene addressable set.
5. Existing availability and addressability checks still pass. This change does not add an availability rule.
6. The player line does not name a different addressee, a declared switch, or a spoken vocative to someone else.
7. The scene has not changed since that interlocutor was committed.
8. The NPC has not been removed from the addressable set, and the line is not a player-performed departure, attack, or self-directed watch.
9. Referent resolution is not ambiguous.
10. Speaker selection still has to accept the id through `resolve_authoritative_social_target` and `build_speaker_selection_contract`. A failed addressability check still yields no allowed speaker.

When any item is uncertain, the previous conservative result remains: no allowed speaker, and reduced context stays off.

The repair does not infer an NPC from narration prose, from keyword lists of people in the transcript, or from a new selector. It stops one false clear so the existing continuity path can see the interlocutor that was already stored.

A question may mention "keep watch" as the topic of that interlocutor. That mention is not, by itself, the player character taking the watch. These still clear the interlocutor:

- "He keeps watching the gate for anything unusual."
- "I keep watch" and "I keep watch?"
- Travel, scene change, and an NPC leaving the addressable set.

Reduced context still requires the existing PR-CW predicate chain, including `exactly_one_allowed_speaker` and `reply_plan_kind = harmless_subjective_response_permitted`.
