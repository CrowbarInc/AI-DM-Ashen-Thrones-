# Authority and Isolation

Operational refusals do not commit a gameplay action.

- No world, scene, character, or inventory mutation was observed on the refusal steps. HTTP acceptance recorded `world_unchanged: true`. Browser HP stayed 8/8.
- No faction progression was produced by a refusal.
- The browser turn stayed 5 across the refusal and advanced only on the two examinations.
- The refusal did not add a publication event, so it did not create a phantom gameplay turn.
- Duplicate refusal submissions do not add a second gameplay event.
- Player-facing examination text repeats the disclosed northwest mud-track clue and does not include the seed canary. The canary remains in private seed notes, which are not projected.
- The provider exception body does not include the planted prompt string. Projected `resolution` is `{}`.
- An arbitrary NPC claim in the fallback fixture is not accepted and is not stored as fact.
- Cross-campaign test H20 and `test_cross_campaign_refusal_does_not_touch_the_other_store` leave the other session bytes unchanged.
- HTTP, browser, historical, and development runs used isolated data roots. The audit hook blocks writes under the repository `data/` directory.
- Provider request counts move only when a request is actually sent.
