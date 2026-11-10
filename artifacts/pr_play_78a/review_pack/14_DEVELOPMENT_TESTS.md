# Development tests

`tests/test_pr_play_78a_authored.py` collects 133 tests. Together with `tests/test_pr_play_71_lifecycle.py` (8 tests) the run exited 0.

The file covers exact phrases, paraphrases, unavailable and hidden rows, wrong scene, wrong campaign, missing clues, questions, negation, hypotheticals, ambiguity, provider accept/reject/malformed, foreign-opening replacement, and two full chat branches with save/resume.

Forty of those tests are numbered suffix variants of two sentences ("attempt N" / "pass N"). They execute the matcher, but they are not forty distinct behaviors. The distinct matrix is the CASES and MORE lists plus the function tests and the two HTTP branch tests.

`tests/test_pr_play_78_integrated.py` and `tests/test_pr_play_72_boundary_repairs.py` were run earlier in the cycle and passed, including the boundary sentences that must not execute a patrol action.
