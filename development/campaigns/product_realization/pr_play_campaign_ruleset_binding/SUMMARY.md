# pr_play_campaign_ruleset_binding

Verdict: **A/PASS for the bounded campaign binding milestone**. The existing session document owns the active playthrough id and durable ruleset identity. This does not certify complete ruleset independence of legacy gameplay.

`session.ruleset_binding = {"ruleset_id":"pf1e","ruleset_version":"1","binding_version":1}`.
New Campaign validates an explicit selection, or uses the documented creation-only `pf1e@1` default, and persists it before responding. Registry identity, declared capability, and campaign playability remain distinct. Placeholder and unknown selections are rejected before reset; neither acquires Pathfinder policy.

Legacy migration accepts only explicit persisted session id/version metadata. Missing provenance remains ambiguous; unsupported identities remain unchanged. Existing authoritative bindings are preserved. Migration adds provenance and commits one session envelope atomically. No automatic ambiguity-resolution editor or ruleset conversion exists.

The generic resolver reloads the active campaign and checks its id before registry/capability dispatch. Padded armor remains ELIGIBLE in body_armor, mechanically UNRESOLVED, execution BLOCKED_MECHANICAL_RECONCILIATION. No equipment action was enabled. Request-supplied identity cannot switch this authority.

Acceptance: 60/60 deterministic matrix rows; 48/48 real loopback TCP HTTP requests; four sequences of six requests. Combined before: 455 passed / 17 failed; final: 455 passed / 17 failed. Focused before: 470 passed / 1 failed; final: 470 passed / 1 failed. Exact failure sets unchanged. Lifecycle before: 59 passed / 9 failed; after: 59 passed / 9 failed. New binding/architecture + existing boundary/policy/public-projection selection: 223 passed, zero failures. Final binding + save/load + persistence recheck after fail-closed loader refinement: 94 passed, zero failures.

Provider records: 0; external network attempts: 0 in guarded regression/HTTP runs. Existing legacy combat, skills, conditions, non-combat and character-import pathways are retained explicitly. No broad gameplay improvement claim. No commit, push, or subsequent milestone.

Performance details, exact inherited failure identities, evidence, and limitations are in the adjacent reports and `artifacts/pr_play_campaign_ruleset_binding/`. Archive verification and SHA-256 are recorded externally after packaging in `archive_verification.json`.
