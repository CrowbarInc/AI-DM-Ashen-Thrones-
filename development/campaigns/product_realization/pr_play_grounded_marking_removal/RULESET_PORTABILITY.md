# Ruleset Portability

The same wipe path ran with `ruleset_extension.id` set to `pf1e`, `rules_light`, and `science_fiction`. Each extension's `preserved` and `skill_name` fields were still present after the removal. The published sentence did not contain perception, difficulty class, spell, linguistics, or rarity.

The removal module does not read the ruleset id. A method marked `mechanics: required` returns "That action needs a rules decision before it can be carried out." and does not invent a difficulty class. `ordinary_removal: unable` blocks the action for every ruleset the same way.
