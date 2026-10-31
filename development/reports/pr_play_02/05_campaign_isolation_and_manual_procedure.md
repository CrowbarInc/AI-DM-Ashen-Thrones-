# 05 — Campaign Isolation and Manual Procedure

Exact operator artifact: PR_PLAY_02_LIVE_PLAYTEST.txt in this directory. This is
preparation for external review, not permission to conduct the live session now.
It replaces the PR-PLAY-01 handoff's unmet retry prerequisite; the old handoff and
reports remain untouched historical evidence. DNS troubleshooting is not repeated.

Normal launch is .venv/Scripts/python.exe run.py, port 8000. Controlled launch is
the same game.api:app via uvicorn, localhost 8765, one worker and no reload.
ASHEN_DATA_DIR points at a new timestamped artifacts/pr_play_02/manual-.../data
directory, established before application import. It receives copies of existing
frozen campaign/character/world/conditions/scenes only. No production save is
copied over, deleted, reset or edited. Read-only hashes protect normal data and
frozen/experimental inputs through validation.

The handoff prints the absolute isolated path, checks storage binding, zero SDK
retry options and request limit six without a provider call, and requires matching
browser port/server output. Busy port or failed checks mean stop. New Campaign is
one silent disposable reset; Start Campaign is a separate opening-generation step.
An isolated subprocess test confirms supported storage binding and real reset
behavior; existing reset regressions exercise nested runtime clearing.

Opening, NPC conversation, information, correction/follow-up, noncombat action
and continuity are covered as a budget-aware plan. Names follow the actual visible
scene. More than one operation may be needed per input. Stop on cap, provider
failure, state anomaly, startup failure or 60s without a reply. No resending or
restarting to finish the sequence. Partial evidence is valid and must be labeled.

Exact setup, environment, launch, before/after copy and Compress-Archive commands
are in the handoff, along with timing/notes/screenshots. No .env edits are required.
After Ctrl+C and export, close the disposable PowerShell window. A fresh normal
launch uses the original data directory and environment. Test artifacts are kept.
No live UI, actual opening generation or browser identity check was executed here;
the known HTTP limitation remains a conditional validation gap.
