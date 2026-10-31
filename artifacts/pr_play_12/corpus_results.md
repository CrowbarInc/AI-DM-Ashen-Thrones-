| ID | Interpretation / justification | Current semantics / opening | Reason | Delivered unchanged | FP candidate | FN semantics / delivery | State checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | supported; Exact authored statement. | True / 200 | [] | True | False | False / False | True |
| E2 | supported; Word order preserves actor, exchange, location. | True / 200 | [] | True | False | False / False | True |
| E3 | supported; Gossip is used for informal rumors; no reliability assertion. | False / 422 | ['unauthorized_resolution_decision_fact'] | False | True | False / False | True |
| E4 | supported; Present perfect missing status preserves posting and patrol status. | False / 422 | ['unauthorized_resolution_decision_fact'] | False | True | False / False | True |
| E5 | incidental; Turn-local sensory rain grounded by wet gate scene; no transition. | True / 200 | [] | True | False | False / False | True |
| E6 | unsupported; New navigable topology and opening status; beyond sensory permission. | False / 422 | ['unauthorized_resolution_decision_fact'] | False | False | False / False | True |
| E7 | unsupported; New NPC corruption and hidden transaction. | True / 200 | [] | False | False | True / False | True |
| E8 | unsupported; No player action or resolver success exists. | True / 200 | [] | True | False | True / True | True |
| E9 | unsupported; New death without combat adjudication. | True / 200 | [] | True | False | True / True | True |
| E10 | unsupported; Arrival requires transition authority. | True / 200 | [] | True | False | True / True | True |
| E11 | hidden; Exact scene hidden fact, no reveal receipt. | True / 200 | [] | False | False | True / False | True |
| E12 | unsupported; Unresolved hook turned into completion. | True / 200 | [] | True | False | True / True | True |
| E13 | contradiction; Contradicts active authored guards. | False / 422 | ['unauthorized_resolution_decision_fact'] | False | False | False / False | True |
| E14 | ambiguous; Rumors become reliable and patrol specific; do not accept as equivalence. | False / 422 | ['unauthorized_resolution_decision_fact'] | False | False | False / False | True |
| E15 | unsupported; Supported fact plus unauthorized resource change. | True / 200 | [] | True | False | True / True | True |
| E16 | supported; Conjoins two separate supported statements, no causality. | True / 200 | [] | True | False | False / False | True |
| E17 | omission; Omits all claimed MUST_STATE facts; test obligation enforcement, not invented fact. | True / 200 | [] | True | False | False / False | True |
| E18 | supported; Duplication adds no authority. | True / 200 | [] | True | False | False / False | True |
| E19 | false_provenance; New declaration with forged authored provenance, no source match. | False / 422 | ['unauthorized_resolution_decision_fact'] | False | False | False / False | True |
| E20 | unsupported; Unmodified valid declarations with unsupported resource prose. | True / 200 | [] | True | False | True / True | True |
