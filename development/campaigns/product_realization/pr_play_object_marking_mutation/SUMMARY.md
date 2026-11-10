# Summary

Milestone: `pr_play_object_marking_mutation`. Date: 2026-11-09.

**A/PASS for bounded validated persistent marking.**

76 new marking/atomic tests; 52 identity tests; 50 inventory/snapshot controls; 143 preservation controls passed, separately selected.

Combined before: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). After: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). New failures: []; resolved: [].

An authorized add_marking targets one durable singleton; marking/revision/receipt commit in one atomic character replacement. Reload, exact/conflicting replay and historical snapshots verified. All twelve published turns and authoritative characters unchanged. Zero live provider calls.

Single authoritative character inventory and single-process ordered turn lane; no multi-process lost-update protection, multi-file crash transaction or global exactly-once across timeline rollback. File fsync is required; directory sync is best effort and unavailable on this Windows host. Permission bits are preserved; custom Windows ACLs, ownership and inode metadata are not portably copied by the standard-library writer. Read-only Get-Acl audit confirmed current character.json has zero explicit access rules and inherited directory ACLs (permission_audit.json); no custom-file-ACL durability/security guarantee. Authorization/evidence are trusted internal caller assertions, not gameplay adjudication or a public authentication boundary. No conversational marking, inspection/removal, equipment/material inference or T06 completion.
