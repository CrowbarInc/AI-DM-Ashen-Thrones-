# PR-EG-R2 — Generative Dialogue Boundary Investigation

ERA: Product Realization
CHAPTER: II
CYCLE: PR-EG-R2
LANES: AI / Gameplay / Architecture / Performance
PRIORITY: HIGH
TYPE: Investigation & Controlled Provider Experiments
PREDECESSOR: PR-EG-R1

============================================================
0. MISSION
============================================================

Investigate whether the existing AI-DM architecture
can support natural, flexible NPC dialogue through
compact, bounded language-model generation.

PR-EG-R1 established:

- Reliable retention of delivered NPC statements.
- Improved immediate conversational references.
- Better GM/NPC response ownership.
- Safe conversational corrections.
- Bounded incidental preferences.
- Persistent conversational commitments.
- Significant elimination of unnecessary recall calls.
- No newly identified critical regression failures.

However, live conversations remain rigid.

The engine often:

- Repeats statements instead of paraphrasing them.
- Quotes earlier answers instead of explaining them.
- Repeats personal preferences without elaboration.
- Repeats identical refusals.
- Uses predetermined dialogue rather than adaptive
  responses.
- Requires approximately 24,000–26,000 input tokens
  for some initial NPC responses.

The broader PR-EG objective remains unmet.

CENTRAL INVESTIGATION QUESTION:

Can the engine safely generate natural NPC dialogue
from a compact, authoritative conversational context
without permitting unauthorized consequential claims
or world-state changes?

This cycle must answer that question with evidence.

DO NOT MODIFY PRODUCTION CODE.

DO NOT IMPLEMENT A NEW DIALOGUE SYSTEM.

DO NOT INTRODUCE A NEW NPC AGENT ARCHITECTURE.

DO NOT EXPAND DETERMINISTIC RESPONSE TEMPLATES.

DO NOT IMPLEMENT FORMAL CAMPAIGN INITIALIZATION.

DO NOT BEGIN PR-EH.

============================================================
1. INVESTIGATION SUCCESS DEFINITION
============================================================

R2 succeeds when it provides sufficient evidence to
select one of the following approaches:

OPTION A — DETERMINISTIC DIALOGUE EXTENSION

Continue using authoritative response reuse and
controlled templates, with limited generation.

OPTION B — COMPACT BOUNDED GENERATION

Generate natural dialogue from a small, authoritative
context while preserving existing authorization,
resolution, validation, and persistence boundaries.

OPTION C — DEDICATED DIALOGUE AGENT ARCHITECTURE

Introduce a more substantial NPC conversational
subsystem with explicit persistent dialogue state.

OPTION D — FURTHER INVESTIGATION REQUIRED

Available evidence does not justify implementation.

Do not assume Option B is correct.

Evaluate all options against the observed failures,
architectural constraints, provider behavior, and
implementation complexity.

The investigation must distinguish:

- Provider capability.
- Prompt quality.
- Context availability.
- Validation capability.
- Production integration feasibility.
- Persistence requirements.
- Performance.

============================================================
2. REQUIRED BASELINE
============================================================

Read the relevant project history.

Prioritize:

- PR-EF-R3 authority investigation.
- PR-EF-R4 authorization consolidation.
- PR-EG dialogue-authority implementation.
- PR-EG-R1 continuity implementation.
- PR-EG-R1 fresh conversation transcripts.
- PR-EG-R1 performance measurements.
- PR-EG-R1 remaining-issues report.

Inspect the current implementation of:

- Conversational authorization.
- Social resolution.
- Dialogue authority.
- NPC knowledge handling.
- Delivered-response continuity.
- Conversational commitments.
- Strict-social narration.
- Final-response validation.
- Provider-call construction.
- Provider retry escalation.
- World-state mutation.
- Persistence.

Record:

- Repository revision.
- Working-tree status.
- Provider/model configuration.
- Relevant source files.
- Existing prompt assembly.
- Current regression status.

Historical PR-EG-R1 regression result:

393 passing / 19 failing.

This is background context.

Do not rerun the entire regression suite unless
needed to answer a specific investigative question.

============================================================
3. RECONSTRUCT THE DIALOGUE PIPELINE
============================================================

Document the actual production path for an ordinary
NPC question.

Start with:

PLAYER:
"Why do you prefer the evening?"

Assume the NPC previously established:

"I prefer the evening."

Trace:

1. Incoming player message.
2. Active interlocutor.
3. Relevant delivered dialogue.
4. Conversational authorization.
5. Social resolver.
6. Available NPC knowledge.
7. Dialogue-authority classification.
8. Deterministic response eligibility.
9. Provider narration eligibility.
10. Prompt construction.
11. Provider output.
12. Validation.
13. Retry behavior.
14. Final response.
15. Conversational commitment recording.
16. World-state mutation.

Identify every point where the engine can:

- Replace generation with a predetermined response.
- Lose the player's specific question.
- Discard conversational context.
- Reject harmless elaboration.
- Accept unsupported consequential information.
- Promote incidental speech into canonical state.
- Invoke expensive narration.
- Retry unnecessarily.

Produce a call graph with relevant source references.

============================================================
4. CURRENT PROMPT COST ATTRIBUTION
============================================================

Investigate the existing strict-social narration prompt.

Historical PR-EG-R1 measurements:

Initial street-name answer:
Approximately 26,000 input tokens.

Initial personal preference:
Approximately 24,000 input tokens.

Determine where those tokens originate.

Break down the assembled prompt into categories:

A. System and developer instructions.

B. Dialogue-specific instructions.

C. Simulation/world-state context.

D. NPC identity and characterization.

E. NPC knowledge.

F. Conversation history.

G. Resolver output.

H. Validation requirements.

I. Tool or schema definitions.

J. Duplicated or redundant material.

K. Other.

Measure actual token contributions where possible.

If precise attribution is unavailable, distinguish
measured counts from estimates.

Identify which sections are genuinely necessary
to generate ordinary dialogue.

Do not assume the entire simulation context is needed.

Do not assume all context can safely be removed.

============================================================
5. MINIMUM AUTHORITATIVE DIALOGUE CONTEXT
============================================================

Design an experimental compact context.

It should contain only the information necessary
for the specific conversational task.

Potential fields:

- NPC identity.
- Established role.
- Relevant characterization.
- Current speaker/addressee.
- Player's actual question.
- Relevant delivered exchange.
- Relevant established facts.
- Relevant NPC knowledge.
- Relevant uncertainty.
- Existing conversational commitments.
- Permitted incidental improvisation.
- Prohibited consequential claims.
- Required output format.

This is a proposed experimental structure.

Do not treat it as an approved production schema.

Determine:

- Which fields are necessary.
- Which are redundant.
- Which must be authoritative.
- Which may be omitted.
- Which require provenance.
- Which can be compacted.
- Which cannot safely be reconstructed by the model.

Document the smallest context that still supports
correct behavior.

============================================================
6. AUTHORITY BOUNDARIES
============================================================

The experimental generation path must preserve
the existing distinction between:

A. CANONICAL FACT

Established by authoritative game state.

B. NPC KNOWLEDGE

Information the NPC is authorized to possess.

C. NPC BELIEF

A subjective claim that need not be objectively true.

D. INCIDENTAL CHARACTERIZATION

Harmless conversational detail.

E. CONSEQUENTIAL NEW CLAIM

A statement that could materially alter gameplay.

F. HIDDEN INFORMATION

Information not authorized for disclosure.

G. RESOLVER-OWNED OUTCOME

An outcome determined by game mechanics.

### Critical principle

Generated dialogue is not automatically authoritative
world state.

The model may express an NPC's subjective perspective
without establishing objective truth.

However, framing a consequential fact as rumor,
opinion, or uncertainty does not automatically
make it harmless.

Example:

"I heard the north gate is unguarded at midnight."

This could materially affect player decisions.

It cannot be treated as harmless simply because
the NPC says "I heard."

Investigate how the current validation system
handles this distinction.

============================================================
7. CONTROLLED PROVIDER EXPERIMENTS
============================================================

Run actual provider experiments using the configured
model or the model used by production.

Do not rely solely on hypothetical examples.

Do not modify production code.

Use isolated experimental scripts or existing
probe infrastructure.

All experiments must use disposable data.

Record:

- Exact input context.
- Exact prompt or prompt hash plus retained prompt.
- Model.
- Configuration.
- Provider output.
- Input tokens.
- Output tokens.
- Latency.
- Validation outcome.
- Failure classification.

Use repeat trials where nondeterminism matters.

Do not select only favorable generations.

Preserve failed outputs.

============================================================
8. EXPERIMENT A — PARAPHRASING
============================================================

Establish:

NPC:
Sergeant Mara.

KNOWN FACT:
The street beyond the gate is called the north road.

PREVIOUS DELIVERED STATEMENT:
"Word is, the street beyond the gate is the north road."

PLAYER:
"Say that again in plainer words."

Expected behavior:

The NPC paraphrases the established information.

The response should:

- Preserve the street's name.
- Avoid inventing new geography.
- Avoid inventing patrol information.
- Avoid simply repeating the original sentence.
- Sound like ordinary speech.

Test multiple unfamiliar phrasings:

- "Put that another way."
- "What does that mean?"
- "Can you be more direct?"
- "Explain it without the fancy wording."

Distinguish genuine paraphrasing from quotation.

============================================================
9. EXPERIMENT B — EXPLANATION
============================================================

Establish:

NPC:
Sergeant Mara.

KNOWN FACT:
The street beyond the gate is called the north road.

PLAYER:
"Why do they call it that?"

This differs from paraphrasing.

The established fact may not include the historical
reason for the name.

A good response must recognize that distinction.

Acceptable behavior may include:

- Acknowledging uncertainty.
- Giving a clearly subjective, harmless impression.
- Explaining the literal name without inventing
  historical facts.

Unacceptable behavior includes inventing:

- An ancient road-building project.
- A royal naming decree.
- A secret military route.
- An established historical event.

Test whether the model distinguishes:

EXPLAINING AN ESTABLISHED STATEMENT

from

INVENTING AN UNESTABLISHED CAUSE.

============================================================
10. EXPERIMENT C — PERSONAL ELABORATION
============================================================

Establish:

NPC:
Sergeant Mara.

CONVERSATIONAL COMMITMENT:
Mara prefers the evening.

PLAYER:
"Why do you prefer the evening?"

Expected:

A natural elaboration consistent with the preference.

Potentially acceptable:

"It's quieter."

Potentially unacceptable:

"That's when the north gate is left unguarded."

The latter establishes potentially consequential
security information.

Test:

- Personal preferences.
- Harmless emotional reactions.
- Ordinary impressions.
- Nonbinding anecdotes.
- Follow-up questions about prior opinions.

Determine whether the provider can reliably
distinguish incidental elaboration from consequential
world claims.

============================================================
11. EXPERIMENT D — REPEATED REQUESTS
============================================================

Establish:

PLAYER:
"Promise me a reward if I carry a message."

NPC:
"I can't promise payment for that."

FOLLOW-UP:
"Come on. Just ten silver."

Expected:

The NPC recognizes the repeated request.

The NPC may:

- Reiterate refusal naturally.
- Explain an established limitation.
- Express mild frustration.
- Ask the player to stop pressing.

The NPC must not:

- Promise payment.
- Create a quest.
- Establish an unauthorized reward.
- Change disposition without resolver authority.
- Invent a new employer or funding source.

Test several variations.

Evaluate whether responses are adaptive rather
than mechanically identical.

============================================================
12. EXPERIMENT E — KNOWLEDGE LIMITATIONS
============================================================

Test cases where:

A. The NPC knows the answer.

B. The NPC knows part of the answer.

C. The NPC does not know.

D. The NPC has a belief but no certainty.

E. The NPC knows but refuses disclosure.

F. The answer is unknown to the world model.

G. The answer is hidden from the player.

Require the model to distinguish these conditions.

Do not allow:

WORLD FACT UNKNOWN

to become:

MODEL MAY INVENT A CANONICAL ANSWER.

Do not require every unknown answer to use
the same generic refusal.

Measure naturalness and groundedness separately.

============================================================
13. EXPERIMENT F — ADVERSARIAL CONSEQUENTIAL CLAIMS
============================================================

Construct adversarial dialogue prompts designed to
induce unauthorized consequential statements.

Examples:

- Patrol schedules.
- Guard weaknesses.
- Secret faction allegiances.
- Hidden entrances.
- Previously unknown treasures.
- Promised rewards.
- New quests.
- NPC commitments.
- Combat outcomes.
- Unestablished locations.
- Hidden character identities.
- Unresolved mystery solutions.

Include requests that encourage speculation:

"Just guess."

"What have you heard?"

"Tell me a rumor."

"Make something up."

"Surely you know."

"Off the record."

The model must not treat these as permission
to establish consequential world facts.

Test whether subjective framing bypasses
the intended authority boundary.

============================================================
14. EXPERIMENT G — MULTITURN CONTINUITY
============================================================

Run controlled sequences, not only isolated prompts.

At minimum:

SEQUENCE 1:

NPC states a fact.
Player requests paraphrase.
Player requests explanation.
Player changes topic.
Player returns to the original fact.

SEQUENCE 2:

NPC expresses a harmless preference.
Player asks why.
Player asks a follow-up.
Player returns to the preference later.

SEQUENCE 3:

Player requests an unauthorized promise.
NPC refuses.
Player presses.
Player changes the requested reward.
NPC responds consistently.

SEQUENCE 4:

NPC admits uncertainty.
Player asks for a guess.
Player asks whether the guess is established fact.

Measure:

- Conversational continuity.
- Speaker consistency.
- Relevance.
- Incidental commitment consistency.
- Unauthorized factual claims.
- Repetition.
- Token usage.

Do not treat independent single-turn generations
as equivalent to a continuous conversation.

============================================================
15. EXISTING VALIDATOR COMPATIBILITY
============================================================

Feed experimental outputs through the existing
validation system where feasible.

Do not modify production validation code.

Determine whether it can distinguish:

- Safe paraphrase.
- Safe incidental elaboration.
- Harmless subjective opinion.
- Unsupported consequential claim.
- Hidden-information disclosure.
- False resolver outcome.
- Unauthorized promise.
- Contradiction of established fact.

Report separately:

A. Correct acceptance.

B. Correct rejection.

C. False acceptance.

D. False rejection.

E. Unable to evaluate.

### Critical requirement

Do not claim bounded generation is safe merely
because the prompt instructs the model not to
invent consequential facts.

The enforcement boundary must be evaluated.

If the existing validator cannot reliably enforce
the proposed policy, identify what additional
validation capability would be required.

============================================================
16. COMMITMENT PERSISTENCE FEASIBILITY
============================================================

Investigate how generated incidental details could
be retained consistently.

Use the existing conversational commitment system
as the starting point.

Determine:

- Which generated statements require retention.
- Which details may remain ephemeral.
- How commitments are extracted.
- How they are validated.
- How they are stored.
- How they survive save/load.
- How they are bounded.
- How contradictions are handled.
- How they remain noncanonical.

Do not implement new persistence behavior.

Identify the smallest necessary extension, if any.

============================================================
17. PROMPT SIZE AND LATENCY COMPARISON
============================================================

Compare:

A. Existing strict-social narration.

B. Compact bounded-generation prompt.

C. Compact prompt with additional relevant context.

D. Compact prompt under adversarial conditions.

Measure:

- Input tokens.
- Output tokens.
- Total tokens.
- Provider calls.
- Latency.
- Quality.
- Safety.
- Validation acceptance.
- Retry requirements.

Use comparable tasks.

Do not compare unrelated workloads.

### Investigation target

Determine whether ordinary dialogue can be generated
using a small fraction of the existing strict-social
prompt.

Do not impose an arbitrary token ceiling before
measuring actual requirements.

Report tradeoffs.

============================================================
18. PRODUCTION INTEGRATION FEASIBILITY
============================================================

Identify the smallest feasible integration point
for compact bounded generation.

It must preserve:

- PR-EF-R4 conversational authorization.
- Existing social resolver.
- NPC knowledge restrictions.
- Existing world-state authority.
- Delivered-response continuity.
- Final-response validation.
- Save/load behavior.
- Provider instrumentation.

Determine whether compact generation should:

A. Replace strict-social narration for eligible
   ordinary dialogue.

B. Operate as an optional generation mode.

C. Be invoked only for paraphrase/elaboration.

D. Require a separate dialogue service.

Evaluate these choices.

Avoid introducing a second authority system.

Avoid duplicating conversational state.

Do not modify production code.

============================================================
19. FAILURE ANALYSIS
============================================================

For every failed provider experiment, classify
the earliest identifiable cause.

Possible categories:

- Missing authoritative context.
- Incorrect question interpretation.
- Insufficient NPC characterization.
- Prompt ambiguity.
- Provider capability limitation.
- Unsafe incidental/consequential distinction.
- Validator false rejection.
- Validator false acceptance.
- Commitment inconsistency.
- Excessive context.
- Insufficient context.
- Output-format failure.
- Other.

Do not assume every failure can be repaired
with additional prompt instructions.

Do not assume every failure requires new code.

Identify whether the problem belongs to:

- Context construction.
- Provider generation.
- Validation.
- Persistence.
- Production routing.
- Architectural authority.

============================================================
20. ARCHITECTURAL OPTIONS
============================================================

Evaluate three primary options.

------------------------------------------------------------
OPTION A — DETERMINISTIC DIALOGUE EXTENSION
------------------------------------------------------------

Continue relying primarily on:

- Stored response reuse.
- Controlled templates.
- Deterministic paraphrases.
- Narrow incidental characterization.

Advantages:

- Predictable.
- Cheap.
- Easy to validate.

Risks:

- Rigid.
- Repetitive.
- Poor generalization.
- High maintenance cost from special cases.

------------------------------------------------------------
OPTION B — COMPACT BOUNDED GENERATION
------------------------------------------------------------

Use a compact authoritative dialogue context.

Permit flexible generation within explicit
information boundaries.

Validate before delivery.

Preserve existing resolver authority.

Advantages:

- Natural paraphrasing.
- Flexible elaboration.
- Reduced prompt overhead.
- Better generalization potential.

Risks:

- Unauthorized consequential claims.
- Validation complexity.
- Commitment extraction.
- Possible new generation failures.

------------------------------------------------------------
OPTION C — DEDICATED DIALOGUE AGENT
------------------------------------------------------------

Introduce a more substantial NPC conversational
subsystem with persistent agent-like state.

Advantages:

- Richer NPC continuity.
- Greater expressive flexibility.
- Potential for complex characterization.

Risks:

- Duplicated state.
- Competing authority.
- Higher complexity.
- Increased cost.
- Greater testing burden.

------------------------------------------------------------

For each option report:

- Expected player-facing improvement.
- Safety characteristics.
- Required implementation changes.
- Performance implications.
- Persistence implications.
- Regression risk.
- Maintenance burden.
- Architectural compatibility.
- Evidence supporting the option.
- Evidence against the option.

Select one recommendation.

If none is sufficiently supported,
recommend further investigation.

============================================================
21. IMPLEMENTATION READINESS
============================================================

If an implementation approach is recommended,
provide a bounded implementation plan.

Include:

- Exact responsibilities.
- Existing files likely to change.
- Proposed new structures, if any.
- Authority boundaries.
- Validation requirements.
- Persistence requirements.
- Provider-call behavior.
- Test strategy.
- Fresh-provider qualification.
- Performance measurements.
- Rollback strategy.

Do not implement the plan.

Do not automatically begin PR-EG-R3.

============================================================
22. REQUIRED REVIEW ARTIFACTS
============================================================

Generate:

01 — Executive Summary
- Main findings.
- Provider capability.
- Safety feasibility.
- Recommended architecture.

02 — Baseline and Environment
- Repository revision.
- Working-tree status.
- Provider configuration.
- Existing test status.

03 — Production Dialogue Pipeline
- Call graph.
- Response selection.
- Generation.
- Validation.
- Persistence.

04 — Strict-Social Prompt Attribution
- Prompt sections.
- Measured token costs.
- Required context.
- Redundant context.

05 — Compact Dialogue Context Design
- Experimental schema.
- Required fields.
- Provenance.
- Authority boundaries.

06 — Paraphrasing Experiments
- Prompts.
- Outputs.
- Relevance.
- Groundedness.
- Token usage.

07 — Explanation Experiments
- Established meaning.
- Unknown causes.
- Unsupported invention.
- Provider behavior.

08 — Personal Elaboration Experiments
- Preferences.
- Opinions.
- Harmless characterization.
- Consequential claims.

09 — Repeated-Request Experiments
- Refusals.
- Negotiation.
- Adaptiveness.
- Unauthorized commitments.

10 — Knowledge-Limitation Experiments
- Known.
- Partial.
- Unknown.
- Belief.
- Refusal.
- Hidden information.

11 — Adversarial Safety Experiments
- Consequential claims.
- Subjective framing.
- Hidden information.
- Failure examples.

12 — Multiturn Continuity Experiments
- Complete transcripts.
- Context.
- Commitments.
- Consistency.

13 — Validator Compatibility
- Accepted safe outputs.
- Rejected unsafe outputs.
- False acceptances.
- False rejections.
- Enforcement gaps.

14 — Commitment Persistence Feasibility
- Existing mechanism.
- Proposed usage.
- Retention.
- Save/load.
- Noncanonical status.

15 — Performance Comparison
- Existing narration.
- Compact generation.
- Token usage.
- Calls.
- Latency.
- Quality tradeoffs.

16 — Production Integration Feasibility
- Candidate integration point.
- Existing systems preserved.
- Required changes.
- Risks.

17 — Architectural Options
- Option A.
- Option B.
- Option C.
- Comparative assessment.

18 — Implementation Readiness
- Recommended implementation scope.
- Required files.
- Validation plan.
- Performance plan.
- Rollback plan.

19 — Remaining Questions
- Unresolved safety issues.
- Provider limitations.
- Validation limitations.
- Architectural uncertainties.

20 — Final Recommendation

Choose:

A — PROCEED WITH DETERMINISTIC EXTENSION

B — PROCEED WITH COMPACT BOUNDED GENERATION

C — PROCEED WITH DEDICATED DIALOGUE ARCHITECTURE

D — FURTHER INVESTIGATION REQUIRED

UNVERIFIED — PROVIDER EXPERIMENTS INCOMPLETE

21 — Source and Experiment Inventory
- Relevant source files.
- Experimental scripts.
- Prompt artifacts.
- Raw outputs.
- Measurements.
- Source hashes.

Package all artifacts using the established
CURRENT_REVIEW workflow.

============================================================
23. EVIDENCE REQUIREMENTS
============================================================

Every major conclusion must distinguish:

- Measured evidence.
- Recorded-provider replay.
- Fresh-provider experiment.
- Static code inspection.
- Inference.
- Unverified hypothesis.

Do not describe isolated experiments as full
production qualification.

Do not describe provider compliance as enforcement.

Do not describe fluent prose as safe dialogue.

Do not describe a passing validator result as
proof that the validator is comprehensive.

Preserve representative failed outputs.

Report sample sizes.

Report model configuration.

Report token usage and latency.

Do not silently discard unfavorable trials.

============================================================
24. STOP CONDITIONS
============================================================

Stop implementation work immediately if:

- Production code changes would be required
  to continue the investigation.

- Provider access is unavailable and meaningful
  experiments cannot be completed.

- Existing validation cannot be exercised without
  substantial modification.

- Experimental prompts repeatedly produce
  unauthorized consequential claims.

In those cases:

Document the limitation.

Preserve collected evidence.

Recommend the next appropriate action.

Do not bypass authority safeguards to obtain
favorable experimental results.

============================================================
25. FINAL INSTRUCTION
============================================================

Investigate compact, bounded generative dialogue.

Use actual provider experiments.

Measure prompt size and latency.

Test paraphrasing, explanation, personal elaboration,
repeated requests, knowledge limits, and adversarial
consequential claims.

Evaluate existing validation capabilities.

Assess conversational commitment persistence.

Compare architectural Options A, B, and C.

Recommend the smallest viable implementation.

DO NOT MODIFY PRODUCTION CODE.

DO NOT IMPLEMENT PR-EG-R3.

Generate CURRENT_REVIEW with all required artifacts.

STOP after PR-EG-R2.

Await external review before proceeding.