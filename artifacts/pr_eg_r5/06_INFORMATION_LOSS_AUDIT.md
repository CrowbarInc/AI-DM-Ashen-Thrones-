# 06 — Information Loss Audit

PR-EG-R5 · 2026-10-17 · investigation only

| Turn | Player meaning | Provider/structured meaning | Host operation and subject | Source / delivery | Lost or added meaning |
|---|---|---|---|---|---|
| R4 B1 | who controls docking | no interpretation call retained | ASK Nara; explain harbor operations; general | bell; direct answer | requested responsible agent reduced to topic overlap |
| R4 B2 | reject bell, ask schedule manager | provider bypassed | conversational correction → answer old statement | bell again | rejected proposition mistaken for requested proposition |
| R4 playful4 | two NPC questions | provider: two ASK targets, MIXED | communication_before_execution | condition not established | host adds action-condition requirement absent from request |
| R4 casual14 | address Mara about local traffic | provider bypassed | movement_question | no route to sentence tail | clarification phrase treated as destination |
| R4-R1 primary6 | reason for previously stated morning preference | historical lookup finds morning; no new interpretation | ASK; subject=time, opinion | deterministic evening | resolved antecedent not transferred into authority |
| R4-R1 primary12 | GM recall of Mara’s gate speech | deterministic ambiguity | GM clarification | Mara or Runner? | proposition uncertainty inflated into speaker uncertainty |

[game/dialogue_authority.py:126](../../game/dialogue_authority.py#L126) takes the first three non-stopword tokens; it is not a representation of predicate, negation, requested relation, correction or alternative questions. Raw player_input is still carried into adoption, so the problem is premature commitment and inconsistent consumption rather than wholesale deletion. Provider proposals are also imperfect: MIXED in playful4 is semantically too broad. Proposed design must retain original wording, spans supporting act/addressee/subject, correction linkage, uncertainties, and candidate source IDs through the final plan.

Independent probes show a second inconsistency: orchard shift and cause questions are classified directly_answers by dialogue_authority even when social.authored_answer_sufficient_for_question rejects them. The lexical systems do not even share one relevance decision. See [controlled_probes.json](controlled_probes.json).
