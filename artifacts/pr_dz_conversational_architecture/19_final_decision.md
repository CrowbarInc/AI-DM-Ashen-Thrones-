# Final Decision

Decision: B - ORCHESTRATION REWORK REQUIRED.

Confidence: high.

Reason: the existing resolvers, persistence, prompt-context machinery, and authority validators are worth preserving. The failures are concentrated at the player-turn orchestration boundary: the system understands some ordinary language but accepts it only when it can become exactly one visible-target operation. Natural play needs a stage that can answer, clarify, negotiate, or execute before resolver selection.

Not chosen: targeted repair is insufficient; partial pipeline replacement is more than the evidence requires; no fundamental state/authority blocker was found; evidence is sufficient.
