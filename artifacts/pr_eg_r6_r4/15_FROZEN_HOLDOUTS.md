# 15 — Frozen Holdouts

`freeze.json` contains SHA-256 for all three partition files, corpus/adapter code and relevant unchanged production kernels. `adapter_correction.json` documents the single execution correction without changing partition hashes. Original frozen manifest remains intact. `supplemental_freeze.json` separately hashes the additional challenge data before its calls. Verify with `python -m experiments.pr_eg_r6_r4.run verify`.

Validation and holdout labels were not edited after exposure. No prompt or matcher tuning followed official holdout inspection. Separately frozen challenge cases and paraphrases (paraphrase_freeze.json) broaden coverage after the primary run; they are diagnostic, not replacement holdout evidence. Historical predecessor holdouts were not edited.
