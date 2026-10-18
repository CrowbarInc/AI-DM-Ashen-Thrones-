# Implementation Roadmap

Cycle 1: Conversational Turn Decision
Objective: add a non-mutating orchestration decision before resolver execution. Scope: answer/clarify/decline/execute/plan envelope, primary goal, incidental context, missing slots. Deliverables: deterministic contract tests for the 12 acceptance scenarios with provider disabled. Risk: medium-high.

Cycle 2: Contextual Questions and Dialogue Continuity
Objective: support natural follow-up questions with active interlocutor/topic and recent claim binding. Deliverables: "Who are they?", "What does that mean?", "Ask him why" acceptance tests. Risk: medium.

Cycle 3: Movement and Partial Intent
Objective: distinguish incidental departure/social color from consequential travel. Deliverables: movement clarification and successful destination tests. Risk: medium.

Cycle 4: Latency and Prompt Efficiency
Objective: reduce unnecessary calls after behavior is correct. Deliverables: provider-call budget assertions and prompt-size snapshots. Risk: low-medium.
