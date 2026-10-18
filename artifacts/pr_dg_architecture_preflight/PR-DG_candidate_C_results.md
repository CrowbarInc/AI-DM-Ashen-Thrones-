# PR-DG Candidate C Results

Hand-authored tool transcripts. No tool-using model. Cap: four tool rounds. A fifth call would return `budget` and would not mutate.

Read-only tools: `inspect_visible_scene`, `query_known_entities`, `inspect_permitted_npc_context`, `request_rules_adjudication`, `propose_action`, `inspect_resulting_state`.

State-changing tools: `request_action_execution` and `advance_authorized_time`. Execution re-validates. It calls the same dispatch as B. The time tool is the shared tick; a second call is `already_applied`.

`request_rules_adjudication` for `attack` calls `player_can_act` and checks the enemy id. It does not call `resolve_attack`. For `skill` it reads `_get_skill_check_config` and does not report a guessed DC. `social_check` returns `unsupported` because a pure preview is not separated from the social resolver.

Hidden fields are not a tool output. `inspect_resulting_state` rejects `hidden_facts` with `permission`. A result that contains a fixture hidden string is replaced with an empty refusal.

| # | Status | Transaction | Rounds | Resolver recorded from execution |
|---|---|---|---|---|
| 1 S1 | completed | atomic_per_resolver_call | 3 | social |
| 2 S2 | completed | atomic_per_resolver_call | 3 | social |
| 3 F1 | completed | atomic_per_resolver_call | 3 | social |
| 4 H1 | completed | atomic_per_resolver_call | 3 | social |
| 5 M1 | completed | atomic_per_resolver_call | 3 | travel |
| 6 O1 | completed | atomic_per_resolver_call | 3 | exploration |
| 7 K1 | completed | atomic_per_resolver_call | 3 | exploration |
| 8 B1 | completed | atomic_per_resolver_call | 3 | combat |
| 9 C1 | completed | atomic_per_resolver_call | 3 | social |
| 10 compound | partial | partially_committed | 4 | generation |
| 11 ambiguous | completed | read_only | 3 | None |
| 12 courier | completed | atomic_per_resolver_call | 3 | social |
| 13 declared_canon | completed | read_only | 3 | None |
| 14 mechanical_dump | completed | read_only | 3 | None |

Where the gold transcript executes one legal step, the resulting state hash matches A and B. The compound transcript commits the approach and returns `unsupported` for the pry inside the four-round cap. Illegal transcripts that pass `hit_points` and `hidden_facts` into `request_action_execution` are refused. Goblin HP stays at the setup value on scenario 14.

This does not show that a live model would choose these tool calls.
