# 03 — Output-Budget Implementation

PR-PLAY-06 · 2026-10-28 America/New_York · evidence_scope: structural_only.

600 originates in game.gm.call_gpt via ASHEN_NARRATION_MAX_OUTPUT_TOKENS, default
600. It is operation-shared, environment-configurable and not model-specific.
Before this pass it was sent only when provider accounting was active; outside
accounting ordinary calls had no explicit max_output_tokens. No documented
historical rationale for choosing 600 was found; do not invent one.

The existing host-authored response_type_contract now selects an opening-only
cap through _requested_response_type_from_messages and _opening_max_output_tokens.
Default 3000; ASHEN_OPENING_MAX_OUTPUT_TOKENS accepts 1..4096 and fails before
admission on malformed/out-of-range values. Opening calls always explicitly send
this bound, with or without accounting. Ordinary calls retain 600 (or their
existing override) when accounting is active, and the existing absent-cap behavior
otherwise. No model or response-format option changes.

The selected cap is reserved by the existing atomic admission owner before SDK
construction and passed unchanged to Responses.create and the completion/diagnostic
records. Aggregate request/input/output/total budgets remain authoritative. SDK
and host retries stay disabled under the existing controlled flags. No new call,
retry or larger-budget retry path was added. The manual aggregate ceilings stay
6 requests / 200000 input / 20000 output / 220000 total.

An opening with explicit status incomplete/failed/cancelled/queued/in_progress now
fails using existing _structured_contract_failure after normal parsing diagnostics.
Complete JSON cannot override an explicitly unfinished provider response. Missing
status retains SDK compatibility and still requires all existing validation.
Diagnostic classification provider_not_completed distinguishes valid JSON on an
unfinished response; malformed exhausted responses retain json_parse_failure plus
provider status/finish/limit fields. Final opening_outcome records rejected commit.

Cost exposure: default maximum per opening rises by 2400 output tokens, 5x the
former 600 ceiling. At the configurable hard maximum, exposure is 4096 per request.
Aggregate ceilings do not increase: six 3000-token openings could reserve/use
18000 output tokens if independently authorized, within 20000; other usage reduces
remaining room. Six 4096-token reservations cannot all pass a 20000 aggregate
ceiling. This is not cost-neutral. No monetary quote or current pricing claim.
