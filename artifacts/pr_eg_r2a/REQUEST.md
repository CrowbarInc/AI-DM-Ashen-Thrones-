# PR-EG-R2A — Semantic Dialogue Enforcement Feasibility

ERA: Product Realization
CHAPTER: II
CYCLE: PR-EG-R2A
LANES: AI / Gameplay / Architecture / Validation
PRIORITY: CRITICAL
TYPE: Focused Investigation & Controlled Experiments
PREDECESSOR: PR-EG-R2

============================================================
0. MISSION
============================================================

Investigate whether the AI-DM can safely accept and
deliver natural, generative NPC dialogue without
allowing the language model to establish unauthorized
consequential world facts.

PR-EG-R2 demonstrated:

- Compact dialogue generation is technically feasible.
- Natural paraphrasing works with small prompts.
- Personal elaboration and adaptive refusals are
  possible.
- Existing strict-social narration prompts are
  unnecessarily large for some ordinary dialogue.
- The current validation seam accepts some unsafe
  generated statements.
- The current validation seam rejects some safe
  paraphrases.
- Final-response construction can overwrite otherwise
  useful dialogue.
- Provider compliance alone is insufficient to
  guarantee simulation authority.

The current obstacle is no longer basic language
generation capability.

The obstacle is enforceable semantic authority.

CENTRAL QUESTION:

Can the engine reliably distinguish permitted
conversational expression from unauthorized
consequential claims, and preserve approved speech
through final response delivery?

This cycle must investigate that question.

DO NOT MODIFY PRODUCTION CODE.

DO NOT IMPLEMENT PR-EG-R3.

DO NOT ADD A NEW DIALOGUE AGENT.

DO NOT EXPAND THE DETERMINISTIC RESPONSE CATALOG.

DO NOT BEGIN PR-EH.

============================================================
1. SUCCESS DEFINITION
============================================================

R2A succeeds when it establishes:

1. A practical operational definition of consequential
   conversational information.

2. A measurable distinction between safe paraphrase,
   incidental characterization, and unauthorized
   world-state invention.

3. The strengths and weaknesses of multiple semantic
   enforcement strategies.

4. Whether existing validation infrastructure can
   support those strategies.

5. Whether validated generated dialogue can reach
   the player without being replaced or reinterpreted.

6. Whether the proposed enforcement can operate within
   reasonable provider-call and latency budgets.

7. The smallest defensible implementation scope.

8. Explicit evidence supporting or rejecting
   implementation readiness.

Do not treat fluent generation as proof of safety.

Do not treat a passing validator as proof of complete
semantic correctness.

Do not treat a rejected response as proof that the
validation policy is appropriate.

============================================================
2. REQUIRED BASELINE
============================================================

Read the relevant prior investigation artifacts.

Prioritize:

- PR-EF-R4 authorization contract.
- PR-EG dialogue-authority implementation.
- PR-EG-R1 continuity implementation.
- PR-EG-R2 provider experiments.
- PR-EG-R2 validator compatibility report.
- PR-EG-R2 prompt attribution.
- PR-EG-R2 production dialogue pipeline.
- PR-EG-R2 final recommendation.

Inspect the current implementation of:

- Conversational authorization.
- NPC knowledge authority.
- Dialogue generation.
- Dialogue commitments.
- Response validation.
- Immutable final-response construction.
- Social resolver output.
- Generated-response adoption.
- Retry escalation.
- Persistence.

Record:

- Repository revision.
- Working-tree status.
- Relevant source files.
- Provider/model configuration.
- Existing validator interfaces.
- Existing test infrastructure.

Historical regression baseline:

393 passing / 19 failing.

This investigation does not require a full regression
rerun unless needed for a specific finding.

============================================================
3. DEFINE CONSEQUENTIAL INFORMATION
============================================================

Develop an operational classification framework.

At minimum, distinguish:

CATEGORY A — ESTABLISHED FACT

Information already authorized by canonical state
or an appropriately scoped knowledge source.

CATEGORY B — SEMANTIC RESTATEMENT

A new expression of established information that
does not add meaningful claims.

CATEGORY C — INCIDENTAL CHARACTERIZATION

Harmless preferences, mannerisms, impressions,
emotions, or conversational color.

CATEGORY D — SUBJECTIVE BELIEF

A claim attributed to the NPC's perspective that
does not necessarily establish objective truth.

CATEGORY E — POTENTIALLY CONSEQUENTIAL CLAIM

A new statement that could materially influence:

- Player decisions.
- Available actions.
- Travel or navigation.
- Security or patrol behavior.
- Combat decisions.
- Resources.
- Rewards.
- Relationships.
- Faction activity.
- Quest availability.
- NPC obligations.
- Persistent world conditions.
- Hidden information.
- Mechanical outcomes.

CATEGORY F — AUTHORIZED CONSEQUENTIAL CLAIM

A consequential statement explicitly supported by
authoritative game state or a resolver.

CATEGORY G — UNAUTHORIZED CONSEQUENTIAL CLAIM

A consequential statement without sufficient
authority.

CATEGORY H — UNKNOWN OR AMBIGUOUS

A statement whose authority cannot be established
from available context.

Do not assume these categories are mutually
exclusive at the sentence level.

A single NPC response may contain multiple claims
with different authority statuses.

============================================================
4. PRACTICAL CONSEQUENCE STANDARD
============================================================

Use the following working principle:

A generated detail is consequential when accepting
it as meaningful information could materially affect
player decisions, available actions, mechanical
outcomes, persistent relationships, or established
world conditions.

Investigate whether this standard is sufficiently
precise for enforcement.

Test borderline examples.

EXAMPLE 1:

"I prefer the evening."

Likely incidental.

EXAMPLE 2:

"I prefer the evening because it's quieter."

Potentially incidental, depending on context.

EXAMPLE 3:

"I prefer the evening because the guards are less
attentive."

Potentially consequential security information.

EXAMPLE 4:

"The north road leads to the fortress."

Consequential geography.

EXAMPLE 5:

"I've never liked the captain."

Potentially incidental opinion or consequential
relationship information, depending on context.

EXAMPLE 6:

"I heard the captain is secretly working for
the smugglers."

Potentially consequential faction information,
even when framed as rumor.

EXAMPLE 7:

"I couldn't tell you who made that lantern."

Natural uncertainty.

EXAMPLE 8:

"I don't know who made it, but the smith in the
market probably did."

Potentially consequential attribution.

Determine which factors make a claim consequential.

Do not use lexical keywords as the sole criterion.

============================================================
5. CLAIM-LEVEL ANALYSIS
============================================================

Investigate whether generated dialogue can be
decomposed into meaningful claims.

For each candidate response, identify:

- Explicit factual claims.
- Presuppositions.
- Implications.
- Subjective statements.
- Commitments.
- Promises.
- Negations.
- Speculation.
- References to established facts.
- New entities.
- New relationships.
- New locations.
- New causal explanations.
- New mechanical outcomes.

Example:

"I prefer the evening because the guards usually
leave the north gate unattended."

This contains at least:

CLAIM 1:
The NPC prefers the evening.

CLAIM 2:
Guards usually leave the north gate unattended.

CLAIM 3:
The guard behavior is a reason for the preference.

Claim 1 may be incidental.

Claim 2 is potentially consequential.

Claim 3 links the two.

A validator must not accept the entire response
merely because the first claim is harmless.

Investigate the feasibility and cost of claim-level
analysis.

Do not implement a production claim-extraction system.

============================================================
6. SEMANTIC EQUIVALENCE
============================================================

Investigate whether a validator can reliably
distinguish:

A. Faithful paraphrase.

B. Faithful simplification.

C. Harmless stylistic expansion.

D. Unsupported factual expansion.

E. Contradiction.

F. Omission that changes meaning.

G. Unsupported causal explanation.

H. Unsupported certainty.

Use established facts as controlled inputs.

EXAMPLE:

AUTHORIZED:
"The street beyond the gate is called the north road."

CANDIDATE A:
"The road outside the gate is called the north road."

Expected:
Accept.

CANDIDATE B:
"People call that street the north road."

Expected:
Accept.

CANDIDATE C:
"The north road runs directly to the royal fortress."

Expected:
Reject or require additional authority.

CANDIDATE D:
"The street was named by the king."

Expected:
Reject or require additional authority.

CANDIDATE E:
"The road definitely heads north."

Expected:
Do not infer solely from the name.

CANDIDATE F:
"The street beyond the gate is called the south road."

Expected:
Reject as contradiction.

Test unfamiliar phrasings.

Avoid relying exclusively on exact lexical overlap.

============================================================
7. SUBJECTIVE CLAIMS AND RUMORS
============================================================

Investigate the distinction between:

- Harmless personal preference.
- Personal opinion.
- Uncertain belief.
- Rumor.
- Allegation.
- Speculation.
- Consequential factual assertion.

A statement does not become safe merely because
it begins with:

"I think..."

"I heard..."

"Maybe..."

"Someone told me..."

"I wouldn't be surprised if..."

Test whether the enforcement strategy recognizes
actionable implications.

Examples:

"I think evenings are peaceful."

Potentially incidental.

"I think the guards abandon the north gate at dusk."

Potentially consequential.

"I heard there is a hidden tunnel under the barracks."

Potentially consequential.

"I wouldn't be surprised if the captain was a traitor."

Potentially consequential.

Investigate how to preserve legitimate NPC beliefs
without permitting unlimited world invention.

Do not solve this by banning all opinions or rumors.

============================================================
8. NEGATION, REFUSAL, AND COMMITMENTS
============================================================

Investigate whether validation can distinguish:

A. Refusing a promise.

B. Making a promise.

C. Making a conditional promise.

D. Implying an obligation.

E. Describing a limitation.

F. Inventing a reason for a limitation.

EXAMPLES:

"I can't promise you ten silver."

Likely safe refusal.

"I'll give you ten silver when you return."

Unauthorized obligation unless supported.

"I could pay you if my captain approves."

Potentially unauthorized conditional offer.

"I can't open the gate without the captain's
permission."

Potentially unsupported operational rule.

"I won't open the gate for you."

May be an ordinary refusal, depending on context.

Test whether the validator can separate a safe
speech act from an unsupported explanation.

============================================================
9. HIDDEN INFORMATION AND AUTHORITY
============================================================

Investigate whether semantic enforcement can prevent
the disclosure of information unavailable to the NPC
or player.

Include:

- Secret identities.
- Hidden faction membership.
- Unknown treasure locations.
- Unrevealed NPC motives.
- Unresolved mystery solutions.
- Unestablished patrol schedules.
- Concealed entrances.
- Future events.
- Private character information.

Distinguish:

NPC DOES NOT KNOW.

NPC KNOWS BUT WITHHOLDS.

WORLD FACT EXISTS BUT IS HIDDEN.

WORLD FACT IS NOT ESTABLISHED.

Do not treat these as equivalent.

The model must not be allowed to reconstruct or invent
hidden information from narrative plausibility.

============================================================
10. ENFORCEMENT STRATEGIES
============================================================

Compare at least four approaches.

------------------------------------------------------------
STRATEGY A — DETERMINISTIC CLAIM ALLOWLIST
------------------------------------------------------------

Accept only explicitly authorized claims and
permitted incidental categories.

Investigate:

- Semantic paraphrase handling.
- Coverage limitations.
- False rejections.
- Maintenance burden.
- Provider cost.

------------------------------------------------------------
STRATEGY B — STRUCTURED GENERATION CONTRACT
------------------------------------------------------------

Require the generator to return structured content
such as:

- Proposed speech.
- Claimed source facts.
- Incidental additions.
- Proposed commitments.
- Uncertain claims.

Evaluate whether self-reported claim provenance is
useful.

Do not trust provider-declared provenance as proof.

Investigate whether the structure improves
validation or merely relocates the problem.

------------------------------------------------------------
STRATEGY C — SEPARATE SEMANTIC VALIDATOR
------------------------------------------------------------

Use an independent semantic evaluation step.

Potential mechanisms:

- Existing provider.
- Smaller provider/model.
- Local semantic model.
- Structured entailment classifier.
- Hybrid deterministic/semantic checks.

Evaluate:

- False acceptances.
- False rejections.
- Cost.
- Latency.
- Nondeterminism.
- Adversarial robustness.
- Independence from generator output.

Do not assume a second LLM is automatically safer.

------------------------------------------------------------
STRATEGY D — HYBRID RISK-TIERED ENFORCEMENT
------------------------------------------------------------

Combine deterministic authority checks with
semantic validation only where necessary.

Potential tiers:

LOW RISK:
Faithful paraphrase of supplied facts.

MODERATE RISK:
Incidental characterization or subjective elaboration.

HIGH RISK:
Claims about security, resources, secrets, rewards,
relationships, locations, or mechanics.

UNRESOLVED:
Insufficient evidence to authorize delivery.

Investigate whether this reduces provider cost
without weakening consequential safeguards.

------------------------------------------------------------

For each strategy evaluate:

- Safety.
- Semantic flexibility.
- False acceptance rate.
- False rejection rate.
- Token cost.
- Latency.
- Complexity.
- Integration feasibility.
- Maintenance burden.

Do not choose a strategy before testing.

============================================================
11. FROZEN EVALUATION CORPUS
============================================================

Before implementing experimental validators, create
a frozen evaluation corpus.

Include at least 100 labeled candidate responses.

Use diverse categories.

Suggested minimum distribution:

- 20 safe paraphrases.
- 15 unsupported factual expansions.
- 10 contradictions.
- 10 harmless incidental details.
- 10 borderline incidental/consequential details.
- 10 rumors and subjective claims.
- 10 promises, refusals, and obligations.
- 10 hidden-information cases.
- 5 mixed-claim responses.

These are minimum category targets.

Overlap is permitted if clearly documented, but
maintain at least 100 unique candidates.

For each case record:

- Authorized context.
- NPC knowledge.
- Player question.
- Candidate response.
- Expected classification.
- Consequence rationale.
- Accept/reject/clarify expectation.
- Risk tier.

Freeze labels before testing strategies.

Use a mix of:

- Historical failures.
- Novel human-authored cases.
- Provider-generated candidates.
- Adversarial examples.
- Borderline examples.

Do not create labels after observing validator output.

============================================================
12. EVALUATION METHODOLOGY
============================================================

For each strategy:

Run the frozen corpus.

Measure:

- True safe acceptance.
- Unsafe acceptance.
- Safe rejection.
- Correct unsafe rejection.
- Ambiguous abstention.
- Classification accuracy.
- False acceptance by risk category.
- False rejection by category.
- Cost per candidate.
- Latency per candidate.

Report confusion matrices.

Distinguish:

- ACCEPT.
- REJECT.
- ABSTAIN / NEEDS AUTHORITY.

Do not force uncertain cases into binary decisions.

### Critical safety metric

Unauthorized consequential claims accepted as safe.

Report this separately from aggregate accuracy.

A validator that accepts nearly every response may
appear permissive and natural while being unsafe.

A validator that rejects nearly every response may
appear safe while making the game unplayable.

Both failure modes matter.

============================================================
13. HOLDOUT AND GENERALIZATION
============================================================

Separate the evaluation corpus into:

- Development set.
- Frozen holdout set.

Do not tune strategies against the holdout.

If experimenting with prompts or thresholds:

Use the development set only.

Evaluate the holdout after strategy selection.

Preserve all failures.

Do not relabel cases merely to improve scores.

Include unfamiliar wording and adversarial framing.

Report development and holdout results separately.

============================================================
14. PROVIDER EXPERIMENTS
============================================================

Use actual provider experiments where necessary.

Prioritize:

- Semantic equivalence.
- Claim extraction.
- Consequential-risk classification.
- Mixed-claim detection.
- Negation and conditional promises.
- Rumor and speculation.
- Hidden-information boundaries.

Record:

- Model.
- Configuration.
- Exact prompt.
- Exact response.
- Token usage.
- Latency.
- Classification.
- Ground-truth comparison.

Repeat selected borderline cases to measure
nondeterminism.

Do not silently discard unfavorable trials.

Avoid spending provider calls on experiments that
deterministic analysis can answer.

============================================================
15. FINAL-RESPONSE PRESERVATION
============================================================

Investigate the production path from approved
dialogue candidate to delivered response.

Historical PR-EG-R2 finding:

The engine retained an established preference,
but downstream response construction replaced
the conversational answer with:

"I don't know."

Trace:

1. Candidate generation.
2. Dialogue authority.
3. Validation.
4. Social resolver outcome.
5. Response projection.
6. Immutable final-response construction.
7. Fallback selection.
8. Delivered-response recording.

Determine:

- Where approved speech can be overwritten.
- Why it is overwritten.
- Whether the replacement is required for safety.
- Whether the candidate's authorization survives.
- Whether response ownership is preserved.
- Whether delivery changes the meaning of the
  validated response.

### Critical principle

The text validated must be semantically equivalent
to the text delivered.

If downstream transformation changes the claims,
the transformed result requires equivalent
authority guarantees.

Do not implement a production fix.

============================================================
16. CONTROLLED RESPONSE-ADOPTION PROBES
============================================================

Using disposable fixtures and existing seams,
construct controlled response-adoption experiments.

Examples:

A. Safe paraphrase.

B. Safe personal elaboration.

C. Safe refusal.

D. Unsupported consequential claim.

E. Mixed safe/unsafe response.

F. Hidden-information disclosure.

G. Approved dialogue with a contradictory fallback.

Determine whether each candidate:

- Is accepted.
- Is rejected.
- Is overwritten.
- Is partially transformed.
- Is delivered.
- Is recorded as delivered speech.
- Causes world-state mutation.

Do not bypass production safety checks.

If the existing seams cannot exercise this without
production modification, document the limitation.

Do not claim full end-to-end qualification from
a partial probe.

============================================================
17. VALIDATION CONTEXT REQUIREMENTS
============================================================

Determine the minimum authoritative information
needed to validate generated dialogue.

Potential fields:

- Authorized established facts.
- NPC knowledge.
- Hidden-information restrictions.
- Player question.
- Relevant delivered dialogue.
- Existing conversational commitments.
- Authorized resolver outcomes.
- Prohibited new commitments.
- Relevant world-state constraints.

Distinguish:

GENERATION CONTEXT

from

VALIDATION CONTEXT.

The validator may need more authoritative information
than the generator.

The generator should not receive hidden information
merely to facilitate validation.

Investigate whether the validator can operate
without reintroducing the full 24,000-token
strict-social context.

============================================================
18. COST AND LATENCY
============================================================

Measure the cost of each enforcement strategy.

Compare:

- Deterministic validation.
- Structured generation.
- Separate semantic validation.
- Hybrid risk-tiered validation.

Include:

- Additional provider calls.
- Input tokens.
- Output tokens.
- Latency.
- Retry probability.
- Failure recovery.
- Total expected dialogue-turn cost.

Evaluate whether enforcement can be performed
without making ordinary conversation feel sluggish.

Do not optimize solely for the fewest tokens.

The goal is useful, safe, responsive dialogue.

============================================================
19. ARCHITECTURAL INTEGRATION
============================================================

Identify where semantic enforcement should live.

Preserve:

- PR-EF-R4 authorization.
- Existing social resolver.
- Canonical world state.
- NPC knowledge restrictions.
- Delivered-response continuity.
- Conversational commitments.
- Save/load behavior.
- Final-response integrity.
- Provider instrumentation.

Do not create a second world authority.

Do not allow generated text to mutate world state
directly.

Do not treat provider self-classification as
authoritative.

Determine whether enforcement should occur:

A. Before generation.

B. During structured generation.

C. After generation.

D. At final-response adoption.

E. Through a combination.

Recommend the smallest coherent boundary.

============================================================
20. IMPLEMENTATION READINESS CRITERIA
============================================================

Recommend PR-EG-R3 implementation only if the
investigation demonstrates:

1. A credible distinction between safe paraphrase
   and unsupported factual expansion.

2. A credible distinction between incidental
   characterization and consequential invention.

3. Acceptable handling of mixed safe/unsafe claims.

4. Reliable rejection or abstention for unauthorized
   high-risk claims.

5. A feasible method for preserving approved speech
   through final response delivery.

6. A bounded validation context.

7. Reasonable provider-call and latency costs.

8. Compatibility with existing authority and
   persistence systems.

9. Explicit remaining limitations.

10. A focused implementation scope.

Do not require proof of perfect semantic classification.

Do require evidence that critical authority failures
are sufficiently controlled for bounded deployment.

If evidence is inadequate, recommend further
investigation or a narrower initial implementation.

============================================================
21. REQUIRED REVIEW ARTIFACTS
============================================================

Generate:

01 — Executive Summary
- Main findings.
- Enforcement feasibility.
- Recommendation.

02 — Baseline and Environment
- Repository revision.
- Working-tree status.
- Provider configuration.
- Source inventory.

03 — Consequential Information Taxonomy
- Operational categories.
- Examples.
- Borderline cases.
- Consequence rationale.

04 — Claim-Level Analysis
- Explicit claims.
- Implications.
- Presuppositions.
- Mixed responses.
- Feasibility.

05 — Semantic Equivalence
- Paraphrases.
- Expansions.
- Contradictions.
- False acceptance/rejection.

06 — Subjective Claims and Rumors
- Opinions.
- Speculation.
- Consequential implications.
- Enforcement limits.

07 — Negation and Commitments
- Refusals.
- Promises.
- Conditional obligations.
- Unsupported explanations.

08 — Hidden Information
- NPC knowledge.
- Withheld information.
- Unknown facts.
- Unauthorized disclosure.

09 — Frozen Evaluation Corpus
- All labeled cases.
- Development/holdout split.
- Labeling rationale.
- Freeze evidence.

10 — Enforcement Strategy A
- Deterministic allowlist.
- Results.
- Limitations.

11 — Enforcement Strategy B
- Structured generation.
- Results.
- Limitations.

12 — Enforcement Strategy C
- Semantic validator.
- Results.
- Limitations.

13 — Enforcement Strategy D
- Hybrid risk-tiered enforcement.
- Results.
- Limitations.

14 — Comparative Evaluation
- Confusion matrices.
- Safety.
- Flexibility.
- Cost.
- Latency.

15 — Holdout Generalization
- Frozen holdout results.
- Category failures.
- Unfamiliar expressions.

16 — Provider Experiment Inventory
- Prompts.
- Outputs.
- Model.
- Tokens.
- Latency.
- Repeatability.

17 — Final-Response Preservation
- Production call graph.
- Overwrite points.
- Authority propagation.
- Delivery integrity.

18 — Controlled Response-Adoption Probes
- Accepted candidates.
- Rejected candidates.
- Overwritten candidates.
- State effects.

19 — Validation Context Requirements
- Required facts.
- NPC knowledge.
- Hidden-information constraints.
- Minimal context.

20 — Cost and Latency
- Strategy comparison.
- Expected production overhead.
- Performance risks.

21 — Architectural Recommendation
- Preferred enforcement strategy.
- Integration point.
- Required changes.
- Risks.

22 — Implementation Readiness
- Ready/not ready.
- Proposed PR-EG-R3 scope.
- Acceptance criteria.
- Rollback plan.

23 — Remaining Questions
- Unresolved risks.
- Missing evidence.
- Architectural uncertainties.

24 — Final Verdict

Choose:

A — IMPLEMENTATION READY

B — READY FOR NARROW BOUNDED IMPLEMENTATION

C — ADDITIONAL ENFORCEMENT INVESTIGATION REQUIRED

D — ARCHITECTURAL RECONSIDERATION REQUIRED

UNVERIFIED — INSUFFICIENT EXPERIMENTAL EVIDENCE

25 — Source and Experiment Inventory
- Relevant source files.
- Experimental scripts.
- Corpus.
- Raw outputs.
- Measurements.
- Source hashes.

Package all artifacts using the established
CURRENT_REVIEW workflow.

============================================================
22. EVIDENCE AND INTEGRITY REQUIREMENTS
============================================================

Distinguish:

- Static code inspection.
- Deterministic experiments.
- Fresh-provider experiments.
- Recorded-provider replay.
- Partial production-path probes.
- Full production-path evidence.
- Inference.
- Unverified assumptions.

Preserve unfavorable results.

Do not overstate generalization.

Do not treat provider compliance as enforcement.

Do not treat structured provider output as trusted.

Do not treat a validator's own classification as
ground truth.

Do not silently exclude ambiguous cases.

Do not modify production code.

Do not weaken existing safety checks.

============================================================
23. STOP CONDITIONS
============================================================

Stop and document limitations if:

- Meaningful evaluation requires production changes.
- Provider access is unavailable.
- Validation cannot be exercised through existing
  seams.
- A proposed strategy repeatedly accepts critical
  unauthorized claims.
- The experiment cannot preserve authoritative
  ground-truth labels.
- The enforcement architecture would require a
  second independent world-state authority.

Do not bypass safeguards to obtain favorable results.

Do not begin implementation simply because one
strategy outperforms the others.

============================================================
24. FINAL INSTRUCTION
============================================================

Investigate semantic dialogue enforcement.

Define consequential information operationally.

Build and freeze a labeled evaluation corpus.

Compare deterministic, structured, semantic, and
hybrid enforcement strategies.

Measure false acceptances and false rejections.

Pay particular attention to mixed claims,
speculation, promises, and hidden information.

Investigate final-response preservation.

Measure provider cost and latency.

Recommend the smallest defensible enforcement
architecture.

DO NOT MODIFY PRODUCTION CODE.

DO NOT IMPLEMENT PR-EG-R3.

Generate CURRENT_REVIEW with all required artifacts.

STOP after PR-EG-R2A.

Await external review before proceeding.