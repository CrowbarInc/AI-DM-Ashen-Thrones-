# 03 — Evaluation Methodology

Evaluation-only tooling. Frozen protocol, prompts, fixtures, profile allocation and budgets precede provider evidence. Production /api/chat?ui_mode=player is called through FastAPI TestClient, with real configured provider calls and no dialogue-generation helper substitutes. Only storage paths are patched by the inherited setup helper.

A fresh model player produces one utterance from the actual public transcript, then the production endpoint responds, raw evidence and before/after state are durably written, and a separate evaluator scores delivery. Engine metadata never substitutes for player experience. Scores are independently reviewed by the root agent.

Sampling is purposive, not statistical: one stochastic adaptive conversation per allocated scene/profile pair; no certainty or population claim. Exact denominators are shown. Stressors are observed categories, not a fixed question script.

Interrupted attempts and monitor correction: see `evaluation_events.json`. No production code, prompt or regression expectation was changed. Authorized authored-topic discovery events are explicitly checked against the fixture; all other canonical changes stop the run. No rejected candidate is assumed safe merely because the validator accepted another sentence.
