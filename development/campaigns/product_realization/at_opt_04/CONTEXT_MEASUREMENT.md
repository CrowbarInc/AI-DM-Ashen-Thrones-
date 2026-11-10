# Context Measurement

The captured F3 provider payload was not stored. Current `chat()` does not build a prompt for “I step back from the notice board.” This measurement calls `build_messages` on snapshot `2026-11-08T16-50-45_8caf7aff`, with scene files from `artifacts/pr_play_79df3/http_data`, `resolution=None`, and `prompt_profile="manual_play_auto"`. That is the AT-OPT-03 reconstruction, not the historical request bytes.

OpenAI construction was replaced with a class that raises. `call_gpt` was replaced with a counter that raises. Constructions: 0. Entries: 0. Copied session, world, character, scene, combat, and log objects were unchanged. The temporary state files were unchanged.

## Sizes

Serializer: `json.dumps(messages, ensure_ascii=False)` encoded as UTF-8. Admission estimate: `(byte length // 3) + 64`.

| Measure | Baseline | Optimized |
| --- | ---: | ---: |
| Message blob | 83,040 | 80,403 |
| User JSON string | 68,675 | 66,186 |
| System text | 9,558 | 9,558 |
| Admission estimate | 27,744 | 26,865 |

Byte reduction: 2,637 (3.18% of the blob). Estimate reduction: 879. The user string shrinks by 2,489 because the outer dump escapes quotes inside it. AT-OPT-03's offline cut recorded the same pair, user 66,186 and blob 80,403. The hypothesis matches. Neither number is provider usage. The recorded F3 input is still 22,777, so the reconstruction remains above that bill by about the same unexplained gap, now starting from 26,865 instead of 27,744.

## Structural comparison

Root policy SHA-256 is unchanged (`e2224fcb72b152f2c0b9e06b27ea4bcf183d918f6d787ad41dd16376f6ccee3f`). Root keys are unchanged.

Removed from `turn_packet.response_policy`: `rule_priority_order`, `must_answer`, `forbid_state_invention`, `forbid_secret_leak`, `allow_partial_answer`, `diegetic_only`, `prefer_scene_momentum`, `prefer_specificity`, `no_validator_voice`, `scene_momentum_due`, `uncertainty`, `response_type_contract`.

Preserved, with unchanged value hashes:

- `response_delta` — same child keys, different values.
- `answer_completeness` — root also has `answer_exposition_plan`.
- `planner_seam_trace` — nested also has `response_type_contract_resolution`.

Every other top-level section hash matches, including `turn_packet` with `response_policy` removed. Instruction count stays 78. `must_advance_scene` stays true.

Machine-readable record: `artifacts/at_opt_04/semantic_comparison.json`.

## Limitation

This is a serialized-structure measurement. It does not show that a model assigns the same meaning to a value that now appears only on the root policy.
