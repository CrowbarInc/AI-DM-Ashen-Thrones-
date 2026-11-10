# Idempotency Contract

Milestone: `pr_play_object_marking_mutation`. Date: 2026-11-09.

Caller supplies stable bounded request_id. Canonical SHA-256 covers all meaningful request fields including scopes, target, expected revision, exact content, source and authorization; excludes only request_digest. Canonical JSON sorts mapping keys, uses compact separators, ASCII escapes and forbids NaN. Unknown request fields fail closed. Caller-supplied digest must match recomputation.

Durable receipt is character.object_marking_receipts={version:1,campaign_run_id,character_id,entries:{request_id:result}}. Both receipt and marking are checked bidirectionally, including reconstructed semantic digest, identity, unique marking/request IDs, original/result revisions and status. Exact retry returns original result/UUID with no save or allocation, even though its original expected revision is now stale. Changed digest on same request_id explicitly rejects conflicting_request. New IDs allow identical content. No in-memory response-cache bypass: ordered_turn is entered without a cache key.

Receipts retained for the lifetime of the saved character timeline; no pruning, silent eviction or external dedupe DB. O(applied operations) storage outside prompt projection. Restoring pre-operation snapshot removes its marking and receipt, allowing the original request to apply in that rolled-back timeline; restoring post snapshot restores exact replay. No global exactly-once claim across arbitrary rollback. On ambiguous completion reconcile the original ID against authoritative disk, never invent a new ID.
