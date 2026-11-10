# Object and Resource Resolution

Targets are sought only in the current character inventory. A unique surface alias, such as `sleeve` on an identified coat, binds that surface. An object-name match uses that object's single accessible ordinary-writing surface. Several matches return `ambiguous_target`. A row without an existing identity is not migrated and does not become a target. Scene objects are not bound.

A writing medium is an inventory row whose `marking_medium` record is accessible, usable, and lists compatible surface kinds. A row merely named Mud, and muddy scene prose, do not qualify. Compatibility requires the surface kind to be in `compatible_surfaces`. `consumption: required` and `mechanics: required` are recorded as missing prerequisites and do not decrement quantity or call a skill check.

Content is either a quoted literal (`explicit_literal`, reference `player_utterance`) or one disclosed source. Disclosed sources are `session.clue_knowledge` entries that have text, plus discovered scene-runtime clue strings. Generic tokens such as warning, message, name, and wording do not select a source by themselves. Distinctive tokens must all occur in exactly one known source. The copied text is that source's stored text. Zero matches are `content`. More than one match is `ambiguous_content`. Hidden facts and undisclosed scene clues are not read.

Affordance fields are explicit. They are not inferred from item names. Ruleset extension fields are copied through and never consulted.
