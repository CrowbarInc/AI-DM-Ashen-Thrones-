# PR-DG Candidate A Results

Interpretation was pinned off. No narration provider call was made. Failures were not repaired.

| # | Resolver | Kind | Unsupported | Fast-path abstained | Narration bytes | HP | Interlocutor |
|---|---|---|---|---|---:|---|---|
| 1 S1 | social | question | False | False | 86764 | {} | guard_captain |
| 2 S2 | social | question | False | False | 86238 | {} | guard_captain |
| 3 F1 | social | question | False | False | 88106 | {} | guard_captain |
| 4 H1 | social | question | False | False | 86169 | {} | guard_captain |
| 5 M1 | travel | custom | False | False | 77693 | {} | None |
| 6 O1 | exploration | observe | False | False | 78018 | {} | None |
| 7 K1 | exploration | investigate | False | False | 71744 | {} | None |
| 8 B1 | combat | attack | False | False | 85617 | {'goblin_1': 0} | None |
| 9 C1 | social | question | False | False | 86282 | {} | guard_captain |
| 10 compound | travel | custom | False | True | 77835 | {} | None |
| 11 ambiguous | social | interact | True | False | 77916 | {} | None |
| 12 courier | social | question | False | False | 86831 | {} | guard_captain |
| 13 declared_canon | world_action | custom | False | True | 78552 | {} | None |
| 14 mechanical_dump | social | attack | True | False | 90649 | {'goblin_1': 6} | None |

Ordinary social lines (S1, S2, F1, H1, C1) selected `social` / `ask` and the social resolver ran. The interlocutor stayed `guard_captain`. No clue ids were added on F1. That is the resolver's result on this fixture, not a harness repair.

M1 selected `travel`. The scene id stayed `frontier_gate`. O1 selected `exploration` / `perceive`. Entity ids did not change.

K1 selected `exploration` / `inspect`. `resolve_exploration_action` returned a perception check: modifier 2, DC 8, roll 10, total 12, success true. The roll is `game.skill_checks._deterministic_d20`, not the combat `roll_die` patch. The observed roll happened to be 10.

B1 selected `combat`. `resolve_attack` with `roll_die` patched to 10 wrote goblin HP from 6 to 0. The same HP appears for B and C.

The compound sentence selected `travel` even though `fast_path_abstained` and `model_interpretation_appropriate` were both true. The pin skipped the interpreter. The scene did not change and the board facts stayed. The pry was not a second resolved step.

The ambiguous line selected `social`, and the social entry did not route (`social_entry_did_not_route`). The parsed kind was `interact`. No interlocutor was stored.

The declared-canon line selected `world_action` and resolved as `custom`. World flags and clue ids did not change.

The HP-dump line selected `social`. The parsed kind was `attack`, and `resolve_attack` was not called. Goblin HP stayed 6.

The courier tick appended one `npc_moved` and the courier location became `market_quarter` before the social resolver ran.
