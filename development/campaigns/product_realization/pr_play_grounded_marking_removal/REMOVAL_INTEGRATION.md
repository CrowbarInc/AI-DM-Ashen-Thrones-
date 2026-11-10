# Removal Integration

The player turn stays in `api_chat` → `_chat_turn`. No second engine, parser, object store, or HTTP route was added.

| Stage | Owner |
|---|---|
| Player message | Existing `POST /api/chat` |
| Removal recognition | `game.marking_removal.recognize_removal` |
| Object and marking resolution | `resolve_removal` |
| Physical prerequisites | `resolve_removal` against established medium and surface records |
| Mutation | `game.object_marking.prepare_removal` |
| Character commit | Existing `save_character` inside the chat turn's commit scope |
| Publication | Existing `_publish_reconciled_narration` and `reconcile_publication` |

Creation is still claimed first. Removal is claimed only when recognition matches and the deterministic decision is absent or is not an `EXECUTE`. Observation remains the next claimant. The chat turn already holds the ordered mutation lane, so the turn calls `prepare_removal` directly and then `save_character`. It does not call `remove_inventory_object_marking`, which would take that same lane again. The request shape, digest, revision check, and receipt are the removal service's.

`game/marking_action.py`, `game/object_marking.py`, `game/object_observation.py`, and `game/storage.py` were not edited.
