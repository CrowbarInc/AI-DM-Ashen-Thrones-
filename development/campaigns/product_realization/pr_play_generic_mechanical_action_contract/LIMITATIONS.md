# Limitations

- Verdict is B/PARTIAL. No production action both belongs to a ruleset and has a safe mutation. The commit lifecycle is demonstrated by an unregistered fixture.
- Pathfinder equipment policy remains unresolved. Padded armor is still eligible and still blocked. Equip and unequip were not implemented.
- The session ledger records a contract marker. It is not a character statistic, an equipment slot, or a world fact.
- `rules_light@1` and `scifi@1` are identity-only. They are not playable campaigns.
- Legacy combat, skills, conditions, non-combat resolution, character import, travel, conversation, and marking were not moved onto this boundary.
- One active campaign is stored per data directory. Cross-campaign cases swap that session. They do not prove multi-tenant isolation.
- `save_session` remains one session envelope. This milestone does not add atomicity across character, world, and combat files.
- Replay safety is the receipt on that session. Two processes committing the same new action id are still serialized only by the in-process lock and the atomic file replace.
- The public HTTP route can commit only when the selected authority returns `authorized` and a valid proposal. Production Pathfinder does not. The fixture is not registered.
- Broad gameplay quality was not remeasured.
- Provider calls in the guarded contract, HTTP, performance, and combined-before runs were zero. That does not certify an unguarded live deployment.
