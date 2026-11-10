# Mutation Integration

`stage_grounded_marking` builds an `add_marking` request and a `set_marking_visibility` request and calls `prepare_marking` and `prepare_visibility`. Visibility authorization is the existing private assertion inside the marking service. Default classification is `visible`. An utterance containing secretly, concealed, or in secret uses `concealed`.

The marking request id is `sha256(operation_id|add_marking)`. Visibility uses `sha256(operation_id|set_visibility)`. A stored mark with the same request id and the same content is rebuilt from the stored mark, including `expected_revision = applied_revision - 1`, so the digest matches and the receipt replays. Different content on the same request id returns `conflicting_request` and does not save. A later revision does not turn an exact replay into a new mark.

A successful add plus visibility moves the object revision by two. The mark exists on the inventory row, with visibility metadata, and a receipt under `object_marking_receipts`. Narration is not the store of the mark.

Identity is not created or migrated by this path. The instance must already pass `inspect_object_identity`.
