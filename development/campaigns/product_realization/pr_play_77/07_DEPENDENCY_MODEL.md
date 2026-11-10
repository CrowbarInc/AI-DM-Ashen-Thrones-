# Dependency Model

Kinds distinguished in the planner:

- Explicit: "if the door opens", "if I am beside the notice board".
- Physical: move or open, then inspect what that change reveals.
- Target: the same grounded entity across steps.
- Positional: approach, then read.
- Mechanical: climb, then look from the new vantage.
- Independent: stand, greet, or wave when the later action does not need the earlier result.
- Uncertain: stop rather than guess.

Player order is kept. Adjacent actions are not treated as dependent merely because they share a sentence.

If the first step has no grounded target, later steps are not attempted. That preserves the earlier "open the hatch and sit" behavior when the hatch is not established.
