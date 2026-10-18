# PR-CH Diagnostic Report

Mode: social answer selection and refusal attribution.

Live provider calls: 0.

Baseline:
- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Worktree was heavily dirty before PR-CH; no reset or discard was performed.
- PR-CC added bounded social reply-plan kinds for missing-topic social turns.
- PR-CE expanded harmless subjective recognition while preserving consequential/restricted precedence.

Focused result:
- `.venv\Scripts\python.exe -m pytest tests\test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b -q --tb=short`
- Reproduced target failure: `Kiln Tender says, "I cannot answer that from what is settled here."`
- Captured stdout included `[CLUE DISCOVERED] social_brine_yard_kiln_tender_kiln_bank`.

Adjacent result:
- `.venv\Scripts\python.exe -m pytest tests\test_social_question_relevance_answer_selection.py -q --tb=short`
- Result: 20 passed, 4 failed.

Decision: D - FALLBACK / VALIDATION DEFECT.

The authored answer exists, is retrieved, is selected by deterministic social resolution, and can be formatted by the authored-answer helper. The earliest failing boundary is after social answer selection, in final player-facing emission validation/fallback/immutability.

