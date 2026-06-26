# CL5 Semantic Mutation Policy Extraction

## Files changed

- `tests/helpers/golden_replay_projection_semantic.py`
  - New focused semantic mutation projection helper.
- `tests/helpers/golden_replay_projection_extractors.py`
  - Removed the local `project_semantic_mutation_summary` implementation.
  - Re-exported `project_semantic_mutation_summary` from the new semantic helper for compatibility.
- `tests/test_golden_replay_projection_semantic.py`
  - Added focused locks for summary shape, JSON byte-equivalent ordering-insensitive output, compatibility imports, optional-value filtering, and observed-turn projection.
- `tests/test_golden_replay_projection_modules.py`
  - Added the semantic helper to the projection module import graph.
  - Locked facade identity against `golden_replay_projection_semantic.project_semantic_mutation_summary`.

## Functions moved

- `project_semantic_mutation_summary`
  - From: `tests.helpers.golden_replay_projection_extractors`
  - To: `tests.helpers.golden_replay_projection_semantic`

No semantic mutation aggregation, classification, or rendering helpers were moved because those responsibilities already live outside the replay projection extractor in existing semantic mutation helpers such as `tests.helpers.semantic_mutation_attribution` and related measurement/closeout modules.

## Compatibility wrappers retained

- `tests.helpers.golden_replay_projection_extractors.project_semantic_mutation_summary`
  - Retained as an import/re-export of the semantic helper.
- `tests.helpers.golden_replay_projection.project_semantic_mutation_summary`
  - Public facade remains unchanged and resolves to the same callable.

## Before/after module responsibility summary

Before CL5:

- `golden_replay_projection_extractors.py` owned payload/FEM/sanitizer extraction, protected extraction specs, flat protected projection, compatibility presence wrappers, and semantic mutation summary projection.

After CL5:

- `golden_replay_projection_semantic.py` owns semantic mutation summary projection.
- `golden_replay_projection_extractors.py` still owns protected extraction specs, FEM/sanitizer extraction, trace source extraction, flat protected projection, semantic mutation compatibility re-export, and presence compatibility wrappers.

## Validation commands and results

Requested command failed because `python` is not on PATH in this PowerShell session:

```powershell
python -m pytest tests/test_golden_replay_projection.py tests/test_golden_replay_projection_metadata.py tests/test_golden_replay_projection_presence_integration.py -q
```

Successful equivalent with bundled runtime Python:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection.py tests\\test_golden_replay_projection_metadata.py tests\\test_golden_replay_projection_presence_integration.py -q
```

Result: `16 passed`.

Module-boundary validation:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection_modules.py -q
```

Result: `44 passed`.

Semantic-specific CL5 locks:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection_semantic.py -q
```

Result: `4 passed`.

Existing semantic attribution suite:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_by_first_semantic_mutation_attribution.py -q
```

Result: `21 passed`.

## Remaining responsibilities inside `golden_replay_projection_extractors.py`

- Protected extraction registry and spec validation.
- FEM flat observed-field extraction and shaping.
- Sanitizer trace and sanitizer lineage extraction.
- Runtime lineage event extraction from payload/FEM.
- Route resolution and trace source extraction.
- Flat protected observed-field projection.
- Semantic mutation compatibility re-export.
- Presence/unavailable compatibility wrappers from CL2.

## Recommendation for next block

CL6 should target another cohesive extractor responsibility only if it has a similarly small, clear boundary. The best candidates are sanitizer lineage extraction or runtime lineage extraction; avoid combining either with protected spec ownership in the same block.
