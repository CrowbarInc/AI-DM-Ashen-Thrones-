PR-PLAY-05 · 2026-10-27 (America/New_York) · evidence_scope: structural_only. Synthetic provider controls; no live generation or gameplay-quality claim.

# 05 — Diagnostic Validation Matrix

The final integrated suite runs real production call_gpt, RequestAttempt admission/dispatch, extraction, `_safe_json`, claim/response validation, API endpoint functions and persistence. Only OpenAI transport is replaced with synthetic SDK objects; the standard test guard prevents live calls. This is not a standalone classifier test. The separate HTTP placeholder control exercises actual TestClient transport.

| Control | Result / HTTP | Extraction, parse, validation evidence |
|---|---|---|
| D1 valid opening envelope | 200 accepted | text extracted; JSON/envelope/structured valid; final accepted; committed once |
| D2 valid JSON, no envelope | 422 | JSON true, envelope false; missing_structured_envelope diagnostic; actual parser malformed_envelope rejection preserved |
| D3 malformed JSON | 422 | JSON false; json_parse_failure; no progression |
| D4 empty text | 422 | extracted empty; empty_provider_content; no progression |
| D5 SDK message content instead of convenience attribute | 200 | typed output_text segment fields recovered; no object stringification; final accepted |
| D6 truncated structured JSON | 422 | JSON false; usage reaches 600; explicit status incomplete/reason max_output_tokens records provider-reported exhaustion |
| D7 provider exception | 422 | provider_error; no invented finish/request/usage metadata; one consumed admission |
| D8 missing usage | 200 | all token fields null; accounting correctly marks usage unavailable/stops future admission; no invented zeros |
| D9 missing finish metadata | 200 | provider_status/finish_reason null; no inferred completion reason |
| D10 output limit reached, completed JSON lacking envelope | 422 | output_limit_reached true, possible_output_truncation true, provider_output_limit_exhausted null; primary cause remains missing envelope |

Additional controls cover refusal/unextractable segments (extraction_failure), structurally invalid declarations (structured_validation_failure), literal `[Narration]`, default-off events, SDK repr prohibition and the actual installed OpenAI Response/ResponseOutputMessage/ResponseOutputText classes with two segments and distinct request/response IDs. D5's shape uses only the SDK's supported message/output_text fields. Native SDK validation confirms the same extraction/parser boundary, without network.

Each generated response control verifies its endpoint status, player text/error, acceptance, campaign latch, turn/time/factions, one admission, persistent gameplay values and ledger export/reconciliation. Synthetic narration/exception/refusal sentinels are absent from diagnostic ledger output. The existing accounting inspector reports exactly one admission even with diagnostic rows present.

`artifacts/pr_play_05/diagnostics/D1..D10.json` contain lifecycle, diagnostic and state observations. Other named JSONs retain negative, retry, repeated, concurrency and budget controls. `integrated.txt/xml` is the final executable result. No assertion claims the original live model's text, statistical reliability, or confirmed historical truncation.
