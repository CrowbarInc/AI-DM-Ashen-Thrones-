# 02 — Structured Output Requirements

PR-PLAY-06 · 2026-10-28 America/New_York · evidence_scope: structural_only.

The provider must emit JSON with declared_claims (list) and narration (nonempty
string). Each declaration is audited against gm_resolution_decision claims,
relation/authority and authored corpus; parsing alone grants no acceptance.
The scene_opening response must still satisfy opening-specific completion and
final emission gates. Empty declarations are legal for these existing accepted
controls; no declaration requirement was weakened. No schema change.

| Fixture | Serialized chars/ASCII bytes | Estimated tokens | Envelope/escaping chars | Narration chars | Declaration chars | Declarations | Host HTTP |
|---|---:|---:|---:|---:|---:|---:|---:|
| declarations | 2142 | 536 | 38 | 458 | 1646 | 8 | 200 |
| minimal | 626 | 157 | 38 | 91 | 497 | 3 | 200 |
| multiple_details | 2142 | 536 | 38 | 458 | 1646 | 8 | 200 |
| npc | 2142 | 536 | 38 | 458 | 1646 | 8 | 200 |
| over_600 | 3726 | 932 | 38 | 458 | 3230 | 8 | 200 |
| rich | 3726 | 932 | 38 | 458 | 3230 | 8 | 200 |
| typical | 190 | 48 | 38 | 150 | 2 | 0 | 200 |

All token values are ceil(characters/4) ESTIMATES. tiktoken is unavailable locally;
no tokenizer/model download was attempted. Synthetic SDK usage fields deliberately
use these estimates to exercise accounting; they are not actual provider usage.
Raw fixtures, measurements, requests and lifecycle observations are included.

Reuse: MARKET_NARRATION and VALID_NARRATION from PR-PLAY-04; typical text from
test_start_campaign_api; declarations use that test's claim projection. Rich and
over_600 reuse the existing _decl helper from structured-realization tests, with
the same authorized narration and eight real source_claim_id references. They
are deliberately the same response representation under two matrix labels,
not independent samples. Richness here is declaration detail. Multi-detail, NPC
and declaration cases also share the existing gate fixture; no new lore.

Smallest accepted sampled output: 190 chars (~48 tokens); market opening with
three explicit declarations: 626 chars (~157). These are fixture minima, not a
proof of the mathematically shortest valid opening. The serialized empty shell
{"declared_claims": [], "narration": ""} occupies 38 chars and is invalid until
nonempty adequate scene text exists. Eight short declarations plus narration
occupy 2142 chars (~536); fuller supported declarations occupy 3726 (~932).
Historical verbose 1258-char narration parses but fails gameplay authority; see
historical_rich_rejection.json. More tokens do not make that fixture acceptable.

Practical allowance: 3000, about 3.2x the richest sampled estimate, accommodates
JSON keys/IDs, declarations, narration and serialization/generation variability.
It is a bounded trial hypothesis, not proof of live adequacy or token-exact fit.
The output allowance does not require longer narration; prompts/style unchanged.

Production source map (all functions retain existing ownership):

| Boundary | Module/function | Input → output | Relevant configuration | Existing/new tests |
|---|---|---|---|---|
| Start | game.api.start_campaign / _start_campaign_after_admission | player Request + initialized stores → one opening result/failure | request gate, persistence lock, isolated ASHEN_DATA_DIR | PR-PLAY-04 matrix, start_campaign_api |
| Opening seed | game.api._opening_scene_normalized_action_and_resolution / _build_opening_scene_resolution | scene + internal bootstrap → scene_opening resolution | existing scene content | PR-PLAY-04, opening seam |
| Prompt | game.gm.build_messages / collect_narration_context_call_kwargs; game.prompt_context.build_narration_context | state + resolution → system/user JSON messages | existing prompt profile/policy | captured two-scene inventory, AST identity |
| Response type | game.api._derive_response_type_contract_for_turn / _attach_response_type_contract_to_resolution | action/resolution → required scene_opening | response_type_contract.required_response_type | opening/type tests |
| Realization | game.gm_resolution_decision.audit_realization_envelope_against_decision | declarations + decision + corpus → authority audit | unchanged structured realization contract | structured envelope suite |
| Provider request | game.gm.call_gpt; game.provider_budget.admit_request / RequestAttempt.dispatch | messages/route → admitted SDK kwargs or refusal | existing model, retries, aggregate reservations | PR-PLAY-02, accounting, new budget selection |
| Limit | game.gm._requested_response_type_from_messages / _opening_max_output_tokens | host response contract/env → 3000 opening allowance | ASHEN_OPENING_MAX_OUTPUT_TOKENS 1..4096 | new bounded/config tests |
| Extraction | game.gm._extract_provider_response_text | SDK output_text or content segments → text + extraction observations | diagnostics flag only affects recording | PR-PLAY-05 native SDK/segment controls |
| Parsing | game.gm._safe_json; structured_player_output.classify_model_output | JSON/fenced JSON → normalized response or contract failure | existing provider envelope selection | PR-PLAY-05 + structured suite |
| Envelope/acceptance | immutable_valid_response.run_preserve_if_valid; game.api._opening_response_rejection | parsed/audited opening → accepted seal or explicit failure | unchanged opening/type/authority gates | PR-PLAY-04, invalid/incomplete controls |
| Commit | game.api._complete_opening_turn_persistence_like_chat / _restore_opening_baseline | accepted opening + baseline → persisted single progression or rollback | existing storage/world/faction owners | PR-PLAY-04 concurrency/repeat/retry/persistence |

The map names current functions; historical PR-PLAY-03 line numbers are not used
as current source locations. Raw current source snapshot is in the review ZIP.
