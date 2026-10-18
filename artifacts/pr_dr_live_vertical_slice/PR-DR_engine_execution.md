# PR-DR Engine Execution

Accepted IC actions call the existing exploration or social resolver on the disposable world. Deterministic response text comes from that resolver path, not from the model.

| ID | Executed | Resolver calls | Reason | Scene after | Response |
| --- | --- | --- | --- | --- | --- |
| DR01 | False | none | no_hand_authored_action | waystation_courtyard | That in-character request is not a supported mechanic. No state was changed. |
| DR02 | False | none | ooc_cannot_execute_authoritative_gameplay | waystation_courtyard | That correction concerns a committed action. Explicit adjudication is required. No state was changed. |
| DR03 | False | none | ooc_cannot_execute_authoritative_gameplay | waystation_courtyard | Correction noted. It does not change committed state. |
| DR04 | False | none | ooc_cannot_execute_authoritative_gameplay | waystation_courtyard | Out-of-character question noted. No gameplay action was executed. |
| DR05 | True | game.social.resolve_social_action | accepted_by_engine | waystation_courtyard | The street beyond the gate is the north road. |
| DR06 | False | none | ooc_cannot_execute_authoritative_gameplay | waystation_courtyard | Rules question deferred. No gameplay action was executed. |
| DR07 | False | none | unresolved_mode_not_executed | waystation_courtyard | Message deferred. No gameplay action was executed. |
| DR08 | True | game.exploration.resolve_exploration_action | accepted_by_engine | waystation_street | The waystation street runs north from the courtyard gate. A notice board stands by the road. |
| DR09 | False | none | ooc_cannot_execute_authoritative_gameplay | waystation_street | Out-of-character question noted. No gameplay action was executed. |
| DR10 | True | game.exploration.resolve_exploration_action | accepted_by_engine | waystation_street | The board names the north road past the waystation. |
