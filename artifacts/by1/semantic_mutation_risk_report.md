# Semantic Mutation Risk Report (BY1 sample)

- total turns: 2
- mutated turns: 2
- attributable first mutations: 2
- first-source coverage rate: 100.00%

## Per-turn risk

| sequence | bucket | source | changed | risk | band |
|---|---|---|---:|---:|---|
| 2 | sanitizer | game.output_sanitizer.sanitize_player_facing_output | 1 | 0 | low |
| 2 | fallback | game.final_emission_visibility_fallback.apply_visibility_enforcement | 1 | 0 | low |

## Bucket frequencies

- fallback: 1
- sanitizer: 1
