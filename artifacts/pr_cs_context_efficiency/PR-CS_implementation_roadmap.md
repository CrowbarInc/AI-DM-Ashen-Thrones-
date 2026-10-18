# PR-CS Implementation Roadmap

Stage 1: Policy and instruction deduplication.
Scope: remove repeated prose from payload instructions when equivalent canonical system/policy references exist. Success: simple captured prompts drop at least 2k estimated tokens with no behavior change. Stop if any rule loses a single canonical owner.

Stage 2: Resolver-specific projection profiles.
Scope: social-preference, authored-answer, observation, exploration, passive, physical-action, consequential-social, combat prompt profiles. Success: simple NPC dialogue under 6k-10k measured input tokens in dry-run/live validation, complex actions retain all authority gates. Stop on validator or continuity regression.

Stage 3: Compact authority projections.
Scope: send minimal claim text/source ids to provider; retain full semantic identity/persistence/premise metadata for validators/finalizer outside provider prompt. Success: 3k-8k additional savings on initial turns. Stop on immutable-response or consequential-claim regression.

Stage 4: Selective scene/NPC/lead projection.
Scope: active speaker, current target/action, directly relevant lead/topic only. Success: ordinary exploration consistently 5k-10k unless complex. Stop if authored knowledge or world-state continuity weakens.

Stage 5: Optional deterministic delivery for narrow authored answers.
Scope: only after profiles are stable; use deterministic output where generation adds no value. Success: zero provider calls for narrow eligible authored responses. Stop if narrative usefulness or agency suffers.
