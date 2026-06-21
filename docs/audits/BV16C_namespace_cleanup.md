# BV16C — Namespace Cleanup

**Date:** 2026-06-21

## Production (`final_emission_terminal_pipeline`)

Delegated finalize-tail calls now use **module-qualified owner lookups**:

- `visibility_fallback.apply_visibility_enforcement`
- `acceptance_quality.apply_acceptance_quality_n4_floor_seam`
- `interaction_continuity.apply_interaction_continuity_emission_step` / `attach_interaction_continuity_validation`
- `emission_repairs._apply_fallback_behavior_layer` (and referent-clarity merge helpers)
- `opening_fallback.reassert_scene_opening_accepted_candidate` (unchanged)

**Removed:** bare `from owner import symbol` bindings that exposed delegate symbols on the terminal module namespace for test monkeypatching.

**Unchanged:** enforcement order inside `run_gate_terminal_enforcement_pipeline`; no ownership or behavior changes when unpatched.

## Tests

- **17** AST importers removed from terminal pipeline (visibility noop cluster migrated)
- **13** files dropped unused `import terminal_pipeline` after migration
- `tests/helpers/terminal_owner_test_seams.py` added for shared visibility noop helper
- `tests/helpers/post_speaker_finalize_probe.py` probes now patch owner modules directly

## Remaining legitimate terminal imports

Tests that still import `terminal_pipeline` for **orchestration** (not delegate monkeypatch):

- Source-order / delegation governance (`inspect.getsource(run_gate_terminal_enforcement_pipeline)`)
- Direct unit calls to `_apply_referent_clarity_pre_finalize`
- Ownership registry BJ-73/74/75 direct-call assertions
- Production exit owners (`strict_social_stack`, `generic_exit`)
