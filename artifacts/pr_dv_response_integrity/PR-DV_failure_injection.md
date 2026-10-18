PR-DV Failure Injection

Injected and observed:

- Generic final emission: repaired from resolver facts after late post-GM transforms.
- Rejected interpretation: blocked before commit.
- Missing interpretation: existing parser path remains available.
- Explicit OOC: blocked before gameplay mutation.
- Unsupported/rejected bridge reasons: routed to non-mutating interpretation rejection.

Not fully demonstrated in this bounded cycle:
- Persistence failure injection.
- HTTP browser-level integration.
- Resolver exception and final-emission exception transaction boundaries.

No transaction atomicity claim is made beyond the tested pre-commit rejection paths.
