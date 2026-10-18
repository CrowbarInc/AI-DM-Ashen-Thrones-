# PR-CH Target Failure Trace

Target: `tests/test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b`

Player input: `I turn to the Kiln Tender. "When is kiln three banked?"`

Authored NPC topic:
- NPC: `kiln_tender` / `Kiln Tender`
- Topic: `kiln_bank`
- Text: `Kiln three is banked from dusk until the morning bell.`

Observed final response:

`Kiln Tender says, "I cannot answer that from what is settled here."`

Expected response contains `morning bell` or `kiln three`.

Deterministic resolver evidence:
- `resolution.kind = question`
- `resolution.success = true`
- `social.npc_id = kiln_tender`
- `social.npc_name = Kiln Tender`
- `social.target_source = explicit_target`
- `social.grounding_reason_code = authoritative_speaker_eligible`
- `social.reply_kind = answer`
- `social.npc_reply_expected = true`
- `social.topic_revealed.id = kiln_bank`
- `social.topic_revealed.text = Kiln three is banked from dusk until the morning bell.`

Authored realization evidence:

`realize_authored_knowledge_answer(...)` returns `Kiln Tender mutters, "Word is, kiln three is banked from dusk until the morning bell."`

First failing boundary: final emission validation/fallback/immutability after deterministic social answer selection.

