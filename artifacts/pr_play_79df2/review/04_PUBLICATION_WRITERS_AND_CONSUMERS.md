# Writers and consumers

Writers of `session.last_publication`:

- `game/integrated_play.py` `commit_integrated` writes the composer record for integrated dialogue.
- `game/bounded_improvisation.py` conversation mode writes the composer record for bounded conversation.
- `game/publication_contract.py` `note_completed_publication` keeps a matching composer record or replaces a stale one. Called from `game/api.py` after `_finalize_investigation_publication` on the action return and the chat completion return, then `save_session`.

Consumers:

- `game/api.py` `api_action` and `api_chat` pass `load_session().get('last_publication')` as `publication_context`.
- `game/publication_contract.py` `record_completed_publication` uses that context only when `context.visible` equals the player-facing text. A match can attribute accepted dialogue or narration. A mismatch uses owner `completed_runtime_response` and validation `engine_or_grounded_fallback`.
- The HTTP boundary in `game/player_http_boundary.py` writes one publication event for chat, action, and campaign start unless the trace is skipped.

`last_background_expression` is written by expression generation and synchronized from the turn audit by the note. It is not the canonical publication pointer.
