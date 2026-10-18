# PR-CX Full / Reduced Comparison

Focused comparison command:

`.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cx_authority_assurance.py tests\\test_pr_cw_social_context_projection.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cx_focus`

Result: 48 passed.

Expanded comparison with immutable boundary:

`.\\.venv\\Scripts\\python.exe -m pytest tests\\test_pr_cx_authority_assurance.py tests\\test_pr_cw_social_context_projection.py tests\\test_pr_br_continuation18_immutable_boundary.py -q --tb=short --basetemp=codex_pytest_tmp_pr_cx_focus2`

Result: 69 passed.

Exact validation outcomes:

| Case | Full Context | Reduced Context |
|---|---|---|
| Harmless preference | accepted | accepted |
| Harmless opinion | accepted | accepted |
| Incidental characterization | accepted | accepted |
| Grounded observation | accepted in authored finalization coverage | accepted in authored finalization coverage |
| Authored factual answer | accepted in PR-CP | accepted path unaffected |
| Unsupported biography | rejected | rejected |
| Unsupported geography | rejected | rejected |
| Hidden information | rejected | rejected |
| Consequential NPC action | rejected | rejected |
| Unauthorized discovery | rejected | rejected |
| Unsupported certainty | rejected | rejected |
| Unauthorized state change | rejected | rejected |
| Smuggled declarations | rejected as `unexpected_declared_claims` | rejected as `unexpected_declared_claims` |

