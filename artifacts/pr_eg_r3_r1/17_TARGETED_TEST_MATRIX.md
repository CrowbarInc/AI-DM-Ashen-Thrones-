# 17 — Targeted Test Matrix

All of the following passed in `final_relevant_junit_confirm.xml`.

| Id | Test | What is inspected |
| --- | --- | --- |
| T01–T02 | `test_t01_t02_authorized_preference_explanation_allows_harmless_grammar` | Contract premise, historical "everything" sentence, adopted player text |
| T03–T06 | `test_t03_t06_unauthorized_explanations_are_rejected` | External, relationship, security, and promise candidates |
| T07–T10 | `test_t07_t10_paraphrase_entity_alias_and_rumor` | Safe paraphrase, rename, alias, rumor hedge |
| T11–T18 | `test_t11_t18_proposition_identity_recall_and_ambiguity` | Shared id, separate propositions, exact recall, speakers, ambiguity |
| T19–T23 | `test_t19_t23_answer_sufficiency_and_refusal` | Direct, partial, unrelated, unknown, nonbinding refusal |
| T24–T28 | `test_t24_t28_mixed_rejection_persistence_and_no_canonical_mutation` | Mixed candidate, history exclusion, save/load, no world mutation |
| T29–T30 | `test_t29_t30_relevant_modules_keep_single_expression_call` | One expression call, no retry loop |
| Degree | `test_degree_grammar_can_modify_an_authorized_feeling` | "more peaceful" adopted; "the world" rejected |
| Premise | `test_unestablished_preference_does_not_invent_a_premise` | No contract without an established preference |
| Partial | `test_partial_fact_reaches_the_player_without_topic_promotion` | Player line, topic not revealed, world updates empty |
| Holdouts | `test_frozen_holdout` | R1H01–R1H10 |
| Production | `test_production_chat_delivers_characterization` | Stubbed `/api/chat` delivers the historical sentence and survives save/load |

The production test stubs the provider. The fresh conversations in reports 19 and 20 do not.
