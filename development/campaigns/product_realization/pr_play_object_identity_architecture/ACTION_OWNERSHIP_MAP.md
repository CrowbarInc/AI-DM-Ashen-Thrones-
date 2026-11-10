# Action ownership map

Milestone: `pr_play_object_identity_architecture`.

| Operation | Current entry / semantic owner | Current write boundary / limitation | Proposed integration |
|---|---|---|---|
| Local approach/contact | conversational_orchestration -> local_interaction.resolve_transient_local_action | Transient receipt, no position/inventory/world write; experimental gate yields away | Keep T04 owner; normalize its receipt read-side, no instance creation required |
| Genuine travel | exploration.resolve_exploration_action; API _apply_authoritative_scene_transition | Scene graph/destination authority and scene/combat/session transitions | Preserve precedence; common object binding must not reinterpret destinations as contact |
| Inspection/read | referenced_surface classification -> exploration; authorized_information/clues | Classification is read-only; discovery/knowledge applied by existing API seams | Add current-instance inspection branch with disclosure filter; never bypass hidden gates |
| Acquisition | items_added/items_removed projection; defaults/importer bootstrap rows | No general gameplay acquisition writer found; projection may contain explicit synthetic resolver effects | Future ownership service must validate an actual transfer/mint before any acquisition receipt |
| Inventory transfer | No general semantic writer found | No atomic cross-host transfer/instance invariant today | Instance owner stages source removal/destination insert once under API scope |
| Equipment changes | No generic equip relation writer found; attacks are separate | Clothing/slot/part binding absent | Generic wearing/wielding relation with adapter-specific legality, later phase |
| Object manipulation/open/close/move | experimental physical_adjudication.plan_physical / commit_physical via exploration | _apply mutates session ledger directly; _write_props alternate host. Gate-disabled in ordinary T04/T06 | Keep interpretation/check specialty; delegate migrated object writes to instance owner. Do not activate it now |
| Persistent marking | T06 orchestration _unbound_physical_decline | Declines before resolution/prerequisites; no carried-object marking owner | New narrow semantic instance mutation owner called from existing resolution staging |
| Consumption/destruction | Mechanical narration recognizes limited deltas; combat owns HP/spell mechanics | No general item consume/destroy lifecycle; no assumption that items_removed is destruction | Deferred typed lifecycle operations, conservation and adapter evidence required |
| Authored consequences | authored_consequences.resolve -> world.apply_resolution_world_updates | Finite flags/conditions; no generic item edit | Remain own world-progression semantics; no inscription-as-world-flag shortcut |
| Check/rules adjudication | skill_checks / combat / conditions; noncombat_resolution delegates | PF1e-inspired engine mechanics, no adapter runtime | Wrap relevant existing calls behind proposed object-mechanics adapter; absence of support returns unsupported |
| State transaction | API _apply_authoritative_resolution_state_mutation:2620; integrated_play.ordered_turn:69; storage.runtime_commit_scope:209 | api_chat serializes mutations per store and accepts client_request_id; completed cache is 32 in-memory results, not durable idempotency. Exception rollback protects listed files; not a semantic object validator | Reuse lane/request field; add durable key/digest checks and delegated object application, keeping result provisional until save/publication succeeds |

## One coherent boundary

The proposed `game.object_instances` is the single semantic validator/applier for canonical object-instance fields. It is not a new independent physical-action authority. Routing/adjudication stays with the existing turn/exploration/local/specialized owners. Storage remains I/O. Every operation names its existing host, and at most one record owns an instance. A read index is rebuildable and cannot grant writes.

Domain mapping must be explicit before implementation: character-held object truth is a **world_state semantic facet persisted in the character document**, not a sixth domain. Amend state_authority registry/doctrine to permit the narrow new owner; do not claim it currently registers character inventory. Scene bindings/overlays remain scene_state. API coordinates any allowlisted cross-domain effects. A same-record inventory modification must not quietly grant permission to modify every character mechanic.

Precedence: mode/authorization and hidden gates first; retain committed specialized travel/combat/social/inspection decisions; route a uniquely classified object operation to its specialist; reject ambiguous multi-owner intent; fallback unsupported only after supported specialists decline. Local T04 is selected only for its bounded transient class. New manipulation routing must be consulted before today's unconditional unbound-manipulation decline. The enabled experimental gate currently prevents T04 resolution and can still be short-circuited; migrating this explicitly is a later phase, not solved by ordering prose.

Before a fixture is migrated, its existing writer remains exclusive. After migration, legacy physical writes must delegate or fail closed for that binding. Never dual-write the same object's open state to a canonical row and an independent physical overlay. Inspectors read the selected host at the current revision.
