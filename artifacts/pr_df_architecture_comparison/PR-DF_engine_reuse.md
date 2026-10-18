# PR-DF Engine Reuse

The prototype is a harness around existing owners. It is not a second engine. This cycle does not build it.

## Smallest interfaces to reuse

| Interface | Call | Role in B and C |
|---|---|---|
| Fixture state | `create_fresh_session_document`, PR-DE `_social` / `_explore`, K1 and B1 builders | Same initial copy for every candidate. |
| Referents | `build_canonical_referent_catalog` | Validate ids. |
| Contract | `attach_interaction_obligation` with `enable_model_interpretation=False` | Build the contract for a step from executor-authored step text, not from model prose stored as canon. |
| Selector | `select_ordinary_resolver`, `select_resolver_family` | Override the planner's proposed family when they disagree. |
| Social / exploration | `resolve_social_action`, `resolve_exploration_action`, `resolve_noncombat_action` | Execute a permitted step. |
| Combat | `resolve_attack`, `resolve_skill`, `player_can_act` | Execute or refuse combat. Preview must not call the rolling functions. |
| Mutation | `_apply_authoritative_resolution_state_mutation` on the copy | Only writer for resolver results. |
| Time | `advance_world_tick`, `advance_clock` | Once per turn, in the harness. |
| Visibility | `build_narration_visibility_contract` | Filter query and tool output. |
| Improvisation | `validate_bounded_improvisation_proposal` | Accept or reject ledger proposals. |
| Narration payload | Existing `build_messages` path used by `measure_pr_de_affordability.py` | Same payload for A, B, and C after resolution. |
| Validation | Existing policy and emission checks when the live arm runs | Unchanged reject rules. |
| Dice | The `roll_die` patch pattern from the B1 builder | One stream for all candidates. |
| Bytes | PR-DE recorder: UTF-8 length and `ceil(chars/4)` | Same accountant. |

## Missing interfaces

| Missing piece | Why it is small | Why it is not optional |
|---|---|---|
| Plan JSON validator | Closed enum, four steps, dependency cycle check, drop forbidden fields. | Without it, B can smuggle a write. |
| Step runner | Loop: snapshot, contract, selector, one resolver, mutator, restore on exception. | Without it, B and C have no shared commit rule. |
| Tool dispatcher | Eight names, allow-lists, call the step runner for the two write tools. | Without it, C is unspecified in code. The spec itself is in `PR-DF_candidate_C.md`. |
| Read-only adjudication preview | Wrap precondition checks without `resolve_attack` / `resolve_skill`. If a clean wrap is impossible, return `unsupported`. | A preview that rolls breaks scenario 8 and 14. |
| Hidden-string scanner | Fixture list versus player text, tool JSON, and provider input. | Disclosure checks must be mechanical. |
| Isolated runner | In-memory copies only. Refuse paths under `data/session.json` and `data/world.json`. | Production saves are already dirty and must stay that way. |

No new domain owner. No new clue writer. No new clock. The dispatcher and the runner call the modules above.

## Effort estimate

These are planning ranges for a later cycle, not a quote and not a schedule commitment. One developer familiar with this tree.

| Slice | Range | Notes |
|---|---|---|
| Deterministic preflight for Candidate A on the twelve existing fixtures | 1–2 days | Mostly a caller around `measure_pr_de_affordability.py` plus the state tuple. No model. |
| Hypothetical scenarios 10–14 as fixture functions | 1–2 days | Copies and assertions. Scenario 12 depends on tick behavior that must be observed, not assumed. |
| Plan validator and step runner | 2–4 days | The risk is deep-copy correctness, not the schema. |
| Tool dispatcher over that runner | 1–2 days | Thin. Preview refusal is the careful part. |
| Scripted B and C transcripts (hand-written plans and tool lists, no provider) | 1–2 days | Proves authority before any live call. |
| Optional live arm | separate cycle | Needs a provider budget, a pinned model name, and the stop conditions. Not estimated as part of the preflight. |

Total for the authority preflight, including scripted B and C: about one to two weeks. That is an estimate from the surface area above. It is not evidence that the work will land in that window.

A rewrite of `chat`, the parser cascade, or the narration payload is not in this estimate. If the step runner cannot drive the resolvers without those rewrites, the experiment stops and the decision becomes C — current architecture constraint. That stop is part of the design.

## Competing owners to avoid

- A plan interpreter that sets `resolution["world_updates"]` from model JSON.
- A tool that calls `_apply_post_gm_updates`.
- A second improvisation ledger.
- A second clock advanced inside the planner.
- Using `interpret_for_contract` as the B planner while also scoring it as part of A.
