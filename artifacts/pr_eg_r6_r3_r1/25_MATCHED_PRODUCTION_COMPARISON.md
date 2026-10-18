# 25 — Matched Production Comparison

The same 60 utterances, cast, and `/api/chat` path were run twice. Candidate mode: operation 41/60, roles 33/60, answers 29/60, corrections 5/10, follow-ups 12/20. Existing semantic planner: operation 46/60, roles 43/60, answers 37/60, corrections 4/10, follow-ups 14/20. Both leaked nothing and failed no integrity check. Candidate mode did not improve the matched production result. Corrections were the only family with a one-turn edge, 5 against 4.
