# PR-DG Transaction Safety

There is no engine undo. One successful resolver call commits on the harness copy. A later rejected step does not roll the earlier step back. Discarding a deep copy is not rollback, and these rows do not claim that it is.

## successful_single_action

```json
{
  "transaction": "atomic_per_resolver_call",
  "status": "completed",
  "executed": true,
  "state_changed": true,
  "authority_violations": []
}
```

## invalid_action

```json
{
  "transaction": "rejected_before_execution",
  "status": "completed",
  "executed": false,
  "errors": [],
  "cleared": [
    "duke_of_nowhere"
  ],
  "scene_same": true,
  "clues_same": true,
  "pressure_delta": 1
}
```

## partially_valid_compound

```json
{
  "transaction": "partially_committed",
  "status": "partial",
  "steps": [
    {
      "step_id": "approach",
      "status": "committed",
      "code": null
    },
    {
      "step_id": "pry",
      "status": "unsupported",
      "code": "unsupported"
    }
  ]
}
```

## invalid_second_step

```json
{
  "transaction": "partially_committed",
  "status": "partial",
  "executed": true,
  "errors": [],
  "forbidden_steps": [
    "bad"
  ],
  "steps": [
    {
      "step_id": "ask",
      "status": "committed",
      "code": null
    },
    {
      "step_id": "bad",
      "status": "rejected",
      "code": "forbidden_field"
    }
  ],
  "note": "a forbidden field rejects that step; an earlier valid step can still commit"
}
```

## repeated_action_request

```json
{
  "transaction": "partially_committed",
  "status": "partial",
  "codes": [
    "ok",
    "already_applied"
  ]
}
```

## read_only_query

```json
{
  "code": "ok",
  "mutation": "none",
  "hash_unchanged": true,
  "authority_violation": null
}
```

## read_only_combat_preview

```json
{
  "code": "ok",
  "mutation": "none",
  "hp_unchanged": true,
  "result_keys": [
    "check_prompt",
    "combat_active",
    "player_can_act",
    "target_present",
    "would_require_roll"
  ],
  "authority_violation": null
}
```

## world_clock_advancement

```json
{
  "first": "ok",
  "second": "already_applied",
  "time_pressure": 1,
  "tick_events": [],
  "single_increment": true
}
```

## hidden_information_request

```json
{
  "field_code": "permission",
  "npc_code": "ok",
  "hidden_in_results": false,
  "authority_violations": []
}
```

## unauthorized_state_mutation

```json
{
  "code": "permission",
  "mutation": "refused",
  "hp_unchanged": true,
  "authority_violation": null
}
```

## How to read the ten rows

1. Successful single action: one social resolver call commits. The transaction is one resolver call, not a multi-step transaction.
2. Invalid action: unknown id `duke_of_nowhere` is cleared, the plan stops before a resolver, scene and clues stay put. The shared tick still advances `time_pressure` by 1, which is chat's order.
3. Partially valid compound: the approach commits and the pry is `unsupported`. Partially committed.
4. Invalid second step: the ask commits and the step that carries `hit_points` is rejected. Partially committed. The forbidden step does not run.
5. Repeated action: the second `request_action_execution` for the same step id returns `already_applied`.
6. Read-only query: `inspect_visible_scene` leaves the state hash unchanged.
7. Read-only combat preview: HP is unchanged and `roll_die` is not called.
8. World clock: the first time tool commits `time_pressure` 1. The second returns `already_applied`.
9. Hidden-information request: `hidden_facts` is `permission`. The fixture hidden string is not in the tool result.
10. Unauthorized HP write: `permission`, mutation `refused`, HP unchanged.

Compound execution is not atomic. A well-formed unsupported second step is partially committed. A forbidden field on a later step is also partially committed when an earlier step was valid. An unknown entity id stops the plan before any step.
