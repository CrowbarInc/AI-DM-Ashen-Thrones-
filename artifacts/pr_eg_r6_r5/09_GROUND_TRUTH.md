# 09 — Ground Truth

Every turn was labeled before the provider ran. Labels live in `experiments/pr_eg_r6_r5/corpus.py` and in `frozen_corpus.json`. The engine output is not an input to those labels.

## Fields fixed before execution

| Field | Use |
|---|---|
| `act` | Intended conversational operation |
| `addressee` | Intended speaker. Empty when the addressee is genuinely ambiguous. |
| `referent` | `new`, `previous`, or a text needle for an earlier question |
| `predicate`, `roles`, `proposition` | Intended relationship, named roles, qualifiers, missing argument |
| `eligible_source_ids` | Sources the addressed NPC may use. Never a secret id. |
| `source_propositions` | Propositions copied from those eligible sources |
| `correspondence` | `direct`, `partial`, `related_but_nonanswer`, `unrelated`, or `unknown` per source id |
| `answer_class` | DIRECT, PARTIAL, RELATED_NONANSWER, UNKNOWN, CLARIFICATION_REQUIRED, RESTRICTED |
| `allowed` | Phrases a sufficient public answer must be able to say |
| `forbidden` | Phrases that must not appear, including restricted fixture values |
| `distractors` | Related facts that do not answer this question |
| `hedge_any` | Required epistemic wording for rumor or belief |
| `clarification_required` | Whether a clarification is the correct response |

## Rules used while authoring

- A DIRECT label has a public source that states the allowed fact.
- A PARTIAL label has a public source that states only part of the request.
- An UNKNOWN label has no eligible source.
- A RESTRICTED label has a secret topic and an empty eligible set.
- A CLARIFICATION_REQUIRED label has more than one live referent or addressee and no unique gold target.
- Correspondence `direct` is not assigned to a secret topic. `correspondence_for_text` refuses secret topics.
- `authorized_fact` returns a line only for DIRECT or PARTIAL when `npc_source_permitted` is true.

## Independence

The scorer compares delivered text with these fields. It does not treat `response_kind`, selected source ids, or the model's act as correct. Where the rubric and a human reader could disagree, the human review packet keeps both texts and marks review pending.
