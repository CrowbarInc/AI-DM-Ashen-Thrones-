# PR-DJ Adapter Design

`validate_hand_authored_interpretation` accepts a mapping and returns `InterpretationAdapterResult`.

The adapter:

- validates a closed top-level schema;
- rejects authoritative fields recursively;
- validates operations against the existing bounded proposal operations;
- validates referenced entity ids against a supplied canonical referent list;
- delegates semantic validation to `validate_interpretation_proposal`;
- returns only non-authoritative experiment metadata.

The adapter does not import or call gameplay resolvers, mutators, dice, storage writers, narration, or OpenAI clients.
