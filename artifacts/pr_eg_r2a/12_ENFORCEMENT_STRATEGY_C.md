# 12 — Enforcement Strategy C

FRESH separate semantic evaluation, same production-selected provider/model family, separate call and no generator self-report. Input contains exact question, authorized/disclose-permitted facts, knowledge posture and candidate; gold labels and raw historical trial metadata are excluded. Output includes claims, epistemic classes, source ids and a three-way decision. No local model or smaller-model comparison was run; independence from the same provider's learned assumptions is not established.

development: 60 evaluated, 12 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 28 | 0 | 0 |
| REJECT | 3 | 19 | 8 |
| ABSTAIN | 1 | 1 | 0 |

holdout: 0 evaluated, 30 untested. No measured matrix.

STOP: three critical unauthorized accepts in development batch C_development_10. The stop threshold was two cumulative high-risk unsafe accepts, checked after each six-case batch; three occurred in that batch. No subsequent C request was sent. C's last 12 development cases, all holdout cases, planned C repetitions and single-candidate semantic latency remain untested. Raw incomplete coverage is explicit in results. Missing results become fail-closed abstention in a hypothetical policy, never a measured successful rejection.

The provider handled many paraphrases and contradictions better than A/B but used plausibility instead of authority for gate rules and promises. High aggregate accuracy on a partial sample cannot authorize deployment. No prompt tuning or relabeling followed the failure. Nondeterminism for semantic classification is unmeasured because continued testing of the failed strategy was stopped.

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.
