PR-DU Authority Validation

Findings:
- Stored interpretation is treated as input classification only, never as a state patch.
- Target validation is against the current visible scene/world catalog.
- Existing resolvers remain the authority for execution.
- OOC correction returns before authoritative mutation.
- Narration stubs and final emission do not commit inventory, HP, time, or scene state.

No unauthorized state mutations were observed in focused tests.
