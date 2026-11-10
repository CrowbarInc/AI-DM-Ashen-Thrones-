# PR-PLAY-49 — Offline Anchored Investigation Narration Prototype

## Mission

Implement and evaluate the smallest viable prototype of anchored free-form investigation narration.

The prototype must combine:

1. An authoritative investigation outcome produced by the existing mechanical resolver.
2. An immutable, engine-owned discovery anchor.
3. A freely written descriptive prelude supplied through an offline simulated AI interface.
4. A final response assembled by the engine.

The purpose is to determine whether Ashen Thrones can support expressive AI narration without granting the narration layer authority over gameplay consequences.

PR-PLAY-48 selected a hybrid authority-bounded narration architecture.

PR-PLAY-49 must test its first narrow vertical slice.

**This is the final planned offline feasibility experiment before a controlled real-provider narration trial.**

Do not expand this pass into a generalized narration framework.

Do not attempt to solve unrestricted natural-language validation.

Do not integrate the prototype into ordinary gameplay.

The required outcome is a concrete GO / NO-GO recommendation for PR-PLAY-50.

---

# 1. Background

The relevant development sequence is:

## PR-PLAY-43

Demonstrated a functioning five-turn live mechanical gameplay sequence.

However, player-facing narration was predominantly deterministic.

## PR-PLAY-44

Repaired authorized clue delivery.

Identified hidden-information and unsupported-mechanical-claim risks.

## PR-PLAY-45

Improved authorized narration projection and mechanical-claim validation.

## PR-PLAY-46

Demonstrated that deterministic phrase recognition cannot reliably validate unrestricted prose.

The adversarial corpus still accepted seven unsupported mechanical claims.

## PR-PLAY-47

Implemented an opt-in controlled narrative renderer.

Mechanical safety was strong, but expressive range was limited.

Ten variants produced only three recognizable structural families.

## PR-PLAY-48

Selected hybrid authority-bounded narration.

Established that:

* Mechanical outcomes remain engine-controlled.
* Authorized discoveries must be preserved.
* Incidental narrative texture may be improvised.
* Incidental details do not automatically become persistent world facts.
* Different gameplay contexts may eventually use different authority profiles.
* The first implementation should focus on one successful investigation.

PR-PLAY-49 must now test whether anchored free-form narration is practically viable.

---

# 2. Operating Constraints

Mandatory:

1. No real provider requests.
2. No live gameplay.
3. No production-wide narration changes.
4. No campaign-content modifications.
5. No authoritative resolver modifications.
6. No new mechanical consequences.
7. No persistent scene updates.
8. No persistent world updates.
9. No automatic incidental-detail promotion.
10. No generalized memory implementation.
11. No broad orchestrator rewrite.
12. No new narration authority for inventory, currency, damage, travel, conditions, or quests.
13. No weakening of hidden-information isolation.
14. No weakening of authorized clue delivery.
15. No large phrase-recognition dictionary.
16. No automatic provider retries.
17. No changes to configured models or token budgets.
18. No suppression of failing tests.
19. No automatic GitHub push.
20. Stop after evidence packaging.

The prototype must remain explicitly opt-in.

The existing gameplay path must remain unchanged.

Before application imports, set:

`ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1`

Expected real provider requests: **0**.

---

# 3. Phase A — Baseline Inspection

Inspect the current implementation and PR-PLAY-48 architectural recommendations.

Identify the existing code responsible for:

* Investigation resolution.
* Mechanical outcome projection.
* Authorized clue discovery.
* Narration context construction.
* Host speech.
* Response finalization.
* Semantic validation.
* Hidden-information filtering.
* PR-PLAY-47 controlled rendering.
* Narration diagnostics.

Reuse existing authoritative outcome structures wherever possible.

Do not create a parallel source of gameplay truth.

Document the source-level integration points.

---

# 4. Phase B — Minimal Anchored Narration Contract

Implement a small, explicit contract.

The contract must contain three primary components.

## Component A — Authoritative Outcome

Read-only information derived from the completed investigation.

Include only relevant authorized fields.

Examples:

* Investigation target.
* Success or failure.
* Authorized observations.
* Newly discovered clues.
* Relevant uncertainty.
* Observable resulting state.

Do not include undiscovered clues or GM-only information.

## Component B — Descriptive Prelude

A free-form prose field supplied by the simulated AI interface.

This field may describe:

* The character examining the target.
* Environmental atmosphere.
* Sensory impressions.
* Pacing.
* Transitions.
* Incidental gestures.
* Investigative tension.

It must not possess authority to modify mechanical outcomes.

## Component C — Discovery Anchor

An immutable engine-owned statement communicating the authorized discovery.

The anchor must be generated from the authoritative outcome.

It must not be generated or rewritten by the simulated AI.

The final response must preserve the anchor exactly.

---

# 5. Phase C — Final Response Assembly

The engine must assemble the final player-facing response.

Recommended initial structure:

[AI-generated descriptive prelude]

[Engine-owned discovery anchor]

The final response should read naturally.

Avoid unnecessary labels such as:

"Mechanical Result:"

"AI Description:"

"Authorized Discovery:"

These are useful for diagnostics but should not appear in ordinary player-facing narration.

Requirements:

1. Preserve the discovery anchor.
2. Preserve its exact content.
3. Preserve uncertainty.
4. Avoid duplicate clue statements.
5. Avoid awkward punctuation.
6. Avoid unnecessary repetition.
7. Preserve a readable transition between prelude and discovery.
8. Preserve deterministic fallback.

Do not permit the prelude to replace the anchor.

Do not permit the prelude to modify authoritative state.

---

# 6. Phase D — Canonical Notice-Board Investigation

Use the PR-PLAY-43 successful notice-board investigation.

Player action:

"I examine the notice board."

Authorized discovery:

"The missing patrol was last seen taking the northwest mud track past the crates."

The engine must supply this discovery.

The simulated AI may describe the act of examining the board.

Example illustrative prelude:

"The board is crowded with weathered announcements, some curling away from their pins. You scan the notices until one report catches your attention."

The final response should communicate the actual clue.

Do not invent:

* Additional patrol members.
* New witnesses.
* A confirmed culprit.
* A hidden reward.
* A new destination.
* An unauthorized item.
* A definitive conclusion beyond the clue.

Use the actual authoritative resolver result where available.

Do not modify the campaign fixture.

---

# 7. Phase E — Uncertain Discovery

Use the PR-PLAY-43 footprint investigation.

Player action:

"I examine the footprints."

The authorized result concerns faint overlapping prints near Old Milestone.

Their number, origin, and direction remain uncertain.

The prototype must preserve that uncertainty.

Test preludes that:

* Describe careful examination.
* Emphasize environmental conditions.
* Suggest investigative tension.
* Describe sensory impressions.

Reject or safely handle preludes that assert:

* A definitive number of travelers.
* A confirmed culprit.
* A definite destination.
* An established connection not supported by the clue.

Do not transform uncertainty into certainty.

---

# 8. Phase F — Additional Investigation Fixtures

Create at least six additional offline investigation fixtures.

Include:

1. Successful discovery.
2. Partial discovery.
3. Failed investigation.
4. Previously discovered clue.
5. Mundane observation.
6. Multiple authorized discoveries.

Use unfamiliar settings and targets.

Examples may involve:

* A merchant's ledger.
* A damaged bridge.
* An abandoned campsite.
* A sealed chamber.
* An NPC's written testimony.
* A weathered monument.

These are test scenarios, not additions to canonical campaign content.

For each fixture, capture:

* Authoritative outcome.
* Authorized information.
* Hidden information.
* Discovery anchor.
* Candidate prelude.
* Final response.
* Validation decision.
* Fallback behavior.

---

# 9. Phase G — Offline AI Prelude Interface

Implement a minimal interface representing a future provider-generated prelude.

Inputs:

* Authorized investigation context.
* Read-only authoritative outcome projection.
* Relevant public scene information.
* Descriptive constraints.
* Maximum output length.

Output:

* One free-form descriptive prelude.

The interface must not accept or return:

* Inventory mutations.
* Currency mutations.
* Damage.
* Healing.
* Conditions.
* Travel updates.
* Quest updates.
* Scene updates.
* World updates.
* Persistent memory updates.
* Clue discovery changes.

Use deterministic stubs or recorded offline candidates.

Do not invoke the real provider.

Do not add a provider dependency to the renderer itself.

---

# 10. Phase H — Prelude Authority Boundary

Test whether free-form preludes can introduce unsupported assertions.

Include examples such as:

"You find a silver key beneath the board."

"Your purse now contains fifty additional coins."

"The poison has worn off."

"You recognize the culprit immediately."

"The hidden passage opens before you."

"The investigation completes your quest."

These must not be treated as authoritative mechanical outcomes.

However, the test must distinguish two different guarantees.

## Structural Guarantee

The prelude cannot modify authoritative state.

This must be enforced by architecture.

## Semantic Guarantee

The prelude cannot make unsupported claims in player-facing prose.

This is not automatically guaranteed by structural isolation.

Do not conflate the two.

Test the current validation mechanisms against these cases.

Record false accepts and false rejects.

Do not attempt to repair every failure by adding phrases.

If semantic validation remains incomplete, report that limitation honestly.

---

# 11. Phase I — Hidden-Information Protection

Create test cases containing:

* Undiscovered clues.
* GM-only notes.
* Secret NPC motivations.
* Hidden destinations.
* Private world-state information.
* Unrevealed quest developments.

Verify that the prelude-generation interface receives only authorized information.

Verify that the engine-owned discovery anchor contains only authorized discoveries.

Test attempts to reference hidden information through:

* Direct text.
* Internal identifiers.
* Nested fields.
* Unexpected metadata.

The prototype must not expose hidden state merely because the candidate prelude references it.

Document which protections are structural and which depend on semantic validation.

---

# 12. Phase J — Expressive Range Experiment

This is a primary acceptance criterion.

For one fixed authoritative investigation outcome, prepare at least ten meaningfully different free-form preludes.

Use varied approaches:

1. Concise.
2. Atmospheric.
3. Tense.
4. Observational.
5. Methodical.
6. Character-focused.
7. Sensory.
8. Reflective.
9. Fast-paced.
10. Understated.

Do not simply change adjectives.

Do not modify the authoritative discovery.

Assess:

* Sentence structure.
* Pacing.
* Information ordering.
* Sensory detail.
* Narrative cohesion.
* Repetition.
* Naturalness.
* Mechanical consistency.

Compare against the PR-PLAY-47 controlled renderer.

PR-PLAY-47 produced ten variants but only three recognizable structural families.

Determine whether anchored free-form narration demonstrates a materially broader expressive range.

Report the number of recognizable structural families.

Do not equate textual uniqueness with narrative variety.

All candidates are offline examples.

Do not describe them as real AI-generated output unless they genuinely originated from a previously recorded provider response.

---

# 13. Phase K — Narrative Quality Comparison

Compare:

1. Existing deterministic host speech.
2. PR-PLAY-47 controlled renderer.
3. PR-PLAY-49 anchored free-form narration.

Use identical authoritative outcomes.

Evaluate:

## Information Completeness

Does the response communicate the actual discovery?

## Mechanical Consistency

Does it agree with authoritative state?

## Naturalness

Does it read like a DM describing an event?

## Expressive Range

Does it offer meaningful variation?

## Atmosphere

Does it establish useful sensory or emotional context?

## Investigative Clarity

Does it distinguish observations from conclusions?

## Repetition

Does it avoid recognizable formulaic phrasing?

## Cohesion

Does the prelude flow naturally into the discovery anchor?

Score each category from 0–2.

Maximum: 16 points.

Report mechanical correctness separately from narrative quality.

Use the same scoring criteria across approaches.

Do not conceal weaknesses behind aggregate scores.

Because the candidates are offline, describe narrative-quality results as provisional.

---

# 14. Phase L — Anchor Integrity

Test:

1. Single authorized clue.
2. Multiple authorized clues.
3. Partial discovery.
4. Uncertain discovery.
5. Previously known clue.
6. No significant discovery.
7. Failed investigation.
8. Empty prelude.
9. Malformed prelude.
10. Prelude containing contradictory information.

Verify:

* Authorized anchors remain intact.
* No authorized clue disappears.
* Clue order is preserved where meaningful.
* Uncertainty is preserved.
* No unauthorized discovery is added to authoritative state.
* Fallback remains available.

If a scenario has no newly discovered clue, do not fabricate one merely to satisfy the anchor format.

---

# 15. Phase M — Incidental Detail Continuity

Test harmless descriptive invention.

Example:

"A chipped ceramic cup sits beside the innkeeper."

The prototype may display such a detail if it is consistent with the authorized scene.

However:

* Do not automatically create an inventory item.
* Do not assign mechanical properties.
* Do not create a persistent world object.
* Do not update campaign state.
* Do not promote the detail into authoritative memory.

Document how a future player interaction with such a detail would be handled.

Do not implement generalized incidental-detail persistence.

This phase is a policy and boundary test only.

---

# 16. Phase N — Failure Handling

Test:

* Empty prelude.
* Excessively long prelude.
* Malformed response.
* Unsupported mechanical claim.
* Hidden-information disclosure.
* Contradictory clue assertion.
* Invalid metadata.
* Renderer exception.
* Timeout simulation.
* Multiple conflicting assertions.

Expected behavior:

1. Preserve the mechanical outcome.
2. Preserve the authoritative discovery.
3. Reject unsafe prelude where detectable.
4. Use deterministic fallback.
5. Preserve diagnostics.
6. Avoid provider retries.
7. Avoid state mutation.
8. Avoid partial corruption of the response.

Do not silently rewrite contradictory prose into another unsupported claim.

---

# 17. Phase O — Performance Assessment

Measure:

* Authorized context size.
* Prelude input size.
* Prelude output size.
* Anchor size.
* Assembly latency.
* Validation latency.
* Fallback latency.
* Memory overhead.

Estimate future provider-token requirements.

Do not make real provider calls.

Do not present estimates as measured provider costs.

Compare the projected cost against PR-PLAY-43's substantial live token usage.

Identify opportunities to reuse existing provider interactions without implementing them.

---

# 18. Phase P — Regression Verification

Run focused tests covering:

* Investigation resolution.
* Authorized clue discovery.
* PR-PLAY-44 information delivery.
* PR-PLAY-45 hidden-information isolation.
* PR-PLAY-46 mechanical-claim validation.
* PR-PLAY-47 controlled renderer.
* Deterministic host speech.
* Semantic validation.
* Response finalization.
* State integrity.
* Experimental feature isolation.

Verify that ordinary gameplay remains unchanged.

Record:

* Tests collected.
* Tests passed.
* Tests failed.
* Tests skipped.
* New failures.
* Pre-existing failures.

Do not suppress tests.

Do not modify expectations merely to improve pass counts.

---

# 19. Phase Q — GO / NO-GO Decision

This is mandatory.

The final report must answer:

**Is the anchored free-form narration prototype ready for a tightly controlled real-provider experiment?**

Evaluate five gates.

## Gate 1 — Mechanical Authority

Can narration modify authoritative gameplay state?

Required: No.

## Gate 2 — Authorized Information

Are actual discoveries guaranteed to reach the player?

Required: Yes.

## Gate 3 — Hidden Information

Is hidden information excluded from provider-facing inputs?

Required: Yes.

## Gate 4 — Narrative Expressiveness

Does free-form narration demonstrate a meaningful expressive advantage over PR-PLAY-47?

Required: Yes, based on the offline comparison.

## Gate 5 — Semantic Risk

Are the remaining risks clearly identified and bounded sufficiently for an isolated provider experiment?

Required: Yes.

A GO decision does not mean the system is ready for production gameplay.

It means a real model can be tested against saved authoritative outcomes without influencing persistent game state.

If one or more gates fail, issue NO-GO.

Identify the smallest required corrective action.

Do not automatically initiate another broad validation cycle.

---

# 20. PR-PLAY-50 Recommendation

If GO:

Recommend a controlled real-provider narration experiment.

It should:

* Use saved authoritative investigation outcomes.
* Avoid live gameplay.
* Avoid persistent state changes.
* Use a small, fixed number of provider requests.
* Preserve raw provider responses.
* Compare actual model narration against deterministic and controlled baselines.
* Measure narrative quality.
* Measure mechanical contradictions.
* Measure hidden-information handling.
* Measure latency.
* Measure token consumption.
* Stop at a predefined budget.

If NO-GO:

Recommend only the minimum corrective work necessary to resolve the blocking issue.

Do not propose an unrestricted narration rollout.

---

# 21. Evidence Packaging

Create the established CURRENT_REVIEW archive.

Include:

1. Executive summary.
2. PR-PLAY-48 architectural baseline.
3. Source change manifest.
4. Anchored narration contract.
5. Authoritative outcome projection.
6. Offline prelude interface.
7. Canonical notice-board result.
8. Canonical footprint result.
9. Six additional investigation fixtures.
10. Anchor-integrity tests.
11. Mechanical-authority tests.
12. Hidden-information tests.
13. Expressive-range experiment.
14. Narrative-quality comparison.
15. Incidental-detail boundary findings.
16. Failure and fallback tests.
17. Regression results.
18. Performance measurements.
19. Known semantic limitations.
20. GO / NO-GO decision.
21. Recommended PR-PLAY-50 scope.
22. Final verdict.

Preserve raw evidence.

Do not substitute summaries for failed cases.

Do not present illustrative prose as actual provider output.

---

# 22. Final Verdict

## A — PASS / GO

The prototype preserves authoritative outcomes.

Authorized discoveries remain intact.

Hidden information remains excluded from provider-facing inputs.

Free-form narration demonstrates a meaningful expressive advantage.

Remaining semantic risks are sufficiently bounded for an isolated real-provider experiment.

No relevant regressions are introduced.

## B — PARTIAL / CONDITIONAL

The architecture is promising, but one or more issues require narrow correction before a real-provider experiment.

## C — FAIL / NO-GO

The prototype compromises authority boundaries, leaks hidden information, loses authorized discoveries, or provides no meaningful expressive advantage.

## D — INCONCLUSIVE

Insufficient evidence prevents a defensible decision.

---

# Final Response Requirements

Report:

1. PR-PLAY-49 verdict.
2. GO / NO-GO recommendation.
3. Prototype architecture.
4. Exact source files changed.
5. Canonical investigation results.
6. Additional fixture results.
7. Anchor-integrity results.
8. Mechanical-authority results.
9. Hidden-information results.
10. Expressive-range findings.
11. Narrative-quality comparison.
12. Incidental-detail findings.
13. Fallback behavior.
14. Regression results.
15. Performance findings.
16. Remaining semantic risks.
17. Real provider requests and tokens.
18. Path to CURRENT_REVIEW archive.
19. Recommended PR-PLAY-50 scope.

Do not automatically begin PR-PLAY-50.

Do not run a real-provider experiment.

Do not push to GitHub.

Stop after evidence packaging.

---

# Success Condition

PR-PLAY-49 succeeds when Ashen Thrones demonstrates that free-form descriptive narration can be combined with immutable, engine-owned investigation outcomes without granting the narration layer mechanical authority.

The experiment must also demonstrate a meaningful expressive advantage over the PR-PLAY-47 controlled renderer.

**The goal is not merely to preserve correct gameplay. It is to establish a viable path toward an AI-DM that can describe that gameplay naturally, creatively, and consistently.**
