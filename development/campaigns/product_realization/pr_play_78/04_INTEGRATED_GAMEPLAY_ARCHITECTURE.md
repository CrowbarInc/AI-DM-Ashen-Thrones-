# Integrated gameplay architecture

The seam is `game/integrated_play.py`. It is called from the existing improvisation owner. It does not replace physical adjudication, dialogue authority, or campaign actions.

```
player text
  -> plan_integrated
       pure physical sequence: return None (plan_physical keeps it)
       single authored interactable: return None (authored discovery keeps it)
       dialogue / observation / investigation / social approach: build a shared plan
  -> commit_integrated
       physical steps: existing physical commit
       speech: background_conversation, bounded_social_line when the speech gate is on
       observation / investigation: visible facts and established uncertainty
  -> maybe_narrate, only if ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION=1
  -> player-safe publication
  -> existing session persistence
```

Ordering is `ordered_turn`: one FIFO lane per store path. Readers share. Writers are preferred and serialized. A duplicate in-flight text or `client_request_id` waits and returns the first result. A completed `client_request_id` is reused on retry. A different store does not wait.

Fragment that remains:

- A mixed "examine the notice board and ask..." inspects the visible fact and does not run the authored discovery. A dedicated "I examine the notice board." still reveals the patrol clue.
- A sentence that copies a suggested-action label ("I return to report the uncertain trail to the watch.") is parsed as travel to an unknown destination.
- A conditional sentence at the milestone published the Cinderwatch opening while the authoritative scene stayed `old_milestone`. The cause was not isolated. State did not move.
- More than three steps still asks for a shorter request and does not mutate.
- Climbing, carrying, and unconfigured checks are refused. No DC or roll is invented.
