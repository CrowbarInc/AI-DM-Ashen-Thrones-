# 03 — Historical Failure Reproduction

The isolated reproduction was saved before the production repair in `historical_reproduction_before.json`.

| Case | Before | After the repair, same harness |
| --- | --- | --- |
| A Harmless characterization | adopt false, `unsupported_addition` | adopt true |
| B Equivalent paraphrases | ambiguous | still ambiguous in this harness |
| C Unattended question | "I couldn't tell you." | watch fact plus "I couldn't say whether it is ever left unattended." |
| D North street | adopt false, `missing_authorized_claim`, `name_changed` | still rejected |
| E Security explanation | adopt false | still rejected, now including `prohibited_addition` |

Before:

```json
{
  "A_characterization": {
    "adopt": false,
    "reasons": [
      "unsupported_addition"
    ],
    "candidate": "I prefer the evening because I find it a little easier to think when the day is winding down and everything feels calm and peaceful."
  },
  "B_equivalent_paraphrases": {
    "result": "ambiguous"
  },
  "C_partial_question": {
    "selected_topic": null,
    "player_line": "",
    "answer_relation": "none",
    "delivered": "Sergeant Mara says, \"I couldn't tell you.\""
  },
  "D_entity_rename": {
    "adopt": false,
    "reasons": [
      "missing_authorized_claim",
      "name_changed"
    ]
  },
  "E_security_characterization": {
    "adopt": false,
    "reasons": [
      "unsupported_addition",
      "not_an_explanation"
    ]
  }
}
```

After:

```json
{
  "A_characterization": {
    "adopt": true,
    "reasons": [],
    "candidate": "I prefer the evening because I find it a little easier to think when the day is winding down and everything feels calm and peaceful."
  },
  "B_equivalent_paraphrases": {
    "result": "ambiguous"
  },
  "C_partial_question": {
    "selected_topic": null,
    "player_line": "Sergeant Mara says, \"Guards watch the north gate throughout the night. I couldn't say whether it is ever left unattended.\"",
    "answer_relation": "partially_informs",
    "delivered": "Sergeant Mara says, \"Guards watch the north gate throughout the night. I couldn't say whether it is ever left unattended.\""
  },
  "D_entity_rename": {
    "adopt": false,
    "reasons": [
      "missing_authorized_claim",
      "name_changed"
    ]
  },
  "E_security_characterization": {
    "adopt": false,
    "reasons": [
      "prohibited_addition",
      "unsupported_addition",
      "not_an_explanation"
    ]
  },
  "contract_keys": [
    "addressee",
    "answer_sufficiency",
    "authorized_propositions",
    "authorized_source",
    "canonical",
    "delivery_frame",
    "disclosure_posture",
    "entity_identities",
    "epistemic_posture",
    "fallback_response",
    "knowledge_posture",
    "operation",
    "permitted_expression_scope",
    "permitted_meaning",
    "player_question",
    "prior_delivered_statement",
    "prohibited_additions",
    "prohibited_speech_acts",
    "prompt",
    "proposition_id",
    "source_identity",
    "source_revision",
    "speaker_id",
    "speaker_identity",
    "speaker_name"
  ]
}
```

Case B stays ambiguous in `reproduce_historical.py` because that harness records the second sentence without copying `proposition_id`. The production path copies the identifier. The unit matrix and the final live recall are the evidence for grouping. Case C on the current deterministic path was false ignorance before the repair, rather than a complete yes. The repair answers with the authorized watch fact and an explicit limit.
