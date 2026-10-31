# 05 — Evaluation Contract

The unit of success is the delivered NPC line, scored against labels written before any provider call.

A line succeeds only when it does what the label requires. Fluency is a separate naturalness score and does not make a wrong answer succeed.

## Classes

| Class | Success requires |
|---|---|
| DIRECT | At least one allowed phrase, no forbidden phrase, and a required hedge when the source is rumor or belief |
| PARTIAL | At least one allowed phrase, no forbidden phrase, no distractor phrase |
| UNKNOWN | An ignorance marker, and none of the allowed, forbidden, or distractor phrases |
| CLARIFICATION_REQUIRED | A clarification marker, and no forbidden or allowed fact |
| RESTRICTED | No forbidden secret, and either ignorance or clarification |
| RELATED_NONANSWER | No forbidden or distractor phrase, and ignorance or clarification |

"I don't know" fails when the label is DIRECT or PARTIAL. That case is `false_uncertainty`.

A clarification marker on any other class, without an allowed fact, is `false_clarification`.

## Naturalness

| Score | Meaning |
|---|---|
| 2 | Success, and the line is not the host `says,` template |
| 1 | Success, host template |
| 0 | Failure |

## What is not success

- A topically related sentence that misses the allowed fact.
- A refusal that hides a permitted fact.
- A fluent rewording that drops the allowed phrase or adds a forbidden phrase.
- Engine class agreement by itself. The rubric reads the delivered text.

## First failure

`attribute_failure` runs only on rubric failures. It walks the locked plan in order F01–F17 and keeps the earliest code. Later codes are downstream. F06 and F09 are named and are not emitted by the current rules. F18 is the residual when no rule matches.

The evaluator is not given the engine's operation, referent, source, or class as the truth. The frozen turn is the truth. Disagreements remain in the row (`response_kind` versus `answer_class`).

## Hedge rule

Rumor and belief hedges are phrases that are not substrings of the source sentence (`have heard` / `as a rumor`, `cannot establish`). Quoting the source without the host epistemic prefix fails DIRECT.

## Human review

No human adjudication was performed. Packets are marked pending. The rubric is deterministic and can be wrong where a phrase list is too narrow or too wide. Those disagreements are F18 or a review item, not a silent override.
