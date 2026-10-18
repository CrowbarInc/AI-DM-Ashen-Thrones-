# PR-CN Extraction Contract

A contextual visible-figure lead must identify an actual figure or entity described in narration.

Valid extraction:
- Extracts the visible figure or entity, such as `guard`, `merchant`, `traveler`, `cloaked figure`, or `rider`.
- May preserve a concrete location phrase when the narration supplies one, such as `near the bridge` or `near the checkpoint`.
- Remains non-authoritative continuity metadata.

Invalid extraction:
- Must not treat introductory observer framing as a figure subject.
- Must not store subjects such as `as you`, `while you`, `when you`, `looking around`, `watching the scene`, or `from where you stand`.
- Must not invent a lead from no-figure narration, negated observations, absent figures, or background rumor framing.

Authority boundary:
- Contextual leads are not world truth.
- They do not create NPCs.
- They do not mutate NPC locations.
- They do not reveal clues or hidden facts.
- They do not modify `gm_resolution_decision`.
