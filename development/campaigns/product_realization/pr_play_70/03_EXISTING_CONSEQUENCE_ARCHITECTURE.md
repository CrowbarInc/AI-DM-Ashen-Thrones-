# EXISTING CONSEQUENCE ARCHITECTURE

Player choice → existing action DTO/normalization → exploration resolver using current server-authored action ID and existing clue/flag conditions → existing API Stage 5 → existing world flag mutation owner → save_world/save_session → existing conditional affordances → trusted final publication → unchanged explicit HTTP DTO → existing frontend buttons. Minimal extension: finite authored set_flags/text contract; no new state store or intent model.

Existing owners inspected: game/exploration.py, game/affordances.py, game/world.py, game/storage.py, game/models.py, game/noncombat_resolution.py, game/api.py, game/player_http_projection.py, static/app.js. Flags, conditions, progression effects, discovery, persistence, scene travel and projection already exist. Quest/lead progression is broader than needed; flags express this experiment without a parallel decision store.
