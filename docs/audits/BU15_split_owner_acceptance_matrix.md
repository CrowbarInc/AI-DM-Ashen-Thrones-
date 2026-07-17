# BU15/BU16/BU17/BU18/BU19 Split-Owner Acceptance Matrix

Canonical cross-family owner literals shared by classifier, dashboard, golden replay FEM projection, runtime lineage summary, and attribution inventory tests.

| matrix_id | family | event_kind | fallback/mutation kind | selection_owner | content_owner | owner_bucket_field | owner_bucket | repair_kind | dashboard_case_id | fem_projection |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scene_opening | opening | fallback_selected | scene_opening | game.final_emission_gate | game.opening_deterministic_fallback | opening_fallback_owner_bucket | upstream-prepared | opening_deterministic_fallback | scene_opening_split_owner | matrix_fem |
| opening_failed_closed | opening | fallback_selected | opening_failed_closed | game.final_emission_gate | game.final_emission_gate | opening_fallback_owner_bucket | sealed-gate | opening_deterministic_fallback_failed_closed | opening_failed_closed_split_owner | matrix_fem |
| visibility_enforcement | visibility | fallback_selected | visibility_hard_replacement | game.final_emission_visibility_fallback | game.final_emission_sealed_fallback | visibility_fallback_owner_bucket | sealed-gate | visibility_enforcement | visibility_enforcement_split_owner | matrix_fem |
| first_mention_enforcement | visibility | fallback_selected | first_mention_hard_replacement | game.final_emission_visibility_fallback | game.final_emission_sealed_fallback | visibility_fallback_owner_bucket | sealed-gate | first_mention_enforcement | first_mention_enforcement_split_owner | matrix_fem |
| referential_clarity_enforcement | visibility | fallback_selected | referential_clarity_hard_replacement | game.final_emission_visibility_fallback | game.social_exchange_emission | visibility_fallback_owner_bucket | strict-social-visibility | referential_clarity_enforcement | referential_clarity_enforcement_split_owner | matrix_fem |
| referential_local_substitution | visibility | mutation | referential_clarity_local_substitution_mutation |  |  | visibility_fallback_owner_bucket | strict-social-visibility | referential_clarity_local_substitution | referential_local_substitution_split_owner | matrix_fem |
| sanitizer_empty_output | sanitizer | fallback_selected | sanitizer_empty_output | game.output_sanitizer | game.output_sanitizer |  |  | sanitizer_empty_output | sanitizer_empty_output_split_owner | matrix_fem |
| sanitizer_strict_social | sanitizer | fallback_selected | sanitizer_strict_social | game.output_sanitizer | game.social_exchange_emission |  |  | strict_social_repair | sanitizer_strict_social_split_owner | matrix_fem |
| upstream_fast_fallback | upstream_fast | fallback_selected | upstream_fast_fallback | game.api | game.gm_retry |  | retry |  | upstream_fast_fallback_split_owner | matrix_fem |
| sealed_social_interlocutor | sealed | fallback_selected | sealed_social_interlocutor_fallback | game.final_emission_gate | game.social_exchange_emission | sealed_fallback_owner_bucket | strict-social-sealed |  | sealed_social_interlocutor_split_owner | matrix_fem |
| sealed_passive_scene_pressure | sealed | fallback_selected | sealed_passive_scene_pressure_fallback | game.final_emission_gate | game.final_emission_sealed_fallback | sealed_fallback_owner_bucket | sealed-gate |  | sealed_passive_scene_pressure_split_owner | matrix_fem |
| sealed_npc_pursuit_neutral | sealed | fallback_selected | sealed_npc_pursuit_neutral_fallback | game.final_emission_gate | game.final_emission_sealed_fallback | sealed_fallback_owner_bucket | sealed-gate |  | sealed_npc_pursuit_neutral_split_owner | matrix_fem |
| sealed_anti_reset_continuation | sealed | fallback_selected | sealed_anti_reset_continuation_fallback | game.final_emission_gate | game.final_emission_sealed_fallback | sealed_fallback_owner_bucket | sealed-gate |  | sealed_anti_reset_continuation_split_owner | matrix_fem |
| sealed_global_scene | sealed | fallback_selected | sealed_global_scene_fallback | game.final_emission_gate | game.final_emission_sealed_fallback | sealed_fallback_owner_bucket | sealed-gate |  | sealed_global_scene_split_owner | matrix_fem |
| sealed_unknown_replacement | sealed | fallback_selected | sealed_unknown_replacement | game.final_emission_gate | game.final_emission_gate | sealed_fallback_owner_bucket | unknown-none |  | sealed_unknown_replacement_split_owner | matrix_fem |
| sealed_or_global_replacement_legacy | sealed | fallback_selected | sealed_or_global_replacement | game.final_emission_gate | game.final_emission_gate | sealed_fallback_owner_bucket | sealed-gate |  |  | excluded |

Total rows: 16
Dashboard probes: 15
Sealed subkind dashboard parity: 6/6 non-legacy rows

## Legacy matrix rows (BU17 synthetic-only)
- `sealed_or_global_replacement_legacy`: Synthetic classifier vocabulary only; production FEM maps global_scene_fallback to sealed_global_scene_fallback. Dashboard and FEM projection probes intentionally excluded; classifier coverage remains in test_failure_classifier.py::test_failure_classifier_accepts_sealed_family_runtime_lineage_split_owners.

## FEM projection exclusions
- `sealed_or_global_replacement_legacy`: Synthetic classifier vocabulary only; production FEM maps global_scene_fallback to sealed_global_scene_fallback. Dashboard and FEM projection probes intentionally excluded; classifier coverage remains in test_failure_classifier.py::test_failure_classifier_accepts_sealed_family_runtime_lineage_split_owners.

## Split-owner matrix change workflow (BU22)

Canonical source: `SPLIT_OWNER_ACCEPTANCE_MATRIX` in `tests/helpers/failure_classification_split_owner.py`. Full checklist: `docs/audits/README.md`.

1. Update `SPLIT_OWNER_ACCEPTANCE_MATRIX` (no production emission changes for matrix-only edits).
2. Update dashboard evidence cells only if dashboard strings changed (`tests/test_failure_dashboard_controlled_failures.py`).
3. Regenerate and validate: `python scripts/refresh_split_owner_acceptance_matrix.py` (or `make split-owner-matrix-refresh`).
4. Partial modes: `--write-report-only`, `--check-only`, `--skip-pytest`.
5. Run focused classifier/dashboard/projection tests only when behavior changed.

## Maintainer commands (BU20/BU21/BU23/BU24)

Full refresh (Windows-native; default):

```bash
python scripts/refresh_split_owner_acceptance_matrix.py
```

Unix/mac/Git Bash equivalent:

```bash
make split-owner-matrix-refresh
```

Report only / check only:

```bash
python scripts/refresh_split_owner_acceptance_matrix.py --write-report-only
python scripts/refresh_split_owner_acceptance_matrix.py --check-only
python scripts/refresh_split_owner_acceptance_matrix.py --skip-pytest
```

Contract gate only (also in CI convergence-checks and default fast lane):

```bash
python scripts/check_split_owner_acceptance_matrix.py
# or
make split-owner-matrix-check
# or
python -m pytest tests/test_split_owner_acceptance_matrix_contract.py -q -m split_owner_matrix_contract
```