# 07 — Chat idempotency

A rename retry happens inside the single save of an already resolved turn. Compared with the pre-turn state:

- One player message and one assistant message are stored when the save eventually succeeds.
- Discoveries, journal facts, inventory, and branch flags change once.
- The provider stub is called once.
- A second identical player action after success does not set the other branch and does not add a second survey or report consequence. The duplicate mud-print investigation is ignored by the engine and republishes the already known fact.
- A reload after a successful save shows the same ordered transcript.
- A reload after a permanent save failure shows the pre-turn transcript, not a turn that the HTTP response claimed as committed.
- Two campaigns written through separate data directories do not share turns.

Concurrent writers beyond the existing single-process replace retry were not added. The architecture under test is one process replacing one file.
