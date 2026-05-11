# Golden Replay Baseline - 2026-05-11

Exact prose comparison is opt-in. This baseline records structural and predicate-level observations for drift review.

Refresh / verify:

```powershell
python -m pytest tests\test_golden_replay.py -q
```

If `python` is not on PATH in the Codex desktop environment:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_golden_replay.py -q --tb=short
```

## Drift Categories

- `exact_drift`: opt-in exact normalized `final_text` hash mismatch.
- `structural_drift`: route, speaker, canonical target, FEM, fallback, or required metadata mismatch.
- `semantic_drift`: predicate failure such as scaffold leakage, wrong-speaker persistence, missing action/answer outcome, or branch mismatch.

## Canonical Scenario Baseline

| Scenario | Mode | Turns | Status | Drift | Sources | Fallback | Unavailable | Invariants |
|---|---:|---:|---:|---|---|---|---|---|
| directed_npc_question | end-to-end | 1 | pass | exact=0, structural=0, semantic=0 | generated_candidate | none | fallback_family | runner target, dialogue/social route, no scaffold leakage |
| vocative_override_after_prior_continuity | end-to-end | 2 | pass | exact=0, structural=0, semantic=0 | generated_candidate | none | fallback_family | turn 2 guard target, spoken vocative source, no scaffold leakage |
| wrong_speaker_strict_social_emission | end-to-end | 1 | pass | exact=0, structural=0, semantic=0 | normalized_social_candidate | none | fallback_family | canonical runner target, illegal Merchant removed, no scaffold leakage |
| declared_alias_dialogue_plan | direct-seam | 1 | pass | exact=0, structural=0, semantic=0 | block_s_stub | none | fallback_family | declared alias accepted, runner target preserved, no scaffold leakage |
| thin_answer_action_outcome_final_emission | end-to-end | 1 | pass | exact=0, structural=0, semantic=0 | action_outcome_upstream_prepared_repair | upstream_prepared_emission | selected_speaker_id | action outcome contract survives, no thin generic identity line, no scaffold leakage |
| sanitizer_scaffold_leakage | end-to-end | 1 | pass | exact=0, structural=0, semantic=0 | global_scene_fallback | gate_terminal_repair | selected_speaker_id | scaffold terms stripped, final text non-empty, no scaffold leakage |
| opening_fallback_path | direct-seam | 1 | pass | exact=0, structural=0, semantic=0 | opening_deterministic_fallback | scene_opening | none | scene opening repair, first impression fallback, no scaffold leakage |
| lead_followup_with_dialogue_lock | end-to-end | 2 | pass | exact=0, structural=0, semantic=0 | generated_candidate | none | fallback_family | tavern runner lock persists, dialogue route persists, no scaffold leakage |
| scenario_spine_three_branch | schema-smoke + golden harness | 3 branches / 3 turns | pass | exact=0, structural=0, semantic=0 | generated_candidate, retry_output, action_outcome_upstream_prepared_repair | upstream_prepared_emission on notice branch | selected_speaker_id on notice branch | branch ids represented, branch turn counts represented, structural divergence present, no scaffold leakage |

## Notes

- Non-fallback dialogue rows usually leave `fallback_family` unavailable; this is expected.
- Scenario 5 and scenario 9 notice branch expose `fallback_family=upstream_prepared_emission`.
- Scenario 6 exposes `fallback_family=gate_terminal_repair`.
- Scenario 7 exposes `fallback_family=scene_opening` and `fallback_temporal_frame=first_impression`.
