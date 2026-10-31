# 02 — Scenario Design

PR-PLAY-09 · 2026-10-30 America/New_York · evidence_scope: structural_only.

FiveTurnGameplay v1.0.0 is pinned to frontier-gate-v1. Opening occurs once through
/api/start_campaign after /api/new_campaign and baseline capture. It is not a player turn.

| Step | Exact input | Fixture authority |
|---|---|---|
| T1 | I take a moment to look around the gate district. What do I notice? | scene visible_facts/opening_seed_facts |
| T2 | I approach the gate serjeant and ask what happened to the missing patrol. | world.npcs gate_serjeant; route_change topic; scene visible_facts |
| T3 | I examine the notice board carefully. What notices are posted? | scene.interactables notice_board; discoverable notice_patrol_route |
| T4 | I want to investigate the missing patrol. What leads can I pursue from here? | established notices, authorized prior discoveries and NPC topics |
| T5 | I approach the gate and try to enter the city. | Enter Cinderwatch exit targets market_quarter |

The serjeant is authored in world.npcs despite a different set of scene.addressables;
runtime recognition is tested rather than patched. Private identities and unearned
route-clue disclosure are not assumed available. No curfew hours, prices or patrol
fate are invented. Each action defines ID, input/category, properties, permitted and
forbidden changes, criteria, timeout, stop conditions, subject probes and scene prerequisite.

All inputs use production /api/chat, including movement. No direct resolver calls
in the harness, injected outcomes, forced quest acceptance, rewritten failed actions,
or invented alternatives. A refusal/check/obstacle may be legitimate. Unexpected
pre-turn scene invalidates the remaining fixed script: PARTIAL with skipped reasons.
No unbounded AI player exists. Changing the scenario requires a new explicit version.
