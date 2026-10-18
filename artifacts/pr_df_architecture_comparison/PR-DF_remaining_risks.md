# PR-DF Remaining Risks

PR-DF decision: A — COMPARISON READY.

The comparison is specified. It has not been executed. Nothing below is a measured win or loss for B or C.

## Specification risks

- The step runner is described, not built. A deep-copy bug could make the rollback tests lie. The design requires a control copy on scenarios 8 and 14 before any live call. That test does not exist yet.
- Read-only adjudication preview may be impossible without touching rolling functions. The specified behavior is then `unsupported`, which makes Candidate C clumsier on skill checks. That is an allowed outcome. Implementing the preview by rolling is not.
- Scenario 12's courier is hypothetical. If `advance_world_tick` ignores it, every candidate fails together. The report must say so. It must not be rewritten into a story that the courier moved.
- M1's unbound movement is the rule for scenario 5 and for the first half of scenario 10. A later fix to binding would change the oracle. The preflight should pin the resolver result it observed and version that pin.
- Gold plans test the executor. They do not test model planning. A pass on scripted B is not evidence that a live planner is safe or cheap.
- Narrative quality has no score until the live arm. A preflight-only reading of this packet cannot prefer an architecture for voice.

## Engine risks the experiment inherits

- Observe-only `_post_gm_adoption_gateway` remains on production `chat`. The harness omits it. A later integration that calls `chat` directly reintroduces the seam and invalidates the comparison.
- Shared pipeline: 41 passed / 24 failed. Required suite: 326 passed / 27 failed. Same sets as PR-DE, not re-run here. Dialogue-lock and strict-social failures can fail S2 and C1 for all candidates equally.
- Authored-knowledge HTTP failures named by PR-DE (notice question, notice board, authored-topic retry) are not the F1 oracle. F1's oracle is the resolver's known-clue set on the fixture copy.
- `chat` increments the turn counter and ticks before classification. The harness copies the tick and must copy the counter rule when a scenario chains S1 to S2, because PR-DE showed the counter changes contract ids and hashes.
- Dice are only comparable under the injected patch. An unpatched live combat run is not a comparison.
- Hidden strings may be present in A's provider input. The experiment records that separately from player-visible leaks. This cycle did not scan the stored PR-DE payloads for a secret-tunnel string.

## Cost risks

- `ceil(chars/4)` is the only token method available. Provider token bills can differ.
- Output tokens are unknown. A short plan with a long narration, or a tool loop with long arguments, can dominate.
- Retry counts are unknown. The cost model refuses to treat them as zero.
- No prices were computed. A future price file would multiply the measured token sums. It should not be back-solved from this packet.

## Process risks

- The worktree was dirty at HEAD `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Game modules and production JSON were already modified. This cycle did not revert them and did not depend on a clean tree.
- Running the future harness from a developer checkout without the save-path assertion would write the dirty session. The assertion is a stop condition.
- Declaring B or C better because the plan schema looks more flexible than `select_ordinary_resolver` would skip the experiment this packet exists to require.

## What would move the decision off A

- Fair comparison needs a new mutator or a resolver change → later decision C.
- Token sums cannot be recorded for every call → later decision D.
- Preflight results contradict this specification (for example, resolvers cannot run except through `chat` with the gateway on) → later decision B or C, with the contradiction attached.
