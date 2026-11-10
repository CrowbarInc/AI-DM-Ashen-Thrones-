# Persistence Verification

Milestone: `pr_play_object_marking_mutation`. Date: 2026-11-09.

marking_round_trip.json demonstrates two identified otherwise identical objects, selected-ID mutation, exact prior second row, revision=1, recovered marking/provenance/authorization and durable result. Reloaded exact retry returns original result and leaves bytes unchanged. marking_snapshots.json captures pre/post snapshots, post restore historical revision/receipt and exact replay; pre restore returns original character without marking or receipt. Re-execution after historical rollback is legitimate, not global exactly-once. Both snapshots use actual storage.create_snapshot/load_snapshot and coherency checks. Existing 52 identity and 50 inventory/snapshot controls pass. Failures before replacement and injected post-write Python exception return no successful result and restore original bytes; rollback failure surfaces coherency error rather than completion.
