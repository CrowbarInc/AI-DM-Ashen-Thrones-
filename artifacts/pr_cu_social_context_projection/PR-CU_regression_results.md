# PR-CU Regression Results

No post-implementation regression suite was run because PR-CU did not implement a projection.

Pre-implementation gate results:

| Suite | Result |
|---|---|
| PR-CU prompt-contract tests | Not created; gate blocked before implementation |
| PR-CT prompt-contract tests | 3 passed |
| PR-CP finalization tests | 9 passed |
| PR-CR recovery focus | 54 passed |
| PR-CI authored-answer tests | Not run in Phase 10 because implementation did not occur |
| PR-CC social planning tests | Not run in Phase 10 because implementation did not occur |
| PR-CE subjective classification tests | Not run in Phase 10 because implementation did not occur |
| PR-CK resolver-selection tests | Not run in Phase 10 because implementation did not occur |
| PR-CN contextual extraction tests | Not run in Phase 10 because implementation did not occur |
| PR-BT policy tests | 3 passed, 3 failed in combined PR-BT command; policy-instruction file itself had 1 passed, 2 failed |
| Authored-knowledge realization tests | 14 passed, 2 failed |
| Immutable-response tests | Covered by PR-CR focus subset; 54 passed across retry/immutable/hard-authority files |
| C18/C19 authority tests | C18/C19 hard-authority file included in PR-CR focus; passed |
| Entire shared turn-pipeline suite | 41 passed, 24 failed |

Decision: C - REGRESSION GATE BLOCKED.
