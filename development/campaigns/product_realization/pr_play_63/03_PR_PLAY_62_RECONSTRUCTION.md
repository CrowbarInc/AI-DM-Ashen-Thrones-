# Original rejected interactions

Full original five rows, candidates, resolutions, mandatory/context projections, validation traces, published fallbacks and state are preserved in pr_play_62_reconstruction.json. These are PR62 samples, distinct from PR61 samples discussed in PR62 report 04.

Barrel: investigate success=true, no discovered_clues/clue_text, prior route known. Candidate reports no new clues and accurately uses “they were last seen”. Semantic PASS; legacy hard_valid=true; coverage REVIEW_REQUIRED: current status covered, prior route partial. Combined REVIEW_REQUIRED; full-route fallback published. **FALSE REJECTION**: unnecessary historical requirement, plus bounded recognizer missing anaphora.

Gate: observe success=null, no current clue. Same PASS/true/REVIEW_REQUIRED chain with prior route partial; fallback repeated route. **AMBIGUOUS** overall: historical coverage is overbroad, but “remains the only lead” is an unsupported exhaustive claim, and usual bustle is not proven. An automated PASS does not resolve this human-review question.

Updated saved-text replay (not publication) passes both rejected samples after prior coverage removal. The originally accepted discovery now conservatively fails the new route safety check. See entry_revalidation.json and pr_play_62_updated_revalidation.json. Original final state retains exactly one route, no barrel/gate discovery.
