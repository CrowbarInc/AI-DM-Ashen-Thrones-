# PR-DZ Executive Summary

Mode: read-only architectural investigation. Live provider calls made by this investigation: 0. Production code changes: 0.

Decision: B - ORCHESTRATION REWORK REQUIRED. Confidence: high.

The existing system can execute recognized actions because it has capable downstream pieces: visible catalog construction, deterministic/social/exploration resolvers, state mutation, persistence, CTIR/narration-plan prompt construction, final-emission validation, and bounded authority controls. The human playtest fails because ordinary player messages are forced through an action/target/action-component contract before the system decides whether execution is actually needed.

Primary finding: the architecture conflates player intent understanding with executable operation eligibility. The live interpretation path can understand a turn, but production accepts it only if it becomes exactly one connected operation with a visible target (`PERCEIVE`, `INSPECT`, `ASK`, `MOVE`). Questions, partial movement, social color, and multi-step intentions become clarification failures before the rest of the gameplay stack can negotiate them.

Secondary finding: conversational memory exists for narration and some semantic-contract paths, but it is not a general conversational router. The saved session remembers `active_interaction_target_id = gate_serjeant`, and prompt memory can select recent turns and NPC lead discussion, yet the live interpretation bridge still rejects unbound questions and multi-component turns before narration can answer naturally.

Recommended direction: preserve simulation/resolution/persistence/narration-authority components, but introduce a bounded conversational orchestration layer that classifies the turn as answer, clarify, execute, plan/sequence, or decline before resolver eligibility. This is not a full rewrite; it is a meaningful redesign of the player-turn contract.
