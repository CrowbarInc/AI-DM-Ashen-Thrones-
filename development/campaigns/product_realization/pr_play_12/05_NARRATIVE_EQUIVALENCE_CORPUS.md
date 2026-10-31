# 05 — Narrative Equivalence Corpus

PR-PLAY-12 · 2026-10-31 America/New_York. Offline investigation and isolated prototypes only.

E1–E20 execute the production opening pipeline once each using synthetic SDK transport, the latest captured baseline documents and the same nine valid structured declarations. Only E19 adds a forged declaration with no valid source. For other cases prose varies while declarations remain valid, deliberately exposing the declaration-to-prose boundary. Cases are synthetic boundary/stress controls, not human gameplay or independent held-out evidence.

All input text, interpretations and exact delivered text are in corpus.json; raw nested audits and API output are in results/E*.json. In particular, opening HTTP status, semantic hard-validity and final emitted text are separate columns. The direct prototype experiments are separate from these production results.

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


Interpretation judgments: E2 moves the same location clause without introducing a barrel or actor. E3 substitutes informal gossip for rumors without upgrading reliability; E4 preserves the warning and present missing-patrol status. E5 adds already plausible rain-on-stone texture, turn-local and without mechanics. E6 adds a second open gate, a navigable spatial affordance outside incidental permission. E7 establishes corruption; E14 upgrades rumors to reliable patrol-specific intelligence. Neither is a harmless synonym. E16 joins two known independent facts without asserting a causal relationship. E18 repeats a fact without increasing authority.

E17 is an omission probe, not a proven false-negative violation: all nine model declarations request MUST_STATE, but model role flags are not themselves an engine obligation that every sentence must appear. The current decision also marks many alternative/journal/runtime rows MUST_STATE without a simple globally executable completeness requirement. The observed acceptance shows this ambiguity. The next contract must select explicit required public anchors instead of treating every generated role string as an obligation.

Observed false-positive candidates: E3 and E4. Observed semantic-stage false-negative candidates: E7, E8, E9, E10, E11, E12, E15 and E20. E7 and E11 are replaced downstream with grounded rain/gate fallback text; they are **not final-delivery failures** for these exact strings. Final-delivery false-negative candidates are E8, E9, E10, E12, E15 and E20. E11 uses an exact hidden fact in the restored scene, not a fabricated secret. No claim of exhaustive paraphrased-secret protection follows.

All twenty runs preserve the six domain comparisons recorded in state_protection. Rejected openings preserve the normalized entire captured gameplay document set and transcript. Accepted controls produce ordinary initialization progression. No prose is injected as accepted state and no hard-valid assertion was changed to make the corpus pass. Tests assert the evidence mechanics and containment, then report actual semantic failures rather than pretending the desired safe outcomes already hold.
