## Objective #15 — UI mode separation (final architecture note)

### Authorities (single source of truth)

- **Canonical boundary policy**: `game/ui_mode_policy.py`
- **Request ui_mode resolution**: `game/api_ui_mode.py`
- **Lane projection / channel stripping**: `game/state_channels.py`
- **Authoritative frontend render source**: `GET /api/state?ui_mode=...`

### Canonical modes (fail closed)

- **player**: public runtime surface only
- **author**: authoring surface only
- **debug**: diagnostic/operator surface only

**author** and **debug** are **siblings**, not supersets.

### Canonical tabs (frontend contract)

- **player**: `play`, `character`, `world`
- **author**: `scene`, `campaign`, `world`
- **debug**: `debug`

### Backend state envelope (shipped contract)

- **player**: `{ ui_mode, public_state }`
- **author**: `{ ui_mode, public_state, author_state }`
- **debug**: `{ ui_mode, public_state, debug_state }`

### Frontend rendering contract (shipped)

- UI renders **only** from `GET /api/state?ui_mode=...`
- Public surface uses `renderPublicState(public_state)`
- Author surface uses `renderAuthorState(author_state)` (author mode only)
- Debug surface uses `renderDebugState(debug_state)` (debug mode only)
- `/api/chat` and `/api/action` are **not authoritative render-state sources**; they end by reloading from `/api/state`.

### DOM boundary behavior (must clear, not just hide)

On mode change (and on render envelope application), forbidden panels must be **cleared immediately** and not populated:

- **Outside author**: clear author-only fields (e.g. `hidden_facts` / `sceneHiddenFacts`)
- **Outside debug**: clear debug JSON / trace boxes and Advanced World Debug content

### Shared World tab (player + author)

`world` exists in both **player** and **author** modes intentionally.
The **content remains public-lane** (spoilers stripped), but the UI should still make it obvious which mode you are in.

