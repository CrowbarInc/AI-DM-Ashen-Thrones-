# Failure analysis

## What is confirmed

The provider call succeeded. The response parsed as the structured opening envelope. `game.immutable_valid_response.run_preserve_if_valid._check` then rejected the candidate with `hard_validation_failed` and semantic reason `unauthorized_resolution_decision_fact`. The application classified the result as `safe_nonresolution` (`nonresolution_origin: application`) at `game.api._opening_response_rejection`. `final_validation_passed` is false. `opening_accepted` is false. `gameplay_committed` is false. HTTP status is 422.

The player was shown the generic start failure, not the generated narration. Campaign start stayed false. Turns 1–5 were not attempted. Initialization was not repeated.

Process ownership matched: controller pid 29220, worker pid 19236, parent 29220, base interpreter `Python312\python.exe`, only child `conhost.exe` pid 24940. Isolation attestation passed. Owned shutdown stopped pid 19236 with exit code 1, which is the harness terminate. The user campaign fingerprint was unchanged.

## What is not confirmed

The ledger does not record the decision-audit violations. The exact sentence or claim that failed `audit_realization_envelope_against_decision` is not in the evidence. Two readings remain possible: the model paraphrased an authorized gate fact into a proposition the decision did not allow, or the validator rejected a legitimate realization of the authored opening. The captured claims are marked `provenance_requested: authored_world_fact` and `declaration_mode: realize`, but that request flag does not prove the audit accepted them.

## Classification

Primary cause: **engine failure**. The semantic validator rejected a structurally valid opening and the start path refused to commit the campaign.

Contributing **AI-DM** factor: the generated narration did not satisfy the pre-narration resolution decision. The evidence is not sufficient to call the narration the sole cause.

Not an infrastructure failure. Ownership, startup, isolation, and cleanup held.

Not a provider failure. One completed response, no timeout, no malformed JSON, no retry.

Not a scenario-content gap at the five-turn layer. The frontier-gate baseline was loaded and the ordinary player lines were never reached.

## Bookkeeping writes

A rejected opening still rewrote session save metadata, cleared the turn-start interaction target to an empty string, and duplicated a scene-entity rebuild trace. Combat content did not change. These writes did not start the campaign.

## Controller note

The first preflight stopped on an incorrect source-string check before any worker existed. That check was corrected and is not a second gameplay attempt.
