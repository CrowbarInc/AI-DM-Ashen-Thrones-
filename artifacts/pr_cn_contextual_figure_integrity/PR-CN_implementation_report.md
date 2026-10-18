# PR-CN Implementation Report

Decision: B - PARTIAL REPAIR.

Live provider calls: 0.

Summary:
- Repaired contextual visible-figure extraction so observer framing such as "As you watch..." and "While you survey..." is stripped before subject selection.
- Added bounded subject validation for observer, negated, absent, and rumor-frame subjects.
- Preserved non-authoritative contextual-lead behavior: no NPC creation, no world mutation, no `gm_resolution_decision` changes.
- Added PR-CN focused positive, negative, extraction, persistence, next-turn context, and passive-pressure selection tests.
- Updated the inherited PR-CM diagnostic to assert the repaired contract: target sentence now stores `guard`, not `as you`.

Implementation:
- `game/gm.py`: added observer-frame stripping and invalid-subject filtering around `_extract_visible_figure_candidate`.
- `tests/test_pr_cn_contextual_figure_integrity.py`: new PR-CN focused tests.
- `tests/test_pr_cm_passive_pressure_contract.py`: diagnostic expectation updated from documented defect to repaired boundary.

Limitations:
- Existing saved sessions that already contain malformed `as you` leads are not migrated or rewritten. This cycle prevents newly extracted malformed leads.
- Broader shared-pipeline failures remain at the inherited baseline: 41 passed / 24 failed.
