# 05 — Authority and State Integrity

**Deterministically validated — protected state preservation.** Entry hashes cover 2,228 files across game/, static/, data/, experiments/, tests/, tools/atgb/ and prior artifacts/atgb/. All match after the offline checks (integrity.json). This includes the existing campaign, frozen corpus/baseline and prior evidence. Frozen frontier-gate-v1 manifest/file verification also passed. No new file was intentionally added in those owners; final inventory verification records additions separately.

Initial versus final canonical campaign: byte-identical files. No representative turn ran; location, present NPCs, actions, pending actions, inventory, time, discovered information, event/faction fields and combat have no persisted delta. Canonical personal/play content is not copied into this review: entry hashes and empty mismatch list prove preservation without unrelated campaign disclosure. This is not proof that future live inference preserves authority.

| Boundary | Controlled evidence | Authorization |
|---|---|---|
| Reset | Existing six reset tests replace session root, rotate ID, reset combat/world runtime, clear log | Explicit reset calls in temporary test-owned stores only |
| Conversational correction | R1-02/R1-07 controlled production calls retain authoritative world/character/combat/time and avoid fabricated pending actions | Existing communication owner permits response/context, no automatic execution |
| Mechanical pending revision | Revision guards distinguish eligible pending work, absent intention and already executed actions | Existing pending-intention eligibility; correction alone grants no world authority |
| Participant grounding | 46 R2-02 tests include known speaker, departed/absent/ambiguous recipient, explicit switch and resolver disclosure controls | Present/grounded addressee; no hidden-knowledge entitlement |
| Question/evidence | 18 R2-04 tests include current request plus captured-control host outcomes | Public selected evidence only; unavailable detail remains unavailable |

Relevant exact preconditions/assertions are in packaged test sources and test identities in offline.xml. There is no single initial/final six-interaction state snapshot because that scenario was blocked. No invented completed action, unearned inventory, unexplained time, contradictory presence, silent reset, duplicate execution or failed-interpretation mutation was observed in the executed controls; broader live checks remain Blocked. No unexpected canonical mutation or unresolved persisted discrepancy detected. Temporary fixture mutations are expected and authorized deterministic validation, not player campaign changes.
