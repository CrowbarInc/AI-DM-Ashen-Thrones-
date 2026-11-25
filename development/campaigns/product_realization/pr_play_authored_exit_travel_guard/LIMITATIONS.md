# Limitations

The guard authorizes one existing exit. It does not run two actions.

- "I examine the notice board and then enter Cinderwatch." is clarified. Neither action is performed. A later single sentence can do either one.
- "If the gate is open, I enter Cinderwatch.", "I might enter Cinderwatch later.", and "I plan to travel to Old Milestone tomorrow." do not move. The patterns are the existing commitment and nonaction checks, not a planner for every conditional in English.
- "I go to the tavern." from the gate matches Tavern Runner as someone present. The reply says approaching that person is not a supported action. The character does not move. It does not use the known-unreachable sentence, because the local name is resolved first.
- "I ask the guard about Cinderwatch." stays at the gate. With providers disabled, the reply is the disabled-narration sentence rather than a grounded answer about the city.
- "Tell me about the road to Old Milestone." asks which person is meant.
- "Don't move me to Old Milestone." uses the existing communication-before-execution sentence. It does not move and does not advance clocks.
- "Where am I?" in the supplementary failure-recovery sequence still does not report the active scene.
- The meeting-room crossroads action still requires `patrol_route_known` and is still not an exit. The refusal does not name that flag.
- Known-but-unreachable matching lists scene ids already stored for the campaign. It prefers the most specific id and does not print hidden prose. A phrase that uniquely matches a fixture scene id would be declined as unreachable rather than unknown.
- Forty-probe "I stop and stay here." is now an explicit stay. The sentence still says nothing has been attempted.
- Waiting beside the rain barrel is not executed. The engine only confirms that the character stayed.
- `test_pr_br_continuation26_semantic_closure` still fails two contract rows. See `REGRESSION_RESULTS.md`. Those rows are outside the combined selection.
- No live provider narration was evaluated.
