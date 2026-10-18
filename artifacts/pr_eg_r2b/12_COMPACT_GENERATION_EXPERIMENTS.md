# 12 — Compact Generation Experiments

FRESH generation used one ten-task batch plus one single-case interactive request, with an initial failed transport attempt retained. Tasks cover paraphrase, clarification, preference, personal elaboration, repeated refusal, partial answer, natural uncertainty, authorized security, hidden request and mixed pressure. Exact prompts, model outputs and usage are in provider.jsonl; gen tasks contain only compact contracts. gen06 supplies the road name and declines to invent its destination; gen08 repeats the explicitly authorized security fact.

generation_review.json evaluates the ten-task batch separately from the frozen validation corpus: 8 investigator accepts, 1 rejection, 1 abstention. The model’s own check of those ten outputs is fallible and not authoritative. One task per category and one model/configuration cannot establish generalization. No fresh provider candidate was inserted into the production handler; controlled handler seams use frozen candidates.

All generation requests including interactive: 3 attempted, 2 completed; 2495 input and 251 output tokens. Returned model gpt-4.1-mini-2025-04-14. Cap 3500, default sampling, SDK retries zero. Batch latency is retained as request latency, not per-player latency. Interactive generation took 1295.7 ms. No production generation module was modified.

Evidence classes: STATIC = current source inspection; LOCAL = executed current production functions with disposable fixtures and external wire doubles; FRESH = new provider request; HISTORICAL = retained predecessor evidence; REPLAY = recombination of measured results; INFERENCE = proposed design; UNVERIFIED = not exercised. No fresh full-production API test was performed.
