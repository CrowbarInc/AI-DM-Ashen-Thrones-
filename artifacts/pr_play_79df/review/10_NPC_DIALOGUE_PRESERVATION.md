# NPC dialogue

Typed input: `Gate Guard, what does the notice board say about the patrol?`

Player-facing result: `Gate Guard mutters, "Word is, check the notice board."`

The speaker is the Gate Guard. The reply is speech. It is not a “which person” clarification and it is not an unrelated narration. No primary narration request ran. One interpretation request and one expression request ran. Screenshot: `artifacts/pr_play_79df/screenshots/npc_dialogue.png`.

The expression completed: attempt `a47332cdcfcf44e5b4721a69f309ede4`, 164 input tokens, 14 output tokens, 178 total, latency 931.592 ms, sent true, no refusal recorded in the ledger. The publication record does not accept that expression. Category is `engine_response`, validation is `engine_or_grounded_fallback`, and the accepted-expression list is empty. The candidate sentence is not stored in the provider ledger, so the rejection reason is not available from this evidence.

`last_background_expression` and `last_publication` still describe an earlier accepted guard line from 12:38 UTC, “The notice board does mention a missing patrol, but I don’t have any details beyond that.” That line was already in the campaign before this cycle. It is not this turn’s published sentence.

The turn also stored clue `lead_frontier_gate_notice_board` with text `Check the notice board`, state `discovered`, presentation `actionable`, and added `social_lead_event_ids` as an empty list. The clue text matches the published fallback. It does not add the northwest track. The player journal showed that lead at turn 16 after the reply.

This cycle therefore shows the dialogue route still producing visible, attributed speech, and it does not show an accepted live provider line being the sentence the player reads.
