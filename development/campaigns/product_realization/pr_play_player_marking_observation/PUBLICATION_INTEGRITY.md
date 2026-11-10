# Publication Integrity

## Reproduced mismatch

`_publish_committed_marking` sealed the committed sentence and then published `gm["player_facing_text"]` even when it differed. `publication_matches_commit` was exact string equality, and `resolution.success` became null. A raising sealer escaped the turn, and `runtime_commit_scope` restored the character bytes from before the marking save.

The controlled warning sentence is accepted unchanged by the real sealer. A committed clue whose text is `The password is cedar.` makes `seal_host_speech` replace the line, because "password" is protected disclosure. Before this repair that denial could become the published response while the marking remained, or the exception path could roll the marking back.

## Repair

`reconcile_publication` compares the sealed sentence with the committed evidence:

- the committed content is present
- the surface and medium are present
- a denial such as "nothing was written" is absent
- visible output does not say concealed or hidden, and says the marking is present
- concealed output says concealed and does not say "on it now"
- the sentence does not claim that the medium was used up
- no other marking content from the same object is introduced

Whitespace-equal text is `unchanged`. A sentence that passes the checks is `paraphrase` and may be published. Empty text, an exception, or a failed check is not published. The player receives the deterministic committed sentence, and that sentence is sealed with `seal_accepted_response` so a later restore cannot put the rejected draft back.

`publication_matches_commit` is true when the published sentence is the reconciled result. `publication_failure` is true for a rejected sealer, an exception, or a failed session/log write. `resolution.success` stays true because the marking committed.

`preserve_committed_runtime("CHARACTER_PATH")` runs after `save_character` returns. A later publication exception restores that committed character, not the pre-marking bytes. The caught publication failure returns the committed sentence and does not call the marking service again. A retry of the same operation id uses the existing receipt.

Observation uses the same publisher. Its check requires the permitted contents, the surface, and the absence of undisclosed marking text. An unknown result must say that no writing is visible and must not claim that no concealed marking exists.
