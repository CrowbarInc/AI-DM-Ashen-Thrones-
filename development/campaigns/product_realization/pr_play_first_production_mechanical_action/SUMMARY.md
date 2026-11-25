# pr_play_first_production_mechanical_action

Verdict: **A/PASS**. A player can persuade, intimidate, or deceive one present person through ordinary chat. The campaign's persisted ruleset authorizes the check. Pathfinder resolves it with the existing Diplomacy, Intimidate, and Bluff rules. The core commits the stance. The world remembers it, and a later question reads it back.

The ordinary line "I try to persuade the guard captain" published "Diplomacy check to persuade Guard Captain succeeds (d20=9+4=13 vs DC 10). Their trust is now 1." A repeat of that maneuver replayed the result and did not raise trust again. A die fixed at 1 published a failure and left trust at 0. A missing Diplomacy modifier stayed unresolved and did not roll. `rules_light` and `scifi` do not inherit the check. Equipment policy still proposes nothing.

Acceptance: 79/79 recorded evaluations passed. Ordinary HTTP coverage includes the full player-turn sequence plus the negative and preservation cases, with provider delta 0. Four multi-turn sequences passed, provider delta 0. Combined regression before and after: 455 passed / 17 failed, same identities. Focused before and after: 470 passed / 1 failed, the inherited initiative assertion. Provider records in those guarded runs: 0.

The forty probes were rerun from the frozen inputs. Visible text matched the prior replay, so the scores stay 12/40 successful, minimum quality 22/40, mean actionability 1.675. Supplementary publications also matched, so executable successes stay 5/55. No broad improvement is claimed. The historical probes do not ask for this check.

No commit and no push. The next milestone has not been started. Recommended next milestone: `pr_play_social_check_repeat_and_legacy_stance`. Last updated: 2026-11-14.
