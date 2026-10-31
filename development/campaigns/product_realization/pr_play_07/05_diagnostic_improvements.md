# 05 — Diagnostic Improvements

PR-PLAY-07 · 2026-10-29 America/New_York. Synthetic-provider evidence only.

The existing generation_diagnostic ledger remains the event infrastructure. Opening ID
correlates provider_response, opening_semantics, opening_validation, opening_response_capture
and opening_outcome. Provider attempt/status, logical operation/type, parser validity,
independent final validation, semantic reasons/source/reason, field presence/length/claim
count, rejection stage and actual commit are separate. Outcome runs after commit/rollback.
Old structured_validation_result conflation is removed; final_validation_passed is separate.

First semantics event identifies _check and actual hard reasons; second identifies _finish,
adoption provenance/reason. API opening_validation identifies independent final predicate.
Outcome retains semantic source and rejection_stage=API acceptance. nonresolution_origin
application means host selected safety fallback; model means unchanged initial_generation
plus the exact generic fallback marker. This does not infer intent for every refusal;
inspect preserved response content for other cases. Actual stub records/schema examples:
artifacts/pr_play_07/diagnostic_examples.json.

ASHEN_OPENING_RESPONSE_CAPTURE=1 is separate, disabled by default. Requires generation
diagnostics, active accounting/opening scope, both explicit retry-disable flags, absolute
isolated ASHEN_DATA_DIR matching active storage and a noncanonical data directory. Only
opening GM output is collected: no prompts, SDK object dumps, credentials, headers or
unrelated request/configuration. JSON is parsed independently from original text before
application normalization/recovery; whole JSON fences supported. All original JSON fields
and values, including differing narration/player_facing_text, declarations and proposals,
remain preserved. No silent rewrite/redaction.

Files: <isolated-root>/opening_response_evidence/<opening-ID>-N.json; sensitive_game_content
marker and provider linkage. Six artifacts per scope maximum; each <=65,536 bytes.
Oversize explicitly marks truncated and preserves an 8,000-character serialized prefix
and original serialized length. Malformed JSON yields capture_failed because a parsed
object is unavailable; normal parser diagnostics remain. Exclusive writes avoid replacement;
resolved capture directory must remain within isolated parent. Normal production logging
and campaign saves never receive these files. Manual evidence export includes them only
when explicitly enabled; share sensitive game content with intended reviewers only.

Capture errors are caught, emit content-free capture_failed where possible, and cannot
change acceptance, gameplay or retries. Existing ledger write failure policy stops future
admissions but a current valid opening still completes, verified by synthetic failure.
Capture count/size, enabled/default/off gates, exact parsed content, oversize, filesystem
failure, ledger failure and metering reconciliation are tested. This review includes
synthetic schema/examples, not nonexistent original October 29 output.
