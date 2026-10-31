# State-Integrity Validation

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

Baseline and after capture both API projection and all bounded isolated persistent
documents, including session/world/combat/character/campaign/conditions/scenes/log.
Copied files are retained exactly; normalization applies to comparison only.

Gameplay comparison unwraps known persistence envelopes and excludes saved_at /
derived integrity metadata plus session last_saved_at, diagnostic debug_traces,
and __turn_start_active_interaction_target_id request metadata. Empty rollback log
materialization is equivalent to an absent empty log. These explicit exclusions
are reported as bookkeeping changes; arbitrary JSON changes are not ignored.

Failure requires no normalized gameplay mutation. Success requires exactly one
turn/log increment, started=true, and only documented opening-owned runtime roots
and top-level fields may change. Character/conditions/authored scenes/combat or
unknown session/world fields are unexpected. Changed fields and unexpected files
are recorded. The conservative allowance is versioned in the tooling; it is not
an independent semantic authority over world ticks. Nested changes within allowed
opening-owned fields are observed, not a full gameplay-quality proof.

H2–H9 negative fixtures preserve gameplay state; H1/H10 commit exactly once.
H19 distinguishes timestamp bookkeeping from an injected world mutation. Persistent
after-state survives interruption even if API after-state is unavailable. Every
relevant protected file was hash-checked across validation; ordinary saves and
frozen fixture bytes stayed unchanged. See protected_before.json and
protected_integrity.json. Frozen ATGB content was never used as a writable store.
