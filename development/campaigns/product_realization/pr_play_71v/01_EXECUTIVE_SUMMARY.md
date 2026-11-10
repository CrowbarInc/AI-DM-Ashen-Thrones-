# 01 — Executive summary

**Verdict: A — PASS / FINAL LIFECYCLE VERIFIED.**

The final PR-PLAY-71 source, including the Windows rename retry and the runtime commit scope added before this cycle's holdout, created, played, saved, resumed, and continued two independent campaigns. Survey and report consequences stayed exclusive. Persistence retries did not repeat gameplay or provider work. Permanent rename failure did not report success. Failed new-campaign setup rolled back. Player-visible transcripts followed the loaded campaign.

This is a developer-authored verification closure. It is not official ATGB certification and not external independent validation. No commit or push was made. PR-PLAY-72 was not implemented.

## What passed

- Windows atomic replacement: immediate success, one to three transient WinError 5 failures, success on the fourth attempt, and exhaustion after four attempts. Delays are 10, 30, and 90 milliseconds. A real exclusive file lock recovered (holdout W13).
- Permanent failure leaves the prior file intact and does not publish a committed success.
- Chat and branch work stay single-shot across a rename retry.
- Both real HTTP campaigns and both browser campaigns completed the notice → milestone → exclusive branch → follow-up → save → resume → continuation path.
- Cross-load restored Campaign A's survey transcript and removed Campaign B's report-only lines, then the reverse held in the saved report slot.
- Isolated lifecycle and persistence tests: 39 passed, 0 failed.
- Executed HTTP and browser payload scans: 0 hidden-information exposures, 0 mandatory-disclosure omissions, 0 unsafe AI publications.

## What remains disclosed

- Frozen holdout W12 failed with `KeyError: expect_delays` after the product assertions for content and replace-call count had passed. The case was not edited or rerun. Development tests cover the delay schedule.
- The historical publication HTTP 500 was not reproduced in 8 attempts. Its cause is not identified.
- A long combined pytest process recorded 17 extra focused failures from an unhealthy in-process preflight cache. The same modules passed in a clean process. Those combined failures are retained and are not product regressions.
- Three historical focused failures, six historical boundary failures, and nine historical broader failures remain.
- This cycle made 0 live provider requests and used 0 provider tokens. Narration evidence is deterministic or stubbed.
- An isolated pytest truncated `data/session_log.jsonl`. The protected working-tree bytes were not recovered. Session, combat, and world bytes that matched the protected baseline were restored. The log was returned to the committed blob, which does not match the protected hash.
