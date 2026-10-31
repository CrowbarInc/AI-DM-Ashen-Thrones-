# 08 — Live-Test Readiness

PR-PLAY-11 · 2026-10-30 America/New_York · evidence_scope: structural_only.

**B — Conditionally ready for external review of the controlled diagnostic.** Historical failure reproduced; exact offending prose and rule identified; conservative generation constraint reconciled; positive/negative, atomicity, overlay and continuation controls pass. No relevant new regression remains. C23's missing wire bytes/original full request cannot be recovered; parsed captures and relevant reconstructed public context remain inspectable. C5/C6's source-ID fallback is a preexisting contract limitation, not repaired or hidden here.

Original reproduction: raw response remains rejected as required by the existing lexical guard; a one-sentence compliant equivalent passes. Failure-class guidance: now explicitly communicates the empty-identity lexical constraint. Reliability: **not established**; no independent live openings run. Do not promise the prompt prevents every future rejection.

Future command, for external review and a separately authorized later run only:

```powershell
.\scripts\run_live_playtest.ps1 -Scenario FiveTurnGameplay -Mode Live -AuthorizeLiveProvider -CaptureResponse
```

Existing FiveTurnGameplay v1.0.0, same five actions, same configured model and output allowances (normally opening 3000 / ordinary narration 600), maximum six requests, no SDK/host retries, isolated fresh campaign, state-integrity checks, bounded response capture and automatic evidence export retained. Aggregate ceilings remain 200000 input / 20000 output / 220000 total or stricter inherited limits. No connectivity test. Failed-call usage can be unknown. No cost estimate fabricated.

Synthetic normal HTTP pipeline passes opening and T1–T4, then safely skips T5 at the unchanged six-request ceiling. Full five-turn completion in six requests is unproven. Stop on any semantic or state-integrity failure and retain evidence without retry. Live execution is not authorized in PR-PLAY-11 and was not executed. One next action: external review of this archive.
