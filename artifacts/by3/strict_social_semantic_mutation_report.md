# Strict-Social Semantic Mutation Report (BY3)

- schema version: 1
- corpus: protected_replay
- total turns: 8
- mutated turns: 3
- attributable first mutations: 3
- first-source coverage rate: 100.00%
- unknown first-source count: 0

## Before/after BY3 coverage

- target turn: wrong_speaker_strict_social_emission|idx:0
- gap closed: True

### Before (BY2)

- changed_count: 0
- trace_continuity: False
- post_gate_mutation_detected: True
- first bucket/source: None / None
- missing checkpoint: writer_or_pre_policy_checkpoint

### After (BY3)

- changed_count: 1
- trace_continuity: True
- post_gate_mutation_detected: True
- first bucket/source: fallback / game.social_exchange_emission.build_final_strict_social_response
- first checkpoint: normalized_social_candidate

## Bucket distribution

- fallback: 1
- policy: 1
- sanitizer: 1

## Top mutation sources

- game.response_policy_enforcement.apply_response_policy_enforcement: 1
- game.output_sanitizer.sanitize_player_facing_output: 1
- game.social_exchange_emission.build_final_strict_social_response: 1

## Remaining attribution gaps

- (none)

## Remaining BY4 candidates

- (none)
