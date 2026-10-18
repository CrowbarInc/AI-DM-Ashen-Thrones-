# PR-DG Interpretation Limitations

Live interpretation was pinned off. Nothing here is a claim about a live model's plan.

## A. Ordinary correctly classified actions

S1, S2, F1, H1, and C1 select `ask` / `social` with interlocutor `guard_captain`. O1 selects `perceive` / `exploration`. K1 selects `inspect` / `exploration` and the synthetic check runs. B1 selects `act` / `combat` and `resolve_attack` runs. M1 selects `act` / `travel` and the scene does not change. A, B, and C match on the mechanical tuple for these nine.

## B. Deterministic abstentions

Scenarios 10 and 13 set `fast_path_abstained` and `model_interpretation_appropriate`. The pin made the interpreter return skipped, and the provider tripwire stayed at zero calls. The contract that remained was still executable: travel for the compound sentence, world_action for the declared-canon sentence. An abstention-only fallback that stopped whenever `fast_path_abstained` is true would have refused both. The selector did not stop. Abstention-only fallback would miss these, because they are abstentions that still carry a selected resolver.

## C. Confident deterministic misclassifications

Scenario 14's contract selects `social` / `ask` with no interlocutor. Inside the social entry, the parser's kind is `attack`. `resolve_attack` is not called, and HP stays 6. The mislabel is confident in the parser output and contained by the combat gate, which only attacks when the selector says combat and the utterance is the quarterstaff line.

Scenario 11's contract selects `social` / `ask` with no interlocutor. The social entry does not route. The parsed kind is `interact`. No interlocutor is stored. The selector was confident. The entry abstained. B's gold plan expresses the ambiguity directly and runs no step. The existing social resolver, given that the entry does not route, also does not pick an NPC. What remains unsupported is a clarification line that names the two candidate referents. The harness does not invent that line as canon.

## D. Compound actions

A resolves the whole pry sentence as one travel action and does not remove the board. B and C can express two steps. The approach runs under the M1 rule. The pry selects `generation` and returns `unsupported`. No new pry mechanic was added. The first step stays committed.

## E. Ambiguous player requests

The fresh-state line has two addressable people and no discourse focus. A's selector does not set `ambiguous`. B's hand-authored plan does, and stops. Both leave the interlocutor empty. A live planner is not shown to do what the hand-authored plan does.

## F. Unsupported mechanics

Pry, a direct HP assignment, a hidden dump, downtime (`delta` other than 1, or a rest activity), a social-check preview, and an item spend are unsupported. The skill preview can see a configured check without rolling. Attack preview can see `player_can_act` without rolling.

## What a hand-authored plan can express, and what the resolvers can execute

A plan can name the approach and the pry, the ambiguity, and the refusal. The resolvers can execute the approach, the social ask, the synthetic check, and the patched attack. They cannot execute the pry, the fiat HP write, or a hidden reveal. Those stay unsupported. A live model is not inferred to produce the hand-authored plan.
