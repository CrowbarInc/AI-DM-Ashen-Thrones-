# PR-PLAY-19 Request Contract
PASS. This report embeds actual captured data from artifacts/atgb/pr_play_19/live/20261101T155921Z-dece64b94204/diagnostics/actual_assembled_request.json, captured before original RequestAttempt.dispatch invokes the existing SDK. sdk_serialized_request.json independently records the actual HTTP JSON body; exact equality verified. These are live captures, not source-template reconstructions.

Model gpt-4.1-mini; application purpose primary_turn, logical operation scene_opening. Sequence 1, admission sequence 1; owner gm.call_gpt. The generic purpose label does not mean an ordinary turn occurred. System and user roles only; no separate developer message. max_output_tokens=3000; temperature/top_p not set by application. No tools, fallback, or judges added. Provider response reports temperature=1, top_p=1, tools=[].

Responses API text.format: type=json_schema, name=opening_presentation, strict=true. Root requires only selected_entries; every item requires catalog_id and variant_id, with per-entry enum pairing. additionalProperties=false at root and each choice. Array minItems=1/maxItems=24. Eleven public catalog choices, six required. Required coverage, order, duplicates and disclosure are independently engine validated. No legacy narration/declaration/state-change fields required or permitted. Dedicated selection instructions replace legacy narration instructions. Contract alignment passed before SDK dispatch.

Source references: game/gm.py:5305 (preparation), :5417 (kwargs), :5427 (dispatch); game/provider_budget.py:312; game/opening_presentation_renderer.py:264, :287, :330, :378, :422. Exact schema also saved separately as diagnostics/exact_schema.json. No API keys, authorization headers or environment dumps captured.

## Actual sanitized assembled request and exact schema

```json
{
  "capture_boundary": "RequestAttempt.dispatch immediately before original dispatch",
  "timestamp": "2026-11-01T15:59:27.796910+00:00",
  "request_sequence": 1,
  "admission_sequence": 1,
  "purpose": "primary_turn",
  "owner": "gm.call_gpt",
  "attempt_id": "044e3a324dc24a3aa1e1d806155f8177",
  "request": {
    "model": "gpt-4.1-mini",
    "input": [
      {
        "role": "system",
        "content": "OPENING PRESENTATION PLAN: Return one JSON object and no other text. The only allowed key is selected_entries. Each entry may contain only catalog_id and variant_id. Select every required entry in increasing sequence. Optional entries may be included. Do not write narration, facts, outcomes, or state changes.\nOPENING_PRESENTATION_CATALOG\n{\"entries\":[{\"catalog_id\":\"rc_a83c5bcfc65e\",\"required\":false,\"sequence\":0,\"variant_ids\":[\"authored\",\"concise\"]},{\"catalog_id\":\"rc_d40a1efdddb3\",\"required\":false,\"sequence\":1,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_3b26b521977b\",\"required\":false,\"sequence\":2,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_b59727e13c62\",\"required\":false,\"sequence\":3,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_be348e85a5e6\",\"required\":false,\"sequence\":4,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_31feab1dcf72\",\"required\":true,\"sequence\":5,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_a0201a45af25\",\"required\":true,\"sequence\":6,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_280f5390057f\",\"required\":true,\"sequence\":7,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_4a217a3c17bc\",\"required\":true,\"sequence\":8,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_819bf0e987bb\",\"required\":true,\"sequence\":9,\"variant_ids\":[\"authored\"]},{\"catalog_id\":\"rc_6c31b34a1529\",\"required\":true,\"sequence\":10,\"variant_ids\":[\"authored\"]}]}\nEND_OPENING_PRESENTATION_CATALOG"
      },
      {
        "role": "user",
        "content": "{\"response_type_contract\": {\"required_response_type\": \"scene_opening\"}, \"opening_public_choices\": [{\"catalog_id\": \"rc_a83c5bcfc65e\", \"variants\": {\"authored\": \"The notice board lists taxes, curfew rules, and a warning about a missing patrol.\", \"concise\": \"The notice board lists taxes, curfew rules, and a warning about a patrol that has gone missing.\"}}, {\"catalog_id\": \"rc_d40a1efdddb3\", \"variants\": {\"authored\": \"A gate serjeant manages the crowd and keeps one eye on the roster board.\"}}, {\"catalog_id\": \"rc_3b26b521977b\", \"variants\": {\"authored\": \"A tavern runner trades hot stew and rumors near the rain barrel.\"}}, {\"catalog_id\": \"rc_b59727e13c62\", \"variants\": {\"authored\": \"Threadbare watchers and refugees cluster along the muddy gate line.\"}}, {\"catalog_id\": \"rc_be348e85a5e6\", \"variants\": {\"authored\": \"Ash Compact census delays have tightened the eastern caravan choke point.\"}}, {\"catalog_id\": \"rc_31feab1dcf72\", \"variants\": {\"authored\": \"Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate.\"}}, {\"catalog_id\": \"rc_a0201a45af25\", \"variants\": {\"authored\": \"Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in.\"}}, {\"catalog_id\": \"rc_280f5390057f\", \"variants\": {\"authored\": \"A notice board lists new taxes, curfews, and a posted warning about a missing patrol.\"}}, {\"catalog_id\": \"rc_4a217a3c17bc\", \"variants\": {\"authored\": \"A tavern runner shouts offers of hot stew and paid rumor.\"}}, {\"catalog_id\": \"rc_819bf0e987bb\", \"variants\": {\"authored\": \"A well-appointed townhouse overlooking the square flies noble colors\u2014a quiet contrast to the mud and clamor.\"}}, {\"catalog_id\": \"rc_6c31b34a1529\", \"variants\": {\"authored\": \"One figure in threadbare clothes stands uncannily still, gaze flicking to packs and faces more than the gate queue.\"}}]}"
      }
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": "opening_presentation",
        "strict": true,
        "schema": {
          "type": "object",
          "properties": {
            "selected_entries": {
              "type": "array",
              "minItems": 1,
              "maxItems": 24,
              "items": {
                "anyOf": [
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_a83c5bcfc65e"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored",
                          "concise"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_d40a1efdddb3"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_3b26b521977b"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_b59727e13c62"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_be348e85a5e6"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_31feab1dcf72"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_a0201a45af25"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_280f5390057f"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_4a217a3c17bc"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_819bf0e987bb"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "properties": {
                      "catalog_id": {
                        "type": "string",
                        "enum": [
                          "rc_6c31b34a1529"
                        ]
                      },
                      "variant_id": {
                        "type": "string",
                        "enum": [
                          "authored"
                        ]
                      }
                    },
                    "required": [
                      "catalog_id",
                      "variant_id"
                    ],
                    "additionalProperties": false
                  }
                ]
              }
            }
          },
          "required": [
            "selected_entries"
          ],
          "additionalProperties": false
        }
      }
    },
    "max_output_tokens": 3000
  }
}
```
