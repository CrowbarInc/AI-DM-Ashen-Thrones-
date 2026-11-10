# PR-PLAY-22 review archive

Start with PR_PLAY_22_FINAL_VERDICT.md. Review counts supersede raw HTTP-only counters; protocol deviation is disclosed.

PR_PLAY_22_TRANSCRIPT.md is the player-facing transcript. All live/ and offline/ snapshots, HTTP captures, prompts, provider responses, diagnostics, diffs and source are INTERNAL DIAGNOSTIC EVIDENCE and may contain GM-only campaign material. Do not serve this archive to players.

live/ is the single live campaign. offline/ is one readiness cycle plus a clearly separate synthetic budget test (six fake dispatches, zero live calls). No historical campaigns packaged. Configuration contains no credential values. Native raw records remain unchanged. Request_01..04 and response_01..04 reconstruct all provider interactions.

Test controller semantic stop missed T1; T2–T4 retained as post-failure observations. Do not replay execute_validation.py against the provider. Its durable single-run marker blocks another live attempt. No PR-PLAY-23 work performed.
