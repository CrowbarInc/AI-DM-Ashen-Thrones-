# Context Cost Audit

Actual PR-CA input tokens: 23,413 / 24,124 / 24,890 / 24,763; total 97,190. No new token usage. Attribution below uses serialized character shares, apportioned against recorded token usage; it is an estimate, NOT exact tokenizer accounting. Payload keys/framing and escaping add a residual.

| Component (T1) | Characters | Share of system + user content | Approx. tokens |
| --- | ---: | ---: | ---: |
| System instructions | 4166 | 4.42% | ~1,035 |
| response_policy | 21242 | 22.53% | ~5275 |
| instructions | 14332 | 15.20% | ~3559 |
| turn_packet | 10645 | 11.29% | ~2644 |
| mechanical_resolution | 6253 | 6.63% | ~1553 |
| narrative_plan | 4965 | 5.27% | ~1233 |
| context_separation_contract | 3359 | 3.56% | ~834 |
| referent_tracking | 3005 | 3.19% | ~746 |
| decision_facing_answer_recipe | 2507 | 2.66% | ~623 |
| interaction_continuity_contract | 2157 | 2.29% | ~536 |
| scene | 1630 | 1.73% | ~405 |
| speaker_selection | 1455 | 1.54% | ~361 |
| anti_railroading_contract | 1451 | 1.54% | ~360 |
| fallback_behavior | 1403 | 1.49% | ~348 |
| gm_resolution_decision | 1184 | 1.26% | ~294 |
| character | 1059 | 1.12% | ~263 |
| campaign | 1057 | 1.12% | ~262 |
| scene_state_anchor_contract | 930 | 0.99% | ~231 |
| conversational_memory_window | 886 | 0.94% | ~220 |
| social_context | 784 | 0.83% | ~195 |
| resolution_contract | 723 | 0.77% | ~180 |
| social_response_structure_contract | 623 | 0.66% | ~155 |
| dialogue_social_plan | 557 | 0.59% | ~138 |
| transition | 529 | 0.56% | ~131 |
| referent_clause_prompt_hints | 502 | 0.53% | ~125 |
| response_type_contract | 416 | 0.44% | ~103 |
| narration_obligations | 404 | 0.43% | ~100 |
| turn_summary | 385 | 0.41% | ~96 |
| player_facing_narration_purity_contract | 373 | 0.40% | ~93 |
| bounded_improvisation | 359 | 0.38% | ~89 |
| session | 353 | 0.37% | ~88 |

response_policy contributes roughly 21-23%; instructions 15%; turn_packet 11%; mechanical_resolution 5-7%; narrative_plan 5%. These are operational policy/projections, not a full Pathfinder ruleset. Character mechanics, empty combat, campaign setup, faction pressures/agendas, lead machinery with empty lead rows, transitions and generic fallback contracts are weakly relevant to a bread opinion. No full rules book or large NPC biography is present. The actual scene and NPC profile are small.

Duplication is concrete: hierarchy prose appears in system and instructions; social knowledge hints appear both in instructions and social_context; refusal appears in resolution hint, the final instruction, obligations and narrative-mode structural deltas. turn_packet includes another response_policy subset and contracts; history appears in both recent_log and selected_conversational_memory. Equivalent material is not necessarily byte-identical. Cost evidence records every top-level field for every turn; nested duplicates are already included in parent sizes, so must not be added again.

History grows from zero to three selected excerpts, but cannot account for the high 23k baseline. The response schema itself is one small narration JSON object, no API schema; most cost is policy and operational payload scaffolding. Field-attribution does not prove causal attention dilution. Context cost is a separate finding; no optimization was performed.
