# PR-DM Completeness Checks

## Why the two rows were missed

`var_compound_subtle` is "I drift over to the notice board, then try to pull it free." The PR-DK compound check splits on `and` and `then`, then looks for a movement verb in a fixed list (`walk`, `go`, `head`, `approach`, `move`, `step`). `drift` is not in that list, and the selected resolver is `world_action`, so the travel-or-social mismatch does not fire. The stored independent checks are all false. The deterministic gameplay score is FAIL.

`var_quote_control` is "I say, \"Walk closer and pry it off,\" as a joke." The PR-DK check removes quoted text before it looks for action clauses, so the quoted walk and pry disappear. The selected resolver is `travel`, which consumed the quoted verbs. The stored routing label says assistance is not justified. The deterministic gameplay score is FAIL because the resolver is travel.

## Checks added

`temporally_sequenced_components` splits unquoted text on `then`, `and then`, `before`, `after`, and `once`. It does not split on bare `and`. A hypothetical `if`, `suppose`, or `imagine` suppresses the split. The clauses need two different head tokens, a directional phrase in one clause, and an object in another. A negated later clause does not count as a second attempt. Head tokens are the first non-closed-class word. There is no added synonym list for `drift`, `slide`, `edge`, `tug`, or `work`.

`action_contract_uncovered` is that sequence when the stored independent checks and, when present, the contract's secondary operations do not already record it.

`quoted_speech_boundary` requires a player speech frame outside the quotes (`I say`, `I remark`, `as a joke`, and the same small frame). A sign or a document that "says" something is not a player frame.

`quoted_action_resolver_mismatch` requires that boundary, a physical resolver (`travel`, `combat`, `world_action`, `exploration`), and action verbs that occur only inside the quotes. Verbs that also occur outside the quotes are the player's own action, so the quote does not escalate.

Only the uncovered sequence and the quote/resolver mismatch request interpretation.

## Original matrix

`var_compound_subtle` fires the uncovered sequence. `var_quote_control` fires the quote mismatch. No other original row fires a new check. Inherited false positives `var_social_control` and `var_hypothetical_control` stay inherited. They are not new.

## Holdout

Temporal paraphrases that use `slide`/`tug`, `edge`/`work`, and a fronted `after` are structurally detected. The bare-and sentence "I edge toward the notice board and work it loose" is not escalated by the new check. That miss is intentional: a conjunction alone is not a sequence. Quoted weather, a sign, a quote followed by a real walk, a hypothetical, a negated pull, ordinary combat, ordinary movement, ordinary observation, an ordinary question, and an ambiguous pronoun do not newly escalate.

Inherited PR-DK checks still fire on some holdout sentences. Those are recorded in the holdout report and were not retuned.
