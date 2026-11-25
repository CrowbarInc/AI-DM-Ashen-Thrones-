# pr_play_generic_mechanical_action_contract

Verdict: **B/PARTIAL**. The generic mechanical-action contract, campaign-selected delegation, proposal validation, and core-owned commit exist. A controlled test-only resolver demonstrates resolution, validation, commit, publication, and exactly-once replay. No legitimate production action yet has both ruleset-owned mechanical authority and a safe mutation, so this is not A/PASS.

`game/mechanical_action_contract.py` names the request, one ledger proposal, and the result envelope. `game/mechanical_action.py` loads `session.ruleset_binding`, discovers the capability, and asks only that ruleset to resolve. Policy evaluation cannot authorize a commit. The core validates owner, target, revision, operation, field, and value, then writes the existing session envelope. Ruleset modules do not call session or character saves. `committed` is the only status that publishes. A matching receipt replays and does not write again.

Pathfinder equipment policy remains unresolved and proposes nothing. The production adapter has no `resolve_mechanical_action`. `rules_light@1` and `scifi@1` do not inherit Pathfinder results. A request-supplied ruleset identity cannot replace the binding. The chat and action turn spine does not call this boundary. Combat, skills, conditions, non-combat resolution, character import, travel, conversation, and marking stay on their current owners.

Acceptance: 80/80 deterministic evidence rows; 79 contract tests passed. HTTP: 37/37 loopback requests, provider calls 0. Contract sequences: 21 turns across four sequences. Combined before and after: 455 passed / 17 failed, then 455 passed / 17 failed. Focused before and after: 470 passed / 1 failed, then 470 passed / 1 failed. No new or missing failure identities. Provider records in the guarded regression, HTTP, and performance runs: 0.

The broad sample was not rerun. Historical results remain 12/40 successful, 22/40 minimum quality, actionability 1.675, supplementary executable 5/55. No gameplay improvement is claimed. No commit, push, or subsequent milestone.

Read MECHANICAL_AUTHORITY_AUDIT.md, LIMITATIONS.md, and NEXT_STEP_DECISION.md before continuing. Recommended next milestone: `pr_play_legacy_campaign_ruleset_resolution`. Last updated: 2026-11-14.
