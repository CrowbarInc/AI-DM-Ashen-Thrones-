# Implementation

Milestone: `pr_play_object_marking_inspection`. Date: 2026-11-09.

Production files changed: game/object_marking.py and game/api.py only. object_marking adds inspect_markings, prepare_removal, exact request/authorization schemas, common target validation and compatible current/history validation. Add collision detection includes removed IDs in durable history. api adds internal inspection/removal wrappers and factors the existing marking coordinator so additions/removals share serialization, authority, rollback and atomic save. Storage, state-authority registry, identity owner, routing, parser, prompt, noncombat results, publication, T04/T05/T06 and ruleset code are unchanged.

Validation: tests/test_object_marking_inspection.py. Cycle-local runner reuses exact predecessor regression selections and unchanged twelve-turn HTTP harness with networking/provider guards and isolated runtime state. Production.diff compares authenticated entry bytes, not HEAD, preserving unrelated dirty work. service_extension.txt is the cycle-local construction input; shipped code is game/object_marking.py. No general mutation engine, campaign registry, alternate ledger, public endpoint or provider call introduced.
