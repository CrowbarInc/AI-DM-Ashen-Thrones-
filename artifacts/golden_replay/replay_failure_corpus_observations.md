# Protected Replay Observation Corpus

Report-only expansion corpus for protected replay recurrence history.
Rows map controlled failure classifications to existing protected scenarios.

## Run Summary

- Status: `failed`
- Command: `python tools/expand_protected_replay_observations.py`
- Generated at: `2026-06-20T12:00:00Z`
- Artifact location: `artifacts/golden_replay/replay_failure_corpus_observations.md`
- Classified failures: `3`

## Failure Table

| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| wrong_speaker_strict_social_emission | tests/test_golden_replay.py::test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants | 0 | selected_speaker_id: exact value mismatch | structural_drift | runner | merchant | speaker | medium | speaker | none | game/speaker_contract_enforcement.py |
| directed_npc_question | tests/test_golden_replay.py::test_golden_replay_directed_npc_question_structural_invariants | 1 | final_emitted_source: exact value mismatch | structural_drift | anti_reset_local_continuation_fallback | global_scene_fallback | fallback | medium | fallback | none | game/final_emission_gate.py |
| sanitizer_scaffold_leakage | tests/test_golden_replay.py::test_golden_replay_sanitizer_scaffold_leakage_structural_invariants | 8 | scaffold_leakage: exact value mismatch | semantic_drift | false | true | sanitizer | medium | sanitizer | none | game/output_sanitizer.py |
