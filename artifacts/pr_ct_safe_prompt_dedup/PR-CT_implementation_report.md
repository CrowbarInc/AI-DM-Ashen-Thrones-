# PR-CT Implementation Report

Git HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

Implementation: `game.gm._dedupe_provider_payload_instructions` removes exact system-owned duplicate instruction strings at the provider-payload boundary after resolver-specific payload assembly and before JSON serialization.

Live provider calls: 0.

Tokenizer: local estimate `ceil(chars/4)`; exact GPT-4.1 tokenizer was not installed or fetched.

| Fixture | Name | Baseline bytes | Reduced bytes | Byte reduction | Estimated token reduction |
|---|---:|---:|---:|---:|---:|
| A | harmless_npc_preference | 131172 | 129755 | 1417 | 368 |
| B | authored_npc_fact_question | 145670 | 144253 | 1417 | 369 |
| C | observation_notice_board | 131512 | 130095 | 1417 | 368 |
| D | ordinary_observation | 126609 | 125116 | 1493 | 398 |
| E | natural_language_exploration | 148799 | 147366 | 1433 | 375 |
| F | consequential_social_interaction_proxy | 106169 | 104872 | 1297 | 324 |
| G | physical_world_action_proxy | 98473 | 97176 | 1297 | 324 |
| H | exploration_hypothesis_proxy | 100420 | 99123 | 1297 | 324 |

Total byte reduction across measured fixtures: 11068. Per-fixture range: 1297 to 1493 bytes.

Decision: B - LIMITED SAVINGS. The reduction is intentionally small and exact; no semantic prompt profiling was introduced.
