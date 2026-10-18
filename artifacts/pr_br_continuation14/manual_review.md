# PR-BR Continuation 14 manual review

Session `20261001T013504Z`. Human-DM standard: the final line must still resolve the proposition the player asked, not merely stay on a related grounded fact.

| Turn | Player | Contract | Initial useful | Final | Manual | Evaluator | Degradation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | what's required before they'll let me through | ask / gate_guard / next_step | yes, papers, curfew, permission from Thoran, plus who commands | same text | PASS | PASS | no |
| 2 | When did that start? | ask / gate_guard / time | yes, asks which "that" (curfew, patrol, or posting) | "I cannot say how recently that was." | FAIL | FAIL | yes |
| 3 | How sure is he about that? | ask / gate_guard / confidence | yes, "I can't say for certain" | same text | PASS | PASS | no |
| 4 | What's that notice board used for? | ask / Notice board / use | yes, taxes, curfew, patrol warning, updates before entry | same text | PASS | FAIL | no |
| 5 | what travelers have been saying | ask / Gate Guard / dimension None | yes, worn travelers, census at the eastern choke point | "Captain Thoran commands the gate watch tonight." | FAIL | PASS | yes |
| 6 | I'll do whatever he just told me to do | act / dimension None | a restatement of papers and curfew, scored as not an action outcome | generic refusal, another route | PASS | PASS | no |

Turn 1 is the superset case. Identity and procedure stay in the same speech. The procedure is not erased.

Turn 2 is a same-rank nonresolution swap. The generated clarification is the better resolution of an ambiguous "that". The emitted line is a legal time inability and does not say which fact it cannot date. Evaluator FAIL agrees with the manual fail.

Turn 3 keeps the certainty sentence. Dimension is confidence. Coverage still reports the dimension uncovered because the inability span strips "certain", but the player-visible line is the generated one.

Turn 4 keeps a real use answer. The contract dimension is use. The scorer marks `dimension_substituted` because the sentence also says "recently", so the evaluator false-fails. The text was not replaced.

Turn 5 is the remaining equal-rank failure. Both lines score `inquiry_answered` because the contract has no dimension. The Thoran fact replaces what travelers have been saying. Evaluator false-passes. `best_safe_candidate` is the Thoran line, and that line is what was emitted, so this is a bad update of the best candidate, not a bypass of it.

Turn 6 is an unbound act. Dimension None is appropriate. The generic refusal is the legitimate nonresolution. It does not revive the Thoran sentence as the action.

Discourse: the gate guard stays the interlocutor on all six turns. The Thoran sentence is stored as `active_claim` after turn 5, not as the interlocutor. The notice board is not written into `active_inspected` because turn 4 is an ask, not an inspection. No canonical denial. No literal foot-on-a-step reading.

Correct contracts: 5/6. Turn 5 should have carried content. Initial manual PASS: 6/6. Final manual PASS: 4/6. Useful answers degraded after generation: 2 (turns 2 and 5). Equal-rank harmful replacements attempted: 2 (turns 2 and 5). Blocked: 0 of those two live cases. `best_safe` emission mismatches: 0. Missing obvious dimension: 1 (turn 5 content). Evaluator PASS: 4/6. False PASS: 1 (turn 5). False FAIL: 1 (turn 4).
