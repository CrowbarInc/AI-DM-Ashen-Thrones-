# Adaptive gameplay

The player policy saw opening prose, later GM prose, and visible affordance labels. It did not read action ids, flags, or test expectations. It typed chat. It did not click suggested actions.

Meaningful turns: 28
Objective completed: True
Objective detail: {'discovered_patrol': True, 'investigated_trail': True, 'branch': True, 'consequence': True, 'continued': True, 'save_resume': 'old_milestone'}
Repeated observations: 5
Scene contradictions: 0
Clarifications: 1
Unsupported marker count from the runner: 2
End flags include `patrol_survey` and `patrol_survey_recorded`.
Scene after resume: old_milestone
Latency: {'mean': 314.2, 'median': 242.6, 'p95': 661.4, 'max': 687.4, 'n': 28}

PR-PLAY-78 comparison: 34 meaningful turns, 14 repeated observations, objective not completed. This run: 28 meaningful turns, 5 repeated observations, survey branch and record committed, save/resume at Old Milestone.

The policy is a visible-text chooser with a fixed list of candidate sentences, the same family of harness used in PR-PLAY-78. It is not a hidden-oracle script, and it is not a claim about an unguided human.

Additional non-executing replies in the transcript include one target clarification, "I cannot provide a validated response", and "I cannot answer that from what is settled here." Those are truthful refusals, not repeated observations of the same look-around.
