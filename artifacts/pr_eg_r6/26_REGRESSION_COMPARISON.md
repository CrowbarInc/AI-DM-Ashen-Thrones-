# 26 — Regression Comparison

The PR-EG-R4 relevant file list, plus the R4-R1 delivery file and the R6 tests, was run once.

Passed 753. Failed 27. Name-matched inherited failures 25. Names not in the R4-R1 failure set:

[
  {
    "name": "tests.test_pr_ef_r1_semantic_handoff::test_semantic_ownership_precedes_active_npc[SESSION-RULES-components1]",
    "kind": "failure",
    "message": "PermissionError: [WinError 5] Access is denied: 'C:\\\\Users\\\\Master Mandalcio\\\\Documents\\\\Tabletop Gaming\\\\AI Dungeon Master\\\\ashen_thrones_ai_gm\\\\development\\\\tmp\\\\pytest\\\\test_sem"
  },
  {
    "name": "tests.test_pr_ef_r1_semantic_handoff::test_semantic_confirmation_rejects_stale_scene",
    "kind": "failure",
    "message": "PermissionError: [WinError 5] Access is denied: 'C:\\\\Users\\\\Master Mandalcio\\\\Documents\\\\Tabletop Gaming\\\\AI Dungeon Master\\\\ashen_thrones_ai_gm\\\\development\\\\tmp\\\\pytest\\\\test_sem"
  }
]

The two semantic-handoff names failed with `WinError 5` while replacing `session.json` and passed when rerun by themselves. They are environmental file-lock flakes in the large run, not a semantic-plan assertion change.

The preseal test that expects `initial_generation` already failed in the repaired R4-R1 JUnit. It was not modified.
