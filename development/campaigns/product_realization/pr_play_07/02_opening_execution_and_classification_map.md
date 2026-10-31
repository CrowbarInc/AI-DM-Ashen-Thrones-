# 02 — Opening Execution and Classification Map

PR-PLAY-07 · 2026-10-29 America/New_York. Synthetic-provider evidence only.

| Stage | Module / function | Input -> output | Contract / failure behavior | Tests |
|---|---|---|---|---|
| 1 POST admission | game/api.py start_campaign, _start_campaign_after_admission | Request/ui_mode + saved state -> opening scope or 409/503 | Mode, preflight, budget, empty transcript/latch; one persistence lock; refusal before dispatch | PR04 admission/repeat/concurrency |
| 2 Opening bundle | game/api.py _opening_scene_normalized_action_and_resolution, _build_opening_scene_resolution | Active scene + internal bootstrap -> normalized type/kind scene_opening | Engine opening flags; no fabricated player action; tracked exceptions rollback | PR04, start_campaign_api |
| 3 Response type | game/api.py _run_resolved_turn_pipeline; game/response_type_gating.py derive_response_type_contract | Action/resolution -> scene_opening, decision/recipe/policy | Opening overrides question heuristics; strict_answer_expected false; failure grants no commit | S7, response-type tests |
| 4 Presentation plan | game/opening_scene_realization.py build_opening_scene_realization, merge_opening_instructions; game/api.py _build_gpt_narration_from_authoritative_state | Visible facts/scene/decision -> grounded plan/prompt | Authorized presentation, hidden/consequential authority retained; no synthetic opening success | opening_scene_realization, scene_opening_narrative_plan |
| 5 Request/envelope | game/gm.py build_messages, _provider_response_contract_from_payload, call_gpt | Payload -> structured_realization messages + 3000 request | Model/schema unchanged; narration_only only for eligible incidental dialogue | PR06 and structured suites |
| 6 Dispatch/completion | game/provider_budget.py admit_request, RequestAttempt; game/gm.py call_gpt | One Responses request -> metered SDK response/exception | Atomic admission, controlled zero retries, aggregate budgets; failure accounted without added requests | PR02, provider accounting |
| 7 Extraction | game/gm.py _extract_provider_response_text | SDK response -> output_text or message segments | No object repr; empty/extraction failures distinguished | PR05 extraction/native SDK |
| 8 JSON/envelope | game/gm.py _safe_json; game/structured_player_output.py classify_model_output | Text -> normalized GM/realization_envelope or rejection | Claims list + nonempty narration; no nested envelope; rejection flags survive | PR05, structured direct |
| 9 Structural observation | game/gm.py _generation_response_diagnostic; game/provider_budget.py record_generation_diagnostic, capture_opening_response | Text/parser/SDK status -> shape classification + opt-in parsed evidence | accepted_structured_response grants no semantic authority; explicit unfinished status fails; capture failure cannot change acceptance | Capture controls, PR06 |
| 10 Semantic interpretation | game/api.py narration catch-all -> game/immutable_valid_response.py run_preserve_if_valid._check, validate_generated_response | Text/claims + decision/authored corpus -> hard validity/reasons | Decision facts, disclosure, attribution and realization authority enforced | S9/S12, immutable/social regression |
| 11 Nonresolution selection | game/immutable_valid_response.py _terminal_after_fidelity, safe_nonresolution, seal_accepted_response, _finish | Rejected candidate/no authorized recovery -> sealed host fallback | regenerate=None here; fallback never grants opening success; original reasons retained | S9/S12, immutable boundary |
| 12 Opening acceptance | game/api.py _complete_opening_turn_persistence_like_chat, _opening_response_rejection; game/final_emission_validators.py candidate_satisfies_scene_opening_contract | Final GM/meta/text/required type -> None or reason | Reject structured/provider/safe/generic/inadequate scene; 422 failure, budget 409, no gm_output | S1–S12, PR04 |
| 13 Commit/rollback | game/api.py persistence completion, _OpeningScope.close, _restore_opening_baseline | Eligible result + baseline -> one turn/log/start latch or restored gameplay | Engine owns world/factions; restore session/world/combat/transcript on failure; diagnostics outside saves | PR04 persistence/retry/concurrent, world |
| 14 API/UI | game/api.py _opening_failure_response; static/app.js Start handler, loadState/loadLog | 200/422/provider/transport failure -> narration or visible feedback | No auto-retry; failure state-only refresh; safe catches; state controls button | U1–U7, network/JSON controls |

The exact transition is AFTER parsing/structural diagnostics: API's unresolved/no-
interlocutor catch-all invokes run_preserve_if_valid; _check can reject structured
content. With regenerate=None and no authorized recovery, _terminal_after_fidelity
calls safe_nonresolution, seal_accepted_response stores PROVENANCE_SAFE, _finish seals
delivery. API reads provenance and rejects. This is application-assigned provenance,
not an enum emitted by the provider. S9/S12 reproduce that path. S2 instead retains
initial_generation for the provider's literal fallback and fails the API marker check.

Producer/consumer inventory: artifacts/pr_play_07/classification_inventory.txt.
Producers include safe_nonresolution and host terminal safety/sealing; consumers include
API rejection/recovery, immutable final-delivery enforcement, emission/provenance audits
and ordinary unresolved handling. lifecycle_applies excludes scene_opening; the API
catch-all still explicitly preserves valid structured openings. PR04 blocks it only
when structured failure is already set. The semantic validator receives resolution kind
and decision authority but no required_response_type parameter. It inspects content,
claims, disclosure and attribution; the opening predicate is separate. Empty narration
fails earlier in parsing. Missing authoritative answers, unsupported actions, unresolved
interpretation and invalid realization are distinct causes that safe provenance can hide.

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
