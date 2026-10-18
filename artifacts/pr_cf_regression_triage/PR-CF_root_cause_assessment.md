# PR-CF Root Cause Assessment

## 1. HTTP/TestClient Instability - SUPPORTED
Failure count: affects HTTP-heavy clusters; PR-CF reproduced a hang during representative rerun.
Observed: faulthandler stack in Python 3.12 Windows `socket.socketpair()` fallback `accept`, via Starlette TestClient/AnyIO portal.
Runtime impact: deterministic test reliability risk; does not by itself prove gameplay regression.
Repair scope: bounded test infrastructure/event-loop policy or TestClient fixture hardening.

## 2. Response Projection And Fallback Contract Drift - SUPPORTED
Failure count: includes dialogue plan, narration transcript, social relevance HTTP, final emission metadata signatures.
Observed: tests expected deterministic/minimal fallback families or no quoted NPC speech; actual output accepted normalized social candidate, minimal emergency fallback, or quoted uncertainty.
Runtime impact: can affect player-facing dialogue/narration quality and authority presentation.
Repair scope: final emission/social fallback contract reconciliation.

## 3. Social Speaker/Reply Classification Drift - SUPPORTED
Failure count: speaker grounding, dialogue establishment, social absence, social quality, and part of turn pipeline.
Observed: `speaker_contract.mismatch_present` true where parity expected false; `reply_kind` unknown where refusal expected; redirect/source metadata changed.
Runtime impact: can misroute ordinary NPC dialogue and block controlled live dialogue validation.
Repair scope: social routing/speaker contract diagnostics first, then fallback emission behavior.

## 4. Governance And Prompt Expectation Drift - CONFIRMED
Failure count: import guard, duplicate-name governance, prompt guidance, provider payload size/rule-presence tests.
Observed: static allowlists/caps and expected prompt text no longer match current dirty tree.
Runtime impact: mostly test governance, low direct gameplay impact unless the drift hides ownership violations.
Repair scope: audit whether new imports/tests are legitimate, then update allowlists or route through owner APIs.

## 5. Exploration/Investigation/Observation Projection - POSSIBLE
Failure count: PR-CE inventory has 7 exploration, 7 investigation, 7 later-turn observation, plus related HTTP files.
Observed: fresh rerun blocked by TestClient hang before clean assertion capture.
Runtime impact: likely ordinary gameplay impact if authored clues, grounded absence, or observation restacking are wrong.
Repair scope: after TestClient stabilization, rerun representative non-live HTTP cases and inspect state/provenance deltas.

## 6. Reactive Player Harness Drift - SUPPORTED
Failure count: 5 non-noise failures.
Observed: objectives resolve early where harness expects follow-up/rephrase/max-attempt termination.
Runtime impact: validation harness risk more than core runtime defect.
Repair scope: decide whether current behavior is valid improved completion or harness expectation drift.
