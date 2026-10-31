PR-PLAY-05 · 2026-10-27 (America/New_York) · evidence_scope: structural_only. Synthetic provider controls; no live generation or gameplay-quality claim.

# 04 — Provider Diagnostic Implementation

The existing provider budget ledger remains the single diagnostic persistence owner. No parallel logger, gameplay schema or world-state authority was added. Opt in with ASHEN_GENERATION_DIAGNOSTICS=1 and the existing ASHEN_PROVIDER_USAGE_PATH/accounting settings. Default operation records no new diagnostic events; raw provider content is never stored by this mode.

## Production path and owners

1. API narration construction builds messages using the existing route, response policy, authority decision and provider-envelope projection.
2. gm.call_gpt selects the existing model, host-retry guard and budget admission. OpenAI construction retains key/timeout and existing sdk_retry_options.
3. Request uses existing model/input; accounting mode retains max_output_tokens=600. No API response-format setting is added; envelope instructions are already in the prompt. No prompt or schema edit.
4. RequestAttempt.dispatch performs the existing durable admission/dispatch/completion accounting around client.responses.create. Token accounting precedes parser work.
5. `_extract_provider_response_text` reads output_text, with fallback to SDK output message/output_text segments. It replaces unsafe object stringification with supported content extraction. Other representations fail closed; refusal content is not treated as narration.
6. Existing `_safe_json` / classify_model_output performs the actual required structured parse. Diagnostic syntax inspection separately records whether JSON parses (including the parser's supported fenced JSON). A JSON object alone does not establish the required envelope.
7. Existing decision/claim validation, recovery, immutable adoption and final emission execute unchanged. Structural parsing does not grant gameplay authority.
8. Existing `_opening_response_rejection` governs final opening acceptance. The diagnostic observer records its rejection and recovery provenance. `_OpeningScope.close` records commit disposition after commit or rollback in the same ledger.

## Changed functions and fields

gm.py: new extraction/structural observation helpers; call_gpt attaches structural ledger events after real extraction and parse, and sanitized provider_error observations on exception. provider_budget.py: opt-in helpers and an ephemeral ContextVar correlate provider attempts with one opening operation; existing _append supplies durable writes. api.py: opening scope begin/end, final validation observation, budget-admission and repeated-start dispositions. tools/atgb/accounting.py: explicitly recognizes diagnostic observations without altering admission/completion state; still rejects unknown stages/unknown attempt references and reconciles the complete event list.

Provider-response events include logical operation, requested response type, configured provider model (returned model remains in completion), SDK request ID when exposed as _request_id, distinct response ID, provider status, incomplete/finish reason, requested output cap, reported input/output/total tokens, usage-at-limit flag, segment count, content/extraction presence, extraction source/length/empty status, JSON status, known envelope keys, expected-envelope presence, parser form, parser/structured result and rejection reason. Null means unavailable, not zero.

Categories include provider_error, empty_provider_content, extraction_failure, json_parse_failure, missing_structured_envelope, structured_validation_failure and accepted_structured_response. A separate possible_output_truncation flag requires limit-reaching invalid output; authoritative provider max_output_tokens exhaustion is recorded separately. It never converts usage equality into proven truncation or suppresses the actual failure category.

Opening-outcome events record accepted_structured_opening or opening_rejected, final validation, recovery provenance, rejection reason and gameplay_committed. Admission refusal records provider_budget_refused. Related events share opening_attempt_id; provider events also carry attempt_id. No provider operation is added. An interrupted process can lack an outcome: that is unknown and must be reconciled with snapshots.

## Safety and export

Only explicit structural fields are constructed: no raw SDK repr, request payload, narration, declarations, key, header, exception message, arbitrary JSON keys or environment dump. Known envelope keys and safe identifier tokens only; unknown finish values are unavailable. Provider exception diagnostic contains a category without the exception message. Existing unrelated application logging behavior was not redesigned.

Ledger I/O failure stops future admissions and does not retrospectively turn committed gameplay into a failed opening. Diagnostic writes use existing lock/fsync. Default-off behavior is tested. Export is the existing provider_usage.jsonl plus existing campaign snapshots, copied/ZIPped with PowerShell; the ledger reader now tolerates these explicit observations without double-counting tokens/attempts. Unknown raw-output ambiguity remains a limitation; no unrestricted raw-capture mode was introduced.
