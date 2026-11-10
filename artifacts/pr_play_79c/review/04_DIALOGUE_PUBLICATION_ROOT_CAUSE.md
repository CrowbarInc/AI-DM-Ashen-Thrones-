# Dialogue publication root cause

Accepted speech was sent through `maybe_narrate` as part of the whole publication. The narration instruction says to rewrite the committed outcome in ordinary sensory prose. The provider turned the quote into third person, token overlap let validation accept it, and that prose replaced the speech.

The repair is in `commit_integrated`. A dialogue-only turn is not narrated. `last_narration.reasons` is `dialogue_already_final`. A mixed turn may narrate only the non-speech part, then appends the accepted speech unchanged. The conversation owner in `bounded_improvisation` records the same publication stamp and does not narrate speech.
