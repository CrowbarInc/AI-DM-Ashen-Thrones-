# 05 — Pending-Action Control

Base content: artifacts/atgb/atgb_r1_03/L4/before.json, copied without importing
experiments.pr_dq. The base's manually seeded pending context is removed.
Production game.api.chat receives 'I ask one of them what happened.' with a stubbed
NPC/QUESTION interpretation. Existing ambiguity/authority checks create the
pending ASK with two scene-local candidates, Sergeant Mara and Corporal Bren.
The model's suggested Mara target cannot override the ambiguous player wording.
World and turn counter remain unchanged during setup. Actor exists; candidates
are validated against the scene-local world catalog. No original ask executes.

The control then submits the unchanged frozen correction_pending text,
'Instead, make that a question about the lamp.', through production chat with a
stubbed GM/CORRECTION interpretation. Effective live interpretation is true so
the genuine interpretation/adaptation/orchestration path runs. It revises the
pending record with status pending and revised_text, returning 'revised' without
social resolution or authoritative gameplay execution. The before/after response
and full relevant state are in pending_control.json. This is a synthetic positive
control and structural evidence; not model semantic or human-realism evidence.

World (including factions/event log), clocks, turn, scene, character and combat
are unchanged. Only permitted conversation history, revision context and save
metadata differ. Separate direct-chat controls use all three unchanged frozen
mechanical inputs: pending revises, synthetic executed-state negative control
refuses undo, empty state asks what to change. Preflight rejects executed,
wrong-scene and invalid-target pending fixtures. No production safeguard changed.

Provider-failure stubs for APIConnectionError and InternalServerError both leave
pending/gameplay snapshots unchanged. These are deterministic failure-path
observations with zero actual requests/admissions. A future live control is
structurally supported; actual provider interpretation and useful revision
meaning remain unproven until separately authorized execution.
