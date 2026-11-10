# Request ordering

PR-PLAY-77 saw overlapping browser chat requests. This cycle:

- `static/app.js` sets `chatBusy`, disables Send and the chat input, and sends `client_request_id` (`crypto.randomUUID` or a timestamp). The browser session showed Send disabled while a turn was in flight.
- `game/api.py` takes `ordered_turn` on the store path for chat and action (writers) and for state reads (readers). Snapshot create and load take the write lock and do not share a text key, so two saves are not collapsed into one.
- Duplicate in-flight text or the same client request id returns the first result. A completed client request id is replayed. The holdout's first H098 miss was this cache being shared across cases. The product behavior was kept. The harness keys were scoped by case id.

Writers for one store run FIFO. A second campaign store does not wait on the first. Tests: `test_two_reads_overlap_and_writes_stay_ordered`, `test_write_waits_for_write_and_read_waits_for_write`, `test_duplicate_request_runs_once`, `test_independent_campaigns_do_not_block`, `test_failed_write_releases_the_lane`. All passed in the 136-test file.

A second browser click during a disabled Send was not separately fired. The backend duplicate test is the evidence that a repeated mutating request does not apply twice.
