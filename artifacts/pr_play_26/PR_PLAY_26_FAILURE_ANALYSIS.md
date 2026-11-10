# PR-PLAY-26 failure analysis

First experiment stop boundary: 15, Expression validation. Confidence HIGH. Expected: authorized faithful paraphrase accepted, useful first answer followed by authored-topic test. Actual: provider paraphrase "I've got hot stew and rumors to share." rejected unsupported_addition; authorized host fallback 'Tavern Runner says, "I offer hot stew and rumors."' published successfully. This is a validation rejection of an optional expression, not a failure of public-fact selection or published first-answer relevance.

Evidence: request_03.json, response_03.json, trace_023_request_expression_output.json, trace_024_validate_expression_output.json, expression_token_analysis.json and accepted_response expression_decision=rejected/expression_adoption=HOST_FALLBACK.

Source anchors: game/expressive_dialogue.py:_faithful_reasons (634; unsupported_addition at 657), validate_expression (761), _attempt (893). Raw native structural classifier treats the accepted fallback as completion and does not stop; manual experiment review enforces section 13. Generic raw controller stop_reason first_response_not_pass is a gate-label limitation corrected in stop_and_quality_analysis.json; published answer quality is PASS.

Known history: PR-PLAY-24 also rejected expression for unsupported_addition, but that earlier run lacked offerings authority and published uncertainty. This run fixes the authority symptom live. No test suite was rerun, so no claim of an exact matching known failing test. Smallest next investigation: offline reproduction of this exact authorized proposition/returned paraphrase against lexical coverage, to determine whether rejection is intended or overly strict. No production repair implemented.

No confirmed defect in the first delivered answer; two-turn continuity remains untested because the experiment hard-stop rule fired.
