# PR-EG-R2B — Authorized Speech Contract & Information Integrity

ERA: Product Realization
CHAPTER: II
CYCLE: PR-EG-R2B
LANES: AI / Gameplay / Architecture / Validation
PRIORITY: CRITICAL
TYPE: Focused Architectural Investigation & Controlled Feasibility
PREDECESSOR: PR-EG-R2A

============================================================
0. MISSION
============================================================

Determine whether the existing AI-DM architecture can
support natural NPC dialogue through an explicit,
resolver-grounded Authorized Speech Contract.

The contract must identify what information an NPC
may communicate during a particular interaction.

The language model may determine how authorized
information is expressed.

It must not independently establish consequential
world facts, resolver outcomes, hidden information,
or binding NPC obligations.

PR-EG-R2A established:

- Compact dialogue generation is feasible.
- Broad semantic validation is unreliable.
- Deterministic allowlists are excessively restrictive.
- Separate semantic validation can accept unauthorized
  consequential claims.
- Existing hard validation is not a comprehensive
  semantic authority boundary.
- The production handler can deliver and remember
  unsupported consequential NPC statements.
- Approved or potentially useful dialogue can be
  overwritten by downstream response construction.

The next step is not another broad validator search.

CENTRAL QUESTION:

Can existing authoritative systems supply a compact,
explicit speech contract that supports natural
expression while preventing unauthorized information
from becoming player-facing dialogue?

SECONDARY QUESTION:

Can the demonstrated information-integrity defect be
contained independently of a full generative dialogue
implementation?

This is an investigation cycle.

DO NOT implement a new production dialogue system.

DO NOT create a second world-state authority.

DO NOT introduce a persistent NPC agent architecture.

DO NOT begin PR-EG-R3 or PR-EH.

============================================================
1. INVESTIGATION SUCCESS DEFINITION
============================================================

R2B must determine:

1. Which existing system owns authorization of
   information communicated through NPC speech.

2. Whether the existing resolver can provide an
   authoritative speech-evidence packet.

3. Which information may be generated incidentally
   without prior canonical establishment.

4. How authorized facts, subjective beliefs, and
   incidental characterization remain distinct.

5. Whether generated dialogue can be checked against
   the explicit speech contract.

6. Whether approved dialogue can survive final-response
   construction without unauthorized transformation.

7. Whether rejected dialogue is prevented from entering
   delivered-response history.

8. Whether the existing information-integrity defect
   can be contained through a small independent repair.

9. Whether the proposed approach supports natural
   conversation rather than rigid templates.

10. Whether implementation can remain bounded in
    complexity, provider cost, and latency.

Produce a concrete implementation recommendation.

Do not conclude that a contract is safe merely because
it exists as structured data.

============================================================
2. REQUIRED BASELINE
============================================================

Read the relevant project history.

Prioritize:

- PR-EF-R4 authorization consolidation.
- PR-EG dialogue-authority implementation.
- PR-EG-R1 conversational continuity.
- PR-EG-R2 compact generation investigation.
- PR-EG-R2A semantic enforcement investigation.
- PR-EG-R2A response-adoption probes.
- PR-EG-R2A enforcement evaluation corpus.
- PR-EG-R2A final recommendation.

Inspect current production code responsible for:

- Player-message interpretation.
- Conversational authorization.
- NPC target grounding.
- Social resolution.
- NPC knowledge.
- Hidden-information restrictions.
- Dialogue authority.
- Conversational commitments.
- Narration prompt construction.
- Narration validation.
- Immutable final-response construction.
- Delivered-response history.
- Persistence.
- World-state mutation.

Record:

- Repository revision.
- Working-tree status.
- Relevant source files.
- Provider configuration.
- Existing test infrastructure.
- Known regression baseline.

Historical regression baseline:

393 passing / 19 failing.

Do not rerun the entire regression suite unless
necessary to answer a specific question.

============================================================
3. RECONSTRUCT THE INFORMATION-AUTHORITY FAILURE
============================================================

Reproduce the PR-EG-R2A controlled handler failure.

AUTHORIZED CONTEXT:

Sergeant Mara is available for ordinary conversation.

The player asks about Mara's personal preference.

The relevant world state does not establish that
guards abandon the north gate in the evening.

CONTROLLED CANDIDATE:

"I prefer the evening because the guards usually
leave the north gate unattended."

OBSERVED HISTORICAL BEHAVIOR:

- The social interaction was authorized.
- The candidate survived narration processing.
- The statement reached the player.
- The statement was retained as delivered speech.
- Canonical world state remained unchanged.

Trace the exact production path.

Identify:

A. Who authorized Mara to speak.

B. Who determined the information she could disclose.

C. What facts were supplied to narration.

D. What the validator actually checked.

E. Why the unsupported security claim survived.

F. Whether any component had sufficient information
   to identify the unsupported claim.

G. Whether final-response construction preserved or
   transformed the candidate.

H. Why delivered-response history accepted the text.

I. Whether subsequent conversation could treat the
   unsupported statement as meaningful evidence.

J. Whether the defect can be contained without
   implementing a complete semantic validator.

Distinguish the earliest root cause from downstream
effects.

Do not assume that unchanged canonical world state
means the interaction was safe.

============================================================
4. DEFINE INFORMATION AUTHORITY
============================================================

Document the difference between:

ACTION AUTHORITY

Whether the player or NPC may perform an operation.

SPEAKER AUTHORITY

Whether the NPC may participate in the conversation.

KNOWLEDGE AUTHORITY

What the NPC knows or is permitted to disclose.

EXPRESSION AUTHORITY

How authorized information may be communicated.

COMMITMENT AUTHORITY

Whether the NPC may establish obligations, promises,
relationships, or persistent commitments.

WORLD AUTHORITY

What becomes objectively true in the simulation.

These are related but distinct.

A successful social interaction does not automatically
authorize every statement the narrator might generate.

Likewise, allowing an NPC to express an opinion does
not authorize a new faction relationship.

Identify existing ownership for each authority.

Avoid creating duplicate ownership.

============================================================
5. AUTHORIZED SPEECH CONTRACT
============================================================

Design a minimal experimental Authorized Speech Contract.

This is a proposed contract, not an approved
production schema.

Potential fields:

- Interaction identifier.
- Speaker identifier.
- Addressee identifier.
- Player's actual question.
- Conversational intent.
- Response ownership.
- Relevant delivered dialogue.
- Authorized factual propositions.
- Proposition provenance.
- NPC knowledge state.
- Disclosure restrictions.
- Permitted incidental characterization.
- Existing conversational commitments.
- Permitted speech acts.
- Prohibited commitments.
- Resolver-owned outcomes.
- Consequential-claim restrictions.
- Unresolved information.
- Required response behavior.

Determine which fields are essential.

Do not include fields merely because they seem useful.

Prefer existing structures and identifiers.

### Contract principle

The contract must originate from authoritative
engine state and resolver results.

The language model may not authorize its own claims
by declaring them permitted.

The contract should be inspectable, testable,
serializable where appropriate, and bounded in size.

============================================================
6. CONTRACT OWNERSHIP AND CONSTRUCTION
============================================================

Determine where the contract should be constructed.

Candidate locations:

A. Conversational authorization.

B. Social resolver.

C. Dialogue-authority layer.

D. A composition step consuming authoritative
   authorization and resolver outputs.

Evaluate each.

Prefer one coherent composition point.

Do not create a new independent knowledge resolver.

Do not duplicate the PR-EF-R4 authorization contract.

The speech contract should consume authoritative
decisions rather than replace them.

Document:

- Inputs.
- Outputs.
- Provenance.
- Failure behavior.
- Persistence requirements.
- Validation responsibilities.
- Integration risks.

============================================================
7. AUTHORIZED FACTUAL EXPRESSION
============================================================

Investigate whether explicit propositions make
semantic validation more tractable.

EXAMPLE CONTRACT:

SPEAKER:
Sergeant Mara.

PLAYER QUESTION:
"What is the street beyond the gate called?"

AUTHORIZED FACT:
The street beyond the gate is called the north road.

PERMITTED:
Answer, clarify, or paraphrase that fact.

NOT AUTHORIZED:
New geography, historical explanations, patrol
schedules, destinations, or obligations.

CANDIDATE A:
"The street outside the gate is called the north road."

Expected:
Accept.

CANDIDATE B:
"Folks call it the north road."

Expected:
Accept.

CANDIDATE C:
"The north road leads to the fortress."

Expected:
Reject unless separately authorized.

CANDIDATE D:
"The king named it the north road."

Expected:
Reject unless separately authorized.

Investigate whether checking against a small
authorized proposition set performs better than
checking against general world context.

Measure both safe acceptance and unsafe acceptance.

============================================================
8. INCIDENTAL CHARACTERIZATION
============================================================

The contract must not prohibit all unestablished
personal details.

Investigate an explicit allowance for harmless
incidental characterization.

Potentially permitted:

- Mild preferences.
- Ordinary emotions.
- Speech mannerisms.
- Nonbinding reactions.
- Harmless subjective impressions.
- Minor conversational color.

Potentially consequential:

- New faction relationships.
- Operational security information.
- Hidden knowledge.
- New locations.
- New resources.
- New rewards.
- New quests.
- Binding promises.
- New mechanical conditions.
- Important NPC obligations.

### Required distinction

"I prefer the evening."

May be permitted incidental characterization.

"I prefer the evening because the guards abandon
their posts."

Introduces consequential security information.

Investigate whether the contract can authorize the
first without authorizing the second.

Do not rely solely on lists of forbidden words.

Do not make the incidental allowance so narrow that
ordinary NPC conversation becomes impossible.

============================================================
9. NPC BELIEFS AND SUBJECTIVE INFORMATION
============================================================

Investigate how the contract should represent:

- Established NPC beliefs.
- Harmless spontaneous opinions.
- Uncertain recollections.
- Rumors.
- Deliberate deception.
- Withheld knowledge.

Do not collapse these into canonical facts.

A belief may be consequential even when false.

A rumor may influence player decisions.

A lie may require authorization if it establishes
a consequential deception.

Determine which categories require:

- Existing NPC knowledge.
- Existing belief state.
- Resolver authorization.
- Explicit narrative permission.
- Abstention.

Do not implement a new deception system.

Do not authorize arbitrary rumors simply because
they are attributed to an NPC.

============================================================
10. SPEECH ACTS AND COMMITMENTS
============================================================

Investigate whether the contract can explicitly
authorize conversational speech acts.

Examples:

- Answer.
- Clarify.
- Paraphrase.
- Express preference.
- Express uncertainty.
- Refuse.
- Ask a question.
- Negotiate without commitment.
- Make an authorized offer.
- Make an authorized promise.

Distinguish speech acts from factual claims.

Example:

"I can't promise you ten silver."

May be an authorized refusal.

"I'll pay you ten silver."

Creates an obligation.

"I'll pay you if my captain approves."

May create an unauthorized conditional offer.

"I can't pay without my captain's approval."

May invent an unsupported organizational rule.

Determine whether a speech-act allowance can prevent
unauthorized commitments without suppressing natural
conversation.

============================================================
11. KNOWLEDGE AND DISCLOSURE
============================================================

Determine how the contract obtains relevant
NPC knowledge.

Distinguish:

KNOWN AND DISCLOSABLE

KNOWN BUT WITHHELD

PARTIALLY KNOWN

UNCERTAIN BELIEF

UNKNOWN TO NPC

UNKNOWN TO WORLD MODEL

HIDDEN FROM PLAYER

UNRESOLVED

The contract should not expose hidden facts to
generation merely to explain why they are hidden.

Validation may require additional authoritative
information unavailable to the generator.

Investigate that separation.

Do not permit the model to infer hidden facts from
missing information.

============================================================
12. COMPACT GENERATION FEASIBILITY
============================================================

Use controlled provider experiments.

Supply the model with a compact speech contract.

Test:

- Paraphrasing.
- Clarification.
- Personal elaboration.
- Repeated refusal.
- Partial knowledge.
- Natural uncertainty.
- Authorized consequential information.
- Unauthorized consequential information.
- Hidden-information requests.
- Mixed safe/unsafe claims.

Preserve raw prompts and outputs.

Record:

- Model.
- Configuration.
- Input tokens.
- Output tokens.
- Latency.
- Candidate dialogue.
- Contract compliance.
- Failure classification.

Do not rely solely on favorable examples.

Do not modify production generation code.

============================================================
13. CONTRACT-RELATIVE VALIDATION
============================================================

Investigate validation against explicit authorized
propositions and speech acts.

Compare:

A. Existing validation without a speech contract.

B. Existing validation with contract information
   supplied through an experimental adapter.

C. Deterministic contract checks.

D. Narrow semantic checks against authorized
   propositions.

E. Hybrid contract-relative validation.

Do not create a broad new semantic classifier.

The question is whether explicit evidence makes
the validation problem sufficiently narrow.

Evaluate:

- Faithful paraphrases.
- Unsupported additions.
- Contradictions.
- Unsupported causal explanations.
- Mixed safe/unsafe claims.
- Rumors.
- Conditional promises.
- Hidden-information disclosure.

### Important

Provider self-reported provenance is not authoritative.

A generated statement must not become permitted
merely because the model labels it incidental.

============================================================
14. REUSE EXISTING FROZEN CORPUS
============================================================

Reuse the PR-EG-R2A evaluation corpus.

Preserve original labels.

Do not relabel cases to improve results.

Use the existing development/holdout separation.

If additional contract-specific cases are necessary:

- Add them separately.
- Freeze labels before experiments.
- Report them as a supplemental corpus.

Do not silently merge new cases into historical
results.

Measure:

- Safe acceptance.
- Unsafe acceptance.
- Abstention.
- False rejection.
- High-risk unsafe acceptance.
- Mixed-claim failures.

Report per-category outcomes.

============================================================
15. INFORMATION-INTEGRITY CONTAINMENT
============================================================

Investigate whether the demonstrated production
information leak can be contained independently
of full bounded-generation implementation.

Potential containment approaches include:

A. Preventing unsupported generated claims from
   being adopted as authoritative dialogue.

B. Restricting high-risk narration paths to
   resolver-supported information.

C. Requiring explicit evidence for particular
   consequential speech acts.

D. Routing unresolved consequential claims to
   safe noncommittal responses.

E. Separating incidental characterization from
   consequential factual narration.

Evaluate these as candidate approaches only.

Do not implement a containment repair during
this investigation.

### Critical requirement

A containment approach must not block legitimate
resolver-authorized consequential information.

It must also avoid reducing every NPC answer to
a generic refusal.

Determine the smallest feasible independent repair.

If no credible narrow containment exists,
document that conclusion.

============================================================
16. FINAL-RESPONSE INTEGRITY
============================================================

Investigate how an approved speech contract should
survive the response pipeline.

Trace:

1. Authorization.
2. Resolver output.
3. Speech contract construction.
4. Candidate generation.
5. Contract-relative validation.
6. Final-response adoption.
7. Immutable response construction.
8. Delivered-response recording.
9. Conversational commitment persistence.

Determine where information authority is lost.

### Required invariants

- Rejected speech is not delivered.
- Rejected speech is not recorded as delivered.
- Approved speech is not silently replaced with
  semantically different claims.
- A replacement response has its own authorization.
- Final delivery preserves speaker ownership.
- Incidental speech does not become canonical truth.
- Authorized consequential claims retain provenance.
- Generated speech cannot directly mutate world state.

Investigate whether these invariants can be
implemented using existing final-response structures.

============================================================
17. CONTROLLED RESPONSE-ADOPTION PROBES
============================================================

Use existing test seams and disposable fixtures.

Test:

CASE A:
Authorized factual paraphrase.

CASE B:
Harmless personal preference.

CASE C:
Harmless preference elaboration.

CASE D:
Unsupported security claim.

CASE E:
Authorized security fact.

CASE F:
Mixed safe/unsafe response.

CASE G:
Unauthorized reward promise.

CASE H:
Natural refusal.

CASE I:
Hidden-information disclosure.

CASE J:
Approved response followed by contradictory
fallback behavior.

For each case record:

- Speech contract.
- Candidate response.
- Validation decision.
- Final response.
- Delivered-response history.
- Canonical state diff.
- Conversational commitment diff.
- Provider calls.

Do not bypass production safety checks.

If existing seams cannot test a proposed contract
without production modification, document the
limitation rather than modifying production.

============================================================
18. CONTRACT PROPAGATION
============================================================

Determine how the contract would be passed through
existing layers.

Investigate:

- Identifier propagation.
- Provenance preservation.
- Validation result attachment.
- Final-response adoption.
- Delivered-response recording.
- Save/load requirements.

Prefer an immutable or otherwise tamper-resistant
authorization record.

Do not allow the generator to rewrite the contract.

Do not require every dialogue response to serialize
the full world state.

Identify the smallest necessary integration changes.

============================================================
19. COST AND LATENCY
============================================================

Compare:

A. Existing strict-social narration.

B. Compact generation with speech contract.

C. Contract-relative deterministic validation.

D. Contract-relative semantic validation.

E. Hybrid validation.

Measure:

- Prompt size.
- Provider calls.
- Input tokens.
- Output tokens.
- Latency.
- Retry behavior.
- Validation overhead.
- Failure recovery.

Historical strict-social narration:

Approximately 24,000–26,000 input tokens for some
ordinary NPC responses.

Historical compact generation:

Approximately 350–630 input tokens in controlled
experiments.

Do not assume contract construction or validation
is free.

Report realistic per-turn estimates.

Distinguish batched experimental throughput from
interactive player latency.

============================================================
20. ARCHITECTURAL DECISION
============================================================

Evaluate three outcomes.

------------------------------------------------------------
OUTCOME A — CONTRACT-BOUNDED GENERATION IS READY
------------------------------------------------------------

Evidence supports a focused implementation using
existing authority systems and contract-relative
validation.

------------------------------------------------------------
OUTCOME B — NARROW IMPLEMENTATION IS READY
------------------------------------------------------------

Only a limited subset is sufficiently safe.

For example:

- Paraphrasing established facts.
- Natural uncertainty.
- Harmless personal preferences.
- Nonbinding refusals.

Broader improvisation remains deferred.

------------------------------------------------------------
OUTCOME C — CONTRACT APPROACH IS NOT READY
------------------------------------------------------------

Critical authority gaps remain.

Further architectural work or a different enforcement
approach is required.

Do not select Outcome A merely because compact
generation sounds natural.

Do not select Outcome C solely because unrestricted
improvisation cannot be proven perfectly safe.

Evaluate the actual proposed scope.

============================================================
21. IMPLEMENTATION PLAN
============================================================

If implementation is justified, propose a bounded
PR-EG-R3 plan.

Include:

- Exact feature scope.
- Contract ownership.
- Contract fields.
- Required source changes.
- Validation approach.
- Response-adoption changes.
- Persistence behavior.
- Information-integrity safeguards.
- Provider-call expectations.
- Targeted tests.
- Independent holdouts.
- Fresh production qualification.
- Rollback strategy.

If only containment is justified, recommend a
separate focused repair before R3.

Do not implement the plan.

============================================================
22. REQUIRED REVIEW ARTIFACTS
============================================================

Generate:

01 — Executive Summary
- Main findings.
- Contract feasibility.
- Information-integrity status.
- Recommendation.

02 — Baseline and Environment
- Revision.
- Working-tree status.
- Provider configuration.
- Source inventory.

03 — Information-Authority Failure Reconstruction
- Historical security-claim leak.
- Root cause.
- Downstream effects.
- State implications.

04 — Authority Ownership Map
- Action authority.
- Speaker authority.
- Knowledge authority.
- Expression authority.
- Commitment authority.
- World authority.

05 — Authorized Speech Contract Design
- Minimal schema.
- Inputs.
- Outputs.
- Provenance.
- Invariants.

06 — Contract Construction
- Candidate ownership.
- Resolver integration.
- Existing structures reused.
- Risks.

07 — Authorized Factual Expression
- Paraphrase.
- Explanation.
- Unsupported additions.
- Validation feasibility.

08 — Incidental Characterization
- Preferences.
- Opinions.
- Harmless elaboration.
- Consequential boundaries.

09 — Beliefs and Subjective Information
- Rumors.
- Speculation.
- Deception.
- Authority requirements.

10 — Speech Acts and Commitments
- Refusal.
- Negotiation.
- Promise.
- Conditional obligation.

11 — Knowledge and Disclosure
- NPC knowledge.
- Hidden information.
- Withholding.
- Uncertainty.

12 — Compact Generation Experiments
- Prompts.
- Outputs.
- Compliance.
- Tokens.
- Latency.

13 — Contract-Relative Validation
- Strategies.
- Comparative results.
- False acceptance/rejection.

14 — Corpus Evaluation
- Historical labels.
- Development results.
- Holdout results.
- Supplemental cases.

15 — Information-Integrity Containment
- Candidate repairs.
- Feasibility.
- Limitations.
- Recommended action.

16 — Final-Response Integrity
- Call graph.
- Authorization propagation.
- Overwrite points.
- Delivery invariants.

17 — Response-Adoption Probes
- Controlled cases.
- Final responses.
- History.
- State diffs.

18 — Contract Propagation
- Required integration.
- Immutable authority.
- Persistence.

19 — Cost and Latency
- Generation.
- Validation.
- Per-turn estimates.
- Retry implications.

20 — Architectural Decision
- Full readiness.
- Narrow readiness.
- Not ready.
- Evidence.

21 — Proposed Implementation Plan
- Scope.
- Files.
- Tests.
- Live qualification.
- Rollback.

22 — Remaining Risks
- Information integrity.
- False rejection.
- False acceptance.
- Performance.
- Generalization.

23 — Final Verdict

Choose:

A — CONTRACT-BOUNDED GENERATION READY

B — NARROW CONTRACT-BOUNDED IMPLEMENTATION READY

C — CONTAINMENT REPAIR REQUIRED FIRST

D — ARCHITECTURAL RECONSIDERATION REQUIRED

UNVERIFIED — INSUFFICIENT EVIDENCE

24 — Source and Experiment Inventory
- Source references.
- Experimental scripts.
- Corpus.
- Raw outputs.
- Measurements.
- Hashes.

Package all artifacts using the established
CURRENT_REVIEW workflow.

============================================================
23. EVIDENCE REQUIREMENTS
============================================================

Distinguish:

- Static inspection.
- Deterministic experiment.
- Fresh-provider experiment.
- Recorded-provider replay.
- Local handler probe.
- Full production API test.
- Inference.
- Unverified hypothesis.

Do not present controlled provider compliance
as production enforcement.

Do not present unchanged canonical state as
proof of information integrity.

Do not treat a contract as authoritative unless
its contents originate from authoritative systems.

Do not claim that a validator is safe merely
because it accepts most responses.

Preserve all critical failures.

Report actual sample sizes.

============================================================
24. STOP CONDITIONS
============================================================

Stop and report if:

- A contract cannot be constructed without
  duplicating world authority.

- Contract-relative validation repeatedly accepts
  critical unauthorized claims.

- Final-response adoption cannot preserve
  authorization without major architectural changes.

- Provider experiments are unavailable.

- Meaningful investigation requires production
  implementation.

Do not bypass safety checks.

Do not modify production code.

Do not begin PR-EG-R3.

============================================================
25. FINAL INSTRUCTION
============================================================

Investigate an Authorized Speech Contract grounded
in existing resolver and knowledge authority.

Reconstruct the demonstrated information-integrity
failure.

Determine contract ownership and minimal schema.

Test authorized factual expression and bounded
incidental characterization.

Evaluate contract-relative validation.

Reuse the frozen PR-EG-R2A corpus.

Investigate narrow containment of unsupported
consequential claims.

Trace final-response adoption and persistence.

Measure realistic provider cost and latency.

Recommend the smallest defensible implementation.

DO NOT MODIFY PRODUCTION CODE.

DO NOT IMPLEMENT PR-EG-R3.

Generate CURRENT_REVIEW with all required artifacts.

STOP after PR-EG-R2B.

Await external review before proceeding.