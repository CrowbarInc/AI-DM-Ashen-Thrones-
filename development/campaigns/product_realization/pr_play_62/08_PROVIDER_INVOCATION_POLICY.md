# Invocation policy

ASHEN_INTEGRATED_REPEAT_FAST_PATH is exact-1 and off by default. Inside the
existing integrated hook it skips only a resolved known/repeated outcome with
no newly revealed facts or inventory effects, when live narration would otherwise
run. Records deterministic_fast_path=true and
provider_skip_reason=resolved_repeat_without_new_information. Requests and
generator calls are zero; response shape and fallback marker remain unchanged.

Explicit generators and injected faults are never bypassed. Leaving the flag
unset preserves live repeat exercise. Discoveries, first no-new-information
observations and ordinary scene observations are not automatically skipped.
Unavailable provider and deterministic-only behavior retain existing recovery.
No retry, cache or cross-session information reuse was added.

Turns 3 and 5 skipped requests because resolution marked already_searched,
including the second barrel action without the word “again.” Session-bound
publication remains a separate requirement; no global enablement changed.
