# 02 — Baseline and Repository State

PR-EG-R5 · 2026-10-17 · investigation only

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. The working tree already contained extensive tracked modifications and untracked production modules; HEAD alone does not identify the investigated implementation. `initial_git_status.txt` preserves this state; `source_inventory.json` binds source bytes and function locations. No repository AGENTS.md was found in the repository search. Python used: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\.venv\Scripts\python.exe`; the separate `venv` runtime is broken, so checks use `.venv`.

The R4 metrics recompute 69 scored turns, quality≥2 on 2 and playability≥2 on 1; five conversations started, four reached 15 and the fifth stopped at nine. Historical recovery 1/11 and continuity 8/57 are preserved evaluation judgments, not R5 rescoring. [artifacts/pr_eg_r4/metrics.json](../../artifacts/pr_eg_r4/metrics.json) and [artifacts/pr_eg_r4/playability_metrics.json](../../artifacts/pr_eg_r4/playability_metrics.json).

R4-R1 retains 63 focused passes and 692 passed/25 failed relevant regressions, with no newly reported failures; its final 24-turn sample has 24 exact authorized and history matches. These broad counts are historical. R5 reran the selected integrity/expression tests, obtaining {'passed': 77}; it did not rerun the 717-test family. [artifacts/pr_eg_r4_r1/regression_comparison.json](../../artifacts/pr_eg_r4_r1/regression_comparison.json).

Preservation: 9500 files hashed across game, data, tests, runtime experiment dependencies and both predecessor evidence trees. Changes detected: `[]`; additions: `[]`. R5's scripts, evidence and handoff are the only intended additions/updates. No production repair, NPC content change, save migration or gameplay implementation.
