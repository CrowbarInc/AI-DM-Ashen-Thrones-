# PR-DM Holdout Results

Holdout sentences were written for this experiment. They are not scored by copying a PR-DL label. No provider was called. `live_model_success_claimed` is false.

Detection failures: none.
New false escalations: none.
Conjunction misses: holdout_and_novel_verbs.
Authority failures: none.
Save guard verified: True. Provider tripwire hits: none.

## holdout_slide_then_tug

Temporal paraphrase with verbs absent from the PR-DK movement list.

Utterance: I slide over to the notice board, then tug it free.

Resolver `generation`, operation `unresolved`. New route: True. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_edge_then_work

Second temporal paraphrase. Direction is toward, not a listed motion verb.

Utterance: I edge toward the notice board, then attempt to work it loose.

Resolver `generation`, operation `unresolved`. New route: True. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_after_pull

Fronted temporal clause rather than a mid-sentence then.

Utterance: After I get over to the notice board, I pull it free.

Resolver `social`, operation `ask`. New route: True. Inherited route: True. Structural detection held: True. Quote result: not_applicable.

## holdout_and_novel_verbs

Bare and plus uncovered verbs. The new check must not treat every conjunction as two actions.

Utterance: I edge toward the notice board and work it loose.

Resolver `generation`, operation `unresolved`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_and_companion

Conjunction joins a destination and a person, not a second action.

Utterance: I walk closer to the notice board and the captain.

Resolver `travel`, operation `act`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_remark_kidding

Quoted physical verbs are not the player's attempt when the player frames them as a remark.

Utterance: I remark, "Step closer and pull it off," just kidding.

Resolver `world_action`, operation `act`. New route: True. Inherited route: False. Structural detection held: True. Quote result: detected.

## holdout_tell_weather

A quote without a physical action verb is not a resolver mismatch.

Utterance: I tell the captain, "The rain feels endless."

Resolver `social`, operation `ask`. New route: False. Inherited route: True. Structural detection held: True. Quote result: not_applicable.

## holdout_sign_quote

A sign's quoted words are not player speech.

Utterance: The notice board says "walk closer," so I stay put.

Resolver `travel`, operation `act`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_quote_then_walk

The real action is outside the quote.

Utterance: The board reads "keep out." I walk closer to the notice board.

Resolver `travel`, operation `act`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_hypothetical_sequence

A conditional then-clause is not an attempted sequence.

Utterance: If I edged toward the board, then I would pull it free, but I am only asking.

Resolver `social`, operation `ask`. New route: False. Inherited route: True. Structural detection held: True. Quote result: not_applicable.

## holdout_negated_pull

The later clause is negated, so it is not a second attempt.

Utterance: I drift over to the notice board, then do not pull it free.

Resolver `world_action`, operation `act`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_ordinary_combat

Ordinary attack.

Utterance: I strike the goblin.

Resolver `combat`, operation `act`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_ordinary_movement

Ordinary movement.

Utterance: I step closer to the notice board.

Resolver `generation`, operation `unresolved`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_ordinary_observation

Ordinary observation.

Utterance: I look around the yard.

Resolver `exploration`, operation `perceive`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_ordinary_question

Ordinary NPC question.

Utterance: Captain, is the gate shut for the night?

Resolver `social`, operation `ask`. New route: False. Inherited route: False. Structural detection held: True. Quote result: not_applicable.

## holdout_ambiguous_pronoun

Pronoun ambiguity is an inherited check, not a new compound or quote check.

Utterance: Ask them whether the other one saw the board.

Resolver `social`, operation `ask`. New route: False. Inherited route: True. Structural detection held: True. Quote result: not_applicable.

Inherited routes on holdout sentences come from the unchanged PR-DK checks. PR-DM did not retune those checks. A new false escalation is only a new-check route where the structural expectation was no route.

Unsupported authority cases are rejections. They are not executed plans and they are not live-model successes.
