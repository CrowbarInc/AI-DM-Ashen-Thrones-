# Persistence Verification

Milestone: `pr_play_object_instance_identity`. Date: 2026-11-09.

52 identity tests include actual character file save/load and actual create_snapshot/load_snapshot. persistence_round_trip.json contains before/assigned/reloaded/restored records and snapshot ID. Identity, revision, provenance, legacy extension and untouched second row compare equal. Repeated assignment leaves saved bytes unchanged. After snapshot, inventory reversal and character changes are made; restoration returns the captured identity without any generator call. Test fault injections cover character write partial/complete failure and snapshot creation/restore failure. Existing snapshot tests add 50 inventory/snapshot controls.

Existing storage writer remains non-atomic; these are Python exception guarantees in the tested local process, not crash durability.
