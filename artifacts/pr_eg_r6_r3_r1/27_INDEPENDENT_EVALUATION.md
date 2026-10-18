# 27 — Independent Evaluation

`tools/score_pr_eg_r6_r3_r1.py` labels each utterance's intended operation and topic without reading `candidate_id`. A safe "I couldn't tell you" counts only when the operation and topic also match. Fresh totals: operation 99/150, roles 83/150, answers 70/150, corrections 13/25, follow-ups 26/50. Disclosure failures: 0/150. Integrity-check failures: 0/150.
