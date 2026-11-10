# Limitations and risks

- Final physical deduplication repair has deterministic accepted/fallback proof but no fresh live physical rerun.
- Browser sequence spans revisions; only the post-reload turn used the final HTTP boundary. The earliest trace's provider provenance was wrong and is preserved, not rewritten.
- Browser paint/completion latency was not measured. Server latency is separately labeled.
- New frozen holdout primarily covers recall and trace helpers; it is narrower than the requested complete integrated frozen matrix. No independent external validation claim.
- A legacy archived holdout output write was safely blocked. Its failed export remains evidence.
- Structured provenance/validity controls are conservative. Historical missing/ambiguous mappings, modified facts and invalid facts can yield no recalled text. No broad memory migration/invalidation redesign was introduced.
- Existing semantic interpretation still costs provider requests for some deterministic investigation/actions. This is deferred to AT-OPT-01.
- Historical baseline failures remain; no full-repository green claim.
- Detailed rejected-output cost is unavailable from the retained ledger; no fabricated zero.
