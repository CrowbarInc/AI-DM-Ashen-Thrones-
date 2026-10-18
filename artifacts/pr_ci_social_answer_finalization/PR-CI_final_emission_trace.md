# PR-CI Final Emission Trace

Target: `tests/test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b`

Input:

`I turn to the Kiln Tender. "When is kiln three banked?"`

Provider candidate:

`Kiln Tender mutters, "Word is, the barge clerk hides a copper chit under the weigh-stone."`

Boundaries observed before repair:

1. Social resolution: `resolution.kind = social_probe` / question-like social path, `success = true`.
2. Selected authored topic: `social.topic_revealed.id = kiln_bank`, text `Kiln three is banked from dusk until the morning bell.`
3. Authored realization helper: able to format `Kiln Tender says, "Kiln three is banked from dusk until the morning bell."`
4. Provider response: unrelated barge-chit content.
5. Candidate response assembly: candidate still provider text.
6. Hard validation / preserve-if-valid: provider content rejected for `hidden_information`.
7. Fallback selection: safe nonresolution selected.
8. Immutable sealing: fallback sealed as immutable `accepted_response`.
9. Later authored realization: skipped because the response was immutable.
10. Final HTTP serialization: emitted `Kiln Tender says, "I cannot answer that from what is settled here."`

Exact first failing boundary:

The first failing boundary was `run_preserve_if_valid`: it sealed provider ignorance or a safe nonresolution before the selected authored answer had an opportunity to become the immutable candidate.

After repair:

1. Social resolution still selects `kiln_bank`.
2. Pre-seal projection detects selected authored topic.
3. Candidate is replaced with the existing authored realization.
4. Hard validation validates the projected text.
5. Immutable sealing records the authored answer as accepted.
6. Final HTTP response preserves the authored answer.

Unauthorized trace:

For `When do the rakers scrape the north pans?`, no authorized Kiln Tender topic is selected. Provider text `...after the second horn` is detected as an unauthored concrete time fact and projected to a safe strict-social nonresolution before seal. The final response does not include `second horn`.

