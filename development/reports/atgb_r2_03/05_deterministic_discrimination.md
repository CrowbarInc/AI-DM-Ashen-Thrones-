# 05 — Deterministic Discrimination

Execution: `development/tmp/atgb_r2_03_probe.py` with bundled Python 3.12.14 and existing .venv site-packages. The script is packaged as an investigation artifact, not a production tool or frozen fixture modification. See exact inputs and outputs in deterministic_results.json and adapter_controls.json. No provider execution occurred. Provider and live interpretation are disabled in environment; socket.socket raises in the experiment block; request_interpretation is replaced only for offline request capture and saved JSON adapter controls.

## Arms and outcomes

16 decision invocations, four current request reconstructions, four raw-JSON adapter controls, three membership controls and one corrected social-resolver control were executed. The 16 decision invocations include an intentional duplicate S05 input used for resolver handoff, not 16 independent examples.

| Substitution | Outcome | Causal meaning |
| --- | --- | --- |
| Four unchanged captured adapted records | S02 repeats its category sentence; current S05 EXECUTE ASK runner | Reproduces S02 behavior at current decision boundary and accepted R2-02 recipient repair. |
| S02.3 communication.subject only → `curfew start time` | Same category sentence | Subject string alone cannot control selection or realization. |
| S02.2/.3/.4 evidence refs → []; projected evidence → {} | .2/.4 unestablished-information answer; .3 emits wrong patrol-start clarification | Selection matters, but .3 also has wrong disposition/question. |
| S02.3 corrected subject + empty evidence | Still wrong patrol-start clarification | Correct subject plus no evidence is insufficient if purpose and clarification text remain wrong. |
| Three S02 supported QUESTION dispositions + empty evidence + no operations | All return `That has not been established in the information available to you.` | Existing contract and GM owner can honestly handle an understood question whose answer is unavailable. |
| S05 alternative board subject only | Same ASK route; proposed record retained | No unique topic binding is established merely by changing a string. |
| S05 assume GM/RECALL, no action, unchanged disclosed rumor evidence | Emits rumor passage | Positive transport control: host can use the valid rumor on that route. This is an assumed reading and restatement, not a solution to “more.” |
| S05 GM/CLARIFICATION, [], no action, supported account question | Focused runner-versus-board clarification | Existing host can ask the right slot without inventing facts. |

The raw adapter controls use original captured raw JSON with precisely recorded communication/disposition substitutions. The legacy adapter may mark zero-operation OTHER as SAFE_ABSTENTION/clarification_required; it still carries a structurally valid record. The same record reconsideration used by api.chat returns ANSWER for the three understood S02 questions and CLARIFY for S05. These adapter labels are retained, not reported as four accepted execution records. No full HTTP request or disk-writing API is invoked.

Membership controls: visible:0 accepted; [] accepted; nonexistent clue:notice_patrol_route rejected. Membership acceptance is not answer sufficiency. No injection of a gated clue or fabricated hour was attempted. **There is no valid nonempty historical evidence substitution that supplies the missing curfew hour or undisclosed posted route.** Experiment B therefore tests removal of non-answer evidence, not an invented correct answer. The S05 recall control supplies genuinely authorized evidence under an explicitly different reading.

## Resolver and integrity

The corrected synthetic S05 resolver call uses keyword arguments, minimal known recipient context and patrol_rumor in revealed_topics. It resolves Tavern Runner, yields genuine_uncertainty, reveals no topic and leaves the copied world unchanged. It does update the copied session's runtime/addressability as expected. No copied session is saved to a gameplay store. A first resolver invocation mistakenly used positional arguments in the wrong order; its “empty scene_id” result is **INVALID investigative harness output**, retained separately in invalid_initial_social_invocation.json. It supports no product diagnosis. The corrected run replaces it as the valid control.

All 16 decision inputs remain equal to deep copies. All 1,311 protected file hashes remain unchanged, including frozen baseline, canonical game state, production, prompts/schema source and experimental files. `integrity.json` records zero protected changes and zero added protected files at experiment completion, before the new review configuration was written. Repository status before/after records report/export additions separately.

Limitations: minimal session replay, no exact original provider requests, no historical full preturn snapshots, no live sampling, no new gameplay evaluation, no response-naturalness measurement, no independent held-out or broad regression result. Offline substitutions show host capability and causal dependencies, not that new prompt wording would reliably produce them.
