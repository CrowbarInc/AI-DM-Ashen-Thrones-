# PR-DF Current Architecture Map

Trace of the code on HEAD `d31beb7` plus the dirty Product Realization worktree. Locations are the functions a later harness must call or avoid. A function's presence is not a correctness claim.

## Stage order

`AUTHORITATIVE_TURN_STAGE_ORDER` in `game/api_turn_support.py` (lines 47–57):

1. `player_input`
2. `intent_normalization_expansion`
3. `action_classification`
4. `engine_resolution`
5. `authoritative_state_mutation`
6. `prompt_context_construction`
7. `gpt_narration`
8. `affordance_derivation`
9. `response_debug_packaging`

Validation and finalization sit after narration, inside the narration builder and `finalize_player_facing_emission` (`game/final_emission_runtime.py`). They are not a named stage in that tuple.

## Path A — free text (`chat`)

Entry: `game/api.py` `chat` (line 5433). Loads campaign, character, session, world, combat, conditions, and the active scene from the production stores.

| Step | Where | What it does |
|---|---|---|
| Load | `chat` | Reads production JSON. This is why the comparison harness must not call `chat` on the developer save. |
| Turn counter | `chat` | Increments `session["turn_counter"]`. |
| World tick | `advance_world_tick` in `game/world.py` (line 325), called near line 5475 | Advances projects, faction pressure, and mobile NPCs with `agenda_move_to_scene_id`. Appends player-facing tick events. Saves the world. |
| Pressure clock | `advance_clock(session, "time_pressure", 1)` near line 5480 | Plus one on every chat turn, before the utterance is classified. Cap is 0–10. |
| Segment | `segment_mixed_player_turn` in `game/intent_parser.py` (line 378) | Splits spoken text, declared action, contingency, and an embedded adjudication question. |
| Address | `resolve_directed_social_entry`, `resolve_declared_actor_switch` | Binds an addressee from vocative, continuity, or an open solicitation. |
| Route label | `choose_interaction_route` in `game/interaction_routing.py` (line 365) | Coarse route. The ordinary contract is the later selector. |
| Contract | `establish_ordinary_gameplay_contract` in `game/ordinary_semantic_ownership.py` (line 142) | Calls `attach_interaction_obligation` (`game/live_resolution.py` line 384) with model interpretation off. If the fast path abstains and a model proposal is marked appropriate, it drops the contract and calls again with `enable_model_interpretation=True`. |
| Model proposal | `interpret_for_contract` in `game/semantic_interpreter.py` (line 241) | One structured completion, temperature 0, max 400 output tokens. Skipped when `ASHEN_DISABLE_LIVE_INTERPRETATION` is set. Malformed output does not become a target. |
| Resolver pick | `select_ordinary_resolver` (line 196) | Returns `generation`, `adjudication`, `combat`, `travel`, `exploration`, `social`, or `world_action`. Raw text is not the selector. `select_resolver_family` (`game/contract_adjudication_bridge.py` line 440) names an adjudication family from the contract subject only. |
| Parser cascade | `chat` lines 5656–5796 | Passive wait, pursuit, exploration parse, world-action recovery, social parse, dialogue-first, generic `parse_intent`. Each candidate passes `stage_permitted` and `reject_contradicting_action`. An attack parsed while not in combat is dropped. |
| Resolve | `_resolve_engine_noncombat_seam` (`game/api.py` line 3635) or `resolve_attack` | `classify_noncombat_kind` routes `exploration` or `social` into `resolve_noncombat_action`. Other types keep a legacy branch. Downtime returns `route="none"` with `downtime_engine_not_wired`. |
| Mutate | `_run_resolved_turn_pipeline` (line 3530) then `_apply_authoritative_resolution_state_mutation` (line 1668) | Applies world updates, scene transition, social leads, and clue discovery from the resolution object. Narration is built only after this returns. |
| Narrate | `_build_gpt_narration_from_authoritative_state` (line 2363) | Builds the provider payload from post-resolution state. Latency key `gpt_call`. |
| Validate | Response-policy enforcement in `game/gm.py`, `game/gm_retry.py`, final emission gate | Up to 2 targeted retries (`MAX_TARGETED_RETRY_ATTEMPTS`). |
| Post-narration writes | `_apply_post_gm_updates` (line 1188) and `_post_gm_adoption_gateway` (line 1064) | Gateway mode is `observe_only`. It records the branch and still allows legacy adoption when shape checks pass. |
| Continuity | `_update_interaction_context_after_action`, speaker adoption, discourse focus | NPC identity and conversational focus persist on the session. |

Pending checks and off-scene social targets skip the provider (`_build_check_prompt_gm_output`, `_build_offscene_target_gm_output`).

## Path B — structured client action (`action`)

Entry: `game/api.py` `action` (line 4292).

`roll_initiative`, `attack`, `skill_check`, `cast_spell`, and `end_turn` call combat resolvers directly. `exploration` and `social` normalize a payload with `normalize_scene_action` (`game/scene_actions.py`) and call the same noncombat seam. This path does not establish the ordinary contract before resolution. The contract is attached later inside `_run_resolved_turn_pipeline`.

PR-CK recorded restored parity for an investigate of the desk, for "I talk to Tavern Runner," and for "Describe the gate" staying non-social. Parity is not universal: the selector and the parser cascade still differ by entry point.

## Authority checks

`game/state_authority.py` names five domains: `world_state`, `scene_state`, `interaction_state`, `player_visible_state`, `hidden_state`. GPT, model, and OpenAI owner strings are in `_NON_AUTHORITATIVE_MUTATION_OWNERS` and cannot pass `assert_owner_can_mutate_domain`.

Hidden facts are carried for the engine and withheld from the player projection. `game/prompt_context.py` tells the model to stay inside `narration_visibility`. `game/narration_visibility.py` builds that contract. The instruction is a prompt constraint. The visibility object is the authoritative filter the tools in Candidate C must call.

`game/gm_resolution_decision.py` builds `gm_resolution_decision` from the contract. The narration prompt says the decision-facing recipe grants no new authority.

## State that already persists

| Concern | Owner |
|---|---|
| Scene and session | `game/storage.py` `save_session`; scene transition helper in `api.py` |
| World flags, projects, factions, NPC location | `game/world.py` |
| Clocks | `game/clocks.py` on the session |
| Combat HP | `game/combat.py` `resolve_attack` writes `enemy["hp"]["current"]` |
| Conditions | combat condition helpers |
| Clues and leads | `game/leads.py`, social reveal helpers |
| NPC address and discourse focus | `game/interaction_context.py`, `game/discourse_state.py` |
| Low-consequence invention | `game/bounded_improvisation.py` ledger key `bounded_improvisation` |
| Player travel commitment | `game/player_commitment.py` |

## Working, incomplete, defective, historical

**Working enough to reuse**

- One resolution contract per ordinary chat turn, built before specialized parsers.
- Resolver family selection from the contract subject.
- Social, exploration, and combat resolvers that return structured results.
- Scene transition and clue discovery applied from that result before narration.
- Visibility contract and hidden-fact terms.
- Bounded improvisation that rejects consequential, mechanical, and hidden proposals (`kind:consequential`, `content:mechanical_authority`, `content:hidden_information`).
- Check-required short circuit that does not narrate a rolled outcome.
- PR-DE fixture builder: `tools/measure_pr_de_affordability.py` reconstructs twelve payloads without a model call and without writing production saves.
- Latency keys already present: `intent_classification`, `engine_resolution`, `prompt_construction`, `gpt_call`, `retry_loop_total`, `fallback_repair`, `final_emission_gate`.

**Incomplete**

- Downtime and rest types are recognized and not resolved.
- No general inventory ledger API.
- No multi-step plan type and no undo after `_apply_authoritative_resolution_state_mutation`.
- Post-narration gateway does not enforce semantic policy.
- Model interpretation is a single proposal with a closed operation enum (`perceive`, `inspect`, `ask`, `repeat`, `confirm`, `follow`, `act`, `unresolved`). It is not a plan and it is not a tool loop.
- World tick movement applies only to NPCs whose `availability` is `mobile` and who carry a destination id. This cycle did not verify that any authored frontier NPC is mobile.

**Known defects on this tree (not architectural laws)**

- PR-DE required suite: 326 passed, 27 failed, same set before and after deduplication.
- Shared pipeline: 41 passed, 24 failed. PR-DE names dialogue-lock, retry, notice-board mixed-turn, and strict-social cases among them.
- Authored-knowledge failures left unrepaired, including notice-board HTTP cases.
- M1, "I walk closer to the notice board," did not bind an exit. Recorded limitation, not a new measurement.
- PR-CK: two pressure tests still fail because the emitted beat lacks the interruption phrases those tests require. "I persuade the gate guard to let me pass" reaches a diplomacy check and does not call the provider.
- `test_manual_play_latency.py`: 5 passed, 1 failed, and PR-DE judged that failure independent of contract omission.

**Historical compatibility machinery**

- Dual entry: `action` versus `chat`.
- Parser cascade retained behind `stage_permitted` after the contract exists.
- Legacy noncombat branch when classification route is `none`.
- Post-GM adoption kept as observe-only rather than removed.
- `api.py` copies `conversational_memory_window` from the surviving `response_policy` child when the top-level key is absent (PR-DE).
- PR-DE hash is `build_messages` with `ensure_ascii=False`. A later API rewrite may use `ensure_ascii=True`. That rewrite is not the benchmark hash.

## Reuse set for A, B, and C

These stay the only writers of world truth:

- `construct_resolution_contract` / `attach_interaction_obligation`
- `select_ordinary_resolver` and `select_resolver_family`
- `resolve_noncombat_action`, `resolve_social_action`, `resolve_exploration_action`, `resolve_attack`, `resolve_skill`
- `_apply_authoritative_resolution_state_mutation` for applied results
- `advance_world_tick` and `advance_clock` once per committed turn
- `build_narration_visibility_contract` and the referent catalog
- `validate_bounded_improvisation_proposal`
- Existing narration validators and `build_messages`
- PR-DE fixture constructors and `create_fresh_session_document`

B and C may add a non-authoritative proposal layer in front of that set. They may not add a second mutator.
