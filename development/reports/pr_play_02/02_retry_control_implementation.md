# 02 — Retry Control Implementation

New test-only opt-in: ASHEN_PLAYTEST_DISABLE_SDK_RETRIES=1. The shared helper
game.provider_budget.sdk_retry_options returns {"max_retries": 0} when enabled
and {} otherwise. All seven production OpenAI constructors expand this helper.
Set it before application import/construction. SDK support was confirmed from the
installed 2.48.0 constructor/source: max_retries defaults to 2. No SDK install,
upgrade, endpoint/model change, or new dispatch owner was introduced.

Normal constructors receive no new retry keyword. Existing timeouts and request
arguments remain unchanged. The setting does not change interpretation/narration
content. Source diff is entry-to-final and includes each constructor.

Existing ASHEN_DISABLE_PROVIDER_RETRIES=1 is retained, separately required by the
manual launch. gm.call_gpt rejects positive retry_attempt before admission/client
construction. API discretionary upstream-error, hard-invalid regeneration and
targeted narration retries all pass positive retry_attempt. Their local orchestration
may still run, but no retry provider dispatch occurs. Interpretation/expression,
contract/candidate/planning and preflight owners make single calls without their
own retry loops. Startup inference preflight is explicitly skipped in the handoff.
Neither flag alone substitutes for the other.

tests/test_pr_play_02_controls.py intercepts effective constructors for every owner,
both flag states, and dispatches production calls under spies. It also constructs
the real installed SDK with its supported local MockTransport: a 429 response
results in exactly one transport invocation, client.max_retries == 0, one failed
admission and unavailable usage. No socket or live provider is involved. A direct
production host retry test forbids even SDK construction and sees zero admissions.

Evidence: focused.xml, constructor_evidence.json, mock_concurrent_ledger.jsonl,
test source, and entry-to-final diff. The seven-owner tests prove coverage; the
sample concurrent ledger records one captured scheduling outcome, not every path.
No live retry behavior, latency or provider availability claim is made.
