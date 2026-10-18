# PR-CV Effective Request Inventory

All entries are deterministic reconstructions from saved fixture state using `game.gm.build_messages`; live provider calls: 0.

| Request | Effective Envelope | System Scope | Payload/Recipe Scope | Authority Notes |
|---|---|---|---|---|
| A. Harmless NPC preference (P2 baker preference) | `narration_only` | Compact narration-only system prompt with exact `{"narration": ...}` schema. | `decision_facing_answer_recipe.turn_operation.response_operation = incidental_dialogue`; `declaration_expectation = reply_not_required`. | Ordinary reply may be narration only; durable preference/history is not authorized. |
| B. Authored NPC fact question | Structured when consequential/authored claims must be realized. | Full structured envelope with declaration lane. | `gm_resolution_decision.realization_claims` and recipe required content govern allowed claims. | Existing authored-answer tests remain 14 passed / 2 inherited failed. |
| C. Narration-only incidental dialogue | `narration_only` | No `declared_claims` exposed. | Recipe states reply belongs in narration and is not a new authored world fact. | Parser rejects declaration smuggling. |
| D. Ordinary observation | Structured or direct-observation projection depending on decision/contract shape. | Structured lane when declaration channel exposed. | Recipe can project `direct_observation` and `observations_only`. | No new inference or world fact. |
| E. Consequential social action | Structured. | Full declaration lane. | `select_provider_response_envelope` chooses structured when consequential realization is required. | Declarations are validated against `gm_resolution_decision`. |
| F. Exploration | Structured for interpretation/hypothesis/consequential results; direct observations remain constrained. | Full structured schema where needed. | Recipe projects bounded interpretation or direct observation from decision shape. | Inference must remain qualified. |
| G. Combat | Not changed in PR-CV. | Existing app mechanics and authority paths remain untouched. | No resolver selection/state commitment changes. | Out of repair scope; no evidence of PR-CV regression. |

