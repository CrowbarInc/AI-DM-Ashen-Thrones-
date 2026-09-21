# Policy Decision Summary

Read this first. Detail lives in `docs/rc10_rc21_policy_resolution_dossier.md`.
Implementation record: `docs/rc10_rc21_policy_implementation.md`.

The user has chosen. These decisions are settled.

## RC-10 = A

Plain-English question:  
Should the retired opening-fallback label `compatibility_local_opening_deterministic` appear as a raw string only in the opening-fallback evidence helper, or may other diagnostic tests name it directly?

**USER DECISION: A — Evidence-only fence.**

Other tests and diagnostics must use `legacy_compatibility_local_opening_authorship_source()` or the dedicated evidence builders. The retired production path stays retired. The allowlist was not broadened.

## RC-21 = B + C

Plain-English question:  
When an NPC says “You’ll find Lirael near the notice board,” what official follow-up should the game record?

**USER DECISION: B + C.**

- B: Official follow-up comes from authored or realized scene evidence. Here that is “Check the notice board.” Narration alone does not instantiate Lirael / `emergent_town_crier`.
- C: The lead registry is the official case file. `pending_leads` and clue surfaces are projections.

## Implementation Status

Implemented in `rc10_rc21_policy_implementation_20260919`. See `docs/rc10_rc21_policy_implementation.md`.
