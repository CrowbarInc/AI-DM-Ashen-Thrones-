# 01 — Executive Summary

Verdict: **D — ARCHITECTURAL OR INTEGRITY BLOCKER**

PR-EG-R6 adds one feature-gated semantic plan for explicit NPC information questions, corrections of those questions, and short follow-ups. The provider proposes the conversational meaning. The host grounds the addressee, accepts or rejects source identifiers, separates relevance from disclosure, and seals the final line through the existing speech-adoption path.

Fresh production `/api/chat` evidence: 119 turns across 8 conversations. Labeled intent 55/58 (94.8%), addressee 55/58 (94.8%), relevance 47/58 (81.0%), sufficiency 43/58 (74.1%), corrections 5/9 (55.6%), recovery 5/9 (55.6%).

Matched legacy comparison on the same harbor inputs: relevance 24/30 legacy versus 28/30 semantic; sufficiency 1/30 legacy versus 25/30 semantic.

- Gate 1_ownership: PASS
- Gate 2_intent: FAIL
- Gate 3_addressee: FAIL
- Gate 4_relevance: FAIL
- Gate 5_corrections: FAIL
- Gate 6_sufficiency: FAIL
- Gate 7_recovery: FAIL
- Gate 8_disclosure: FAIL
- Gate 9_delivery: FAIL
- Gate 10_state: PASS
- Gate 11_baseline: PASS
- Gate 12_performance: FAIL
- Gate 13_holdouts: FAIL
- Gate 14_regression: PASS
- Gate 15_evidence: FAIL

The run status is `STOP`. Dialogue-quality mean 2.411764705882353, playability mean 2.411764705882353. Gate 9 is that same stopping turn: the seal matched and the digest verified, and the check failed because the line contained the hidden name. Fresh holdout turns were not reached. This cycle stops here and does not start PR-EH.
