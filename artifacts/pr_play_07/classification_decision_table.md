| Condition | Boundary / classification | Evidence category |
|---|---|---|
| Bad JSON, missing required claims list, empty narration, nested envelope | gm._safe_json -> structured_contract_failure -> API rejection | A: correct structural rejection, S3/S4 |
| Complete JSON with explicit provider incomplete/failed status | gm.call_gpt -> provider_opening_not_completed | A: incomplete operation, PR06 controls |
| Grounded valid opening; optional proposal/NPC fields absent | hard valid -> initial_generation; opening predicate passes | Accepted, S1/S5/S8 |
| Provider metadata says fallback but actual content satisfies contract | Unknown metadata discarded by parser; no host safe provenance | Accepted, S6; arbitrary metadata grants no authority |
| Host accepted_response provenance or authorization is safe_nonresolution | API rejects before persistence even with plausible prose | A: actual host safety result is disqualifying; separate metadata control |
| Model emits literal generic answer inside valid JSON | May seal initial_generation; API text-marker check rejects | A: model nonresolution, S2 |
| Unauthorized state changes, hidden disclosure or invalid consequential realization | immutable _check fails; no valid recovery -> _terminal_after_fidelity -> safe provenance | A when audit is correct; S9 proves unauthorized change case |
| Missing consequential declaration or unmatched source claim | Decision/claim audit can fail despite a structurally valid list | A if obligation applies; empty list alone is legal. S12 audit rejects rich text |
| Alleged valid opening rejected by unrelated ordinary-action rule | Could produce same terminal provenance | B only if content satisfies opening authority; not established historically |
| scene_opening response type alongside unresolved/answer/referent-ambiguity contract | Conflicting guidance in projected resolution contract/answer recipe | C: residual conflict observed; historical influence unknown |
| Historical structural success then safe_nonresolution without original output/reasons | Same sequence compatible with correct rejection, incorrect rejection or guidance conflict | D: insufficient evidence; no cause selected |
| Empty, generic, question-only or non-scene final text | candidate_satisfies_scene_opening_contract rejects | A: opening-specific failure |
| Budget refusal, disabled provider, fast fallback | API failure, no successful opening commit | A: generation unavailable, no retry |
| Repeated Start after successful opening | already_started 409 before provider dispatch | Correct duplicate prevention, S10 |
