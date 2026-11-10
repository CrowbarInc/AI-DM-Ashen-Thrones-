# Turn Atomicity

The existing `ordered_turn` plus `runtime_commit_scope` is the commit boundary. Marking and visibility are staged in memory. One `save_character` writes both. Unresolved, rejected, stale, conflicting, and visibility-rejected outcomes do not call that save.

If `save_character` raises, the existing scope restores the character bytes. The HTTP route returns 500 and the success sentence is absent. A later retry of the same request id applies the mark once.

If `seal_host_speech` raises after a successful save, the same scope restores the character because the exception leaves the turn. Retry then applies once. If the seal returns different text without raising, the character stays committed, `resolution.success` becomes null, and `publication_matches_commit` is false. A retry uses the receipt and does not add a second mark.

The in-memory lane cache returns the first HTTP body for a repeated `client_request_id` without re-entering the turn. That prevents a second mutation. Conflict behavior for changed text on the same id is verified after the lane cache is cleared. Two different request ids with the same sentence are two actions.

No new transaction coordinator was added. Required consumption is outside the successful class because it cannot be committed safely with the marking.
