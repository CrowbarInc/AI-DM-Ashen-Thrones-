# PR-DI Tool Utility Analysis

Candidate C had zero invalid tool names, but tool utility varied sharply.

| scenario | useful calls | weak/redundant calls | could terminate earlier |
| --- | --- | --- | --- |
| S1 | `inspect_permitted_npc_context` was relevant but argument/result quality was weak. | The run ended without `propose_action` or `request_action_execution`; the inspection did not advance execution. | Yes, after identifying a simple social ask it could have proposed/executed or returned a clarification. |
| C1 | `request_rules_adjudication` directly tested the rain/assassination mechanic and got `unsupported`. | None material. | Yes, the final unsupported answer after round 1 was enough. |
| compound | `propose_action` was relevant to the pry attempt. | `action_type=pry_off` failed accepted shape; no separate supported approach step. | Yes, after shape rejection it could stop with unsupported pry and optional supported approach clarification. |
| ambiguous | NPC inspection was relevant to possible addressee context. | It guessed `tavern_runner`, then repeated permission-denied `query_known_entities` twice. | Yes, after identifying unresolved references it should have asked for clarification. |
| declared_canon | `propose_action` exposed the unsupported world-update attempt. | The proposed `update_world_state` operation was not a valid representation and depended on engine rejection. | Yes, after one rejection it could stop. |
| mechanical_dump | `request_action_execution` exposed unsupported direct HP setting; NPC context showed no permitted hidden motives. | Querying `patrol map` hit permission denial; no supported alternative was available. | Yes, after unsupported/permission denial was established. |

Conclusion: valid tool-call discipline is necessary but insufficient. C needs better termination, shape construction, and clarification policy before it can be considered an execution architecture.
