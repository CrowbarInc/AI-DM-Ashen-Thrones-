# PR-PLAY-79D-F3 Executive Summary

Verdict: **A/PASS**. PR-PLAY-79 is closed in the integration scope demonstrated by this cycle.

Provider-admission and interpretation refusals remain visible, non-mutating operational responses. The HTTP publication layer no longer records them as completed gameplay publications. `session.last_publication` stays on the preceding completed gameplay sentence, so the HTTP event and the session pointer now agree.

The repair does not treat an operational refusal as gameplay, does not advance the publication pointer to satisfy metadata, and does not change authoritative state. Accepted NPC dialogue and grounded fallback publication from PR-PLAY-79D-F2 remain in place.

Branch `feature/product-realization`. HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. No commit. No push. AT-OPT-01 was not started.

## Gates

| Gate | Result |
| --- | --- |
| Defect reproduced before the repair | Pass. Admission and interpretation refusals wrote `engine_or_grounded_fallback` events while the pointer stayed put. |
| Root cause | Publication-event construction, not admission and not `note_completed_publication`. |
| Classification repair | Operational class skips the gameplay event. |
| Admission refusal | Visible, 0 requests, pointer unchanged. |
| Interpretation-service refusal | Provider exception and model mismatch classified operational. A sent request is counted. |
| Visibility | HTTP 200 and the safe sentence remain. |
| Phantom gameplay event | None for the operational refusal. |
| Pointer | Unchanged by the refusal. Advanced by the next completed gameplay response. |
| Transcript | Refusal log line is `operational_refusal`. |
| Save/reload | Preceding gameplay publication survives. |
| Accepted dialogue and grounded fallback | Preserved by the 36 prior publication tests and the new cases. |
| Physical narration and disclosed recall | Preserved by deterministic tests and the browser repeat examination. |
| HTTP acceptance | Pass, with one unintended live narration call recorded below. |
| Browser acceptance | Pass. Typed composer. Simulated admission. 0 browser provider requests. |
| Frozen holdout | 28/28. Developer-authored. Not external validation. |
| Historical regression | Focused 1,065/20, boundary 101/6, broader 0/9. Zero new identities. |
| Protected files | 150/150 unchanged. |

## Limitation

The HTTP acceptance continuation used “I step back from the notice board.” with live interpretation disabled. That path still sent one primary narration request: attempt `12e9b94b02cb49cf984cf975b5e58d5e`, model `gpt-4.1-mini-2025-04-14`, 22,777 input tokens, 600 output tokens, 23,377 total, 0 retries. That exceeds this cycle’s 3,000-token cap. No further live calls were made. The browser host sent none. The step-back sentence is not the bounded physical-narration proof; that proof is the deterministic one-expression test.
