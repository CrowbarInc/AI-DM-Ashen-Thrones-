# Observation Integration

The only gameplay entry remains `POST /api/chat` through `game.api._chat_turn`. No second parser, object database, inventory authority, or endpoint was added.

After the existing marking claim, and only when there is no stored interpretation and the turn is not campaign start, the turn calls `game.marking_observation.recognize_observation`. It claims the turn when a proposal exists and the deterministic decision is absent, `unsupported_physical_manipulation`, or `recent_visible_context_answer`. The last of those is included so a fresh look is not answered from the previous sentence after a marking has been removed. An `EXECUTE` decision, including an established scene inspection, is left alone.

If the target phrase names a scene interactable and does not also match one carried object, the turn returns to the existing path. A carried object and a scene object together are reported as ambiguous. A pronoun such as "there" asks which object is meant and does not select the coat.

`_finish_marking_observation` resolves the surface, projects markings, and publishes through the same reconciled narrator used for a committed marking. It does not call `save_character`.
