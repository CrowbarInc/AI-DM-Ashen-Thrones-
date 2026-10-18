PR-DV Fallback Authority

Implemented distinction:

- No stored interpretation available: existing safe parser path remains available.
- Explicit OOC correction: returns non-mutating OOC response before gameplay execution.
- Rejected/not interpreted/ambiguous via unresolved references: returns non-mutating rejection before counters, clocks, world ticks, or resolvers.
- Unsupported operation, off-scene/unknown target, incompatible operation/entity: returns non-mutating rejection.

Focused evidence:
- Rejected stored interpretation with an otherwise parser-recognizable lantern inspection no longer executes through parser fallback.
- Resolver invocation count remained zero.
- Turn counter and time pressure remained unchanged.
