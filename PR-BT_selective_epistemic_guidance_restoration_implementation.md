# PR-BT Selective Epistemic Guidance Restoration

MODE: SELECTIVE RESTORATION IMPLEMENTATION
MODEL/API CALLS: ZERO
COMMIT: NOT PERFORMED
PUSH: NOT PERFORMED
VALIDATORS CHANGED: NO
RETRY CHANGED: NO

Decision: **A — READY FOR REPEATED MICRO LIVE**
Architecture: **A — PR-BR REMAINS CLOSED**

## A. Executive result

The PR-BT sentence "give the strongest grounded partial answer and keep the limit diegetic" was replaced with the 651-character `EPISTEMIC REALIZATION` paragraph recommended by the differential discovery.

The paragraph teaches: state the authorized observations; if inference is permitted, add one possibility tied to them and leave cause, actor, time, and history unresolved; do not add a mechanism, setting, maintenance history, or causal chain; do not use certainty wording on inferred or hypothetical material, including on the observations in that same sentence; a player hypothesis may fit the visible facts and stays hypothetical.

Net provider cost versus the failed live optimized requests is **552 characters** on P1, P2, and P3. The protocol is 651 characters. The removed sentence is 99. Broad PR-BS essays were not restored.

## B. Root cause addressed

P1 and P3 failed because the realization model lost the linguistic protocol for a permitted epistemic act, while the authority objects stayed byte-identical. The replacement pressure to give the strongest grounded partial produced stronger wording ("significant stress," "leading to," "clearly") and closers the current validator does not treat as equivalent ("is not clear").

P1's initial narration crossed the qualified-possibility ceiling with unsupported history. P3 did not promote the hypothesis; it failed on certainty wording. P2 stayed healthy because mundane refusal did not depend on that prose.

This slice restores only that linguistic family. It does not retune the validator and it does not redesign retry.

## C. Correct owner

`SYSTEM_PROMPT` in `game/gm.py`.

The differential report named that owner because the sentence is on every realization call, it is the sentence PR-BT substituted for the old uncertainty rule, and "strongest" is the pressure that lined up with the failed wording. The answer recipe was identical on the successful and failed gates, and the P3 recipe does not describe a hypothesis answer. `response_policy` already owns the machine-readable flags and those flags were not enough once the prose bridge was removed.

The protocol is model-facing and operational. It does not grant authority, replace `GMResolutionDecision`, replace the answer recipe, or replace response policy. The prompt still says the application owns mechanics and state, and that the recipe is guidance only.

The existing sentence "Player hypotheses remain hypothetical unless the supplied decision/claims authorize more" stays. The new paragraph covers hypothetical status and does not state that exception. Leaving it avoids a protocol that would forbid a hypothesis the decision actually authorizes. It is not a second essay and it adds no characters.

## D. Exact implementation

- `game/gm.py`: `EPISTEMIC_REALIZATION_PROTOCOL` is substituted for the abstract sentence inside `SYSTEM_PROMPT` before any request is built.
- `tests/test_pr_bt_selective_epistemic_guidance.py`: P1, P3, and P2 checks against `build_messages` output.
- `tools/measure_pr_bt_policy_instruction_payloads.py`: `reconstruct_probe` accepts an output directory. Default output is unchanged.
- `tools/measure_pr_bt_selective_epistemic_restoration.py`: reconstructs P1/P2/P3 and writes the three-state comparison.

No edits to `game/gm_resolution_decision.py`, `game/immutable_valid_response.py`, or `game/gm_retry.py`. `game/prompt_context.py` was not edited in this slice.

## E. Protocol semantics

- Observation: start from authorized observations. Do not invent evidence.
- Permitted inference: when the decision allows it, add one useful possibility tied to those observations.
- Explicit modality: say a possibility, or that the facts may be compatible. Those are not the only legal words.
- Unresolved status: cause, actor, time, and history stay unresolved unless the decision authorizes more.
- Certainty ceiling: do not use certainty wording for inference or hypothesis, and do not put it on the observations in the same sentence.
- Player hypotheses: discuss fit. Do not turn the proposal into world truth.
- Usefulness: add the permitted possibility. Do not treat uncertainty as a refusal. "Answer direct questions first" and "Prefer partial truth over refusal" remain.

## F. What remains deleted

The PR-BS narrative-authority essay (554), fallback known-edge essay (459), narrator-anchor line (163), world-facing essay (165), and the 305-character in-character uncertainty rule are still absent. So are the narrative-plan field essays and the long anti-railroading, context-separation, purity, and tone restatements.

Constructed requests assert those distinctive sentences are gone. See `PR-BT_selective_epistemic_protocol_diff.md`.

## G. Validator status

Unchanged. Uncertainty, certainty, causal, lead, hypothesis, narration, and declaration recognizers were not edited.

## H. Retry status

Unchanged. Retry prompt, feedback, decision, fallback, and token handling were not edited.

## I. Answer-recipe status

Unchanged. Reconstructed P1, P2, and P3 `decision_facing_answer_recipe` objects match the frozen failed-live generation-1 payloads. The protocol does not appear in the recipe. P1 still says "could, may, or might." P3 still says to realize the required claims, with inference not permitted, and that no player hypothesis is authorized on that turn.

## J. P1 deterministic evidence

`tests/test_pr_bt_selective_epistemic_guidance.py::test_p1_provider_guidance_teaches_qualified_observation_tied_inference` inspects the constructed P1 system prompt.

Present: authorized observations as the ground; one possibility tied to those observations; explicit unresolved cause, actor, time, and history; a ban on mechanism, setting, maintenance history, and causal chain; "Prefer partial truth over refusal."

The protocol occurs once. The abstract "strongest grounded partial" sentence is absent. System-prompt growth versus the optimized 9,012 characters is 552.

## K. P3 deterministic evidence

`test_p3_provider_guidance_keeps_player_hypotheses_conditional` inspects the constructed P3 request.

Present: hypotheses may be discussed; they stay hypothetical; visible facts may be compatible; observation alone does not settle the hypothesis; certainty wording is barred for inferred or hypothetical material.

The P3 recipe is still the realize-required-claims recipe. Authority did not move into the recipe.

## L. P2 nonregression

`test_p2_mundane_npc_path_stays_incidental_dialogue` inspects the constructed P2 request.

The protocol opens with "On an interpretation, or when the player offers a hypothesis," so it does not script ordinary NPC conversation. The system prompt still allows mundane NPC dialogue, refusal, hesitation, and mannerism as bounded incidental realization. The recipe still allows ordinary dialogue, a refusal, a hesitation, mannerism, and phrasing. The instruction list still says to narrate a refusal without inventing facts the speaker does not have. The protocol does not require "remains unclear" on that path.

## M. Provider-size table

Zero model calls. Same `build_messages` reconstruction as the PR-BT measurement, using the saved PR-BS isolated probe state.

| Probe | Original | Failed live optimized | Selective restoration | System | Instructions | Response policy | Turn packet | Answer recipe | Protocol |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 110,450 | 97,260 | 97,812 | 9,564 | 13,607 | 21,346 | 10,676 | 2,356 | 651 |
| P2 | 121,438 | 109,853 | 110,405 | 9,564 | 14,267 | 21,465 | 10,640 | 1,876 | 651 |
| P3 | 110,665 | 99,200 | 99,752 | 9,564 | 13,675 | 21,138 | 10,910 | 1,691 | 651 |

Optimized system prompt was 9,012 characters. Restoration system prompt is 9,564. Turn-packet and answer-recipe sizes match the PR-BT regression completion gate, which is evidence those objects did not move.

## N. Savings retained

| Probe | Chars restored vs optimized | Chars still removed vs original | Previous reduction | Percent of previous reduction retained |
| --- | ---: | ---: | ---: | ---: |
| P1 | 552 | 12,638 | 13,190 | 95.82% |
| P2 | 552 | 11,033 | 11,585 | 95.24% |
| P3 | 552 | 10,913 | 11,465 | 95.19% |

Fixed restored cost: **552 characters** on every probe. Probe-specific restored cost is 552 for each. All three retain more than 90% of the previous character reduction.

The 651-character figure is the protocol. The measured giveback is 552 because the 99-character abstract sentence was removed rather than stacked. No live token counts are inferred.

## O. Regression results

Command, outside the sandbox, with `TMP` and `TEMP` pointed at `artifacts/pr_bt_selective_epistemic_guidance/pytest_tmp`:

`.\.venv\Scripts\python.exe -m pytest` on every `tests/test_pr_br_*.py`, plus `tests/test_pr_bs_decision_facing_answer_recipe.py`, `tests/test_pr_bt_policy_instruction_deduplication.py`, `tests/test_pr_bt_selective_epistemic_guidance.py`, the prompt/guard files, realization authority and provenance, response-policy contracts, fallback, final emission, schema, and turn-trace tests. Deselected, and not counted as passed: `test_call_gpt_provider_failure_metadata_has_provider_family`. JUnit: `artifacts/pr_bt_selective_epistemic_guidance/regression.xml`.

**916 passed, 1 failed, 0 skipped, 0 errors. 917 tests. 33.306 seconds.**

The failure is `test_pr_bt_provider_requests_remove_at_least_12000_chars_each` at P2: `121438 - 110405 = 11033`, which is under 12,000. That assertion was already red at the PR-BT regression completion gate, when P2 savings were 11,585. This slice did not change the assertion. Section 20's size signal is retention of at least about 90% of the previous reduction. That signal holds.

New guidance tests: 3 passed. Rule-presence and policy/recipe visibility tests passed.

## P. C18

**PASS. ACCEPTED RESPONSE == SEALED RESPONSE == EMITTED RESPONSE.**

`tests/test_pr_br_structured_chat_path.py::test_raw_chat_accepts_authorized_fact_and_seals_it` passed. Every collected test in `tests/test_pr_br_continuation18_immutable_boundary.py` passed.

## Q. Architecture status

**A — PR-BR REMAINS CLOSED**

This slice changes provider wording. It does not create consequential state, promote epistemic material into authoritative state, corrupt provenance, bypass the structured boundary, or diverge accepted, sealed, and emitted text. No ownership contradiction appeared.

## R. Validator debt

Recorded. Not repaired.

- "is not clear" is not treated as "remains unclear" or "is unclear." The P1 retry failed on that distinction.
- "is not something that can be determined" is not treated as "cannot be determined."
- Bare "clearly," including "clearly visible" on an authorized observation, matches the certainty-upgrade recognizer. Removing that word made the P3 sentences valid in the differential replay.
- A hedged sentence can be accepted, causal chain included, once it matches the unknown-slot closer. That exemption is a validator behavior, not a license this prompt grants.

## S. Retry debt

Recorded. Not repaired.

P1 retry moved toward an allowed qualified strain plus an unsettled cause and history, then missed the recognized closer. P3 retry kept "clearly." Retry feedback named `unauthorized_resolution_decision_fact` and did not name the wording that would have passed. After the second failure, both turns sealed as the two authorized observation sentences. PR-BS had zero retries. This slice aims at first-pass competence and leaves retry feedback for a later slice.

## T. Micro-live readiness

**READY FOR THE REPEATED 3-PROBE LIVE GATE. NOT RUN.**

The compact protocol is in the constructed system prompt. Broad deduplication remains. C18 passes. Validators and retry are unchanged. Measured savings remain: 10,913 to 12,638 characters still removed, 95.19% to 95.82% of the previous reduction.

The later gate, when separately authorized, is the same three probes, the same model `gpt-4.1-mini-2025-04-14`, one initial generation each, with retries only if the existing gate retries. Success there is P1 and P3 first-pass acceptance in the PR-BS quality band, P2 still first-pass, and initial input still below the PR-BS token counts. This document does not estimate those tokens.
