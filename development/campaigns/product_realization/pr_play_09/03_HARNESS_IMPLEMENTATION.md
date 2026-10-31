# 03 — Harness Implementation

PR-PLAY-09 · 2026-10-30 America/New_York · evidence_scope: structural_only.

Modified runner.py extends the existing scenario dispatcher and opening checkpoint;
worker.py adds synthetic SDK interpretation/narration records and two deterministic
turn faults. gameplay.py is an observer/evaluator/report helper composed by that
runner, not a second harness or a gameplay authority. PowerShell and Python entry
points recognize FiveTurnGameplay. Coverage registry names the new test module.

Each submitted turn waits for its HTTP response, captures state and native journal
slice, evaluates it, then decides continuation. Before the next submission, exhausted
request limits stop without dispatch. Token admission failures also stop. Structure,
semantic, provider and state failures stop; quality probes may continue. All skipped
turns receive reasons. No automatic retries or concurrently submitted actions.

Turn deadlines include before/API/after capture. The scenario retains the existing
180-second ceiling, individual request/turn cap 90 seconds, startup 30 and owned
shutdown 5. On interruption, owned worker cleanup precedes persistent salvage;
interruption.json and final/turn state survive where available. Missing final API
state remains explicitly unavailable. No restart continues a spent budget.

Exports include opening/, turns/Tn/{before,after,api_response,evaluation}, diagnostics
and reports. Individual source/API captures retain 2 MiB bounds; DM text in results
is bounded to 8192 characters with truncation metadata. Large diff values use 2048
character previews and SHA-256; exact values remain in snapshots. No repeated full
state blobs in result.json. Existing 32 MiB and 30-second evidence bounds remain.
