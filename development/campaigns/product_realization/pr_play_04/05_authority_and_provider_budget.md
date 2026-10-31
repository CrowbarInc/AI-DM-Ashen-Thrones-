# 05 — Authority and Provider Budget

## Structured-output safeguards

Preserved:

- Malformed, incomplete, truncated, and empty provider text fail closed.
- Missing envelope stays a contract rejection. The historical code `missing_structured_envelope` is surfaced as the stable reason when the parser already recorded it.
- Declaration validation and evidence authorization are unchanged. Empty `declared_claims` plus a consequential paraphrase still fails `undeclared_consequential_claim`.
- No prompt, schema, model, or output-token-limit change.
- No automatic provider retry was added.

A response can be safe to display and still be invalid as a campaign opening. The generic ask line remains available for ordinary unresolved questions. It cannot complete `scene_opening`.

## State authority

Opening progression (turn, world tick, time pressure, faction events, `campaign_started`, gameplay log) commits only after acceptance. Campaign creation and stored scene initialization are left in place when narration fails. Combat, NPC knowledge, hidden facts, and simulation rules were not retuned.

## Provider admission

PR-PLAY-02 controls remain:

- The stub asserts `max_retries == 0` whenever `ASHEN_PLAYTEST_DISABLE_SDK_RETRIES` is set. `tests/test_pr_play_02_controls.py` passed in the focused slice.
- Host retry suppression is unchanged.
- A blocked Start at request limit 0 does not construct the SDK client.
- A dispatched invalid opening consumes one admission.
- The next Start is rejected by `playtest_stop_reason` before dispatch.
- No new provider operation or extra narration stage was added on the start path. A successful opening is still one narration dispatch.

## No-extra-call verification

Concurrent rejection happens while the first call is in flight and does not add a second `responses.create`. Repeated Start after success returns `already_started` with no additional call. The failure-then-success case uses one call per explicit attempt and does not hide a retry inside a failed attempt.

## What this does not prove

Admission counts under stubs do not measure live token use or provider latency. No improvement of either is claimed.
