# PR-PLAY-44 — Information Delivery & Narrative Realization Contract

Verdict: **B — PARTIAL**.

## 1. Executive summary

The saved PR-PLAY-43 notice-board omission was reproduced offline and repaired. The response-policy action repair discarded the substance of an already selected public clue and substituted a generic acknowledgment. The repair now retains all resolver-selected discovery texts, preserves failed/repeated-search distinctions, and supplements missing discovery content before semantic validation and immutable sealing. No resolver, campaign fixture, model, credentials, token ceiling, opening recovery, admission rule, or provider routing was changed.

The broader AI narration contract is not fully enforced. Two new unsuppressed probes expose existing gaps: hidden scene material reaches the legacy narrator prompt, and unsupported receipt of coins/key passes the existing semantic validator. These prevent a full PASS. The task does not claim that adding clue content makes arbitrary generated narration safe.

Real provider requests **0**, real provider tokens **0**, live gameplay turns **0**. Every replay here is offline with controlled interpretation/narration and production resolvers.

## 2. Baseline reproduction

Command, before editing production sources:

```powershell
$env:ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT='1'
$env:PR_PLAY_44_EVIDENCE_PHASE='before'
& .venv/Scripts/python.exe -m pytest tests/test_pr_play_44_information_delivery.py --tb=short
```

Observed: **1 failed** at `assert resolution['clue_text'] in _facing(body)`. This is the intended initial reproduction, not a suppressed regression. The assertion compared the complete route text against exactly `You examine the notice board, and you turn up a concrete clue.`

`before_notice.json` captures the original input, resolver invocation count, full resolution, authoritative session before/after, and complete final HTTP response. Input: `I examine the notice board.` Operation: INSPECT. Grounded target: `notice_board`. Exploration called once; social and narration called zero times. Success true; clue `notice_patrol_route`, text `The missing patrol was last seen taking the northwest mud track past the crates.` Discovery is stored in scene runtime. The session advances one turn without moving scenes.

This uses the exact persisted **T3/before/persistent** directory from PR-PLAY-43 run `20261102T225835Z-b91e96381683`, copied into pytest temporary storage. The captured T3 interpretation replaces interpretation transport. It is a saved-state offline replay, not a new opening, reconstructed campaign, or replay of a real provider request. Incidental clock timestamps/diagnostics are not asserted byte-identical to the historic live run.

## 3. Root cause and source map

The clue omission and missing narration calls have distinct causes.

1. `game/exploration.py:191`, `resolve_exploration_action`: successful inspection retrieves the selected clue from the authored scene and returns `clue_id`, `clue_text`, `discovered_clues`, and discovery state changes. The full content is present.
2. `game/api_turn_support.py:259`, `_authoritative_resolution_fact_text`: selects the resolver's public text. `game/api.py:1057`, `deterministic_provider_skip_line`, chooses it under `resolved_clue_discovery`. This is a complete initial host response.
3. `game/upstream_response_repairs.py:174`, `build_minimal_action_outcome_contract_repair_text`: before this repair, `_action_result_summary` reduced any discovery to **you turn up a concrete clue**. This is the earliest lossy projection. The resolution itself still retains the text.
4. Response-policy/final-emission response-type repair can select that prepared generic candidate. `game/final_emission_response_type.py`, `_resolve_upstream_prepared_answer_action_repair`, selects `prepared_action_fallback_text` for an owed action outcome. It checks response shape, not the substance of the discovery.
5. `game/immutable_valid_response.py`, `run_preserve_if_valid`, accepted the generic result. Its generic-fallback recognizer did not recognize this sentence, and the existing semantic checks treated an omission as valid. The immutable response then prevented later preservation helpers from replacing it. The pre-repair response metadata records `response_policy_enforcement_applied`, the generic `prepared_action_fallback_text`, and that same accepted immutable text.
6. `game/api_turn_support.py`, `_finalize_player_facing_for_turn` and `_build_turn_response_payload`, carry the sealed response into serialization.

`source_locations.json` records exact current function line locations, including nested validation/route functions, for every audited module. Source snapshots are included. Relevant additional paths: `game/social.py:3924` for NPC resolution, `game/dialogue_authority.py` for source permission/host speech, `game/conversational_orchestration.py` for admission, and `game/narration_visibility.py` for output visibility validation.

## 4. Information-delivery contract

Authoritative state contains complete engine truth, including facts the character has not learned. Authorized player knowledge consists of specifically selected resolver observations/disclosures and established public context. Hidden information includes unselected clues, NPC secrets, off-screen faction events and private checks. Player-facing narration communicates the authorized result; it has no independent authority to mutate state.

Invariant: an action revealing information must communicate its substance. A generic discovery acknowledgment does not satisfy that obligation.

`game/authorized_information.py` implements the bounded discovery projection. It reads only selected `clue_text` and `discovered_clues` from completed successful discovery/investigation/observation outcomes. It never searches the scene clue database or world state. It deduplicates texts, preserves all selected results, and excludes failed/already-searched outcomes. Status is `newly_revealed`; existing social recall and already-searched result semantics remain separate. It does not infer authorization from a clue identifier alone.

The fallback composer includes these records instead of a generic acknowledgment. Host selection uses the same records rather than losing every discovery after the first. Before sealing, initial and retry drafts receive missing selected content; the ordinary semantic checks still inspect the complete resulting text. A candidate that would subsequently drop the selected content fails completeness. Safe fallback also selects the same public content. None of these functions writes mechanical state.

Paraphrases are allowed. There is no semantic-equivalence oracle: when normalized source coverage cannot establish delivery, a source sentence is conservatively added to the draft. This can repeat a faithful paraphrase; the paraphrase itself is not rejected for differing wording. An exact source sentence is an implementation safeguard for uncertain coverage, not a required provider output format. Multiple facts, qualifiers and uncertainty stay intact.

## 5. Before / after

Before:

> You examine the notice board, and you turn up a concrete clue.

After:

> You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.

`after_notice.json` records the repaired response, accepted-response provenance, full resolution and session snapshots, the initial host selection, and messages built at the narration seam. This response used **zero** narration calls. The clue was already present in narration context; missing context was not the cause of its omission.

## 6. Narrative pipeline audit

| Stage | Functions / inputs | Decision and output | Failure/provenance |
| --- | --- | --- | --- |
| Admission and resolver | conversational orchestration, normalized action, exploration/social | Ground original input, resolve mechanics and store authorized results | No bypass; unsupported actions retain existing admission outcomes |
| Plan and context | `api._build_gpt_narration_from_authoritative_state`, `gm.collect_narration_context_call_kwargs`, `gm.build_messages`, `prompt_context.build_narration_context` | CTIR/plan seam required where applicable; action-outcome mechanics projected from validated plan | Planner convergence emergency uses existing fallback; source/plan diagnostics retained |
| Host adoption | `immutable_valid_response.adopt_host_speech`, `dialogue_authority.select_host_speech` | Resolved non-check NPC ASK with matching authority can select authored/recalled/disclosure-safe host speech | Seals host provenance; authority conflict/ambiguity cannot grant an answer |
| Narration eligibility | `api.deterministic_provider_skip_line` | Recalled topics; determined closed nonresolution; successful selected discovery; local observation questions; completed authored travel can skip provider | Skip metadata records exact reason and zero calls; otherwise returns None |
| Provider selection/invocation | `_call_gpt_route_kwargs`, `_bounded_call_gpt`, `gm.call_gpt` | If no adopted host speech or skip/emergency result exists, invoke provider. Purpose primary_turn, strict_social, or retry_escalation | Existing per-turn request cap, model route, provider admission/budget, disabled-provider and transport handling remain |
| Structured validation | `gm._parse_gm_output`, narration-only or structured-realization contract | Parse narration and declarations; malformed/incomplete envelopes cannot become ordinary prose | Existing structured failure metadata retained |
| Semantic validation | guard/visibility checks; `immutable_valid_response.validate_generated_response`; resolution decision/envelope audits | Check output against admission, speaker/knowledge authority, mechanical decision and visibility | Existing retry, bounded preservation, authored projection, or safe nonresolution; not a complete semantic proof |
| Policy repair | response policy and upstream prepared emission | Action-outcome replacement must now preserve the selected discovery records | Prepared-text mutation diagnostics retained |
| Final sealing | `run_preserve_if_valid`, `seal_accepted_response`, delivery seal | Initial and retry candidates validated before immutable text is accepted | Post-seal semantic mutators remain blocked |
| Serialization | `_finalize_player_facing_for_turn`, `_build_turn_response_payload` | Seal and return gm_output; public state derived from stored authoritative state | Existing engine/player projections retained |

**When does AI narrate after resolution?** When the normal plan seam is eligible and no preexisting result, adopted authoritative NPC speech, deterministic skip, or emergency fallback has already supplied `gm`; `gm is None` then reaches `_bounded_call_gpt`. This is reachable in ordinary gameplay: the synthetic repeated searches reached the controlled narration substitute. NPC characterization/social maneuvers and other non-skipped outcomes can also reach it, subject to existing authority and budget gates. Not every successful action needs provider narration.

**Why zero calls in PR-PLAY-43?** T1 is a host scene-information answer. T2 adopts authored Tavern Runner speech. T3 and T5 skip under `resolved_clue_discovery`. T4 skips under completed scene transition. The request budget was not exhausted, semantic validation did not prevent an attempted narration call, and the provider was not disabled. Provider selection is intentionally avoided where a source-owned result already determines speech. `select_host_speech` explicitly says generated paraphrases do not yet have an enforceable grant on that lane. The opening remains a separate provider-generated operation; its routing/recovery was not changed.

## 7. Narrative realization contract and limits

Allowed inputs: original action; relevant public scene and pre-action context; resolved action/grounded target; authoritative outcome; bounded newly selected information; relevant previously delivered information; observable resulting state. No unrestricted clue catalog, hidden NPC motivation, or off-screen faction state belongs in this proposed outcome-realization input.

Required output: address the action, preserve success/failure and destination, communicate selected information including uncertainty, and introduce no new authoritative entities, encounters, movement, resources or consequences. The engine owns all changes to scenes, HP, inventory, resources, knowledge, NPC state, time and clocks. Consistent atmosphere and incidental gestures are permissible only as nonpersistent texture.

Implemented now: selected-discovery delivery, all selected facts rather than only the first, deterministic fallback, pre-seal supplementation, unchanged admission and semantic safeguards. Existing NPC and travel authority paths remain in use.

**Open gap 1: legacy input isolation.** `prompt_context.build_narration_context` still constructs `scene.gm_only.hidden_facts`, locked discoverables and undiscovered clue records. `state_channels.project_public_payload` is a shallow top-level projection; it does not remove these nested keys. Synthetic SECRET canaries appear in the actual built messages, including a draft that would reach the provider on repeated inspection. They did not appear in tested player-facing responses. The bounded new projection excludes those canaries, but the legacy provider context is not restricted to it. No prompt redesign was made in this pass.

**Open gap 2: incomplete semantic coverage.** A controlled draft `You receive fifty gold coins and a silver key.` passes the current semantic validator even with the resolution decision attached. The unsupplemented verdict and resulting response are recorded in `contradiction.json`. Adding the authorized ledger text does not correct this invented receipt. No inventory or resources actually change, but narration claims an unsupported outcome. The broader contract is therefore not safely enforceable for arbitrary AI narration yet. Routing more turns through it would be premature.

Both probes remain failing in pytest; neither is marked xfail, skipped, or given a weakened expectation. They exercise untouched legacy prompt/semantic behavior, not a new regression induced by the information repair.

## 8. Offline cases A–J

| Case | Result | Evidence / limit |
| --- | --- | --- |
| A Clue delivery | PASS | Exact saved notice replay; generic synthetic disclosures; all selected content delivered |
| B Failed inspection | PASS | Controlled failed production skill check reveals no clue; failure speech retained |
| C Previously known clue | PASS for no false new discovery | Repeated production inspection returns already_searched; no new clue announcement; repeat prose quality remains limited |
| D NPC information | PASS | Saved Tavern Runner and unfamiliar ferry rumor retain actual authorized substance; secret NPC motive not emitted |
| E Travel | PASS | Saved authored exit reaches old_milestone and names Old Milestone, with no invented encounter/state |
| F Blocked travel | PASS | Controlled false arrival rejected by existing travel validator; resolution unchanged |
| G Hidden information | PARTIAL | New bounded projection and tested player responses exclude secrets; legacy prompt-isolation probe FAILS |
| H Harmless texture | PASS | Rain texture consistent with scene survives alongside ledger result; no state mutation |
| I Contradictory narration | PARTIAL | False arrival rejected; unsupported coins/key probe FAILS |
| J Provider unavailable | PASS at fallback seam | Direct safe-fallback substitute retains selected public discovery and leaves resolution unchanged; no real provider outage was induced |

## 9. Cross-scenario results

Market ledger: twelve copper ingots received, nine entered stock, substance delivered. Wilderness tracks: possible animal origin, species/direction uncertain, uncertainty retained. Dungeon mechanism: left lever disengages ratchet, mechanism remains inactive, text delivered without an activation state change. Unfamiliar NPC: Mira's authored ferry rumor delivered with no secret motive. Failed cipher-plate action: controlled failed check reveals no opening sequence. Canonical scenes/fixtures were not edited; scenes were written only into test storage.

All five requested cross-scenario categories pass. `scenario_ledger.json`, `scenario_tracks.json`, `scenario_mechanism.json`, `scenario_npc.json`, and the failed-check test capture the evidence. The synthetic repeated-search drafts are controlled substitutes, not real provider calls.

## 10. State integrity

`state_integrity.json` compares pre/post-repair notice replay resolver cores and mechanical session fields, with the full snapshots in before/after_notice.json. The same clue, outcome, state changes, scene, visited scenes, clocks, turn counter and scene-runtime knowledge are preserved. Controlled narration/fallback tests deep-compare the resolution before and after realization.

The user campaign still matches the independent PR-PLAY-43 fingerprint: **150 files**, `2e006ba7e3387f32bf6180c2b335b5d208624a9ef5de3c4a67f32f946e3e9371`. This is comparison against a historic recorded fingerprint, not a claimed newly captured start-of-task hash. User campaign data was not modified. The working tree already contained substantial uncommitted changes at entry; those were preserved. Nothing was pushed.

## 11. Regression verification

Python launcher attempts using `python` and `py` failed before importing the application (Windows app alias/launcher availability). The existing `.venv/Scripts/python.exe` runs the tests successfully.

The baseline and final commands use `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1`; conftest installs provider isolation before tests. Exact commands are in `commands.txt`. Full outputs and JUnit XML are included.

Baseline: **377 collected, 353 passed, 24 failed, 0 skipped**. Final: **392 collected, 367 passed, 25 failed, 0 skipped**. The original 377 now have **354 passed, 23 failed**. New contract tests: **15 collected, 13 passed, 2 failed**, explicitly documenting the two legacy limits above. **New regressions among existing tests: 0**. One existing failure, `test_http_read_while_bound_communicates_authored_contents`, now passes. No existing test expectation was edited.

PR-PLAY-37 carry-forward: the three start_campaign_api and three PR-CP finalization failures remain; the historical PR-PLAY-11 replay failure was not selected here. PR-PLAY-37's own opening recovery tests pass and do not erase those historical failures. PR-PLAY-40 carry-forward: all five recorded unavailable/stay/leave/pursuit travel failures remain. Other baseline failures in exploration and narration-state consistency remain separately listed in regression_comparison.json. No unrelated repairs were attempted.

## 12. Performance and token findings

No request was added by this repair. The ordinary existing narration output cap is 600 unless already configured otherwise; opening handling is separate. No model or ceiling was changed. Narration uses model-route selection and provider-budget admission after the per-turn cap; retry routing can escalate under existing controls.

The repaired notice builds two messages totaling approximately **122,139 UTF-8 serialized bytes** in this replay, though they are not sent. `context_size.json` records exact measurement. No local character estimate is presented as measured provider tokens. PR-PLAY-43's historical opening used 26,714 input + 1,649 output tokens (28,363 total); all five historical requests used 39,804. Those are historic, not this pass's usage.

Context carries overlapping scene, world/world_state, plan, authority, memory and response-policy scaffolding. Existing ordinary social compaction and mechanical-decision deduplication are present, but this is still substantial context for a fully resolved inspection. Resolver output already contains the necessary discovery; the new projection reuses it directly. Simple discovery/travel and source-bound NPC replies remain viable deterministic cases. A future combined interpretation/realization proposal must still resolve mechanics first and validate any provisional prose against the actual outcome; a single pre-resolution provider draft cannot become mechanical authority. No speculative optimization was implemented.

## 13. Change manifest

Production files changed in this pass:

- `game/authorized_information.py` (new): bounded selected-result projection and conservative source supplementation.
- `game/upstream_response_repairs.py`: discovery content in prepared action fallback; failed outcomes cannot announce stale clues.
- `game/api_turn_support.py`: host observation/discovery projection preserves all selected facts.
- `game/immutable_valid_response.py`: preserve discovery content before initial/retry validation and sealing; safe fallback and completeness check; extend local selected-fact authorization to all returned discoveries.

Added `tests/test_pr_play_44_information_delivery.py`, the evidence/package files in artifacts/pr_play_44, and updated handoff/CURRENT_REVIEW.md. `change_manifest.json` contains source hashes and source_snapshots contains reviewable copies. Other existing dirty source files are not attributed to this pass. No campaign, provider, credentials, prompt source, or admission code was edited.

## 14. Known limitations / blockers

Full PASS is blocked by legacy hidden-input isolation and incomplete validation of unsupported resource narration. Conservative supplementation can duplicate a paraphrase. Coverage guarantees are bounded to resolver-selected clue texts with explicit successful outcomes; this is not a universal theorem over every social/combat result shape. A partial clue observation is preserved as authored uncertain text, not promoted to a definitive identity. Explicitly failed outcomes do not gain authorization from stale text fields.

Existing unrelated regression failures remain. No claim is made that the whole repository suite passes. Newly written synthetic tests were corrected during development for fixture validity and authorized rumor-category wording; existing test expectations were untouched. The saved notice omission was reproduced before implementation.

## 15. Provider isolation and usage

`ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1` was set before every pytest invocation and application import. `tests/conftest.py` disables live interpretation/expression and installs `tests/helpers/live_model_guard.py`. OpenAI/AsyncOpenAI constructors and real generation transports fail closed via BaseException; captured records and controlled drafts replace the intended calls. No forbidden transport was reached. **0 real requests, 0 real tokens, 0 live gameplay turns.** No live campaign experiment, model change, credentials change, budget increase or GitHub push occurred.

## 16. Final verdict and recommendation

**B — PARTIAL.** Information delivery is repaired and generalized across the requested synthetic cases. Narration routing is established by source and observed skip evidence. Selected discoveries survive host fallback, controlled omission and immutable sealing without adding provider calls. Player-facing hidden canaries remained absent and mechanical state stayed authoritative.

The unrestricted legacy narrator context and unsupported-resource validator gap prevent asserting the complete narrative realization contract. Next development step: a separately scoped offline repair that feeds outcome realization only authorized inputs and closes unsupported inventory/resource assertions, retaining these failing probes. Do not broaden provider narration routing or run another live experiment until those pass. This pass stops after packaging; it does not initiate PR-PLAY-45.

The timestamped CURRENT_REVIEW archive path is recorded in artifacts/pr_play_44/archive_path.txt, with SHA-256 and manifest verification in archive_verification.json.
