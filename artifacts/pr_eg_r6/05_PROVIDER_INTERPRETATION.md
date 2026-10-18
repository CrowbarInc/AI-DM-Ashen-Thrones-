# 05 — Provider Interpretation

`propose_semantic_plan` sends one strict JSON-schema request, temperature 0, purpose `semantic_plan`, max 350 output tokens.

The payload contains the utterance, up to eight participant ids and aliases, a 240-character scene summary, the last four delivered lines, the prior question text, and up to twelve permitted public source ids with 180 characters of text.

It does not include hidden topic text, faction secrets, the whole campaign log, or the whole canonical state.

The model does not decide truth, disclosure, mechanical success, or commitments. A returned source id is only a candidate. The host drops ids that are not on that NPC's records.

If the provider is disabled, the call fails, or the JSON is unusable, the turn fails closed to "I didn't catch what you're asking." It does not fall through to lexical topic selection.
