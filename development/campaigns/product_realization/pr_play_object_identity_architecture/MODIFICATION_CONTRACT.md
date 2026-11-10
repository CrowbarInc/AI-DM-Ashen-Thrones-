# Proposed persistent modification contract

Milestone: `pr_play_object_identity_architecture`. Design only. Engine persists the applied result, not a remembered narration.

## Initial operation boundary

First mutation demonstration supports **add_marking** on one established, accessible, suitable singleton with an established compatible medium and supplied disclosed text. Removal by marking ID follows as the next small operation before full T06 integration. A cleaning request maps to remove_marking only if the medium is removable by that established method; it must not erase all state blindly.

Defer general condition edits, attach/detach components, contents changes, appearance editing, damage/repair, renaming rights, temporary/permanent mechanical effects, crafting and destruction. Transfer/placement are separately typed relationships, never arbitrary JSON patches. Scratch/engrave can share marking intent but require damage/tool/adjudication support; until then unsupported rather than harmless add_marking.

## Proposal and evidence

Required logical proposal fields (compact IDs may point to bounded engine evidence):

| Field | Contract |
|---|---|
| request_id + payload_digest | Stable actor/campaign/branch request identity; canonical digest of semantic request, not raw language |
| target reference + expected_revision | Exactly one live singleton, optional validated part selector |
| operation + arguments | Allowlisted typed add_marking; exact bounded text and medium ref; no raw JSON path supplied by AI |
| preconditions | Evidence refs and expected versions for existence, access, custody/rights, part, writable surface, medium availability/compatibility, capability |
| authoritative_inputs | Disclosed source record ID/version/fingerprint, exact copied text or explicit grounded excerpt; campaign physical facts with provenance |
| adjudication | Adapter identity/version, relevant context fingerprint, result/check/cost references; not_applicable must be explicit |
| proposed_delta | Engine-built expected before/after marking delta, never narration-authored state |
| validation | Accepted/rejected plus reason codes and uncertainties. Internal evidence is not automatically player-visible |

Bind copied wording to the authorized knowledge snapshot. For original T06 the candidate full text is “The missing patrol was last seen taking the northwest mud track past the crates.” Store the exact applied wording, content fingerprint and disclosed source lineage. Later source changes cannot rewrite the already copied text; provenance may record that it is an older copy. Hidden content is never fetched merely because the target object exists. An independently player-composed message may use literal user text as content, without asserting that its claims are true; separate this from a request to copy secret information.

## Validate, stage, apply

1. Resolve actor, target and source from authoritative state; preserve unknown/false distinctions. No mutation, material mint or cost on clarification/unsupported outcomes.
2. Validate operation shape, length limits, placement/access, source disclosure/content, revision and adapter result. Nonmechanical allowed operations require no roll; contested/exceptional cases await adapter.
3. Reuse `game.integrated_play.ordered_turn` (api_chat:7132) for the serialized **whole-turn** read/validate/commit critical section; reload/check host revisions and all consumed evidence. Existing per-save locks alone do not prevent stale-read lost updates. Direct service callers must enter the same lane; do not add a competing lock. No concurrent multi-process support claimed.
4. Build detached staged copies of every touched host and costs; apply typed delta exactly once. Verify one-host identity, revision increments, bounded markings and conservation. Failure discards staged copies.
5. Persist object, costs and dedupe record with existing API runtime_commit_scope. Character save primitive must become atomic before this operation ships. Raise on any failure so rollback runs; never swallow a write failure and return a completed result. Reload/discard in-memory staged state after rollback.
6. Produce applied delta, new revision and operation ID only after durable save success. Publish through existing narrative authority/seal. If later pipeline failure raises, the turn scope restores files and no completion escapes.

The receipt records validation result separately from application result. “Validated” is not “applied.” An unapplied proposal is never an inspection source. No generic apply-from-state_changes endpoint accepts untrusted metadata as a grant.

## Duplicate/conflict semantics

Persist a proposed engine-only operation ledger in session, which snapshots already include, with branch/campaign/request key, semantic digest, affected instance IDs, prior/result revisions, applied delta digest and safe receipt reference. It is an audit/dedupe record, not another object state store. Retry of the same request+digest returns its historical applied receipt without another mutation or charge. Same key/different digest conflicts. A fresh deliberate repeat has a new request identity and may create another marking if policy allows. Text hashing alone must not suppress deliberate repeat actions.

Keep current object state bounded (initial limit: 16 active markings, 2,048 UTF-8 bytes per marking, 8,192 total text bytes per object; overflow yields explicit rejection, never truncation). Retain compact idempotency keys for the life of the replayable branch; archive verbose audit events outside prompt context. This ledger grows O(A) with committed operations: a finite cap cannot silently evict replayable keys. Later compaction requires an explicit acknowledged retry floor; older retries fail closed, not reapply. Durable use of existing request identity is a later API integration dependency; existing action_id is not an idempotency key.

Conflicting revisions fail closed with current visible state/clarification; no provider retry or automatic semantic merge. Ownership/material/source changes invalidate the proposal. Transfer increments revision and preserves markings. Reconciliation rejects duplicate host bindings and repair is explicit, not inferred from logs.

Existing ingress already supplies optional `ChatRequest.client_request_id` (models.py:249). `ordered_turn` caches at most 32 completed results in process and coalesces inflight equal text; it does not persist dedupe through restart/restore or compare a completed key's semantic payload. Reuse that request field and lane, extending validation before an object-action cached return so campaign/branch/key/digest conflicts cannot bypass the durable object ledger. Generate a server request identity when absent and return it for explicit retries; identical language on a new deliberate request is not a durable duplicate. Clear or namespace the in-memory cache on reset/restore and never use a prior-branch completed result. This is durable integration work, not missing ingress from scratch.

## Durability and rollback limits

storage.runtime_commit_scope restores runtime bytes on Python exceptions with best-effort restoration; load_snapshot validates first then commits with rollback. Neither is a crash-atomic multi-file database transaction, and rollback failures can leave uncertainty. Initial feature is bounded to the existing single-process file-backed runtime, serialized turns and fault-injected exception guarantees. If rollback fails, stop publication and surface operational failure; do not claim applied or clean rollback. Multi-process/crash consistency requires a later journal/database cycle, not a hidden prerequisite disguised as already implemented.

## Inspection/recall

Inspection reads current active markings by instance and part, filters visibility/literacy/mechanical access, and supplies exact text plus visible condition. Immediate and later inspection share the same function. Conversation binds a stable reference as a hint, then revalidates possession/location and current revision. Transfer/relocation preserve text on that instance, but do not guarantee the old actor still has access. Save/reload rehydrates the same fields. Removal increments revision; subsequent “what is on my sleeve?” reports no current marking. Historical “what did I write before cleaning?” may query a permitted audit record explicitly labelled past, never report it as present. Contradictory actions reread the current record; absence cannot be filled from memory.
