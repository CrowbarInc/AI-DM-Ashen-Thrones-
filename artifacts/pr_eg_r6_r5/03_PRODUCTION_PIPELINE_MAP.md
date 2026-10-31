# 03 — Production Pipeline Map

The fifteen-box diagram in the cycle brief is an illustration. Production does not implement those boxes as separate stages. This map follows `POST /api/chat` in `game/api.py` `chat()` when `ASHEN_UNIFIED_SEMANTIC_PLANNING` is on and `ASHEN_HOST_CONSTRAINED_CANDIDATES` is off.

## Actual order

1. Communication mode. An OOC turn returns before the planner.
2. Load campaign, character, session, world, scene. `synchronize_scene_addressability`.
3. `deterministic_conversational_decision` (`game/conversational_orchestration.py`).
4. That function calls `planning_decision` first.
5. `planning_decision` returns `None` unless the turn is a migrated information turn. Live interpretation then runs. A named addressee, or a prior plan plus a correction, follow-up, or question shape, is required. A question with no name and no prior never enters the planner.
6. `authorize_information_turn` does the rest of interpretation, binding, retrieval, correspondence, sufficiency, and the authorized line in one function. It does not mutate the world.
7. Non-EXECUTE decisions return through `_nonmutating_conversational_decision_response`: optional expression, then the immutable seal.
8. EXECUTE ASK continues into social resolution. `locked_plan_for_social_turn` consumes the already locked plan. It does not plan again when the binding matches.

## What happens inside `authorize_information_turn`

These are gates inside one function, in this order:

1. **Proposal.** `propose_semantic_plan`. One provider call unless a process-local `plan_proposer` is installed. The candidate gate, if on, replaces this call. It is off.
2. **Schema.** `validate_plan_schema`. A malformed plan becomes the line "I can't reliably answer that just now." Sufficiency is not a model field.
3. **Referent bind,** only when `referent_operation` is present. `bind()` rejects a bad target, a stale correction, an unexpected operation on a fresh question, or an unwitnessed delta. Failures become clarification or the revision line. They do not reach retrieval.
4. **Role and witness gates,** when a request proposition is present. Evidence spans must occur in the utterance. `argument_identity` must hold. Failure reason: `unwitnessed_referent_request` or `invalid_role_or_prior_binding`. Retrieval does not run.
5. **Addressee grounding.** A leading vocative selects the addressee. Two mentions and no unique vocative clarify before retrieval. An interior name is not an addressee when a vocative exists.
6. **Source scan.** `_topic_rows` loads every topic for the addressed NPC. `npc_source_permitted` marks the rest `hidden`. Hidden rows are not ranked and are not sent to the planner as candidates.
7. **Correspondence.** For each visible source, a source proposition with the same epistemic status is required. If it is missing, coverage is `unknown` and `coverage()` is not called. Otherwise `coverage()` runs, then `_conservative` can only downgrade the host label using `proposed_coverage`. It cannot upgrade a miss.
8. **Selection.** One direct source is selected. Several directs clarify. Otherwise one partial is selected. A hidden row that lexically covers the requested relationship becomes `refusal` / `unauthorized_source`. Otherwise `unknown` / `no_relevant_source`.
9. **Lock.** `answer_sufficiency` is derived from `response_kind`. The host line is built by `_host_line` / `_select`, including rumor and belief prefixes.

## Expression and sealing

Expression (`apply_expression` / `request_expression`) runs on the host line when `build_expression_contract` returns a contract. Some clarification and failure templates do not. The sealed `accepted_response.text` is the delivered line. History must match it.

A direct selection can attach `topic_rec`. Social resolution may then record a clue for that public topic. Hidden sources are not selected, so they do not take this path.

## Stages the illustration names that are not separate

| Illustrated stage | Where it actually is |
|---|---|
| Intent interpretation | Provider proposal plus schema act check |
| Referent binding | `bind()`, only if the proposal carries an operation |
| Question proposition | Provider `request_proposition`, then witness gates |
| Evidence retrieval | Full topic scan of the addressed NPC, not the model's candidate list |
| Source proposition | Provider `source_propositions`; missing or epistemic mismatch skips `coverage()` |
| Evidence correspondence | `coverage()` plus `_conservative` |
| NPC knowledge / disclosure | `hidden` via `npc_source_permitted`, then lexical hidden-hit refusal |
| Answer sufficiency | Derived from the selected kind. Not an independent classifier. |
| Authorized response plan | The locked plan and `_host_line` |
| Bounded expression | Optional, after the plan is locked |
| Final adoption | Seal and history in the API response path |

## Diagnostic interception limits

These limits are why some gold arms cannot be read as "this stage does not matter" when they show no change.

- **I4 retrieval.** `candidate_source_ids` do not control retrieval. The harness filters `_topic_rows` in-process. It never inserts a source the NPC does not have. If the engine addresses the wrong NPC, that NPC's public topics are removed and the right NPC's topics are not imported.
- **I6 correspondence.** Patching `coverage()` does nothing when the proposal has no source proposition, because production assigns `unknown` before the call. `_conservative` also cannot upgrade a host miss. The arm sets `proposed_coverage` to the gold label so a model downgrade cannot undo a host match that does occur.
- **I7 sufficiency.** The harness may only downgrade an already authorized plan. Upgrading `unknown` to `direct` would invent a fact and is recorded as `upgrade_blocked`.
- **I8 plan.** Replaces the locked host line after authorization, using only a source `npc_source_permitted` already allows. It does not bypass disclosure.
- **I1–I3, I5, I9.** Replay the cached baseline proposal with labeled fields replaced. They do not take a second semantic sample. Expression may still call the provider.
