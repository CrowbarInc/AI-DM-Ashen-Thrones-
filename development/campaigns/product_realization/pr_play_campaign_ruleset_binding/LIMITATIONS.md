# Limitations

- Combat, skills, conditions, non-combat resolution and PF character import retain explicit legacy pathways. The new generic policy boundary is campaign-selected; this is not complete migration of the gameplay turn spine.
- Existing unbound campaigns without explicit authoritative metadata are ambiguous. Generic policy delegation refuses them. The existing legacy gameplay compatibility path remains; no automatic identity is fabricated and no manual resolution editor was built.
- One active campaign/character per configured data directory. Campaign id scoping is not a new authentication system or multi-tenant campaign database.
- No multi-process write coordination or session CAS revision was added. Binding replacement is rejected and omission preserved; unrelated stale session fields retain existing behavior.
- Single session file replacement is atomic. New Campaign and snapshot restore retain best-effort multi-file rollback, not crash-atomic transactions. Windows directory fsync remains unavailable.
- Repeated New Campaign requests create fresh campaigns under existing semantics; no request-id ledger was added for campaign creation.
- Identity-only registered systems are not playable. Equipment consequences remain unresolved and execution blocked. No mechanical conversion or ruleset switching exists.
- Existing inherited regression failures remain. Broad gameplay metrics are historical and no quality improvement is claimed.
