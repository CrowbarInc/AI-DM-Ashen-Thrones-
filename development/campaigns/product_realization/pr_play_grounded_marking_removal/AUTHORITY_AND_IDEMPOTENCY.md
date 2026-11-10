# Authority and Idempotency

The removal request is the existing v1 `remove_marking` request. Authorization is the trusted internal assertion built after resolution, with mechanics `not_applicable` and the six removal preconditions. The caller id is `grounded_marking_removal`. The request id is the SHA-256 of the chat `client_request_id` plus the operation kind `remove_marking`. Player text is not the key.

`prepare_removal` enforces the digest, the expected revision, and the exact active marking id. The historical add receipt stays. The removal receipt stores the request and the removed marking. The active list loses only that id, and the object revision increases by one.

Replay behavior covered by `tests/test_grounded_marking_removal.py`:

- The same request id after a successful wipe returns the stored receipt and does not raise the revision again. This holds in-process after the lane cache is cleared, and in a new process after reload.
- The same request id aimed at a different marking is a conflicting request. The other marking stays.
- A later marking on the same object does not let the original request id remove that new marking.
- A new request id for a marking that is already gone does not mutate.
- The same sentence in a later turn, with a new request id, is a new attempt and does not reuse the first receipt.
- A stale expected revision is rejected and the marking stays.

The in-memory lane still returns the first HTTP body for a repeated client request id inside one process. Durable replay is what remains after that cache is cleared or the process is new.
