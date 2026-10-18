PR-DU Integration Plan

Use the existing player-facing chat entry point: game.api.chat, reached by /api/chat in the app.

Connect only stored interpretation output to production by validating it into normalized actions. Reuse existing resolvers and persistence. Do not call the experimental dispatcher.

Allowed state transitions:
- IC gameplay: existing resolver mutations and existing persistence tail only.
- OOC correction: append transcript response only; no resolver, no clock, no turn counter.
- Narration: downstream of resolution; no authoritative mutation.

Duplicate execution prevention:
- Bridge returns a normalized action; production pipeline still invokes the resolver once.
- OOC branch returns before resolver selection.

Failure behavior:
- Missing/malformed/off-scene interpretation returns None and falls back to existing production parser behavior.
- Narration is stubbed in tests; live provider calls remain blocked.
