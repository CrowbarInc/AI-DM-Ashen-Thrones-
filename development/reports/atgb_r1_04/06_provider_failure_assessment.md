# 06 — Provider Failure Assessment

Read-only evidence: R1-03 L1/L2 trace.json, response.json, accounting.json,
provider_usage.jsonl, before/after snapshots and execute_trial.py. Normalized
extraction is provider_assessment.json. No connectivity probes or provider calls.

L1: request_interpretation returned APIConnectionError / provider_failure before
any model response. Classification: transport failure. One admission and dispatch,
625.517 ms recorded dispatch latency, 1781.25 ms end-to-end; no request id or token
usage. Network restriction is a historical hypothesis, not established cause.
No exception cause chain, DNS/TLS/proxy diagnostics or transport response survives
in the selected evidence. Root cause unresolved.

L2: InternalServerError before any model interpretation. Classification: provider
failure (SDK server-error category); exact status/body/request id were not retained.
One admission/dispatch, 6519.199 ms dispatch latency, 7471.197 ms end-to-end.
No token usage. A provider-side error is supported; the service's underlying
failure and whether upstream intermediaries contributed remain unresolved.

Neither record shows local response-schema rejection or application parsing of a
completed model response. No supporting evidence attributes either to R1-02, which
is a downstream host-routing repair with no new provider call site. L4's import
leak explains its zero-call invalid control, not L1/L2.

R1-03 bounded real OpenAI clients to max_retries=0; each saved SDK-client record
confirms it. Application retries were disabled, no trial retry/continuation or model
switch occurred. The unchanged timeout owner defaults to 45 seconds, clamped 5–120;
current offline configuration evaluates to 45.0 seconds (SDK 2.48.0 installed).
Historical effective timeout/SDK version were not saved, so current observations
are not retroactive facts. Both durations are below the default; timeout causality
cannot be established. Usage accounting stopped after missing usage, correctly
keeping failed billing unknown rather than zero. No retry policy/config changes.

Precautions for separately approved continuation: fresh bounded process/store and
durable ledger per trial, max two application admissions, SDK retries zero, startup
probe skipped, mandatory local preflight, stop on provider error/unknown usage.
Capture nonsecret exception class/status/request id and cause category when
available. Do not add retries or switch models to obtain a passing response.
