# PR-EF — GM Conversational Authority & Continuity

ERA: Product Realization
CHAPTER: II
CYCLE: PR-EF
LANES: Gameplay / AI / Architecture
PRIORITY: Critical
TYPE: Architectural Repair
PREDECESSOR: PR-EE

============================================================
0. MISSION
============================================================

Repair the production AI-DM's ability to conduct natural,
continuous player-to-GM communication.

PR-EE demonstrated that the engine repeatedly misroutes
ordinary conversational messages into executable world
operations, unsupported-action handling, and inappropriate
compound-intent confirmation.

These failures persisted despite PR-EA through PR-ED.

The primary architectural deficiency is that the engine
does not reliably distinguish communication with the GM
from actions performed by the player character.

PR-EF must correct this boundary.

PRIMARY OBJECTIVE:

Enable the player to communicate naturally with the GM
without requiring every message to become an executable
simulation operation.

The engine must distinguish:

- GM-directed communication.
- NPC-directed dialogue.
- Player-character actions.
- Requests for observation or description.
- Rules and mechanics questions.
- Clarification and confirmation.
- Corrections and withdrawals.
- Unsupported or impossible operations.

These categories must remain meaningful throughout the
entire production turn pipeline.

Do not implement the formal New Campaign workflow.

That work is reserved for PR-EG.

Do not introduce new gameplay mechanics.

Do not rewrite the simulation engine.

Do not weaken authoritative world-state boundaries.

Do not solve this cycle by adding a large collection of
phrase-specific handlers.

============================================================
1. REQUIRED INITIAL REVIEW
============================================================

Before modifying production code:

1. Read PR-EE's investigation and root-cause register.
2. Review the PR-EA orchestration architecture.
3. Review PR-EB conversational continuity.
4. Review PR-EC compound-intent handling.
5. Review PR-ED provider instrumentation.
6. Trace the current production /api/chat path.
7. Identify existing conversational ownership contracts.
8. Establish a reproducible regression baseline.

Relevant files may include:

- game/api.py
- game/live_chat_interpretation.py
- game/player_interpretation_bridge.py
- game/conversational_orchestration.py
- game/ordinary_semantic_ownership.py
- game/social.py
- game/gm.py
- Existing conversation context and persistence modules.
- Final-emission validation components.

Inspect the current repository.

Do not assume these are the only relevant files.

Record:

- Repository revision.
- Working-tree status.
- Relevant test commands.
- Existing failures.
- Failure signatures.
- Provider/model configuration.
- Existing latency instrumentation.

PR-EC and PR-ED established regression baseline procedures.

Reuse them.

Do not begin production modifications until the baseline
is sufficient to identify newly introduced regressions.

============================================================
2. CONVERSATIONAL AUTHORITY CONTRACT
============================================================

Establish an explicit distinction between:

A. PLAYER-TO-GM COMMUNICATION

The player addresses the game master as the facilitator
of the game.

Examples:

"What can I see?"
"Why did that happen?"
"Can you explain the rule?"
"What did you mean by that?"
"Remind me what the guard said."

These messages may require grounded answers, clarification,
or existing observation authority.

They do not automatically constitute character actions.

B. PLAYER-CHARACTER ACTION

The player describes something their character attempts.

Examples:

"I open the door."
"I approach the guard."
"I inspect the lock."
"I cast a spell."

Consequential operations require existing authoritative
resolution.

C. NPC-DIRECTED COMMUNICATION

The player character speaks to an in-world entity.

Examples:

"I ask the guard about the patrol."
"Tell the merchant I'm interested."
"I warn the sergeant about the danger."

NPC interaction remains subject to existing social
authority and conversational context.

D. SESSION OR INTERFACE COMMUNICATION

The player asks about game controls, rules, saving,
or other application-level concerns.

These requests must not become world operations.

E. CLARIFICATION AND CONTINUATION

The player responds to a previous GM question, proposal,
or explanation.

Examples:

"Yes."
"The second one."
"No, I meant the gate."
"Why not?"
"Actually, never mind."

Interpret these messages in the context of the preceding
interaction.

F. MIXED COMMUNICATION

The player combines a GM question with a character action.

Example:

"Would opening the gate be dangerous? If not, I'll try."

The engine must distinguish the question from the
conditional action.

Do not automatically execute a consequential operation
whose condition has not been resolved.

Do not silently discard independently consequential intent.

============================================================
3. OWNERSHIP BEFORE EXECUTION
============================================================

Modify the orchestration contract so that communication
ownership is established before the engine commits to
executable operation routing.

Conceptual flow:

Player message
    |
    v
Communication ownership
    |
    +-- GM-directed communication
    |
    +-- NPC-directed communication
    |
    +-- Character action
    |
    +-- Session/interface request
    |
    +-- Clarification/continuation
    |
    +-- Mixed or ambiguous intention
    |
    v
Appropriate handling
    |
    +-- Grounded answer
    +-- Existing observation authority
    +-- Existing social authority
    +-- Existing action resolver
    +-- Focused clarification
    +-- Explicit limitation
    |
    v
Validated player-facing response

This is a conceptual contract.

Do not create an unnecessarily elaborate new routing
framework if the existing orchestration layer can be
extended coherently.

Prefer modifying the existing PR-EA contract.

Do not introduce a parallel interpretation pipeline.

Do not require an additional provider call for every turn.

============================================================
4. GM-DIRECTED COMMUNICATION
============================================================

Implement production support for ordinary player-to-GM
communication.

The player must be able to ask the GM:

- What is happening.
- What their character perceives.
- What was previously established.
- Why a previous response occurred.
- Whether a rule applies.
- What a previous statement meant.
- Whether an attempted action is possible.
- What information is currently available.

The engine must distinguish between:

INFORMATION ALREADY AVAILABLE

Answer using established, player-accessible context.

NEW OBSERVATION REQUIRED

Route through existing observation or exploration
authority where necessary.

UNKNOWN INFORMATION

Acknowledge uncertainty or explain that the information
is not established.

CONSEQUENTIAL ACTION

Route through existing authoritative resolution.

Do not answer an observation request by inventing
undiscovered information.

Do not require a valid NPC target for GM-directed
questions.

Do not treat the GM as an in-world NPC.

Do not create a synthetic GM entity in world state.

============================================================
5. CONVERSATIONAL CONTINUITY
============================================================

Extend the existing PR-EB context contract to preserve
player-to-GM conversational continuity.

The engine should retain enough information to understand:

- The GM's previous response.
- The subject of that response.
- Whether the GM asked a question.
- Whether the GM offered a proposal.
- Whether an action was refused.
- Why the refusal occurred.
- Whether the player is clarifying or correcting something.

Example:

PLAYER:
"I try to open the sealed gate."

GM:
"The gate is barred from the other side."

PLAYER:
"Why can't I open it?"

Expected:

The engine explains the established obstruction.

It must not respond:

"Who are you asking?"

The player is addressing the GM about the previous
interaction.

The engine must not reinterpret this as NPC dialogue.

### Context representation

Prefer a compact extension of existing context.

Potential fields:

- Last GM response category.
- Last conversational subject.
- Last refusal reason.
- Pending GM question.
- Pending proposal.
- Active NPC interlocutor.
- Relevant prior operation.

Do not duplicate the full conversation transcript.

Do not create an unrestricted conversational memory graph.

Do not persist speculative interpretations as world facts.

### Context invalidation

Define when conversational context should be:

- Updated.
- Superseded.
- Cleared.
- Preserved across unrelated actions.
- Restored after save/load.

Do not allow stale context to override explicit new
player intentions.

============================================================
6. CONFIRMATION AND PROPOSAL INTEGRITY
============================================================

PR-EE identified a critical failure:

The engine proposed executing an operation that it had
already classified as unsupported.

The player confirmed.

The engine then rejected the same operation.

Repair this behavior.

### Required invariant

The engine must not ask the player to confirm an operation
that it already knows cannot be executed.

Before offering a consequential operation for confirmation:

1. Identify the proposed operation.
2. Determine whether it is supported.
3. Determine whether required information is available.
4. Determine whether the operation is eligible for
   authoritative resolution.
5. Only then offer confirmation if confirmation is needed.

Eligibility does not imply success.

An eligible operation may still fail during authoritative
resolution.

### Confirmation continuity

When the player responds:

"Yes."

The engine must understand what is being confirmed.

When the player responds:

"No."

The engine must cancel or revise the pending proposal.

When the player responds:

"Actually, I meant the other door."

The engine must recognize a correction.

Do not treat these as unrelated character actions.

### Unsupported operations

If an operation is unsupported:

- Do not propose it as executable.
- Do not ask for confirmation.
- Explain the limitation appropriately.
- Preserve enough context to answer follow-up questions.

Do not repeatedly restate generic engine restrictions
when a more specific explanation is available.

============================================================
7. COMPOUND-INTENT REPAIR
============================================================

PR-EE identified the following problematic condition
in conversational orchestration:

len(connected) > 1 or unsupported

Investigate the current implementation and repair the
confirmed conflation between:

- Multiple recognized intentions.
- A single unsupported intention.

Unsupported operations must not automatically trigger
compound-intent confirmation.

GM-directed communication must not be decomposed into
world operations merely because its meaning is not
represented by an executable resolver.

### Requirements

- Preserve valid compound-intent behavior from PR-EC.
- Preserve incidental versus consequential distinctions.
- Preserve operation ordering and dependencies.
- Preserve pending-intent continuation.
- Prevent false compound-action proposals.
- Prevent silent loss of consequential intentions.

Do not remove compound-intent support merely to eliminate
the observed failure.

Do not add phrase-specific exceptions for the six
original screenshot messages.

Correct the underlying decision condition and contract.

============================================================
8. INTERPRETATION AND PROVIDER CONTRACT
============================================================

Inspect the live interpretation schema.

Determine whether it can represent:

- GM-directed question.
- GM-directed clarification.
- GM-directed correction.
- NPC dialogue.
- Character action.
- Session/interface request.
- Observation request.
- Mixed intention.
- Unsupported operation.

Extend the schema only where necessary.

The interpreter must be allowed to recognize meaningful
communication that does not correspond to an executable
world operation.

### Critical distinction

Interpretation may identify what the player means.

It must not independently authorize:

- World-state changes.
- NPC compliance.
- Item acquisition.
- Successful movement.
- Hidden-information disclosure.
- New consequential world facts.

Existing resolvers retain those responsibilities.

### Provider efficiency

Reuse the existing interpretation call where possible.

Do not introduce a mandatory second interpretation call.

Do not require an LLM call for obvious confirmation
continuations when structured pending context suffices.

Preserve PR-ED instrumentation and provider budgets.

============================================================
9. PLAYER-FACING RESPONSE QUALITY
============================================================

The engine must respond as a game master rather than
exposing internal command-processing terminology.

Avoid generic responses such as:

"I can resolve one supported action at a time."

"What are you trying to accomplish?"

"That is not a supported operation."

These may be appropriate in limited circumstances,
but should not be universal fallbacks.

Prefer responses that address the player's actual
question or intention.

Examples:

PLAYER:
"Why can't I open the gate?"

BAD:
"Who are you asking?"

BETTER:
"The gate is barred from the other side."

PLAYER:
"Can you remind me what the guard said?"

BAD:
"Please specify a valid target."

BETTER:
"The guard said the northern patrol hasn't returned."

Only provide the better response when the relevant fact
is actually established.

Do not fabricate details to improve conversational flow.

### Response ownership

Identify which component owns:

- Grounded GM answers.
- NPC dialogue.
- Action narration.
- Clarification.
- Refusal explanation.
- Session/interface responses.

Do not route all response categories through a generic
unsupported-action fallback.

Preserve existing final-emission authority checks.

============================================================
10. PRODUCTION API ACCEPTANCE
============================================================

PR-EF must demonstrate a continuous, coherent interaction
through the actual production /api/chat path.

Do not rely solely on isolated unit tests.

Use an initialized test campaign.

The formal campaign-start workflow is outside this cycle.

### Required continuous scenario

Establish an authored scene containing:

- A gate.
- A guard or sergeant.
- An environmental detail.
- A known obstacle or restriction.
- A reachable destination.

Then execute a continuous interaction covering:

TURN 1:
Player asks the GM about the surroundings.

TURN 2:
Player asks a follow-up about something described.

TURN 3:
Player asks whether an NPC appears concerned.

TURN 4:
Player initiates dialogue with that NPC.

TURN 5:
Player asks an NPC follow-up without repeating the
NPC's identity.

TURN 6:
Player asks the GM to clarify something the NPC said.

TURN 7:
Player attempts a consequential action.

TURN 8:
Player asks why the action succeeded or failed.

TURN 9:
Player corrects or withdraws a previous intention.

TURN 10:
Player attempts an ordinary movement action.

### Acceptance requirements

The entire sequence must:

- Use the production API.
- Preserve the same campaign/session.
- Preserve relevant conversation context.
- Distinguish GM and NPC communication.
- Preserve resolver authority.
- Avoid unsupported-action loops.
- Avoid unnecessary clarifications.
- Avoid invented consequential facts.
- Produce coherent player-facing responses.

Do not reset the conversation between turns.

Do not manually rewrite player messages to make them
easier for the engine.

A series of individually passing tests does not satisfy
this requirement.

============================================================
11. SEMANTIC GENERALIZATION
============================================================

Create a small holdout set of unfamiliar expressions.

The holdout set must include:

- GM-directed questions.
- NPC-directed questions.
- Character actions.
- Rules questions.
- Corrections.
- Confirmations.
- Withdrawals.
- Ambiguous statements.
- Mixed intentions.
- Negative examples.

### Example distinctions

"Why did you say that?"
GM-directed follow-up.

"I ask the guard why he said that."
NPC-directed communication.

"Can I open the gate?"
Capability question.

"I open the gate."
Attempted action.

"I might open the gate."
Tentative intention.

"Actually, don't open it."
Withdrawal.

"Tell me what the gate looks like."
GM-directed description request.

"I tell the guard what the gate looks like."
Character communication.

These examples are illustrative.

Do not construct the implementation around exact strings.

### Holdout discipline

Where feasible:

- Define holdout expressions before implementation.
- Keep them separate from development examples.
- Do not add exact-match handlers for failures.
- Report holdout results independently.

Provider-disabled tests cannot establish general
natural-language competence.

Where possible, include bounded live-provider validation.

If live-provider access is unavailable, report that
limitation explicitly.

============================================================
12. AUTHORITY AND STATE INTEGRITY
============================================================

Verify that GM-directed communication does not cause
unintended world-state mutations.

Examples:

- Asking why a door is locked must not unlock it.
- Asking about an NPC must not change the relationship.
- Asking whether travel is possible must not move
  the character.
- Asking for clarification must not advance time.
- Correcting an unexecuted action must not execute it.
- Withdrawing a pending proposal must not execute it.

Consequential actions remain resolver-owned.

### Persistence

Verify that relevant conversational context survives
save/load where appropriate.

Do not persist unsupported interpretations as canonical
world facts.

Do not duplicate authoritative execution after reload.

Preserve existing campaign/session persistence contracts.

============================================================
13. PERFORMANCE GUARDRAILS
============================================================

Preserve PR-ED's performance improvements.

In particular:

- Do not reintroduce redundant narration calls for
  completed movement.
- Do not add mandatory provider calls to every turn.
- Do not reintroduce ineffective retries.
- Preserve provider timeouts.
- Preserve token-budget controls.
- Preserve performance instrumentation.

Record:

- Provider calls.
- Input tokens.
- Output tokens.
- Retry counts.
- End-to-end latency.

Compare representative turns before and after PR-EF.

Do not claim performance improvements without measurements.

Do not sacrifice conversational correctness merely to
reduce token consumption.

============================================================
14. REGRESSION ACCOUNTABILITY
============================================================

Use the PR-EC/PR-ED regression baseline methodology.

Before implementation:

- Record exact test commands.
- Record passing tests.
- Record failing tests.
- Preserve failure signatures.

After implementation:

- Rerun the same suites.
- Compare individual test results.
- Identify inherited failures.
- Identify resolved failures.
- Identify new regressions.
- Identify changed failures.

Pay particular attention to:

- NPC dialogue.
- Social resolution.
- Final-emission validation.
- Exploration.
- Movement.
- Clarification continuation.
- Compound intentions.
- Save/load.
- Provider retries.
- Campaign lifecycle.

Do not repair unrelated inherited failures unless
they directly block PR-EF acceptance.

New authority or persistence regressions are unacceptable.

============================================================
15. SCOPE BOUNDARIES
============================================================

IN SCOPE:

- GM-directed communication ownership.
- NPC versus GM distinction.
- Conversational continuity.
- Clarification and correction.
- Confirmation integrity.
- Unsupported-action routing.
- Compound-intent classification repair.
- Interpretation schema adjustments.
- Player-facing response quality.
- Production multi-turn acceptance.
- Semantic generalization.
- Authority and persistence validation.
- Regression accountability.

OUT OF SCOPE:

- Formal New Campaign workflow.
- Campaign creation UI.
- New opening-scene generation.
- New combat mechanics.
- New social mechanics.
- New movement mechanics.
- Autonomous planning.
- Unrestricted world improvisation.
- New NPC personality systems.
- General world-generation redesign.
- Broad UI redesign.
- Comprehensive prompt optimization.
- Unrelated regression cleanup.

Do not expand scope without a demonstrated dependency.

============================================================
16. IMPLEMENTATION STAGES
============================================================

STAGE A — BASELINE

- Review PR-EE.
- Inspect production routing.
- Record regression baseline.
- Record representative performance.

STAGE B — CONTRACT REPAIR

- Establish communication ownership.
- Extend orchestration decisions.
- Separate communication from execution.
- Repair unsupported-action classification.

STAGE C — CONTINUITY

- Preserve GM-directed context.
- Repair confirmation and correction.
- Preserve NPC conversational ownership.
- Define context invalidation.

STAGE D — PRODUCTION INTEGRATION

- Integrate with /api/chat.
- Preserve resolver authority.
- Preserve narration validation.
- Preserve persistence.
- Preserve provider efficiency.

STAGE E — BEHAVIORAL VALIDATION

- Execute continuous ten-turn scenario.
- Execute semantic holdouts.
- Inspect actual player-facing responses.
- Verify state invariants.

STAGE F — REGRESSION COMPARISON

- Rerun baseline suites.
- Classify failures.
- Repair critical new regressions.

STAGE G — CLOSEOUT

- Generate review artifacts.
- Report remaining limitations.
- Recommend acceptance or repair.

Do not begin PR-EG automatically.

============================================================
17. REQUIRED REVIEW ARTIFACTS
============================================================

Generate:

01 — Executive Summary
- What changed.
- What improved.
- What remains incomplete.
- Final recommendation.

02 — Architecture Comparison
- Before and after routing.
- Communication ownership.
- Resolver boundaries.
- Response ownership.

03 — Conversational Authority Contract
- Communication categories.
- Decision representation.
- Context ownership.
- Invariants.

04 — Production Integration Evidence
- /api/chat routing.
- GM-directed communication.
- NPC-directed communication.
- Action resolver handoff.
- Final-emission behavior.

05 — Continuous Ten-Turn Transcript
- Player messages.
- GM responses.
- Interpretation decisions.
- State effects.
- Provider usage.
- Pass/fail classification.

06 — Semantic Generalization Results
- Development examples.
- Holdout examples.
- Positive and negative distinctions.
- Misclassifications.

07 — Confirmation and Compound-Intent Audit
- Unsupported-operation handling.
- Proposal eligibility.
- Pending-intent continuation.
- Corrections and withdrawals.

08 — Authority and Persistence Audit
- Permitted state changes.
- Prevented mutations.
- Save/load behavior.
- Duplicate-execution prevention.

09 — Performance Comparison
- Provider calls.
- Tokens.
- Retries.
- Latency.
- Measurement limitations.

10 — Regression Comparison
- Baseline results.
- Postimplementation results.
- Inherited failures.
- Resolved failures.
- New regressions.

11 — Remaining Issues
- PR-EF defects.
- PR-EG dependencies.
- Conversational limitations.
- Unrelated technical debt.

12 — Final Recommendation

Choose:

A — PR-EF ACCEPTED

The engine demonstrates coherent GM-directed conversation
through the production API, with preserved authority.

B — PR-EF ACCEPTED WITH LIMITATIONS

Core conversational behavior works, but bounded
deficiencies remain.

C — PR-EF REQUIRES REPAIR

The engine still cannot sustain the required conversation,
or critical regressions remain.

D — ARCHITECTURAL RECONSIDERATION REQUIRED

The existing orchestration architecture cannot support
the required conversational behavior without fundamental
replacement.

13 — Changed-File Inventory
- Files modified.
- Purpose of changes.
- Validation commands.
- Relevant source references.

Package the results using the established CURRENT_REVIEW
workflow.

============================================================
18. SUCCESS CRITERIA
============================================================

PR-EF succeeds when:

1. GM-directed communication is explicitly represented.
2. GM-directed questions do not require NPC targets.
3. NPC dialogue remains correctly routed.
4. Character actions remain resolver-owned.
5. Clarifications retain conversational context.
6. Confirmations cannot approve known unsupported actions.
7. Corrections and withdrawals behave appropriately.
8. Unsupported operations do not trigger false compound
   confirmation.
9. Player-facing responses address the actual question.
10. The continuous ten-turn production scenario succeeds.
11. Semantic holdouts demonstrate meaningful generalization.
12. GM communication does not mutate world state.
13. Save/load preserves relevant conversational context.
14. Existing provider efficiency improvements remain intact.
15. No unacceptable new authority or persistence regressions
    remain.

Do not declare acceptance solely because unit tests pass.

Do not declare acceptance solely because the six original
screenshot messages produce different responses.

The relevant measure is whether the engine can sustain
ordinary interaction between a player and a game master.

============================================================
19. FINAL INSTRUCTION
============================================================

Implement PR-EF in the current repository.

Prioritize conversational competence over expanding
gameplay functionality.

Preserve existing simulation authority.

Preserve PR-ED performance improvements.

Avoid phrase-specific workarounds.

Avoid parallel interpretation systems.

Validate through the actual production API.

Demonstrate a continuous, coherent ten-turn interaction.

Document any remaining limitations honestly.

Generate the CURRENT_REVIEW package.

Report the final recommendation and package location.

STOP after PR-EF.

Await external review before beginning PR-EG.