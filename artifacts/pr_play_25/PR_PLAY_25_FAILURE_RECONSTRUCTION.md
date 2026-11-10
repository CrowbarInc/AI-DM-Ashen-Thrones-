# PR-PLAY-25 failure reconstruction

The pre-repair failure is reproduced offline against the exact captured PR-PLAY-24 scene and NPC. `original_reproduction.json` records both original and repaired authority. `dialogue_authority.before.py` is the exact file copied before this pass, not a reconstruction of its logic.

1. Player: “I approach the tavern runner and ask what they're offering.”
2. Selected target: native NPC `tavern_runner`; authoritative name `Tavern Runner`, friendly informant in `frontier_gate`, explicitly addressable in that scene's roster. No NPC promotion or invented identity.
3. Public fact: `scene.visible_facts[2]`: “A tavern runner trades hot stew and rumors near the rain barrel.”
4. Authored NPC topic: `patrol_rumor`, concerning the missing patrol/old milestone. Full exact record is retained in the reproduction fixture. There is no offerings topic.
5. `game/social.py:_next_topic_to_reveal` returned None; candidate sources empty. Social target resolution and execution succeeded. The scene sentence was present at social resolver input.
6. `game/dialogue_authority.py:build_dialogue_authority` received the scene but produced unknown posture, an empty proposition and no selected source. This is the first failed authorization boundary: the topic-only selection had no public-fact fallback. The general request was also excluded from `visible_supporting_sentence`.
7. Expression input: NPC identity and exact player question, operation `uncertainty`, `AUTHORIZED FACTS: (none)`. See `original_expression_request.json`, copied from the existing capture; no new request was sent.
8. Captured expression: “I’m not sure what the tavern runner is offering right now.”
9. Validation: rejected with `unsupported_addition`; `right` and `now` were outside the uncertainty closure vocabulary. No supported answer was discarded. This is secondary to the absent proposition.
10. Host fallback: `Tavern Runner says, "I couldn't tell you."`; accepted response provenance `authorized_host_speech`, expression adoption `HOST_FALLBACK`, hard-valid and interaction-complete.
11. HTTP 200 published that exact fallback. Publication itself did not lose a useful answer.

The original published opening is reproduced verbatim in `original_transcript.md`; it advertises hot stew and paid rumor. That opening is corroboration, not the new authority source. The fix reads only the authoritative visible sentence, never generated opening prose or provider evidence.

Offline reproduction asserts the original no-topic result and exact host fallback using the pre-repair module, then applies the repaired builder to the same unmodified captured state and obtains `I offer hot stew and rumors.` The final integration initializes through the existing opening renderer, replays the compound interpretation through real approach normalization and ASK, adopts a supported mock expression, seals the response and publishes Player HTTP output.

The shared opening test fixture normally substitutes opening seed text for visible facts. The new test restores the captured visible-fact list in isolated temporary storage before opening initialization. It does not change production data, opening generation, or post-turn state to obtain a pass.
