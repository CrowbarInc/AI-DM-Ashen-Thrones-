# 06 — Authority and State Integrity

All measured trials preserve world, character, combat, active scene, simulation
date, turn counter and clocks exactly. World equality includes factions and event
log; character equality covers inventory. Session changes are confined to
conversational_context and last_saved_at; logs append the measured exchange.
state_integrity.json and full before.json/after.json are included per trial.

L1/L2: no pending or executed intention before or after; no intention fabricated,
cleared or rolled back. No gameplay resolution or time advancement. Final questions
repeat only already-public people/weather concepts. Narrow authority PASS.

L4: setup_before shows cleared pending context. Production setup response asks which
NPC; before.json shows the new ambiguous ASK, two valid scene-local choices, status
pending and no last_executed_intention. Setup leaves world/scene/character/combat and
turn unchanged. Preflight pending checks pass. Live measured step copies the actual
pending record, adds revised_text, preserves original question/scene/operation/choices,
keeps pending status, and mirrors it into pending_clarification. No social resolution,
execution, rollback or time advancement. The response requests the still-unresolved
recipient. Narrow authority PASS; no later execution claim.

Information disclosure: available public evidence and selected refs are preserved.
L1/L2 select none; L4 selects the public lantern passage but final host speech only
acknowledges revision and names the pending choices. No restricted fact appears in
the observed final outputs. The full broader disclosure mechanism was not exercised
exhaustively; unavailable internal audit fields are identified in report 03.

Canonical data, production code, frozen ATGB corpus/captures/assessments, fixtures
and experiments match their entry hashes. No candidate merged. Preview setup writes
are confined to new disposable stores; failed preflight does not change its snapshot;
corrected offline payload capture appends only a preview log and advances no gameplay.
No unauthorized gameplay-state mutation observed in this pass. This is distinct from
R1-03's preserved invalid L4 mutation; that historical result is not overwritten.
