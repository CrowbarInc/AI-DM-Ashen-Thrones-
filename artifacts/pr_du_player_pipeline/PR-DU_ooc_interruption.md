PR-DU OOC Interruption

Input: OOC: I was only asking about the lantern's appearance.
Entry point: game.api.chat.
Result: PASS.

Verified:
- explicit OOC correction recognized before turn advancement
- no gameplay resolver invoked
- no provider called
- session and world unchanged
- chronological log entry preserved
- response returned with ooc_correction/non_mutating tags
