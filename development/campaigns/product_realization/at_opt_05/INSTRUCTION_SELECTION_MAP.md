# Instruction selection map

Primary narration is assembled in `game.gm.build_messages`, which calls `game.prompt_context.build_narration_context`. The API narration owner is `game.api._build_gpt_narration_from_authoritative_state`. It passes `prompt_profile="manual_play_auto"`. Compact selection is a payload choice inside that narration request. It is not a separate provider route. Expression calls stay on their own owner and are outside this gate.

`build_messages` defaults `prompt_profile` to `"full"`. That profile never selects compact. Only `manual_play_auto` consults the gate, and `manual_play_compact` forces the compact list.

## Paths

| Path | Owner | What it builds |
| --- | --- | --- |
| Full instructions | `build_narration_context` instruction list, then narrative-mode lines, then policy tail | The 78-line list on the F3 attached rebuild |
| Compact instructions | `_compact_manual_play_instructions` | A short list, plus the same narrative-mode lines when a plan is present |
| Selector | `_should_use_manual_play_compact_prompt` | Called after `must_advance_scene` is overwritten from the transition node |
| Public shape | `project_narration_payload`, then `project_public_payload` | Strips private keys. `_dedupe_provider_payload_instructions` drops user lines already present in the system prompt |

When compact is selected, the same function also limits visible facts to 5, selected memory to 6, and recent log to 4, and it removes `fallback_behavior`, `anti_railroading_contract`, `context_separation_contract`, `player_facing_narration_purity_contract`, `social_response_structure_contract`, `interaction_continuity_contract`, and `first_mention_contract` before public projection. On the F3 public payloads, the only top-level key present in the full request and absent from the forced compact request was `first_mention_contract` (159 bytes). The other named contracts were already absent from the public full payload.

## Eligibility predicates

`_should_use_manual_play_compact_prompt` returns true only when all of the following hold:

| Predicate | Source | Compact if true |
| --- | --- | --- |
| Profile is `manual_play_compact` | Caller | Always compact. Later predicates are skipped |
| Profile is not `manual_play_auto` | Caller. `"full"` is the `build_messages` default | Never compact |
| `narration_obligations.is_opening_scene` | `derive_narration_obligations` from turn counter and visit count | Blocked |
| `narration_obligations.must_advance_scene` | Starts false in `derive_narration_obligations`. Overwritten from `transition.transition_required` | Blocked |
| `resolution.requires_check` | Resolution semantics on the head state | Blocked |
| Non-empty `uncertainty_hint` | `collect_narration_context_call_kwargs` for a direct question without a known answer, unless social authority suppresses it | Blocked |
| `active_topic_anchor.active` | Topic anchor on the payload | Blocked |
| Non-empty `follow_up_pressure` | Follow-up pressure derived from the recent log and the utterance | Blocked |

There is no second fallback that restores the full list after compact is chosen. Public projection and system-prompt dedupe still run on both lists.

`must_advance_scene` is not read again when narrative mode is rendered. `_build_narrative_mode_instructions` ignores the obligation argument and uses `narrative_plan.narrative_mode_contract`, which was built earlier, while `must_advance_scene` was still false.

## Decision table

Measured on the F3 pre-continuation snapshot with current `build_messages`. “Attached” keeps the stored CTIR and plan. “Detached” calls `detach_ctir` first, which is what the API does when `resolution` is not a dict.

| Condition | Compact eligible? | Reason |
| --- | --- | --- |
| Ordinary continuation, attached plan (“I wait and listen.”) | No | `must_advance_scene` true from the same-scene stamp. Mode stays `action_outcome` |
| Ordinary continuation, CTIR detached | Yes | No transition node. No other blocker. 11 instructions |
| Required scene transition (`resolved_transition` or `arrived_at_scene` to another scene) | No | Synthetic plans set `transition_required` and mode `transition` |
| Pending attached plan from the previous resolved turn | No | The stored node is still required, even for a new utterance |
| Completed different-scene transition | Not in the F3 snapshot | Synthetic `resolved_transition` stays required. No recorded completed handoff was replayed |
| Simple physical action, attached (“I step back from the notice board.”, “I push the nearest crate.”) | No | Same stamp. The utterance does not recompute the node inside `build_messages` |
| Simple physical action, detached | Yes | Compact selected. This is the no-resolution API shape, not the attached reconstruction |
| Complex or explicit travel sentence (“I walk through the gate into the district.”), attached | No | Still the old same-scene node. The sentence does not create a transition |
| Same travel sentence, detached | Yes | No resolution and no plan, so the travel sentence is not a transition signal |
| NPC dialogue (“Hello, Gate Guard.”) | No | Attached: advance flag and follow-up pressure. Detached: follow-up pressure alone |
| Scene inspection (“I look closely at the notice board.”) | Attached no; detached yes | Inspection does not clear or set the stamp |
| Scene question (“What do I see?”) | No | Uncertainty hint, plus the advance flag when attached |
| Investigation recall (“What did we already learn about the patrol?”) | Attached no; detached yes | No uncertainty object on this wording. Attached block is only the advance flag |
| Opening scene | No | `is_opening_scene` blocks before the transition flag matters |
| Explicit `manual_play_compact` | Yes | Profile short-circuit. The advance flag does not apply |
| Profile `full` | No | Gate returns false immediately |

Provider routing does not consult this gate. A compact primary narration would still be a `gm.call_gpt` narration request if a caller dispatched it. This cycle did not dispatch one.
