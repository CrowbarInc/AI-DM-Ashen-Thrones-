# Consequence Model

Each successful state change appends one ledger item under `physical_consequences`:

- id `pc_` plus a hash
- target id
- action
- prior state
- resulting state
- campaign id
- scene id
- turn
- provenance `physical_adjudication`

An identical prior and result does not add another item. Posture and character position live on the ledger. Open state and object position live on the fact or the overlay. Narration is copied from `engine_publication` and is not a separate state write.
