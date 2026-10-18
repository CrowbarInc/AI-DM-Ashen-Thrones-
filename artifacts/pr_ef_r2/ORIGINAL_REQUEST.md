# PR-EF-R2 — Social Authority & Final-Response Consistency

ERA: Product Realization
CHAPTER: II
CYCLE: PR-EF-R2
LANES: Gameplay / AI / Architecture
PRIORITY: Critical
TYPE: Bounded Repair & Conversational Requalification
PREDECESSOR: PR-EF-R1

============================================================
0. MISSION
============================================================

Repair the remaining social-authority and final-response
consistency failures identified during PR-EF-R1.

PR-EF-R1 demonstrated that the existing conversational
architecture can sustain a complete ten-turn conversation
using fresh provider outputs through the production API.

It also identified failures in which:

1. A social resolver correctly identifies an NPC, but a
   downstream safeguard rejects the same NPC as unknown.

2. An NPC-directed request reaches the correct authority,
   but the final response becomes a generic nonresolution.

3. Incidental language interferes with an otherwise valid
   primary NPC interaction.

4. Final-response handling can contradict a successful
   authoritative resolution.

5. A minor notice-board presentation regression remains.

These defects must be investigated and repaired without
introducing another conversational architecture.

PRIMARY OBJECTIVE:

Ensure that validated authoritative decisions remain
consistent throughout the production turn pipeline.

Once an authoritative resolver establishes:

- The operation being attempted.
- The relevant target.
- The operation's outcome.
- The permitted state changes.
- The information available to the player.

Downstream components must not contradict those findings
using stale, weaker, or incompatible interpretation data.

IMPORTANT:

Authoritative resolution is not permission to bypass
safety, information-access, or final-emission validation.

A downstream safeguard may still reject an invalid
response when it identifies a genuine violation.

The repair must distinguish legitimate validation from
contradictory re-interpretation.

This is a bounded repair cycle.

Do not begin PR-EG.

Do not implement formal campaign creation.

Do not redesign the AI-DM's overall dialogue style.

Do not introduce a parallel interpretation pipeline.

Do not solve these failures through exact-phrase handlers.

============================================================
1. REQUIRED BASELINE
============================================================

Before modifying production code:

1. Read the PR-EF-R1 review artifacts.
2. Review PR-EF's conversational authority contract.
3. Review PR-EE's original root-cause investigation.
4. Inspect current social-resolution authority.
5. Inspect final-response and immutable-response safeguards.
6. Inspect incidental versus consequential intent handling.
7. Inspect existing regression failures involving dialogue.
8. Inspect PR-ED provider instrumentation.

Record:

- Repository revision.
- Working-tree status.
- Relevant provider configuration.
- Current test commands.
- Current passing tests.
- Current failing tests.
- Existing failure signatures.
- Relevant performance measurements.

Historical PR-EF-R1 regression results:

Before:
271 passing / 30 failing.

After:
293 passing / 26 failing.

Five inherited failures were resolved.
One new presentation regression was introduced.

These are historical reference points.

Re-establish the current baseline before implementation.

Do not assume the repository remains unchanged.

============================================================
2. REPRODUCE THE THREE SOCIAL FAILURES
============================================================

Reproduce the following production holdout failures.

CASE A:

PLAYER:
"I ask Mara what troubles her."

Observed:

The social resolver identifies Mara.

A downstream response safeguard subsequently claims
that the addressed person cannot be identified.

CASE B:

PLAYER:
"I tell the sergeant to describe the courtyard."

Observed:

The request is recognized as NPC-directed communication,
but the player receives a generic response indicating
that nobody can answer.

CASE C:

PLAYER:
"I turn to Mara and ask about the north road."

Observed:

An incidental gesture and unresolved topic interfere
with the supported NPC-directed interaction.

For each case, trace:

- Raw player message.
- Raw provider interpretation.
- Normalized interpretation.
- Communication ownership.
- Primary intent.
- Incidental intents.
- Target identification.
- Target authority.
- Social resolver invocation.
- Social resolver result.
- Final-response construction.
- Final-emission validation.
- Player-facing response.
- World-state changes.

Identify the exact component and condition responsible
for each failure.

Do not assume all three share the same root cause.

Do not modify production code until the failure
mechanisms are documented.

============================================================
3. AUTHORITATIVE RESULT CONSISTENCY
============================================================

Establish an explicit contract for authoritative results
passed into player-facing response construction.

The contract should preserve, as appropriate:

- Operation identity.
- Target identity.
- Target resolution status.
- Authoritative outcome.
- State changes.
- Information-access restrictions.
- Player-visible facts.
- Relevant failure reason.
- Response constraints.

Prefer extending existing result structures.

Do not introduce a large new abstraction unless existing
structures cannot represent the required information.

### Required invariant

A downstream component must not independently replace
an authoritative result with a contradictory conclusion
derived from weaker evidence.

Example:

SOCIAL RESOLVER:
Target = Sergeant Mara.
Target resolution = successful.

FINAL RESPONSE:
"Nobody by that name can be identified."

This is inconsistent unless a separate, legitimate
authority invalidated the result.

### Legitimate validation

Final-response validation must remain capable of rejecting:

- Invented NPC statements.
- Unsupported successful actions.
- Hidden-information disclosure.
- Unauthorized world-state changes.
- Incorrect target substitutions.
- Contradictions with canonical world state.

Do not disable safeguards to make the tests pass.

Instead, ensure safeguards receive the authoritative
information needed to validate correctly.

============================================================
4. LEGACY ADDRESSEE CONTRACT AUDIT
============================================================

PR-EF-R1 identified a possible conflict involving:

immutable_valid_response.safe_nonresolution

and legacy addressee validation.

Investigate the actual current implementation.

Determine:

1. Which component first establishes the NPC target.
2. Whether the target is resolved authoritatively.
3. Whether a later component repeats target resolution.
4. Whether the later component uses weaker context.
5. Whether target identity is lost during normalization.
6. Whether a stale interlocutor overrides explicit input.
7. Whether response validation incorrectly assumes that
   unresolved interpretation means unresolved target.

### Repair requirement

Once the appropriate authority has successfully resolved
the target, downstream response construction should
consume that result.

Do not independently re-derive target identity from
raw text when an authoritative result is available.

If no authoritative target exists, preserve existing
clarification and nonresolution behavior.

If authoritative sources genuinely conflict, do not
silently choose one.

Surface the conflict through a controlled failure or
focused clarification, as appropriate.

============================================================
5. PRIMARY VERSUS INCIDENTAL INTENT
============================================================

Repair cases where incidental language blocks the
player's primary supported intention.

Example:

"I turn to Mara and ask about the north road."

Likely structure:

PRIMARY:
Ask Mara about the north road.

INCIDENTAL:
Turn toward Mara.

The incidental gesture should not automatically block
the primary social interaction.

### Requirements

Distinguish:

- Primary consequential intention.
- Secondary consequential intention.
- Incidental descriptive language.
- Preconditions.
- Conditional intentions.
- Explicit ordering.

Do not treat every verb as an independent world operation.

Do not silently discard genuinely consequential actions.

### Examples

"I glance at Mara and ask about the patrol."

The glance may be incidental.

"I draw my sword and threaten Mara."

Drawing a weapon may be consequential.

"After unlocking the door, I enter."

Unlocking is a prerequisite, not merely incidental.

"I ask Mara about the road, then leave."

Leaving is a separate consequential intention.

Preserve the existing PR-EC compound-intent contract.

Do not implement phrase-specific exceptions.

### Acceptance

The engine must preserve the player's actual primary
intention without inventing, discarding, or prematurely
executing consequential secondary intentions.

============================================================
6. SOCIAL RESOLUTION AND NPC CONTINUITY
============================================================

Verify that NPC-directed communication remains coherent
across turns.

The engine should preserve:

- Explicit NPC addressees.
- Established interlocutors.
- Relevant conversational subjects.
- Previously established NPC statements.
- Valid social-resolution outcomes.

Example:

PLAYER:
"I ask Mara about the north road."

NPC:
Provides an authorized response.

PLAYER:
"Which road do you mean?"

Expected:

The engine preserves Mara as the interlocutor and
resolves the follow-up appropriately.

Do not require the player to repeat the NPC's name.

Do not redirect NPC dialogue into GM exposition unless
the player clearly addresses the GM.

Do not allow an old NPC interlocutor to override an
explicitly selected new target.

### Information boundaries

NPCs must not automatically know everything the GM knows.

A successfully identified NPC is not necessarily capable
of answering every question.

If the NPC lacks relevant knowledge:

- Preserve the correct NPC identity.
- Represent the knowledge limitation accurately.
- Avoid claiming the NPC cannot be identified.

Distinguish:

TARGET UNKNOWN

from:

TARGET KNOWN, ANSWER UNKNOWN.

This distinction must survive final-response validation.

============================================================
7. FINAL-RESPONSE CONSISTENCY
============================================================

Audit response construction and validation for the
following failure classes:

A. Resolved target becomes unresolved.

B. Successful operation becomes generic refusal.

C. Failed operation becomes narrated success.

D. Established NPC statement becomes contradictory
   GM exposition.

E. Correctly grounded information becomes generic
   uncertainty.

F. A valid primary intention is replaced by an incidental
   action.

G. Final narration introduces unauthorized world facts.

For each failure class:

- Identify the authoritative source.
- Identify the downstream consumer.
- Identify the inconsistency.
- Repair the narrowest confirmed cause.
- Add regression coverage.

### Important

Do not simply prioritize resolver output over every
other component.

The final response must satisfy all applicable authority
and information-access constraints.

The goal is consistency between authoritative components,
not the elimination of validation.

============================================================
8. NOTICE-BOARD PRESENTATION REGRESSION
============================================================

PR-EF-R1 introduced a regression involving notice-board
presentation.

The expected response included the phrase:

"notice board"

The actual response referred to:

"the board"

Investigate whether the failure represents:

A. A brittle test requiring unnecessary exact wording.

B. A genuine loss of referential clarity.

C. A violation of an established player-facing contract.

D. A broader response-construction regression.

Do not blindly modify the implementation to satisfy
a literal string assertion.

Do not blindly weaken the test.

Determine the intended behavior and document the reason
for the chosen repair.

If the response is semantically correct and the contract
does not require exact wording, improve the test.

If the response is genuinely unclear or violates a
contract, repair the implementation.

============================================================
9. EXISTING SOCIAL REGRESSION CLUSTER
============================================================

Review the remaining inherited regression failures
related to:

- Social dialogue.
- NPC addressee resolution.
- Final-emission validation.
- Repeated questioning.
- Generic nonresolution.
- Conversational continuation.

Classify each relevant failure as:

A. Same root cause as PR-EF-R2.

B. Direct dependency of PR-EF-R2.

C. Separate conversational defect.

D. Unrelated inherited failure.

Repair categories A and B.

Document categories C and D.

Do not expand into unrelated exploration, combat,
movement, or campaign lifecycle work.

Do not claim a failure is unrelated without examining
its failure signature.

============================================================
10. SEMANTIC REQUALIFICATION
============================================================

Reuse the existing 24-expression semantic holdout set.

Historical PR-EF-R1 recorded-provider result:

21/24 behavioral passes.

Do not remove difficult expressions.

Do not rewrite the holdouts to improve scores.

### Required validation

Run:

1. Deterministic targeted tests.
2. Recorded-provider production replays.
3. Fresh-provider interpretation evaluation.
4. Fresh-provider production behavior evaluation.

Report separately:

- Strict interpretation-label agreement.
- End-to-end behavioral correctness.
- Authority violations.
- State-integrity violations.
- Response contradictions.

Do not conflate label agreement with behavioral success.

### Additional holdouts

Include unfamiliar expressions involving:

- Explicit NPC addressees.
- Implicit NPC continuation.
- GM-directed questions about NPCs.
- Incidental gestures.
- Compound social intentions.
- NPC knowledge limitations.
- Corrections.
- Withdrawals.
- Ambiguous targets.

Freeze the additional holdouts before implementation.

Do not add exact-match handlers for them.

============================================================
11. FRESH LIVE-PROVIDER ACCEPTANCE
============================================================

Run fresh-provider validation through the actual
production /api/chat path.

Use a persistent initialized campaign.

Do not reset the campaign between turns.

Do not manually rewrite player messages.

Do not substitute recorded provider fixtures for
live acceptance.

### Required conversation

Conduct at least one continuous conversation containing:

1. GM-directed observation question.
2. GM-directed follow-up.
3. Explicit NPC-directed question.
4. Implicit NPC follow-up.
5. NPC knowledge limitation.
6. GM clarification about NPC dialogue.
7. NPC interaction with incidental gesture.
8. Consequential inspection or interaction.
9. Correction or withdrawal.
10. Movement to an established destination.

The conversation must include the three previously
failing social interaction patterns, or equivalent
semantically distinct variants.

### Additional validation

Run the original three failure expressions separately
through the final production path.

Prefer a second live conversation with different wording
if provider budget permits.

### Per-turn evidence

Record:

- Raw player message.
- Raw provider interpretation.
- Normalized interpretation.
- Ownership decision.
- Primary and incidental intentions.
- Resolved target.
- Resolver result.
- Final-response validation.
- Player-facing response.
- State changes.
- Provider calls.
- Tokens.
- Latency.
- Pass/fail result.

### Acceptance

No authoritative target may become spuriously unknown.

No successful resolution may become a contradictory
generic nonresolution.

No incidental gesture may improperly block the primary
supported action.

No unauthorized world-state mutation may occur.

No hidden information may be disclosed without authority.

A legitimate inability to answer is acceptable when
properly attributed to the known NPC or GM.

============================================================
12. PROVIDER BUDGET DISCIPLINE
============================================================

Before live testing:

- Verify provider availability.
- Verify provider/model configuration.
- Verify instrumentation.
- Establish a bounded test budget.
- Reserve capacity for final post-repair validation.

Do not exhaust the budget during diagnosis.

If live-provider access is unavailable:

- Continue deterministic testing.
- Preserve recorded-provider evidence.
- Document the limitation.
- Do not claim fresh live acceptance.

If provider access becomes unavailable after repairs:

Report live qualification as incomplete.

Do not substitute pre-repair live results for final
acceptance.

============================================================
13. AUTHORITY AND PERSISTENCE
============================================================

Verify that the repair does not introduce:

- Unrequested NPC dialogue.
- Unauthorized NPC knowledge.
- Unrequested world-state mutation.
- Duplicate operation execution.
- Incorrect target substitution.
- Lost conversational context.
- Stale interlocutor selection.
- Hidden-information disclosure.
- False success narration.
- Invalid movement.
- Save/load inconsistencies.

Compare actual state before and after representative turns.

Do not infer state integrity solely from response text.

Preserve existing resolver authority.

Preserve existing final-emission safeguards.

Preserve PR-EF conversational continuity.

============================================================
14. PERFORMANCE GUARDRAILS
============================================================

Preserve PR-ED performance improvements.

Do not introduce:

- Mandatory additional provider calls.
- Repeated full-context interpretation.
- Broad retry loops.
- Redundant narration calls.
- Unbounded conversational context.

Record:

- Provider calls.
- Input tokens.
- Output tokens.
- Total tokens.
- Retries.
- End-to-end latency.

Historical PR-EF-R1 final-code live conversation:

Approximately 40,755 tokens across ten turns.
Median turn latency approximately 2.74 seconds.

These are reference observations.

Do not claim controlled performance improvements unless
the workloads and instrumentation are comparable.

Correctness remains the priority.

============================================================
15. REGRESSION ACCOUNTABILITY
============================================================

Rerun the established regression suites.

Record:

- Baseline passing tests.
- Baseline failing tests.
- Post-repair passing tests.
- Post-repair failing tests.
- Resolved failures.
- New failures.
- Changed failure signatures.

Use exact test identities.

Do not rely solely on aggregate counts.

Pay particular attention to:

- Social resolution.
- NPC identity.
- NPC knowledge boundaries.
- Conversational continuation.
- Primary/incidental intent.
- Final-response validation.
- Clarification.
- Compound intentions.
- Save/load.
- Movement.
- Provider retries.

New authority or persistence regressions are unacceptable.

============================================================
16. IMPLEMENTATION STAGES
============================================================

STAGE A — BASELINE

Establish current repository and regression state.

STAGE B — ROOT-CAUSE DIAGNOSIS

Reproduce the three known social failures.

Trace resolver authority through final emission.

STAGE C — BOUNDED REPAIR

Repair confirmed authority conflicts.

Repair incidental-intent interference.

Repair final-response contradictions.

STAGE D — TARGETED VALIDATION

Run deterministic tests.

Run recorded-provider replays.

Verify state integrity.

STAGE E — SEMANTIC REQUALIFICATION

Run the frozen 24-expression holdouts.

Run additional independent holdouts.

Evaluate both strict labels and actual behavior.

STAGE F — FRESH LIVE VALIDATION

Run fresh-provider production conversations.

Verify final-code behavior.

STAGE G — REGRESSION COMPARISON

Rerun established suites.

Classify changed failures.

STAGE H — CLOSEOUT

Generate review artifacts.

Recommend acceptance, repair, or reconsideration.

Do not begin PR-EG automatically.

============================================================
17. REQUIRED REVIEW ARTIFACTS
============================================================

Generate:

01 — Executive Summary
- Changes made.
- Failures repaired.
- Remaining limitations.
- Final recommendation.

02 — Baseline and Environment
- Repository revision.
- Working-tree status.
- Provider configuration.
- Test commands.
- Regression baseline.

03 — Social Failure Reconstruction
- Original three failures.
- Production traces.
- Root causes.
- Before/after results.

04 — Authority Contract Audit
- Social resolver authority.
- Target identity.
- Knowledge boundaries.
- Downstream consumers.
- Final-response validation.

05 — Primary/Incidental Intent Audit
- Classification behavior.
- Compound-intent handling.
- Corrected examples.
- Remaining ambiguities.

06 — Final-Response Consistency Audit
- Contradiction classes.
- Safeguards preserved.
- Repaired failures.
- Remaining risks.

07 — Notice-Board Regression
- Root cause.
- Contract interpretation.
- Test or implementation repair.
- Evidence.

08 — Social Regression Cluster
- Relevant inherited failures.
- Root-cause classification.
- Resolved failures.
- Remaining failures.

09 — Semantic Requalification
- Frozen 24-expression results.
- Additional holdouts.
- Strict-label agreement.
- End-to-end behavioral correctness.
- Critical failures.

10 — Fresh Live Conversation Evidence
- Complete transcripts.
- Per-turn routing.
- Resolver results.
- Final-response validation.
- State changes.
- Pass/fail classification.

11 — Authority and Persistence Audit
- State-diff evidence.
- NPC knowledge restrictions.
- Save/load.
- Duplicate execution.
- Hidden-information boundaries.

12 — Performance Comparison
- Provider calls.
- Tokens.
- Retries.
- Latency.
- Comparability limitations.

13 — Regression Comparison
- Baseline.
- Post-repair.
- Resolved failures.
- New failures.
- Changed signatures.

14 — Remaining Issues
- Unresolved correctness defects.
- Dialogue quality limitations.
- PR-EG dependencies.
- Unrelated technical debt.

15 — Final Recommendation

Choose:

A — PR-EF ACCEPTED

Social authority is consistent, final responses preserve
authoritative results, fresh live conversations pass,
and no critical regressions remain.

B — PR-EF ACCEPTED WITH LIMITATIONS

Core conversational correctness is demonstrated through
fresh live testing, with bounded noncritical deficiencies.

C — PR-EF REQUIRES FURTHER REPAIR

Critical social-authority or response-consistency
failures remain.

D — ARCHITECTURAL RECONSIDERATION REQUIRED

The current authority contract cannot reliably preserve
correct social resolution through final response without
fundamental redesign.

UNVERIFIED — LIVE ACCEPTANCE NOT ESTABLISHED

Use this when final-code live qualification cannot be
completed.

16 — Changed-File Inventory
- Modified files.
- Purpose.
- Validation commands.
- Source references.

Package all results using the established CURRENT_REVIEW
workflow.

============================================================
18. SUCCESS CRITERIA
============================================================

PR-EF-R2 succeeds when:

1. The three known social failures are repaired.

2. Resolved NPC identities remain consistent through
   final response.

3. Known NPCs with unknown answers are not misrepresented
   as unidentified NPCs.

4. Incidental gestures do not block supported primary
   social interactions.

5. Consequential secondary intentions remain preserved.

6. Final-response validation consumes authoritative
   resolver results correctly.

7. Legitimate authority safeguards remain intact.

8. The notice-board regression is resolved or its test
   contract is appropriately corrected.

9. Relevant inherited social regression failures are
   investigated and classified.

10. Frozen semantic holdouts are rerun without rewriting
    the test expressions.

11. Fresh-provider production behavior demonstrates
    correct GM/NPC distinctions.

12. At least one continuous final-code live conversation
    passes.

13. No critical authority or persistence violations occur.

14. No unacceptable new regressions remain.

15. Provider efficiency improvements are preserved.

Do not declare acceptance solely because:

- Unit tests pass.
- Aggregate regression counts improve.
- Recorded-provider replay succeeds.
- The three original expressions receive better wording.
- Strict interpretation labels improve.

Acceptance requires consistent, authoritative behavior
through the production system.

============================================================
19. FINAL INSTRUCTION
============================================================

Execute PR-EF-R2 as a bounded repair.

Diagnose the three known social failures before modifying
production code.

Preserve authoritative resolver decisions through
final-response construction.

Do not weaken legitimate validation safeguards.

Repair primary/incidental intent interference.

Investigate related inherited social regressions.

Requalify semantic behavior with fresh provider outputs.

Demonstrate at least one continuous final-code live
conversation through /api/chat.

Generate CURRENT_REVIEW with all required artifacts.

STOP after PR-EF-R2.

Await external review before beginning PR-EG.