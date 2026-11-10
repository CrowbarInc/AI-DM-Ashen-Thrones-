# Root Cause

Failure class: implementation. The publication contract already distinguished a completed sentence from an early block. The HTTP recorder did not carry that distinction.

## Call chain

1. `admit_request` refuses, with `sent` false, or the interpretation service fails after a send.
2. `request_interpretation` returns `{ok: false, sent}`.
3. `interpret_production_turn` returns `_blocked`.
4. `_chat_turn` builds `_live_interpretation_block_response` and does not call `note_completed_publication`.
5. `api_chat` attached ordinary publication provenance.
6. `PlayerHTTPRoute` called `record_completed_publication` because `skip_publication_trace` was unset.

## First incorrect decision

`record_completed_publication` treated nonempty player-facing text as a completed gameplay publication. The refusal reason lived on raw resolution metadata. `project_player_response` strips that metadata to `resolution: {}` and keeps `gm_output.player_facing_text`, so the HTTP adapter could not see the class from the projected body.

## What was already correct

- Provider admission did not send the request and did not count tokens for a pre-dispatch refusal.
- `note_completed_publication` did not move `session.last_publication`.
- Authoritative gameplay state was not committed by the refusal.

The owners that were not the defect are admission, the session pointer writer, and the gameplay resolver. The owner of the defect is publication-event construction after provenance is attached in `api_chat` and `api_action`.
