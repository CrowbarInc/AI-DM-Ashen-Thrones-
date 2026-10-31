# 07 — Conversational Context

Twelve independent conversations. Each turn is replayed from a snapshot taken before that turn, so an intervention cannot change the next turn's history.

State that carries inside a family on the baseline:

- Delivered exchanges.
- Host question referents (`question_referents` on the session).
- The active referent id.
- The locked prior plan, including the relationship the model actually committed.

## Required shapes present

| Shape | Where it is exercised |
|---|---|
| Several recent referents | Families with two public facts before a correction or a "which one" follow-up |
| More than one NPC | c01, c03, c04, c05, c06, c07, c08, c09, c10, c12 |
| Corrected questions | 25 correction-tagged turns |
| Partial answers | 15 partial-tagged turns |
| Follow-up after uncertainty | Follow-ups whose prior baseline answer is unknown or a refusal |
| Follow-up after a correction | Later turns in the same family |
| Source attribution | "Who told you" / "how do you know" follow-ups |
| Role reversal | Questions whose related source swaps speaker and recipient |
| Topic change | A later direct question about a different public fact |
| Ambiguous pronoun | Clarification turns with more than one live referent |

## Binding consequence

A correction's stored proposition is whatever the baseline model committed, not the gold proposition. Supplying a gold role delta can still fail `bind()` when that stored proposition does not match. I8 replaces the locked plan after `bind()`, so it measures expression given an authorized line. I2 and I9 still pass through `bind()`.

`referenced_answer_unknown` stops a source-attribution follow-up when the prior answer status is unknown or refusal. That is host behavior, not a second semantic sample.
