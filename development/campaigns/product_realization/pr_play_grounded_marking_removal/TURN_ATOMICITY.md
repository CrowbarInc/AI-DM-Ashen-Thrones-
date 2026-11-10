# Turn Atomicity

Unresolved and rejected removals are published as "Nothing was removed." The character file is not saved and the object revision does not change.

A ready removal is staged in memory, then `save_character` runs, then `preserve_committed_runtime("CHARACTER_PATH")` runs, and only then is narration sealed. If `save_character` raises, the turn's existing commit scope restores the pre-save bytes when they changed, and the HTTP result is an error. The interrupted test sees status 500, the original character bytes, and no "no longer" sentence.

If the save returns and sealing or the session write then fails, the character save is kept. The player receives the committed sentence. A retry of the same request id finds the removal receipt and does not remove again.
