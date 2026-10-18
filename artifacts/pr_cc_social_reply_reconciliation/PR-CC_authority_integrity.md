# PR-CC Authority Integrity

Verified invariants:
- Declaration validation was not changed.
- Narration validation was not changed.
- `gm_resolution_decision` remains the authority owner for consequential realization.
- No new mutation path was added.
- No provenance promotion was added.
- Harmless subjective reply tests assert `declared_claims_expected=false`.
- Harmless subjective reply tests assert `durable_state_mutation_allowed=false`.
- Harmless subjective reply tests assert `npc_speech_authority=claim_only`.
- Consequential and restricted controls assert `incidental_subjective_allowed=false`.
- Narration-only retry-contract and envelope tests passed.

Validator changes: none.

Live calls: 0.
