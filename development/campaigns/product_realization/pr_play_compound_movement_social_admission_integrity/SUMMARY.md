# Summary

**B/PARTIAL.** Ashen Thrones, Product Realization / PR-PLAY. Milestone `pr_play_compound_movement_social_admission_integrity`.

The inherited request “I go to the fortress trail and persuade the guard to help me.” was traveling to Old Milestone on `leave_for_seek_the_fortress_trail` and leaving “help me” pending. Coverage had classified the sentence as one MOVE because subject-elided “persuade” was not a command. The purpose owner then matched “to help” and committed the trip. The social resolver never ran.

The same sentence is now withheld before travel. Coverage is MOVE plus OTHER. Admission returns `compound_intention_needs_confirmation`. The player is asked whether to go to the fortress trail first, told that “persuade the guard to help me” has not been done, and told that nothing has been attempted. Scene, turn, tick, and pressure are unchanged. A later “Just travel there first.” or “Only go to the trail.” is one trail arrival and does not keep the persuasion. “Forget the persuasion.” and “Never mind.” clear the pending compound. “Actually, return to the gate.” is one gate arrival.

Infinitive purposes that already traveled still travel: “to find the guard”, “to help the guard”, and “to learn what happened”. Incidental posture plus the trail still travels. T05, T11, and T15 are unchanged. “or I return to the gate” still clarifies and does not travel. Committed route ids still name the arrival scene.

Three broader sentences still spend a failed-transition turn without arriving: “looking for the guard”, “so I can persuade the guard”, and “because I want to persuade the guard”. They remain one MOVE span, so this gate does not see them. That is why the verdict is partial.

New acceptance 87/87, with the looking-for row explicitly classified as that pre-existing failed transition. Previous movement acceptance 109/109. Duplicate checks 97 on the new matrix and 117 on the movement rerun. Regression suites match their baselines. New failure identities: 0. Provider calls: 0. Expenditure: $0.00.

Production change is confined to `game/conversational_orchestration.py` relative to the disjunctive review archive. No commit and no push.

Do not start live play. The next slice is the failed-transition turn on those reason and participle tails.
