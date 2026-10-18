# Multi-Action and Partial Intent

Current behavior: live interpretation rejects more than one action component. The observed "Angry, I leave..." turn produced `SOCIAL_SIGNAL` and `MOVE`; production returned "Which single action should I resolve first?" with no narration or mutation.

Alternatives:

A. Strict one-operation-per-message: simple and safe, but product-hostile.
B. Ordered operation plans: flexible, but higher authority and rollback complexity.
C. Primary intention plus incidental narrative context: best initial repair.
D. Clarification before execution: required when consequential slot is missing.
E. Hybrid: use C for harmless context, D for missing consequential slots, B only for validated multi-step sequences.

Bounded initial design:

- Compute primary player goal.
- Extract incidental non-mutating context.
- If one consequential operation is missing a slot, ask slot-specific clarification.
- If two independent consequential operations exist, ask which to resolve first.
- If dependent operations are obvious and safe, propose a plan without executing all steps automatically.
