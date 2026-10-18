# 19 — Complexity and Maintainability

PR-EG-R5 · 2026-10-17 · investigation only

Counts below are reproducible static inventory, not dynamic execution counts. AST branch sites count If, IfExp, Match and ExceptHandler in top-level functions including their nested code. This does not count loops as decisions or prove reachability.

| Module | Top-level functions | AST conditional/exception sites |
|---|---:|---:|
| conversational_orchestration | 66 | 304 |
| conversational_continuity | 32 | 148 |
| live_chat_interpretation | 15 | 45 |
| player_interpretation_bridge | 6 | 58 |
| ordinary_semantic_ownership | 19 | 121 |
| interaction_context | 163 | 1025 |
| social | 89 | 668 |
| dialogue_authority | 21 | 114 |
| expressive_dialogue | 38 | 133 |
| immutable_valid_response | 52 | 319 |
| gm_retry | 54 | 537 |

Operational lower-bound inventory: at least six interpretation/grounding families (deterministic orchestration, continuity, live schema/adaptation, bridge, ordinary ownership, legacy routing/parser); at least six response-selection families (orchestration, social plan, host speech, expression fallback, retry fallback, final adoption); nine distinct fallback trigger families in report 13. At least five modules influence addressee (continuity, orchestration, bridge, ordinary ownership, interaction_context) and four influence subject (continuity, orchestration, social, dialogue_authority). Nine conversational memory/projection families are listed separately from the per-response seal in report 11. These are grouped architectural counts, not exact reachable branch totals.

Typical observed calls: zero for deterministic replies; one for expression; one for interpretation before a host response; interpretation plus expression can require two; historical strict-social fallback reaches three narration/retry calls. Static code permits alternate combinations; the observed sample is not a universal upper bound.

Compatibility debt is concrete: live_chat_interpretation imports experimental adapter/prompt packages; communication and legacy operation/mode coexist; semantic_interpreter also supplies older proposal machinery; preserved helper functions and final-emission stacks remain but cannot rewrite sealed speech. Some branches are disabled by flags or skipped after adoption; no branch is declared globally dead without call-path proof. The recommendation removes superseded semantic selectors slice by slice while retaining necessary enforcement, rather than equating fewer lines with a better architecture.
