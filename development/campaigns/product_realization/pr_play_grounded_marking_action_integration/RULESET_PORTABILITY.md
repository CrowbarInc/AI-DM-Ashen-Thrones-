# Ruleset Portability

The common path reads no ruleset skill, difficulty class, spell list, or technology rule. `test_ruleset_extension_is_not_consulted` runs the charcoal-on-paper action with extension ids `pf1e`, `rules_light`, and `science_fiction`. Each extension's id and extra fields remain on the character. Narration does not contain `linguistics` or `difficulty class`.

When a medium or surface sets `mechanics` to `required`, the action is unresolved and no check is called. The adapter is not asked to invent a result.

Extension fields on the inventory rows are not stripped by the marking stage. The existing character save preserves them.
