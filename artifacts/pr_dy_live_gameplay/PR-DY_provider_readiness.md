# PR-DY provider readiness

Live calls started only after the disabled-provider preflight in `preflight_http.json`.

## Controls used for the live server

- `ASHEN_DATA_DIR` = `artifacts/pr_dy_live_gameplay/disposable_data`
- `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1` so startup itself does not spend a call
- `ASHEN_DISABLE_PROVIDER_RETRIES=1`
- `ASHEN_PIN_PROVIDER_MODEL=gpt-4.1-mini`
- `ASHEN_PROVIDER_REQUEST_LIMIT=6`
- `ASHEN_PROVIDER_INPUT_TOKEN_LIMIT=8000`
- `ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT=2000`
- `ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT=10000`
- `ASHEN_NARRATION_MAX_OUTPUT_TOKENS=600`
- `ASHEN_PROVIDER_USAGE_PATH` = `artifacts/pr_dy_live_gameplay/provider_usage.jsonl`
- `ENABLE_MODEL_ROUTING=0`
- `ASHEN_DISABLE_PROVIDER_CALLS` and `ASHEN_DISABLE_LIVE_INTERPRETATION` unset

Configured model: `gpt-4.1-mini`. Returned model on every sent call: `gpt-4.1-mini-2025-04-14`. No model switch was accepted. A mismatch would poison further calls.

## What one turn tries to spend

| Step | When | Sent during this run |
| --- | --- | --- |
| Interpretation | AUTO or explicit IC, one structured completion | Yes, three times |
| Narration | After a committed gameplay or opening resolution | No. Refused before send |
| OOC assistance | Not a separate live call. AUTO OOC is the interpretation call. Explicit OOC makes none | Explicit OOC: zero |
| Retries | Disabled | Zero |

Narration prompts estimate above 8,000 input tokens. `call_gpt` records `sent: false` and `refusal: input-token ceiling` and does not transmit them. Those rows have no request id and no token counts. Token usage for refused calls is unavailable.

## Actual sent usage

| # | Purpose | Input | Output | Total | Request id |
| --- | --- | --- | --- | --- | --- |
| 2 | interpretation | 700 | 187 | 887 | resp_07ddedbe052db274006acb7f72a2cc87d2bdb4de591b070f20 |
| 4 | interpretation | 724 | 198 | 922 | resp_0b0a7fbd1d15febf006acb7f921bac87d1a9c2920f68597a27 |
| 6 | interpretation | 749 | 198 | 947 | resp_0c2290f0646bf269006acb7fbef62c87d2bbbe561849eb46c1 |

Sent totals: 3 requests, input 2173, output 583, total 2756.

Ledger rows: 6. Sent rows: 3. Refused before send: 3 (opening narration, inspect narration, ask narration). All three sent calls were under the per-call output cap of 320. The run stayed inside 6 requests, 8,000 input, 2,000 output, and 10,000 total.

No automatic retry ran. No background provider call was added. The explicit OOC message added no ledger row.

Raw rows are in `provider_usage.jsonl` and `provider_usage.csv`.
