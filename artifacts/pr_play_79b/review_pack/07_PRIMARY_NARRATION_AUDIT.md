# Primary narration audit

Primary narration is the large gm.call_gpt primary_turn prompt. deterministic_provider_skip_line now asks publication_contract.narration_skip before that call.

Skip when the contract is FINAL_ENGINE_RESPONSE, CLARIFICATION_REQUIRED, UNSUPPORTED_ACTION, or FAILURE and a sentence exists. The legacy skip_primary_narration flag still skips. already_searched is a final examination sentence even when the flag was forgotten. ADJUDICATION_RESULT may take one bounded expression, then the mechanical line if that expression is rejected. It does not call primary narration.

Nonempty text with skip_primary_narration false and no completing contract still uses the provider.
