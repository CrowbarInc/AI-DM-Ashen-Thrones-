# PR-PLAY-30 world audit
The actual frozen campaign contains a related destination and physical prints. It does not establish that the runner's exact clue id is that physical target.

| Source | Identifier | Meaning / rules |
|---|---|---|
| verified_fixture/world.json | cinderwatch | Frontier city settlement; no local coordinates. |
| verified_fixture/scenes/frontier_gate.json | frontier_gate | Cinderwatch Gate District/eastern gate. Active social scene. |
| verified_fixture/world.json | tavern_runner / patrol_rumor | Same-scene NPC; public topic, discovery_categories=[rumor]; no skill or prerequisite. |
| same topic | muddy_footprints_northwest | Clue id attached to hearsay: “The runner heard the patrol vanished near muddy footprints northwest of the crates.” |
| frontier_gate discoverable_clues | notice_patrol_route | “The missing patrol was last seen taking the northwest mud track past the crates.” Discovered by notice_board investigation. |
| frontier_gate interactables | notice_board | Only authored physical investigation target in current scene; reveals notice_patrol_route. |
| frontier_gate exits | market_quarter / old_milestone | Labels “Enter Cinderwatch” / “Follow the missing patrol rumor”; ordinary scene topology, not coordinates. |
| old_milestone | prints / milestone | Existing physical investigation targets. prints aliases: footprints, mud, track, mud track, northwest track. Both reveal milestone_mud_prints. |
| old_milestone discoverable_clues | milestone_mud_prints | “Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.” |

Crates are mentioned only in topic/notice text; no crate object, coordinate, addressable landmark or local-area record. No footprint object in frontier_gate. Northwest is a relative description plus an authored mud-track destination at old_milestone. No authored foreign-key mapping from muddy_footprints_northwest to prints/milestone_mud_prints. No evidence allows equating them automatically.

Old Milestone visible facts explicitly show overlapping prints fading into scrub. Its sole exit returns to frontier_gate. Market Quarter returns to frontier_gate (see full scene). No added locations or content. world.clues is empty in fixture; clue knowledge is created through disclosure.

Footprint classification: exact rumor id = authored disclosure clue + discovered information/lead + narrative relative-location reference; NOT a local physical object, scene feature, destination, or interaction target. Separate destination prints = authored physical scene target and visible environmental evidence, with a distinct discoverable clue id. Distinguish the two.

Movement between scenes is supported by existing exits. No general coordinate/local-access solver. Same-scene approach normalization accepts tightly constrained matching ASK/INSPECT preambles and explicitly executes no movement; it cannot grant access to remote environmental evidence. A staged travel then inspection is plausible existing gameplay, but was not executed after the decisive stop and does not validate the required one-action investigation.
Evidence: offline_run.json (complete public/internal turns, interpreter prompts, before/after snapshots and diffs), source_excerpts.json (numbered implementation excerpts), verified_fixture/ (strictly verified authored files).
