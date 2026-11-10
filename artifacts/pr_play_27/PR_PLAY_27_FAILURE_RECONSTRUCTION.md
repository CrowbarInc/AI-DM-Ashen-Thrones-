# PR-PLAY-27 failure reconstruction

1. Published opening: exact text in pr_play_26_trace/PR_PLAY_26_TRANSCRIPT.md. It describes Cinderwatch's eastern gate, crowd, notice board, runner offering hot stew and paid rumor, townhouse and still figure.
2. Player: `I approach the tavern runner and ask what they're offering.`
3. Selected NPC: tavern_runner / Tavern Runner; in frontier_gate.
4. Local approach normalized to interaction context; ASK executes on the runner. See trace_008 and the new HTTP transcripts' normalized action metadata.
5. Selected public scene fact: `A tavern runner trades hot stew and rumors near the rain barrel.` Source `scene:frontier_gate:visible:2`.
6. Authority: established, sufficient/directly_answers, authorized proposition `I offer hot stew and rumors.`; provenance world_source, relation own_offerings, speaker tavern_runner. Full payload: trace_018 output.
7. Provider request: request_03.json and trace_023 input; one sentence, facts only, faithful_paraphrase, limited wording, all item descriptions preserved. The existing prompt permits I've got, but does not explicitly license to share.
8. Provider response: `I've got hot stew and rumors to share.` Exact captured response_03 and trace_023 output retained. These are historical requests, not requests made by this pass.
9. Validator inputs: trace_024 input has candidate and entire contract, including speaker, public authority, own_offerings relation, fallback, prohibited claims and prompt.
10. Decision: adopt=false.
11. Reason: unsupported_addition. In validate_expression's own_offerings branch, the existing regex replaces offers?/sell/serve/got with offer. `_faithful_reasons` computes content tokens, requires every source anchor, then rejects any candidate content token not covered by source tokens or existing synonym groups. After normalization `share` remains. `_FUNCTION` removes `to` but does not remove `share`. The uncovered-token loop is the exact failure, expressive_dialogue.before.py:650–658. This is missing bounded equivalence, not an invented consequential proposition or a broken authority selection.
12. Deterministic fallback: `Tavern Runner says, "I offer hot stew and rumors."`
13. Final publication: exactly that fallback.
14. Native structural classifier: gameplay completed, no stop. Experiment first_answer_quality=PASS, but first_response_pass=false was the stricter manual continuation gate.
15. Experiment stop: section 13 required stopping on expression validation rejection; followup_prohibited=true. stop_reason=expression_validation_rejected_unsupported_addition. Raw first_response_not_pass was corrected as a gate label, not answer quality.

Offline pre-modification reproduction: original_reproduction.json returns adopt=false, reasons=[unsupported_addition] using the exact captured contract. No transport invoked. Source was saved before modification; baseline tests and complete source-relative diffs are retained.
