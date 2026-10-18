# PR-EF-R1 — Semantic Ownership & Production Handoff Repair

ERA: Product Realization
CHAPTER: II
CYCLE: PR-EF-R1
LANES: Gameplay / AI / Architecture
PRIORITY: Critical
TYPE: Bounded Repair & Live Requalification
PREDECESSOR: PR-EF

============================================================
0. MISSION
============================================================

Repair the remaining conversational correctness failures
identified during PR-EF.

PR-EF introduced explicit conversational ownership,
GM-directed continuity, confirmation integrity, and
improved compound-intent handling.

However, PR-EF did not satisfy its acceptance criteria.

The final assessment was:

C — PR-EF REQUIRES REPAIR.

The primary unresolved problems are:

1. Fresh live-provider interpretation misclassifies
   important communication categories.

2. Correctly recognized operations can fail during
   production resolver handoff.

3. The final implementation has not demonstrated a
   successful continuous conversation using fresh
   provider outputs.

4. Some grounded GM responses technically preserve
   authority but fail to answer the player's actual
   question.

PR-EF-R1 must repair these problems without introducing
another architectural layer.

PRIMARY OBJECTIVE:

Demonstrate that the existing conversational architecture
can correctly interpret, route, and respond to ordinary
player communication through the production API.

This is a repair cycle, not a feature-development cycle.

Do not begin PR-EG.

Do not implement the formal New Campaign workflow.

Do not undertake a broad narration redesign.

Do not introduce a parallel interpreter.

Do not solve the failures through exact-phrase matching.

============================================================
1. REQUIRED BASELINE
============================================================

Before modifying production code:

1. Read all PR-EF review artifacts.
2. Read the PR-EE root-cause investigation.
3. Inspect the current production interpretation schema.
4. Inspect conversational ownership decisions.
5. Inspect operation handoff to authoritative resolvers.
6. Inspect GM-directed answer generation.
7. Inspect the existing regression baseline.
8. Inspect PR-ED provider instrumentation.

Record:

- Repository revision.
- Working-tree status.
- Relevant configuration.
- Provider/model selection.
- Test commands.
- Existing passing tests.
- Existing failing tests.
- Failure signatures.
- Existing performance measurements.

Preserve the PR-EF regression baseline:

256 passing / 30 failing before PR-EF.
271 passing / 30 failing after PR-EF.

These counts are historical reference points.

Re-establish the actual current baseline rather than
assuming the repository remains unchanged.

Do not begin implementation until the baseline is recorded.

============================================================
2. REPRODUCE THE REMAINING FAILURES
============================================================

Reproduce the specific failures identified by PR-EF.

### A. Semantic ownership

The live interpreter classified only 5 of 12 frozen
holdout expressions with their expected strict labels.

Investigate the misclassifications.

Examples:

"What does her worried expression tell me?"

Expected:
GM-directed observation or interpretation request.

Observed:
NPC-directed communication.

"Would a check be needed for that?"

Expected:
Rules/session question.

Observed:
GM-directed communication.

"Actually, use the lantern instead."

Expected:
Correction.

Observed:
Character action.

"All right, proceed."

Expected:
Confirmation.

Observed:
Character action.

"Forget that plan."

Expected:
Withdrawal.

Observed:
Character action.

"That one over there."

Expected:
Ambiguous reference.

Observed:
GM-directed communication.

"Is it safe to go outside? If so, I head out."

Expected:
Mixed conditional intention.

Observed:
GM-directed communication.

These examples are diagnostic evidence.

Do not assume every strict-label mismatch is an
end-to-end gameplay failure.

For each mismatch, determine:

- Raw provider interpretation.
- Normalized interpretation.
- Ownership decision.
- Context-based correction, if any.
- Selected response or resolver.
- Actual player-facing behavior.
- World-state effects.
- Whether the outcome is genuinely incorrect.

Separate:

A. Incorrect labels with correct downstream behavior.

B. Incorrect labels causing inappropriate responses.

C. Incorrect labels causing unintended operations.

D. Correct labels with incorrect downstream behavior.

Do not optimize classification scores at the expense
of actual gameplay behavior.

### B. NPC conversational continuation

Reproduce the original live failure:

NPC:
Refers to a particular road.

PLAYER:
"Which road do you mean?"

Observed failure:

"No one here can answer that from what is settled here."

PR-EF reportedly repaired this behavior after the live
test budget was exhausted.

Verify the repair using fresh provider outputs.

### C. Movement handoff

Reproduce:

"I make for the courtyard gate."

PR-EF recognized this as movement, but production
holdout replay did not complete the expected operation.

Trace the operation through the entire production path.

Determine whether the failure originates in:

- Target identification.
- Destination grounding.
- Interpretation normalization.
- Ownership classification.
- Resolver selection.
- Resolver preconditions.
- State transition.
- Narration or final emission.
- Another identified component.

Do not assume that correct interpretation guarantees
valid movement.

Do not invent a destination to force success.

============================================================
3. SEMANTIC OWNERSHIP CONTRACT REPAIR
============================================================

Review the existing communication categories and
interpretation contract.

The engine must distinguish:

- Player addressing the GM.
- Player character addressing an NPC.
- Player describing a character action.
- Player requesting observation.
- Player asking about rules or mechanics.
- Player confirming a pending proposal.
- Player correcting a previous intention.
- Player withdrawing an intention.
- Player expressing a conditional intention.
- Player making an ambiguous reference.

### Key requirement

These distinctions must not depend primarily on
recognizing specific words or phrases.

Use the existing semantic interpretation architecture.

Inspect whether:

1. The schema represents the categories clearly.
2. The provider instructions distinguish them clearly.
3. Normalization destroys relevant information.
4. Downstream routing overrides correct interpretations.
5. Pending conversational context is applied too late.
6. The same message receives conflicting classifications
   from different components.

Repair the narrowest confirmed causes.

Do not add another independent ownership classifier.

Do not add a second mandatory provider call.

Do not create a growing list of special-case expressions.

============================================================
4. CONTEXT-SENSITIVE CONTINUATIONS
============================================================

Confirmations, corrections, and withdrawals are often
meaningless without conversational context.

Examples:

"Yes."
"Go ahead."
"Actually, the other one."
"Forget it."
"No, I meant the guard."

The engine must interpret these against the appropriate
pending proposal or recent interaction.

### Required behavior

CONFIRMATION:

Execute or continue only a valid, pending proposal.

CORRECTION:

Revise the appropriate unexecuted intention.

WITHDRAWAL:

Cancel the relevant pending intention without executing it.

AMBIGUOUS REFERENCE:

Request focused clarification when the referent cannot
be determined reliably.

NO RELEVANT CONTEXT:

Do not invent a pending proposal or referent.

### Important

Do not require the live interpreter to independently
reconstruct structured context already available to
the engine.

Use existing PR-EF continuity mechanisms.

However, do not let stale context override explicit
new player intentions.

Verify context behavior across save/load.

============================================================
5. GM VERSUS NPC OWNERSHIP
============================================================

Repair the distinction between:

"What does her worried expression tell me?"

and:

"I ask her why she looks worried."

The first is a request to the GM.

The second is character-to-NPC communication.

Likewise distinguish:

"What did the sergeant mean?"

from:

"I ask the sergeant what she meant."

These are different interactions.

### Requirements

GM-directed questions:

- Must not require an NPC dialogue target.
- Must not automatically initiate social interaction.
- Must not advance time unless an authorized operation
  genuinely requires it.
- Must not alter NPC relationships.
- Must not reveal inaccessible information.

NPC-directed communication:

- Must preserve the intended interlocutor.
- Must support natural follow-up questions.
- Must use existing social authority.
- Must not be silently converted into GM exposition.

### Mixed cases

If the player asks:

"Does she seem worried? I'll ask her what's wrong."

Preserve both intentions.

Resolve or answer the observation appropriately.

Then handle the NPC-directed action according to
existing compound-intent and dependency rules.

Do not silently drop consequential actions.

Do not execute conditional actions before their
conditions are established.

============================================================
6. PRODUCTION HANDOFF INTEGRITY
============================================================

Investigate why a correctly identified action can fail
between interpretation and authoritative resolution.

Trace:

Raw player message
    |
    v
Live interpretation
    |
    v
Normalization
    |
    v
Conversational ownership
    |
    v
Operation construction
    |
    v
Resolver selection
    |
    v
Resolver preconditions
    |
    v
Authoritative resolution
    |
    v
Player-facing response

For every tested consequential operation, record:

- Intended operation.
- Interpreted operation.
- Normalized operation.
- Selected resolver.
- Resolver inputs.
- Resolver result.
- State changes.
- Final response.

### Required invariant

The engine must not silently replace a correctly
recognized operation with an unrelated fallback.

If an operation cannot be resolved:

- Preserve the intended action.
- Explain the actual limitation.
- Request missing information when appropriate.
- Avoid false success narration.

### Movement

Use existing location and movement authority.

Do not bypass travel restrictions.

Do not fabricate reachable destinations.

Do not force scene transitions merely to satisfy tests.

The movement acceptance case must use an actually
reachable, established destination.

============================================================
7. GROUNDED ANSWER RELEVANCE
============================================================

PR-EF demonstrated that some GM-directed answers
preserved established facts but did not adequately
answer the player's question.

Example:

PLAYER:
"Why did I find that mark?"

WEAK RESPONSE:
Repeats that a mark was found.

The response may be grounded but not responsive.

Investigate whether the problem originates in:

- Retrieval selection.
- Missing conversational subject.
- Question-type interpretation.
- Prompt instructions.
- Response assembly.
- Overly restrictive fallback logic.

### Requirements

The GM should:

- Answer the actual question when established information
  supports an answer.
- Distinguish what happened from why it happened.
- Distinguish observation from inference.
- Acknowledge genuinely unknown explanations.
- Avoid repeating large passages unnecessarily.
- Avoid inventing consequential facts.

### Important boundary

Do not undertake a broad dialogue-style redesign.

Do not add new lore to make answers sound better.

Do not create deterministic templates for every question.

Repair answer relevance only where directly connected
to the existing conversational correctness defects.

Full dialogue quality and bounded improvisation are
reserved for PR-EG.

============================================================
8. FROZEN SEMANTIC HOLDOUTS
============================================================

Reuse the PR-EF holdout set.

Do not rewrite failed expressions to improve results.

Do not remove difficult cases.

Before implementation, create an additional independent
holdout set covering:

- GM questions.
- NPC dialogue.
- Character actions.
- Rules questions.
- Confirmations.
- Corrections.
- Withdrawals.
- Ambiguous references.
- Conditional intentions.
- Mixed intentions.

Keep development examples separate from holdouts.

### Evaluation

Report two different metrics.

METRIC A:
Strict interpretation-label agreement.

METRIC B:
End-to-end behavioral correctness.

These must not be conflated.

For every disagreement, report whether the actual
player-facing behavior remained correct.

A label mismatch is not automatically a failure.

A correct label is not automatically a success.

### Critical failures

Regardless of aggregate accuracy, classify the following
as critical:

- Unrequested consequential world mutation.
- NPC dialogue initiated by a GM-directed question.
- Character action executed after withdrawal.
- Unsupported operation presented as executable.
- Incorrect movement or destination.
- Hidden information revealed without authority.

Do not hide critical failures behind aggregate pass rates.

============================================================
9. FRESH LIVE-PROVIDER REQUALIFICATION
============================================================

This is the principal acceptance requirement.

Execute a continuous conversation using fresh provider
outputs through the actual production /api/chat path.

Do not use recorded interpretation fixtures as the sole
acceptance evidence.

Do not reset the campaign between turns.

Do not manually correct player messages.

Do not substitute direct function calls for production
routing.

### Required scenario

Use an initialized campaign containing:

- A known location.
- An NPC.
- A visible environmental detail.
- A known obstacle.
- An established reachable destination.

The scenario must include at least ten turns.

Required interactions:

1. GM-directed description request.
2. Follow-up observation question.
3. Question about NPC behavior.
4. NPC-directed dialogue.
5. NPC dialogue continuation.
6. GM-directed clarification about NPC dialogue.
7. Consequential inspection or interaction.
8. GM-directed question about the result.
9. Correction or withdrawal.
10. Movement to an established destination.

Additional turns may be used where necessary.

### Evaluation

For each turn record:

- Raw player input.
- Raw provider interpretation.
- Normalized interpretation.
- Selected ownership.
- Selected resolver or answer path.
- Player-facing response.
- State changes.
- Provider calls.
- Token usage.
- Latency.
- Pass/fail result.

### Required result

The complete conversation must remain coherent.

The engine must preserve GM/NPC distinctions.

Consequential actions must use authoritative resolvers.

No unrequested consequential mutation may occur.

No unsupported-action confirmation loops may occur.

Movement must resolve correctly or fail for a legitimate,
explicitly documented world-state reason.

### Repetition

Run at least two fresh conversations with meaningfully
different player phrasing, if provider access permits.

Do not reuse recorded provider outputs between runs.

A successful replay does not replace live qualification.

============================================================
10. PROVIDER AVAILABILITY AND TEST BUDGET
============================================================

Before beginning live testing:

- Confirm provider availability.
- Confirm credentials/configuration are usable.
- Confirm the expected model is selected.
- Establish a bounded testing budget.
- Verify instrumentation is active.

Do not consume the entire budget on exploratory runs
before final validation.

Reserve enough capacity for post-repair qualification.

If live-provider access is unavailable:

1. Document the exact limitation.
2. Continue deterministic and recorded-provider testing.
3. Preserve evidence.
4. Do not claim live acceptance.
5. Report the cycle as unverified or requiring repair.

If the budget is exhausted before final live validation:

Do not substitute earlier pre-repair live results.

Do not declare the final implementation accepted.

============================================================
11. AUTHORITY AND STATE INTEGRITY
============================================================

Verify:

- GM questions do not mutate world state.
- Rules questions do not advance simulation time.
- NPC dialogue uses existing social authority.
- Withdrawals do not execute canceled actions.
- Corrections do not duplicate operations.
- Confirmations require valid pending proposals.
- Movement respects established destinations.
- Inspection respects information boundaries.
- Save/load preserves relevant conversational context.
- Reload does not duplicate completed actions.

Compare state before and after representative turns.

Report actual state differences.

Do not infer nonmutation solely from response text.

Preserve existing final-emission safeguards.

============================================================
12. PERFORMANCE GUARDRAILS
============================================================

Preserve PR-ED efficiency improvements.

Do not introduce:

- Mandatory second interpretation calls.
- Redundant narration calls.
- Broad retry loops.
- Unbounded context expansion.
- Repeated full-transcript injection.

Record:

- Provider calls per turn.
- Input tokens.
- Output tokens.
- Total tokens.
- Retries.
- End-to-end latency.

Compare representative PR-EF and PR-EF-R1 behavior.

The PR-EF live sequences consumed approximately
85,000–88,000 tokens across ten-turn attempts.

Treat these as historical observations, not directly
comparable benchmarks unless workload and instrumentation
are equivalent.

Correctness takes precedence over optimization in R1.

Do not undertake broad prompt compression here.

============================================================
13. REGRESSION ACCOUNTABILITY
============================================================

Rerun the established PR-EF regression suites.

Compare exact test identities and failure signatures.

Report:

- Baseline passing tests.
- Baseline failing tests.
- Post-repair passing tests.
- Post-repair failing tests.
- Resolved failures.
- New failures.
- Changed failure signatures.

Do not rely only on aggregate pass counts.

Pay particular attention to:

- GM-directed questions.
- NPC dialogue.
- Social resolution.
- Clarification continuation.
- Confirmation.
- Corrections.
- Withdrawals.
- Compound intentions.
- Movement.
- Exploration.
- Save/load.
- Final-emission validation.
- Provider retries.

New authority or persistence regressions are unacceptable.

Do not broaden the cycle to repair unrelated inherited
failures unless they directly block acceptance.

============================================================
14. IMPLEMENTATION DISCIPLINE
============================================================

Use the following sequence.

STAGE A — DIAGNOSIS

Reproduce the known failures.

Identify the precise point where each message becomes
misclassified, misrouted, or unresolved.

STAGE B — MINIMAL REPAIR

Modify the smallest coherent set of existing components.

Avoid introducing parallel routing logic.

STAGE C — DETERMINISTIC VALIDATION

Run targeted tests and recorded-provider replays.

Verify state invariants.

STAGE D — SEMANTIC HOLDOUTS

Run frozen and independent holdouts.

Measure strict-label and end-to-end correctness separately.

STAGE E — FRESH LIVE VALIDATION

Run at least one complete fresh-provider conversation.

Prefer two meaningfully different conversations.

STAGE F — REGRESSION COMPARISON

Rerun established suites.

Classify any changed failures.

STAGE G — CLOSEOUT

Generate evidence and recommendation.

Do not begin PR-EG automatically.

============================================================
15. REQUIRED REVIEW ARTIFACTS
============================================================

Generate:

01 — Executive Summary
- Repairs completed.
- Remaining failures.
- Acceptance recommendation.

02 — Baseline and Environment
- Repository revision.
- Provider configuration.
- Regression baseline.
- Test commands.

03 — Semantic Ownership Diagnosis
- Original misclassifications.
- Root causes.
- Before/after behavior.
- Downstream impact.

04 — Interpretation Contract Changes
- Schema changes.
- Prompt changes.
- Normalization changes.
- Ownership changes.

05 — Continuation and Context Audit
- Confirmation.
- Correction.
- Withdrawal.
- Ambiguous references.
- Save/load.

06 — Production Handoff Audit
- Movement failure diagnosis.
- Resolver selection.
- Operation preservation.
- State transition results.

07 — Grounded Answer Relevance
- Question/answer examples.
- Relevance failures.
- Repairs.
- Remaining limitations.

08 — Semantic Holdout Results
- Frozen holdouts.
- Independent holdouts.
- Strict-label agreement.
- End-to-end correctness.
- Critical failures.

09 — Fresh Live Conversation Transcripts
- Complete transcripts.
- Raw interpretation.
- Routing decisions.
- Resolver results.
- State effects.
- Per-turn pass/fail.

10 — Authority and Persistence Audit
- State mutation checks.
- Information boundaries.
- Save/load.
- Duplicate execution.

11 — Performance Comparison
- Provider calls.
- Tokens.
- Retries.
- Latency.
- Comparability limitations.

12 — Regression Comparison
- Baseline.
- Post-repair.
- Inherited failures.
- New failures.
- Changed signatures.

13 — Remaining Issues
- Unresolved correctness defects.
- Dialogue quality limitations.
- PR-EG dependencies.
- PR-EH dependencies.

14 — Final Recommendation

Choose:

A — PR-EF-R1 ACCEPTED

Fresh live-provider conversations demonstrate coherent
GM/NPC/action distinctions, correct handoff, and
preserved authority.

B — ACCEPTED WITH LIMITATIONS

Core behavior is correct and live-validated, with bounded
noncritical deficiencies remaining.

C — REQUIRES FURTHER REPAIR

Critical correctness defects remain or the required
live conversations fail.

D — ARCHITECTURAL RECONSIDERATION REQUIRED

Evidence demonstrates that the existing conversational
contract cannot reliably support ordinary gameplay
without fundamental redesign.

UNVERIFIED — LIVE ACCEPTANCE NOT ESTABLISHED

Use this status when provider access or testing budget
prevents final live qualification.

15 — Changed-File Inventory
- Modified files.
- Purpose.
- Relevant tests.
- Source references.

Package all artifacts using the established CURRENT_REVIEW
workflow.

============================================================
16. SUCCESS CRITERIA
============================================================

PR-EF-R1 succeeds when:

1. The confirmed semantic ownership defects are repaired.

2. GM-directed questions do not initiate NPC dialogue.

3. NPC-directed dialogue preserves the intended
   interlocutor.

4. Contextual NPC follow-ups work with fresh provider
   outputs.

5. Confirmations, corrections, and withdrawals behave
   correctly.

6. Mixed and conditional intentions preserve their
   execution dependencies.

7. Correctly recognized operations reach appropriate
   authoritative resolvers.

8. Movement to an established reachable destination
   completes correctly.

9. GM answers address the player's actual question
   without inventing consequential facts.

10. At least one complete fresh-provider conversation
    passes through the production API.

11. Preferably, two differently phrased live conversations
    pass.

12. Frozen and independent holdouts demonstrate meaningful
    behavioral generalization.

13. No critical authority or persistence violations occur.

14. No unacceptable new regression failures remain.

15. PR-ED performance improvements are preserved.

Do not declare success based solely on:

- Unit-test counts.
- Strict-label agreement.
- Recorded-provider replay.
- A single successful isolated interaction.
- Changed wording of previously failing responses.

The final measure is whether the player can communicate
naturally with the GM and reliably perform ordinary
actions through the production system.

============================================================
17. FINAL INSTRUCTION
============================================================

Execute PR-EF-R1 as a bounded repair of the existing
conversational architecture.

Diagnose before modifying.

Repair root causes rather than individual phrases.

Preserve simulation authority.

Preserve existing provider efficiency.

Demonstrate production handoff integrity.

Reserve provider budget for final live qualification.

Report strict-label and behavioral correctness separately.

Do not claim live acceptance without fresh live evidence.

Generate CURRENT_REVIEW with the required artifacts.

STOP after PR-EF-R1.

Await external review before beginning PR-EG.
