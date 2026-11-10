# Narration evaluation

Scale: 0 unacceptable, 1 poor, 2 marginal, 3 acceptable, 4 strong.

Automated result for both live preludes: `heuristic_pass_pending_review`. That is not a semantic proof. The scores below are manual review of the captured prose. No single average is given.

## Scenario A — notice board

| Criterion | Score | Evidence |
| --- | --- | --- |
| Mechanical fidelity | 4 | The prelude describes looking at the board. It does not contradict the discovery. The engine appends the route sentence once. |
| Discovery fidelity | 4 | The route is not restated inside the prelude and no second discovery is added. Manual review. |
| Information boundary | 4 | No hidden-fact canary, no noble-house agent, no smuggling contact, no spotter list. The serjeant is already a visible fact. |
| Narrative coherence | 4 | Rain, a crowded board, and the gate line match the scene. |
| Player readability | 4 | With the appended anchor, a player can tell what was found. The player response itself remained the deterministic line. |
| Naturalness | 3 | Competent tabletop prose. "Wary glances" and "the occasional bark" are slightly stock. |
| Concision | 4 | About fifty words, then the one authorized sentence. |
| Continuity | 4 | The board, rain, crowd, and serjeant are already visible. "Faded papers" is harmless texture. |

Critical failure: none.

## Scenario B — rain barrel

| Criterion | Score | Evidence |
| --- | --- | --- |
| Mechanical fidelity | 3 | The prelude does not claim a find. The engine anchor says nothing new is established. "Inviting a closer look" sits a little before an examination that has already finished. |
| Discovery fidelity | 4 | The route sentence is absent. No key, passage, culprit, or confession. Manual review. |
| Information boundary | 4 | The automated canary scan of the provider message was empty. The prose does not add the withheld route. |
| Narrative coherence | 3 | Barrel, drizzle, runner, and watchers fit. "As the day wanes" is not established by the scene. |
| Player readability | 3 | The prelude is clear. The assembled quarantine text then repeats every visible fact, which is existing anchor behavior and makes the experimental text long. |
| Naturalness | 3 | Readable GM prose. "Unassuming container" is a little flat. |
| Concision | 3 | The prelude is short. The assembled text is not, because every public observation is appended. |
| Continuity | 2 | "As the day wanes" adds a time of day the scene does not state. Classified by hand as unsupported environmental detail, not a fabricated discovery. The validator did not flag it. |

Critical failure: none. The dusk phrase is not a hidden-information leak and it does not award a clue, item, or route.

## What the scores do not show

A pass on these two samples does not show that the next sample would be safe. The validator accepted the live text and would also accept several fabricated discoveries listed in `06_FABRICATION_VALIDATION.md`.
