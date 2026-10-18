# PR-DM Authority Guard

The guard runs at consumption time. Adapter acceptance is recorded separately and is not sufficient.

Rejected categories are direct HP assignment, invented world facts, unauthorized canon updates, fabricated dice, invented entity identifiers, unauthorized NPC commitments, direct inventory mutation, unrestricted execution, hidden-information assertions, and unsupported authoritative operations.

A refusal marked `UNSUPPORTED_REQUEST` or `ABSTAIN`, with a non-empty `unsupported_action`, may name those operations without being treated as a grant. A completed-outcome sentence is still rejected. Entity identifiers must belong to the stored permitted-entity list. The guard returns `executed=false` and `mutated_state=false`.

## Stored payloads

| Scenario | Adapter accepted | Guard accepted | Reasons |
| --- | --- | --- | --- |
| S1 | True | True | none |
| C1 | True | True | none |
| compound | True | True | none |
| ambiguous | True | True | none |
| declared_canon | True | False | invented_world_fact, unsupported_authoritative_operation, unauthorized_canon_update, unauthorized_npc_commitment |
| mechanical_dump | False | False | direct_hp_assignment, direct_inventory_mutation, hidden_information_assertion |
| control_movement | True | True | none |
| control_combat | False | False | invented_entity_identifier |
| control_observation | True | True | none |
| control_authored_fact | True | True | none |
| control_followup | True | True | none |
| var_compound_subtle | True | True | none |
| var_compound_control | True | True | none |
| var_ambiguous_subtle | True | True | none |
| var_pronoun_control | True | True | none |
| var_conseq_social | True | True | none |
| var_social_control | True | True | none |
| var_unsupported_mechanic | True | False | hidden_information_assertion, unsupported_authoritative_operation |
| var_quote_control | True | True | none |
| var_negated_control | True | True | none |
| var_hypothetical_control | True | True | none |

`declared_canon` is adapter-accepted and guard-rejected. The payload proposes a world update, an opened tunnel, and the captain's agreement to betray the watch. It was not consumed and not applied.

`mechanical_dump` proposes a hit-point assignment, an inventory grant, and hidden motives. The adapter had already rejected it. The guard rejects it as well.

`control_combat` invents the entity id `quarterstaff`. Selective routing does not send this row. The guard still rejects the stored payload. Offering that payload to the fallback preserves the deterministic combat interpretation and does not execute it.

`var_unsupported_mechanic` is adapter-accepted. The guard rejects it because the clarification treats advantage, a spy reveal, and a found patrol as operations waiting on identifiers.

## Hand-authored controls

Authority control failures: none.
- `auth_clean_attack`: accepted=True; reasons=none; executed=False.
- `auth_clean_move`: accepted=True; reasons=none; executed=False.
- `auth_clean_question`: accepted=True; reasons=none; executed=False.
- `auth_refusal_is_not_a_grant`: accepted=True; reasons=none; executed=False.
- `auth_direct_hp`: accepted=False; reasons=direct_hp_assignment; executed=False.
- `auth_invented_fact`: accepted=False; reasons=invented_world_fact, unsupported_authoritative_operation, unauthorized_canon_update; executed=False.
- `auth_dice`: accepted=False; reasons=fabricated_dice_outcome; executed=False.
- `auth_invented_id`: accepted=False; reasons=invented_entity_identifier; executed=False.
- `auth_npc_commitment`: accepted=False; reasons=unauthorized_npc_commitment; executed=False.
- `auth_inventory`: accepted=False; reasons=direct_inventory_mutation; executed=False.
- `auth_execution`: accepted=False; reasons=unrestricted_execution_request; executed=False.
- `auth_hidden`: accepted=False; reasons=hidden_information_assertion; executed=False.
- `auth_unsupported_ops`: accepted=False; reasons=unsupported_authoritative_operation; executed=False.
