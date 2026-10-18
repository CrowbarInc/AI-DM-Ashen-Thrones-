# PR-CX First Failing Boundaries

Before PR-CX, all five accepted candidates passed through response parsing, claim extraction, claim classification, authority comparison, hard validation, immutable sealing, and final emission.

Earliest incorrect boundary: claim classification.

The shared defect was missing consequential-family coverage in `game.proposition_authority.classify_propositions` for objective biography, geography, hidden information, consequential NPC action, and unauthorized discovery. Because the proposition classifier returned no consequential rows, `audit_narration_against_decision` had no unauthorized claim to compare against the turn-local decision.

This was not a projection defect: PR-CW full and reduced contexts produced identical validation outcomes before and after PR-CX.

This was not a state-mutation defect: the issue was player-facing assertion without state mutation. Lack of persisted mutation did not make the objective assertion acceptable.

