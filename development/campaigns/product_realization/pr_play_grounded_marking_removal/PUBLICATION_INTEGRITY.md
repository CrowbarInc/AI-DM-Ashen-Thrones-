# Publication Integrity

Removal uses the existing `reconcile_publication` helper. The committed sentence is:

`You wipe the marking off the sleeve. It is no longer there. It read: <visible text>`

The verb and the preposition follow the requested method. A sealed paraphrase may replace it only when the sentence still names the surface, includes that exact text, says the marking is no longer there, does not say the removal failed or that the writing remains, does not claim a material was used up, and does not include any other marking on the object. Empty text, a sealer exception, and a contradictory seal are not published. The committed sentence is sealed in their place.

`publication_matches_commit` stays true for that reconciled sentence. `resolution.success` stays true because the removal committed. `publication_failure` is true when the seal was rejected, empty, or raised, or when the session write failed.

The fault test covers an unchanged seal, a compatible paraphrase ("You clear the marking from the sleeve..."), a seal that says the warning is still written, an empty seal, a raising seal, a retry of that raising case, a session-save failure after the character commit, and the retry of that failure. The marking is removed once in each committed case. A concealed marking present beside the removed warning does not appear in the sentence.
