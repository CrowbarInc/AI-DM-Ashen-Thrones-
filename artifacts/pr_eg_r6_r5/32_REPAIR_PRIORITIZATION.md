# 32 — Repair Prioritization

No repair is implemented in this cycle.

## R1 — Accept a witnessed correction or follow-up through bind

Mechanism: `bind()` and the witness checks reject the turn before `_topic_rows`. The player hears "I can't reliably answer that revision just now." Corrections are 0/25.

Evidence: I2 net +4. Intent+referent net +5, with 2 fixes only in the combination. I9, which already supplies gold operations, still fails validation turns on `unlisted_role_change`, `invalid_correction_operation`, `unwitnessed_operation`, and `referent_speaker_mismatch`. I8 speaks an authorized line for most of those turns, so the speaker is waiting on this gate.

Expected gain: the largest single share of the I8-versus-I9 gap, concentrated on corrections and follow-ups. Confidence: high that the gate is causal, medium on the exact gain until a local change is measured. The gold delta itself is still rejected, so a one-line predicate tweak is not yet identified.

Scope: `game/conversational_referents.py` bind rules and the witness call in `authorize_information_turn`. Do not add phrase lists.

Regression risk: medium. A weaker check can bind the wrong prior question.

Security: do not treat a bound proposition as permission to read a hidden topic.

Qualification: rerun this frozen validation set. Correction success must rise. RESTRICTED hits must stay zero. DIRECT baseline successes must not fall.

## R2 — Match a question proposition to a source proposition only when both are present

Mechanism: `named_coverage` requires predicate equality and role identity, and a missing source proposition becomes `unknown` before `coverage()` runs. Replacing one side disturbs matches the model already had.

Evidence: I3 net −2, I5 net −3, question+source net +8, 7 only when both are supplied. I6 alone is net +4 once coverage is actually invoked.

Expected gain: on the order of the question+source arm, about 8 validation failures, if the host accepts the pair it currently rejects as `no_relevant_source`. Confidence: high for the interaction, medium for a larger gain. I9's extra fixes come from referent and act fields, not from correspondence alone.

Scope: the relevance closure in `authorize_information_turn` and `named_coverage`. Do not add a new planner.

Regression risk: medium. Related non-answers and role reversals can look similar.

Security: hidden rows stay out of ranking. A gold label must not promote one.

Qualification: PARTIAL must not be scored as a full DIRECT. RELATED_NONANSWER and RESTRICTED must not gain allowed facts. Rerun validation and read holdout baseline only after the change, without fitting to holdout.

## R3 — Keep host ignorance lines when expression would add a specific claim

Mechanism: c06t07. The host line passes UNKNOWN. Expression adds a named claim and fails.

Evidence: one paired turn. I8 44/54 versus I10B 45/54.

Expected gain: small. Confidence: high for this case, low as a general rate.

Scope: skip expression when the host line is a pure ignorance or refusal template.

Regression risk: low.

Security: this removes a path that can sound like a new fact.

Qualification: the same turn must keep the host sentence. DIRECT lines that expression currently preserves must still contain the allowed phrase.

## Not recommended from this evidence

- A new semantic architecture, or migration of PR-EG-R6-R4-R1 arms B or C.
- A candidate-id retriever. I4 is net 0.
- A sufficiency model. I7 cannot recover a missed source.
- An expression rewrite. The host line is already enough when the plan is right.
