# Read Only Verification

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

The focused read-only test forbids save_character, save_session, save_world, atomic writer, UUID allocation and GM generation where available. Input deep equality, repeated detached DTO equality and every temporary runtime file hash are checked. before_hash=391db463e6fb5ba369927b56f619fee44b90c291a652ce8a5d3fb07c46d0180e; after_hash=391db463e6fb5ba369927b56f619fee44b90c291a652ce8a5d3fb07c46d0180e. Disk equality=True. Tests run with disabled provider/interpretation/expression/retries and a non-loopback network audit guard. No network attempts or provider calls in completed runs.

No identity assignment, revision increment, marking mutation, receipt creation, inventory reorder, equipment/scene/world update, campaign fact, clock advancement or narration log write occurs. Production contains no storage/provider call. Per-read complexity: character inventory identity validation plus bounded selected active state; no full-world or receipt scan. Evidence: read_only.json and noninterference.json. Existing production and canonical data hashes remain identical to entry.
