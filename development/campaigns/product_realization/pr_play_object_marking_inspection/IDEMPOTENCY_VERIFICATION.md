# Idempotency Verification

Milestone: `pr_play_object_marking_inspection`. Date: 2026-11-09.

Exact replay returns the original committed result after reload, after later revision advancement, and after restoring the post-removal snapshot; no save/allocation/receipt/revision change. Conflicting payload with the same ID returns conflicting_request. Both add-to-remove and remove-to-add request-ID reuse refuse; operation participates in canonical digest. New ID against an absent marking returns missing_marking at the current revision, not replay. Historical add retries remain valid after removal. Concurrent identical removals produce one revision/receipt. Removed UUIDs cannot be allocated to a new add. Evidence: idempotency_controls.json, inspection_removal_timeline.json, final_inspection_junit.xml. Snapshot rollback can remove the durable key and is a timeline change, not global exactly-once.
