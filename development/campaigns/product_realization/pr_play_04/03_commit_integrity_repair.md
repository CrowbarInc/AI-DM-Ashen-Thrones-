# 03 — Commit Integrity Repair

## Original sequence

`start_campaign` and the campaign-start branch of chat:

1. Increment `turn_counter`.
2. `advance_world_tick` (faction pressure, agenda, events, in memory).
3. `save_world` immediately.
4. Advance `time_pressure`.
5. Run the narration pipeline.
6. On success, `_complete_opening_turn_persistence_like_chat` sets `campaign_started` and appends the log.
7. On exception, decrement the turn and save the session. The world file already held the tick.

Campaign creation and scene initialization stay earlier, in `new_campaign` and the stored scene files. Those are not opening progression.

## Revised sequence

`_OpeningScope` uses the existing `storage._RUNTIME_PERSISTENCE_LOCK` (RLock). It is not a new lock framework.

1. Admission and eligibility checks run under that lock.
2. `track()` deep-copies session, world, and combat, and records the log length, before the in-memory turn and tick.
3. The opening path still applies the turn, world tick, and clock in memory.
4. The early `save_world` on the opening path is removed. Ordinary chat still saves the world before narration.
5. `mark_committed()` runs only when completion returns a normal success payload, after that payload’s own `save_world`, session save, and log append.
6. `close()` always releases the lock. If the attempt was tracked and not committed, it writes the baseline world, combat, and session back and restores the prior log.

Chat campaign-start uses the same scope through a `ContextVar`, so the chat function did not need to be reindented. Ordinary chat never tracks, so `close()` does not roll it back.

## Persistence behavior

Caught failures, including an injected `OSError` on the first `save_world`, restore the baseline. `test_persistence_failure_before_commit_restores_baseline` passed.

This is not a multi-file transaction. `save_world` is a normal JSON write. A crash during that write can still leave a torn `world.json`. A restore error in `close()` can mask the original exception. Those limits are reported. Full crash atomicity is not claimed.

The lock is held across the provider call for an opening attempt. That serializes concurrent openings in this process and delays other persistence on the same lock. It is the existing persistence lock.

## Failure recovery

Pipeline exceptions still propagate as `RuntimeError`, matching the existing failed-start tests. They no longer leave pressure or faction ticks. The post-change standalone case `pipeline_exception` raises and finishes at pressure 0 and factions 2/2/1 with an empty event log.

The campaign record is not deleted when narration fails.

## Idempotency

- Success then Start again: HTTP 409 `already_started` before another tick or provider call. Turn, pressure, and faction events stay at the single opening commit.
- Failure then failure: both HTTP 422, state unchanged, later success still eligible.
- Failure then success: progression committed once.
- Concurrent starts: the second blocks on the persistence lock while the first is inside the provider call, then receives 409. One SDK call. One committed turn.
