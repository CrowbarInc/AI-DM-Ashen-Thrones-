# Provider Safety Validation

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

No live provider or provider-connectivity calls were performed. Deterministic
transport replaces SDK constructors before requests, rejects asynchronous clients,
and rejects external socket connections. Real game admission still accounts for
synthetic operations; journal attempts in deterministic mode are not billable calls.
H15 verifies this boundary; H16 blocks unauthorized Live before starting a worker.
Live multi-turn/scenario misuse is refused even if an invocation flag is supplied.

Live requires both mode and explicit authorization flag, normal configured credential
presence, provider enablement, retry suppression, fresh isolated DATA_DIR and known
output allowance. Startup and direct connectivity probes are disabled; no health
request consumes a hidden admission. The skipped upstream gate is explicitly not
evidence of provider health. Existing model routing is retained; pin overrides are
refused. Opening output allowance is read from the game owner, never raised by the
harness. SDK max_retries=0 and host suppression use existing controls.

Default opening ceiling: one admission. Scenario ceilings cannot exceed the prior
controlled manual scope: six requests / 200000 input / 20000 output / 220000 total;
opening scenario itself requests one. Inherited stricter environment/.env limits
are retained using min, not replaced. Existing admission reservations and post-call
accounting remain authoritative. Tokens are estimates at admission and observed
usage after completion; an exhausted or unknown accounting record prevents PASS.
Usage, allowances, remaining budget and rejections are reported without inventing
pricing or failed-call token usage. No retry, budget expansion, model change, or
extra production operation occurs after a failure.

Credentials are never serialized. Exception strings are omitted; worker logs are
bounded and redact known environment secret values. Evidence selects only isolated
campaign and explicit diagnostic files, never canonical private play data or .env.
The review generator checks the selected bytes against configured secret values.
Residual: existing static readiness/source attestations are stale, producing two
baseline regression failures. They were not rewritten or relaxed. Native runtime
admission/accounting controls pass their other checks. External review remains
required before any first Live invocation.
