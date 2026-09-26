# Anti-Overfit Review

1. The repair is exercised on `ferry_landing` / `bell_loft`, not only `frontier_gate`.
2. `I proceed toward the bell loft.` transitions. A model claim about a cedar mill does not.
3. Kind `None` and a missing resolution still block false arrival and the transition `scene_update`.
4. `I'll head northwest.` stays unresolved travel. PR-BF's terminal still applies.
5. `I follow the missing patrol rumor.` and `I proceed toward the bell loft.` still transition, and arrival narration is kept.
6. `I walk a few steps closer to the crates.` stays local `custom`. `You step closer to the notice board.` is not rewritten.
7. The integrity guard does not key on `northwest`. The parser may store that compass word as a destination. It does not select an exit from it.
8. The integrity guard does not key on `proceed`. Probe I has no proceed verb.
9. The integrity guard does not key on `old_milestone`.
10. The integrity guard does not key on crates, banners, sheds, or lanterns. Probes use a mooring ring, a ferry road, and a signal cloth.
11. There is no transcript-sentence matcher.
12. A future movement phrase that the parser misses still cannot narrate a transition. The guard runs when `resolved_transition` is not success, including when there is no resolution dict.
13. A `scene_update` that asserts arrival, or that attaches clues, hidden facts, and exploration/travel mode to that assertion, is not written. A same-scene string that does not assert a transition can still be written. That is not a transition smuggle.
14. Same-scene visible facts still adopt when no transition occurred.
15. There is no second travel owner. Directional `proceed` enters `parse_freeform_to_action` and the existing exit resolver.

Parser support does mention `proceed`. The integrity invariant does not.
