# PR-BR - Typed Resolution Contract and Lightweight Discourse State

Date: 2026-09-27

Type: implementation cycle.

Base HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

No completion commit was created. PR-BR remains open.

## 1. Executive Summary

PR-BQ's minimum architecture is now in the live player-input path. A typed Resolution Contract records what the player wants resolved. A small discourse-focus record owns cross-turn referents for the interlocutor, the active claim, the actionable lead, the inspected object, and the last attempted action. Interaction Obligation, PR-BN, narration, retry, final emission, and the evaluator read that same contract instead of each reconstructing the request from prose.

The contract distinguishes perception dimensions, claim follow-ups, and action requests. It does not try to parse every natural-language phenomenon.

Deterministic and real-path tests for the PR-BQ matrix passed. No live-model turn was run, because this environment has no OpenAI API key. Smoke and full synthetic gates were not started. Human playtest is not recommended.

## 2. PR-BQ Architecture Adopted

Adopted without reopening the architectural choice:

1. Typed Resolution Contract, separate from Interaction Obligation.
2. Lightweight discourse slots, not a discourse graph.
3. Interaction Obligation kept, and pointed at the contract.
4. The same contract projected into generation, final emission, and evaluation.

PR-BN authority rules were not replaced. Final-emission safety was not weakened. The contract check can only replace an obvious semantic miss with the existing non-inventive obligation fallback.

No code evidence contradicted the PR-BQ split. The one integration adjustment is that some `/api/chat` turns never build an engine resolution. Those procedural turns now receive a contract on the existing turn resolution object before narration, so the contract still originates from raw player text plus runtime context.

## 3. Resolution Contract Schema

Owner: `game/resolution_contract.py`.

Stored at `resolution.metadata.resolution_contract`.

| Field | Role |
|---|---|
| `contract_id` | Stable id for this turn's raw text. Retries keep it. |
| `turn_index` | Session turn counter when present. |
| `request_kind` | `inquiry`, `action`, `social_action`, or `clarification`. |
| `operation` | `perceive`, `inspect`, `ask`, `confirm`, `follow`, or `act`. |
| `target_ref` | `{type, id_or_text, source}`. |
| `interlocutor_id` | Addressee when the utterance is addressed to someone. |
| `conversational_subject` | Claim text or target label. |
| `dimension` | Primary semantic point, if any. |
| `dimensions` | Every detected point, in textual order. |
| `expected_resolution` | `answer`, `action_outcome`, `refusal`, `clarification`, or `partial`. |
| `epistemic_mode` | `authoritative`, `bounded_incidental`, `npc_claim`, `unknown_allowed`, or `consequential_protected`. |
| `discourse_ref` | `{type, id, label, source_turn}` when a prior slot was bound. |
| `referent_provenance` | `explicit_player`, `inherited_discourse`, `unresolved`, or `ambiguous`. |
| `ambiguous` | True when more than one slot could bind and the utterance does not choose. |
| `raw_input` | Cleaned player text the contract was built from. |

Initial dimensions, extensible by pattern rather than by a closed ontology:

- Perception: `appearance`, `sound`, `smell`, `wear`, `use`, `change`
- Claim / conversation: `source`, `confidence`, `location`, `time`, `next_step`

Action requests are represented by `request_kind` / `operation` / `expected_resolution`, not by collapsing them into inspection.

`location` and `time` bind an active claim only when the utterance is anaphoric (`that`, `it`, `then`). A fresh "where can I..." question does not steal the previous claim.

## 4. Contract Lifecycle

```text
raw player text + session discourse / claim ledger / interaction target / pending lead
    -> construct_resolution_contract
    -> resolution.metadata.resolution_contract
    -> Interaction Obligation.resolution_contract_id
    -> select_resolution_mode stamps authority from the contract
    -> narration prompt receives a short projection
    -> retry keeps the stored contract
    -> final emission assesses the candidate against the contract
    -> discourse focus commits once per contract id
    -> evaluator reads the same contract
```

Construction entry points:

- `attach_interaction_obligation` on the resolved-turn pipeline.
- The procedural `/api/chat` branch that previously called narration with `resolution=None`.

The contract is built from the raw text and current runtime context. Tests do not inject a finished contract into production.

## 5. Discourse-State Model

Owner: `game/discourse_state.py`, stored at `session["discourse_focus"]`.

Slots:

- `active_interlocutor`
- `active_claim`
- `active_actionable_lead`
- `active_inspected`
- `last_attempted_action`

Each slot stores `id`, `label`, `kind`, `scene_id`, `turn_index`, and `source`. The slot is a pointer. The claim ledger, lead rows, and interaction context remain the owners of those records.

Empty slots are filled at read time from those owners:

- latest accepted NPC claim
- `interaction_context.active_interaction_target_id` when it belongs to the current scene
- the latest pending lead in the current scene runtime

Inspected objects and prior actions are not guessed from the scene.

## 6. Referent Ownership

`discourse_focus` is the only owner of active discourse focus.

| Event | Effect |
|---|---|
| Explicit nominal target | Overrides inherited focus for this turn. |
| Pronoun plus one matching slot | Binds that slot. |
| Pronoun plus several eligible slots and no dimension cue | `ambiguous`; expected resolution is clarification. |
| Missing slot for "that lead", "it", or "when I did that" | `unresolved`; clarification, not a guessed id. |
| Scene change | Hides scene-bound slots from the previous scene: interlocutor, inspected object, last action. Claims and leads remain available, but "it" does not bind the old object. |
| Commit | Writes slots implied by the contract after final emission. |
| Same `contract_id` committed again | No-op, so a retry cannot erase the referent. |

## 7. Interaction Obligation Integration

`InteractionObligation` is unchanged in role. `attach_interaction_obligation` still derives kind and requested outcome with the existing rules, then records `resolution_contract_id`.

Inspection fallbacks consult contract dimensions. A sound or smell contract no longer depends on those words surviving inside the prose subject. Question, action, and follow-up fallbacks keep their previous wording when the dimension does not call for a more specific safe line.

## 8. PR-BN Integration

`select_resolution_mode` stamps `requested_dimension` and `contract_id` onto the mode decision.

If `epistemic_mode` is `consequential_protected` and the turn is not an authoritative mechanical action, the mode becomes `unsupported_consequential_request` and no incidental proposal kind is attached. `validate_bounded_improvisation_proposal` also rejects an incidental proposal when the contract is consequential-protected.

Ordinary perception stays `incidental_fact` / `sensory_detail`. Accepted entries may carry `satisfies_contract_id` and `requested_dimension`. Incidental category limits, NPC-claim versus world-truth, and mechanical authority are unchanged.

## 9. Generation Integration

`build_narration_context` adds `resolution_contract` to the model payload when a contract exists. The projection is the compact constraint: request kind, operation, target, interlocutor, subject, dimension, expected resolution, authority, and one sentence of instruction. Internal provenance stays off the prompt.

One instruction tells the model to obey that constraint rather than infer a different request from surrounding prose.

## 10. Retry Preservation

A second `attach_interaction_obligation` on the same resolution object keeps the first contract, including target, dimension, subject, and action, and sets `retry_preserved`. Discourse commit for that `contract_id` does not run again. Retry may still repair speaker, grounding, and wording around that fixed request.

## 11. Final-Emission Integration

`_preserve_resolution_contract_after_gate` assesses the candidate. It does not generate a better answer.

It replaces the candidate with the obligation fallback only when the assessment is an obvious miss:

- sound, smell, wear, use, change, source, or confidence was requested and the text does not address it and is not a legitimate inability, refusal, or clarification
- a generic scene description stands in for an action outcome
- an ambiguous or unresolved referent was not clarified
- protected consequential information was not refused

Appearance, location, and time are assessed, but a merely lexical miss in those dimensions is not auto-replaced, because legitimate answers vary more widely. A recorded `obligation_resolved` flag is not consulted.

## 12. Evaluator Integration

`evaluate_playability` reads `resolution_contract` from the payload, from `resolution.metadata`, or from `gm_output` emission debug.

The assessment is evidence about the player-visible text:

- `unsatisfied` fails `player_intent_addressed` even when token overlap would pass
- `satisfied`, `legitimate_nonresolution`, or `partial` can pass that gate when older token logic would fail
- a malformed response still fails
- a bare runtime success flag does not pass the gate

The synthetic gate runner now passes the production contract into `evaluate_playability`.

## 13. Observability

On each construction, a `resolution_contract` debug trace records raw input, the compact contract, referent provenance, discourse focus, obligation kind, and authority route. Final emission adds `emission_debug.resolution_contract` and `emission_debug.resolution_contract_semantic`. Live resolution metadata includes `contract_id` and `requested_dimension`.

A later failed turn can be split into: contract wrong, referent wrong, authority route wrong, generation wrong, emission replacement wrong, or evaluator wrong.

## 14. Deterministic Test Results

`tests/test_pr_br_resolution_contract.py`: 21 passed.

Covered without transcript-specific noun handlers:

| Case | Result |
|---|---|
| A appearance | preserved |
| B sound | preserved |
| C smell | preserved |
| D wear / use | preserved and bound to the inspected object |
| E claim source | bound to the claim ledger id |
| F claim confidence | bound to the active claim |
| G claim location | bound only because the follow-up is anaphoric |
| H actionable lead | "that lead" bound |
| I inspected referent | "it" bound |
| J prior action | "when I did that" bound |
| K action request | stays `social_action` / `act` |
| L ambiguous referent | clarification, no chosen id |
| M scene change | old inspected object does not bind |
| N consequential information | unsupported mode; incidental proposal rejected |
| Retry | second attach cannot change smell into color |
| Final emission | generic scene for a sound contract is replaced |
| Evaluator | shared contract fails a topical miss and passes a real smell answer |
| Discourse commit | same contract id does not rewrite focus |

## 15. Real-Path Integration Results

Two `/api/chat` tests drive raw text through production orchestration with the model stubbed:

1. "I examine the iron latch." then "What does it smell like?"
   - contract dimension is `smell`
   - referent provenance is `inherited_discourse`
   - target is the latch
   - obligation carries `resolution_contract_id`
   - the narration payload contains the same dimension and target
   - the evaluator receives that contract and marks the smell answer satisfied
2. "What does the cooking pot smell like?" with a generic gate-crowd candidate
   - the emitted text is the non-inventive smell fallback, not the generic scene

## 16. Focused Live-Probe Results

Not run.

`OPENAI_API_KEY` is unset and the repo has no `.env`. Level 2 was not started. Focused live turns used: 0.

## 17. Smoke-Gate Results

Not run. Level 1 is healthy, but Level 2 did not run, so the smoke gate was not authorized by the funnel.

Smoke runs: 0. Smoke turns: 0.

## 18. Full-Gate Results

Not reached.

Full-gate runs: 0. Full-gate turns: 0.

## 19. Failure Clustering

No synthetic campaign was run, so there is no new player-facing failure cluster to score.

Deterministic failures found during implementation were fixed before the recorded test run:

- "smell like" was being parsed as an explicit target named "like", which blocked pronoun binding
- procedural chat skipped contract construction because narration was called with no resolution

## 20. Regression Results

Focused band, 113 passed, 0 failed, before a one-line prompt-article correction:

- `tests/test_pr_br_resolution_contract.py`
- `tests/test_pr_bp_live_resolution_routing.py`
- `tests/test_playability_eval.py`
- `tests/test_bounded_improvisation_authority.py`
- `tests/test_perception_narration_authority_audible_non_invention.py`
- `tests/test_playability_smoke.py`
- `tests/test_prompt_context_public_prompt_boundary.py`

After the correction, the 21 PR-BR tests passed again. No pre-existing failure was reclassified as a PR-BR regression in this band.

Preserved by those suites: PR-BN incidental versus consequential routing, NPC claim versus world truth, interaction-obligation fallbacks, perception non-invention, and evaluator behavior when no contract is present.

## 21. Known Limitations

- This is not a general parser or coreference engine. Only the PR-BQ dimensions and five discourse slots are supported.
- An explicit nominal target is a shallow pattern. Unusual phrasing can remain unresolved and ask for clarification.
- Appearance answers are judged more loosely than smell, sound, wear, or source, so a visual answer is less likely to be replaced.
- Final emission will not invent the missing sensory detail. The replacement is a safe inability line.
- The evaluator can pass intent when the shared assessment says the text satisfies the contract. Other gates, including malformed output, still apply.
- Discourse focus is not a history of every mentioned noun. A scene with several unnamed objects and no prior inspect slot stays unresolved.
- Live narration quality is unmeasured.

## 22. Cost / Turn Accounting

| Bucket | Used |
|---|---:|
| Focused live turns | 0 |
| Smoke-gate turns | 0 |
| Smoke runs | 0 |
| Full-gate turns | 0 |
| Full-gate runs | 0 |

API token or monetary cost: unavailable. No model call was made.

The unused budget was not spent. The funnel stops before Level 2 when a live model cannot be called.

## 23. Whether PR-BR Is Complete

No. Implementation and deterministic/real-path tests are in place. The required synthetic funnel did not reach a healthy Level 2, smoke gate, or full gate.

PR-BR remains open.

## 24. Whether Human Playtest Is Recommended

No.

HUMAN PLAYTEST: NOT RECOMMENDED.

## 25. Recommended Next Step

Provide model credentials and run Level 2 only: at most 10 focused live turns covering one perception dimension, one claim follow-up, one cross-turn referent, and one action request. If those probes show a systemic semantic miss, stop, repair from the deterministic contract trace, and do not start the smoke gate. Do not start a full gate until a smoke gate is healthy. Do not create the completion commit until that evidence supports a human playtest.
