# 03 — Admission Budget Implementation

Reused existing game.provider_budget ownership and ASHEN_PROVIDER_REQUEST_LIMIT=6.
No new counter, persistent budget store or retry framework. Existing token ceilings
and mandatory durable ASHEN_PROVIDER_USAGE_PATH remain active. A single lock
serializes reservation and admission-ledger writes. Admitted identity is required
at RequestAttempt.dispatch; dispatch markers precede SDK invocation, and duplicate
dispatch is rejected. A refused operation cannot reach the SDK.

Admission reserves before client construction, so it is a conservative attempt
allowance: a constructor failure can consume an admission without an outbound
request. Failed outbound calls consume admissions. No refund occurs between turns.
Missing/inconsistent usage stops subsequent admission rather than inventing tokens.
The seventh attempted operation is refused before client construction in all seven
production owners. Existing first-six behavior is retained. Six is not a turn count.

Under the documented SDK-zero/host-zero/limit-six configuration, at most six
transports can be sent by the supported application process. No machine/account/
cross-process guarantee is claimed. Launch uses one worker, no reload, no external
workers/test harnesses, one browser and one request in flight. Production game/
does not spawn provider-calling subprocesses. Guarded concurrent calls cannot
over-admit: a 16-thread production-boundary test sends six and rejects ten.

Counters are process-local. Restart does not restore counters; exclusive ledger
creation refuses an existing ledger, rather than resetting it. Starting a new
process with another ledger would be a new session and is prohibited as a way of
continuing this session. No persistent storage was added.

Added opt-in supplementary gates to chat and Start Campaign, before state loading
or gameplay execution, once allowance is exhausted/accounting stopped. Chat uses
the existing nonmutating rejection response and records the submission transcript;
Start returns a concise blocked error. Tests forbid state loads/saves, interpretation
and SDK construction on those paths. Normal launches bypass these added gates.
An admission race is still protected at the atomic provider boundary. Rejected
interpretation already uses the existing nonmutating blocked route.

Narration can follow a legitimately resolved action. A refusal does not roll back
that earlier authorized action or imply a new action occurred. The playtest-only
narration refusal now says to stop/export, removing the generic claim that an action
resolved. Ordinary production wording is unchanged. Local host fallbacks can finish
an admitted operation, but no seventh request or hidden provider retry is allowed.

No gameplay rules, authority decisions, pending-action semantics or persistent
gameplay structures were changed. Diagnostic log appends are evidence, not actions.
