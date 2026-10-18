# 05 — Grader Reliability Audit

Joined 150 final-run turns from `independent_grades.jsonl` to `local_assessment.json` through `grading_blind_map.json`.

The grader omitted 7 of 23 intended corrections and 13 of 51 intended follow-ups by leaving the label null. Those turns left its denominator. On comparable turns it marked 10 correction successes the local label rejected, 20 follow-up successes the local label rejected, and 38 referent bindings the local label rejected. Wrong operations were still marked relevant and sufficient 17 times.

Causes: null labels shrink the denominator; structural or fluent answers are credited as relevance; the grader sees the engine's accepted act and bound id in the packet. The local rates remain optimistic upper bounds because they imported the grader's relevance flags. Neither set is human gold. This cycle did not use that grader.
