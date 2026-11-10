# Conditional and Independent Actions

Conditional, before the character was beside the board:

"If I am beside the notice board, step back from it."

Result: "That condition is not met, so the later action was skipped. Nothing was changed."

The same sentence after a restored beside position: "You step back from the Notice board."

Independent sequence: "I stand up and approach the notice board." Result: already standing, then beside the notice board. The approach did not depend on the skipped step-back.

Policy: a grounded precondition failure continues into later steps only when every later step is independent and is an interact. Dependents of a failed or unsupported step are blocked. Uncertain later steps stop.

The frozen holdout expected a full stop on H068 and H089, where a refused door was followed by standing. The engine continued the independent stand and said the character was already standing. Those two oracle misses are preserved. The door stayed locked and closed.
