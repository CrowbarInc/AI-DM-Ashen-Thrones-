# PR-CZ Target Continuity Trace

Trace:
1. Turn 1 player input explicitly addresses Guard Captain.
2. Social resolution selects `guard_captain`.
3. Accepted output commits `discourse_focus.active_interlocutor.id=guard_captain`.
4. Turn 2 asks a natural follow-up with no explicit new addressee.
5. Resolution-contract construction recovered an inherited discourse referent, but did not assign it to `interlocutor_id`.
6. Downstream routing therefore had a social ask without an authoritative active interlocutor.

First target-loss boundary:
- The target was persisted but not recovered into the ask contract addressee.

Cause:
- B. The target was persisted but not recovered.

Repair:
- When validation resolves a discourse referent of type `interlocutor` for an ask, the contract now sets `interlocutor_id` and binds the entity as canonical discourse authority.
- Short elliptical follow-ups such as "Why?" can recover the active discourse interlocutor when no explicit switch or scene transition invalidates it.

Controls:
- Scene mismatch hides stale discourse focus.
- Explicit new addressees still override prior discourse focus.

