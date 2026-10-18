# PR-DM Adversarial Controls

These sentences are not the PR-DL 21. Expected behavior was assigned from the structural rule before the replay was used as a score. No provider output exists for them, so none is marked as a live-model success.

| Case | Family | Resolver | New route | Inherited route | Result |
| --- | --- | --- | --- | --- | --- |
| holdout_slide_then_tug | temporal_compound | generation | True | False | detected |
| holdout_edge_then_work | temporal_compound | generation | True | False | detected |
| holdout_after_pull | temporal_compound | social | True | True | detected |
| holdout_and_novel_verbs | conjunction_gap | generation | False | False | miss |
| holdout_and_companion | ordinary_movement | travel | False | False | detected |
| holdout_remark_kidding | quoted_joke | world_action | True | False | detected |
| holdout_tell_weather | quoted_speech | social | False | True | detected |
| holdout_sign_quote | quoted_sign | travel | False | False | detected |
| holdout_quote_then_walk | ordinary_movement | travel | False | False | detected |
| holdout_hypothetical_sequence | hypothetical | social | False | True | detected |
| holdout_negated_pull | negated | world_action | False | False | detected |
| holdout_ordinary_combat | ordinary_combat | combat | False | False | detected |
| holdout_ordinary_movement | ordinary_movement | generation | False | False | detected |
| holdout_ordinary_observation | ordinary_observation | exploration | False | False | detected |
| holdout_ordinary_question | ordinary_question | social | False | False | detected |
| holdout_ambiguous_pronoun | ambiguous_pronoun | social | False | True | detected |

Authority controls use hand-authored payloads against a fixed permitted-entity list and a fixed visible-fact list. They cover a clean attack, a clean move, a clean question, a refusal, direct HP, an invented fact, a fabricated roll, an invented id, an NPC commitment, an inventory grant, an execution request, a hidden-information assertion, and an advantage or patrol-found operation.

Authority failures: none.
