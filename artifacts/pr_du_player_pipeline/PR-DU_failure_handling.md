PR-DU Failure Handling

Covered in bridge behavior:
- malformed/missing interpretation: rejected with reason missing_record
- non-IC interpretation: rejected with reason not_in_world_action
- unresolved references: rejected with reason unresolved_references
- unknown/off-scene target: rejected with reason target_not_visible
- wrong entity kind: rejected with reason operation_incompatible_with_entity_kind
- unsupported operation: rejected with reason unsupported_operation
- unknown destination: rejected with reason unknown_destination_scene
- OOC correction: non-mutating response before resolver execution

Persistence failure was not simulated. Transaction atomicity is not claimed.
