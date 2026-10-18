# PR-CN Before / After Extraction Evidence

Target text:

`As you watch the scene, a guard leans near the checkpoint, watching the road.`

Before repair, the inherited PR-CM diagnostic recorded:
- `_extract_visible_figure_candidate(...)` returned subject `as you`.
- `extract_contextual_leads_from_text(...)` persisted a `visible_suspicious_figure` lead with subject `as you`.
- The stored key was shaped like `visible_suspicious_figure_as_you_near_the_checkpoint_watching_the_road`.
- The malformed lead survived reload and entered the next provider payload.
- Passive-pressure source selection could select that malformed lead.

After repair:
- `_extract_visible_figure_candidate(...)` returns:
  - `kind`: `visible_suspicious_figure`
  - `subject`: `guard`
  - `position`: `near the checkpoint`
- `extract_contextual_leads_from_text(...)` includes a `guard` lead and does not include an `as you` lead.
- The persistence integration test stores and reloads `guard`, not `as you`.
- The next provider payload contains the guard lead key and does not contain `as_you`.
- Passive-pressure source selection returns `source=lead_figure`, `subject=guard`.

Representative command:

`.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cn_contextual_figure_integrity.py tests\\test_pr_cm_passive_pressure_contract.py::test_diagnostic_scene_stall_fallback_stores_guard_lead_subject -q --tb=short`

Result: 14 passed.
