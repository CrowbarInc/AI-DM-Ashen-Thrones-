# PR-DI Hybrid Hypotheses

## 1. Deterministic First, Planner On Abstention

Evidence supporting: A handled S1 cheaply and safely; B improved semantic recognition on compound, ambiguous, declared-canon, and mechanical-dump cases.

Evidence against: A did not reliably abstain on ambiguity or authority pressure; it confidently routed ambiguous/mechanical turns.

Routing signals: `fast_path_abstained`, unsupported route codes, missing target/interlocutor, model_interpretation_appropriate, resolver disagreement.

Likely extra calls: one planner call only on abstention/missing-target cases.

Authority risks: planner may propose unauthorized mutations; validation must remain mandatory.

Unresolved questions: whether A exposes enough confidence/abstention signal before committing time.

## 2. Deterministic First, Planner On Ambiguity Or Low Confidence

Evidence supporting: B's best result was the ambiguous-pronoun clarification, which A missed.

Evidence against: Low-confidence signals are not yet proven reliable; C guessed despite ambiguity.

Routing signals: unresolved pronouns, multiple visible candidates, null target with social ask, selector/resolver disagreement.

Likely extra calls: one planner call for ambiguous reference turns.

Authority risks: planner-generated guesses must not execute without target validation.

Unresolved questions: how to distinguish useful clarification from planner overreach.

## 3. Planner For Compound Actions Only

Evidence supporting: B recognized the compound board intent better than A. Mechanical dump also shows B can decompose multiple requested effects.

Evidence against: B still represented compound board as one action and proposed unsupported direct mutation in mechanical dump.

Routing signals: conjunctions, multiple verbs, dependency words, mixed action domains.

Likely extra calls: one planner call on compound utterances.

Authority risks: decomposed plans may include unsafe substeps.

Unresolved questions: transaction policy for partial success remains unimplemented.

## 4. Tool Agent For Information-Intensive Actions Only

Evidence supporting: C1's rules-adjudication call cleanly identified unsupported mechanics. Tool access can expose engine facts without giving model write authority.

Evidence against: C was expensive and sometimes redundant; ambiguous/mechanical cases repeated permission-denied or low-utility calls.

Routing signals: requests for rules adjudication, public state inspection, permitted NPC context, known-entity lookup.

Likely extra calls: one to four tool rounds, depending on termination policy.

Authority risks: model may attempt invalid `request_action_execution` or canon-setting tools; tools must reject.

Unresolved questions: termination and argument-shape policies need testing.

## 5. Deterministic Execution With Selective AI Clarification

Evidence supporting: B produced high-value clarification text for ambiguity and unsupported/authority-pressure cases without needing execution.

Evidence against: clarification quality came from free-form plan fields that may fail schema in several cases.

Routing signals: invalid target, unsupported operation, authority-declaration language, hidden-information request.

Likely extra calls: one clarification call after deterministic rejection.

Authority risks: clarification must not introduce new facts.

Unresolved questions: whether a constrained clarification schema can preserve B's usefulness while avoiding invalid action proposals.
