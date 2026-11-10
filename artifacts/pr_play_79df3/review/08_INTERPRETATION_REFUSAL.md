# Interpretation Refusal

Only operational failures receive the operational class.

| Pathway | Class | Provider request | Gameplay event |
| --- | --- | --- | --- |
| Admission refuses before interpretation | Operational, stage `provider_admission` | Not sent | None |
| Provider `create` raises `TimeoutError` | Operational, stage `interpretation_service`, reason `provider_failure` | Sent, count 1 | None |
| Stub model does not match `gpt-4.1-mini` | Operational, stage `interpretation_service`, reason `model_mismatch` | Sent, count 1 | None |
| Malformed interpretation JSON | Gameplay | Fixture | Existing gameplay event. Pointer does not move. |
| Context leak | Gameplay | Fixture | Existing gameplay event |
| Empty text clarification | Gameplay | Not required | Existing gameplay event |
| “I fly to the moon.” | Gameplay unsupported action | Not required | Existing gameplay event |
| Rejected expression with grounded fallback | Completed gameplay | Fixture | Fallback event, `dialogue_accepted` false |

The exception path records the exception type, not the exception text. The development case asserts that a planted “secret prompt” string is absent from the HTTP body.

A grounded fallback is not an operational refusal. A valid clarification is not an operational refusal.
