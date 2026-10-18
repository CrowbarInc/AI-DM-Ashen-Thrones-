# 23 — Controlled Tests

`tests/test_pr_eg_r6_r3_r1_candidates.py` contains 68 tests, including T01–T66 plus paraphrased-evidence grounding and participant-role reversal. `python -m pytest tests/test_pr_eg_r6_r3_r1_candidates.py -q` passed. The tests do not call the network. They drive the compiler and `authorize_information_turn` through the selector seam.
