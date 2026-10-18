# PR-BY retry path audit

The selected envelope is stored on the parsed candidate as `metadata.provider_response_contract`. `run_preserve_if_valid` passes that stored value into `regeneration_feedback`. The live regeneration entry in `game/api.py` (`_regenerate_once`) appends that feedback to the original provider messages, so the system prompt stays the prompt chosen before attempt 1.

## Entry points

1. `game/immutable_valid_response.py` `run_preserve_if_valid` converts a hard validation failure into `regeneration_feedback`, then calls the regenerate callback once.
2. `regeneration_feedback` chooses the prose for `structured_contract_failure`, `ungrounded_authoritative_rule`, `unauthorized_resolution_decision_fact`, `wrong_interlocutor` / `unsolicited_npc_speech`, or the generic remainder.
3. `_with_retry_authority` appends `retry_authority_context` from `game/gm_resolution_decision.py`.
4. `game/api.py` `_regenerate_once` sends that string as the next user message on the original message list.
5. After a sealed response, `game/api.py` may run `build_retry_prompt_for_failure` in `game/gm_retry.py` for a later validator class. That path was not the PR-BX failure. Hard narration rejection is sealed inside `run_preserve_if_valid` before that loop.

## Classification

A. Structured-only and correctly guarded.
B. Contract-aware.
C. Unsafe generic structured assumption. Repaired where it was reachable from narration-only retries.
D. Unrelated to retry contract selection.

| Occurrence | Class | Reachable from narration-only retry | Disposition |
| --- | --- | --- | --- |
| `regeneration_feedback` structured_contract_failure structured branch (`declared_claims and narration`) | A | No. The narration-only branch is separate. | Kept. |
| `regeneration_feedback` structured_contract_failure narration-only branch | B | Yes. | Already narration-only. Schema attachment was the leak; see below. |
| `regeneration_feedback` `unauthorized_resolution_decision_fact` wording "same structured envelope with declared_claims plus narration" | C | Yes. This is the PR-BX string. | Repaired. Narration-only uses the narration-only JSON shape. Structured wording kept. |
| `regeneration_feedback` generic fallback "structured envelope shape: declared_claims plus narration" | C | Yes, for every other hard reason, including malformed narration and consequential invention. | Repaired. Narration-only generic text no longer names declarations. |
| `ungrounded_authoritative_rule` and interlocutor prose | B after repair | Yes. The prose did not name declarations, but the shared schema did. | Shape instruction is narration-only when that envelope is selected. |
| `retry_authority_context` `structured_envelope_schema` containing `declared_claims` | C | Yes. Every resolution-backed retry attached it, including narration-only. | Repaired. Omitted when the stored envelope is `narration_only`. |
| `retry_authority_context` `rejected_declarations` | C | Yes. Declaration-correction payload on a contract that has no declaration channel. | Omitted for narration-only. Kept for structured retries. |
| `narration_only_response_schema` | B | Yes. | Added. Keys are `narration` only. |
| `run_preserve_if_valid` reading `metadata.provider_response_contract` | B | Yes. | Consumes the envelope stored at parse time. Does not reselect. |
| `api.py` `_regenerate_once` appending feedback to the original messages | B | Yes. | Does not build a new system contract. |
| `gm_retry.py` "Return the same JSON shape." | B | Only after a response leaves hard validation unsealed. It does not name `declared_claims` or attach `structured_envelope_schema`. | Left unchanged. It preserves the JSON shape already in the original messages. |
| Parser rejection `unexpected_declared_claims` | D | The parser runs before retry. | Unchanged. Smuggled declarations stay rejected. |
| Declaration validation and narration validation | D | They produce the failure reason. | Unchanged. |
| `SYSTEM_PROMPT` structured response contract | A | No. Narration-only turns use `NARRATION_ONLY_SYSTEM_PROMPT`. | Unchanged. |
| `select_provider_response_envelope` | D for this cycle | Not called from retry construction. | Unchanged. |

No remaining C occurrence is reachable from a narration-only retry.

## What a retry may still change

Corrective narration guidance, the named validation reason, and the attempt record. It does not change `response_operation`, `declaration_expectation`, consequential realization, the selected envelope, the authority owner, or the response contract family.
