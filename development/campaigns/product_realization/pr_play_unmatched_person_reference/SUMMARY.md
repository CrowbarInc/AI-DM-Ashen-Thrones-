# pr_play_unmatched_person_reference

Verdict: **A/PASS**. An unmatched person and a question to the DM are no longer answered by offering Guard Captain or Tavern Runner.

"Tell me the hidden motives of the threadbare watcher." now says the watcher is established and the information is not. "Tell me about the patrol." quotes the notice board. "I ask someone about the patrol." still asks which of the two present people, and "The Guard Captain." then speaks the patrol line once. "I ask the Guard Captain about the patrol." still binds the captain. Warden Cole and "the velvet inquisitor" match nobody. Hidden motives of the captain are not invented and do not advance the turn. A repeat of the captain's warning stays with the captain.

The defect is person-specific. `assess_addressee_grounding` treated an unresolved name, and the speech-role "me" in "tell me", as a choice among every visible NPC. Object and location owners do not do that. The book miss and the throne-room refusal were left as they were.

Ordinary-chat probes, providers disabled: person references 4/6 to 6/6, GM requests 0/2 to 2/2, cross-entity 3/3 to 3/3, negation 2/2 to 2/2, multi-turn 6/10 to 11/11. Provider-record delta 0. The frozen forty changed on one row, `unsupported_impossible-04-01`, which was the same watcher failure and was previously MISINTERPRETED with actionability 0. It is not given a new success label. The other 39 rows are unchanged, including all 12 historical successes and all 22 minimum-quality marks. Supplementary row D09 is that same sentence and was not one of the 5 historical executable successes. No broad-score improvement is claimed.

Combined regression: 455 passed / 17 failed, same identities. Focused: 470 passed / 1 failed, still `test_api_roll_initiative_returns_canonical_resolution`. Provider records 0. No live provider call.

No commit and no push. `pr_play_social_check_repeat_and_legacy_stance` was not started. Recommended next milestone: the unique carried-object reference. Last updated: 2026-11-15.
