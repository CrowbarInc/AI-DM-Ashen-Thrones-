# Protected Semantic Mutation Report (BY2)

- schema version: 1
- corpus: protected_replay
- total turns: 8
- mutated turns: 3
- attributable first mutations: 2
- first-source coverage rate: 66.67%
- unknown first-source count: 1
- semantic mutation risk (mean / max): 23.33 / 60

## Bucket distribution

- fallback: 1
- policy: 1

## Top mutation sources

- game.response_policy_enforcement.apply_response_policy_enforcement: 1
- broken_checkpoint_continuity: 1
- game.social_exchange_emission.build_final_strict_social_response: 1

## Representative high-risk turns

- thin_answer_action_outcome_final_emission|idx:0: risk=60 bucket=unknown source=broken_checkpoint_continuity

## Attribution gaps

- thin_answer_action_outcome_final_emission|idx:0: missing=continuity_join_between_checkpoints likely_owner=global_scene_fallback by3=add intermediate checkpoint between broken continuity seam
