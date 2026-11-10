import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
ID="pr_play_t05_composition";RP=ROOT/"development/campaigns/product_realization"/ID;RP.mkdir(exist_ok=True)
read=lambda n:json.loads((OUT/n).read_text(encoding="utf-8-sig"))
r=read("test_results.json");t=read("t05_comparison.json");turns=read("twelve_turn_comparison.json");closed=read("closed_inspection_results.json");changes=read("source_changes.json")
assert not r["newly_failing"] and not r["changed_outcomes"]
assert r["baseline_before"]==r["baseline_after"]=={"passed":378,"failed":20,"errors":0,"skipped":0}
assert r["new_tests_after"]["passed"]==15
assert len(closed)==3 and all(c["passed"] and c["hard_valid"] and c["digest_verified"] for c in closed)
assert [x["id"] for x in turns if not x["text_identical"]]==["T05"]
assert all(x["scene_equal"] and x["state_changes_equal"] and x["disclosures_equal"] and x["intent_before"]==x["intent_after"] and x["route_before"]==x["route_after"] and x["refusal_before"]==x["refusal_after"] for x in turns)
assert changes["changed"]==["game/response_policy_enforcement.py"] and not changes["frozen_changed"]
def write(n,s): (RP/n).write_text(s.strip()+"\n",encoding="utf-8")
limitations="T01/T07 disabled narration; T02 unhelpful NPC answer; T04/T06 incomplete physical actions; T08 generic acknowledgment; T10 improvised trading; T12 operational refusal. Twenty baseline failures remain: twelve obsolete public-resolution assertions, one stew mismatch, four authority/refusal/publication failures including the portal exception, and three unrelated KeyErrors. No full suite, independent held-out generalization, live-provider or Gameplay Benchmark claim."
write("SUMMARY.md",f"""# T05 Authorized Clue Publication Composition Repair

Milestone `{ID}`, client date 2026-11-08. **A/PASS for the bounded repair. The game remains incomplete.** The predecessor `pr_play_preseal_authority` assigned a descriptive next action, not a numbered milestone. This identifier implements that action; PR-PLAY-80 and AT-OPT-07 remain unopened.

Root cause: `game/response_policy_enforcement.py::enforce_scene_momentum` appends synthetic pressure from `render_scene_momentum_diegetic_append` to a resolver-selected clue. The existing compatibility guard verifies that the answer survives, not that the stock addition belongs to the requested disclosure. This is an implementation composition defect; hard validation and immutable publication faithfully retain the already contaminated candidate.

Only production change: decline that renderer's append when `revealed_information(resolution)` selects newly authorized information. Existing candidate prose and resolved events remain intact; no sentence splitting, relevance classifier, exact-string suppression, provider pass, prompt change or authority-projection edit.

Original T05: {t[0]['published_text']}

Corrected T05: {t[1]['published_text']}

The original twelve-turn HTTP path confirms the clue, normal hard validation, immutable digest and accepted/published/pointer identity. Inventory and location stay unchanged; authorized clue knowledge still advances. The other eleven publications, all intent kinds, routes, disclosures, resolution state changes, scenes and refusal outcomes remain equivalent. Pointer text changes on T05 and on T06 while it retains the last successful publication; subsequent pointer behavior is preserved.

Fresh same-source baseline: **378 passed / 20 failed** before and after, matching the predecessor. Added tests: **7 passed / 8 failed before → 15 passed / 0 failed after**. Combined after: **393 passed / 20 failed**, zero collection errors/skips. No new failure identities or changed normalized baseline diagnostics. Three original closed inspections and all 17 pre-seal controls pass; seven conversational HTTP controls and AT-OPT-06 controls remain green.

Remaining limitations: {limitations}

Live provider calls: **0**. No commits or pushes. Archive verification and hash: artifacts/{ID}/archive_verification.json and archive_sha256.txt.
""")
write("ROOT_CAUSE.md",f"""# Root cause and original production trace

Failure class: implementation. Earliest demonstrated incorrect decision: scene-momentum enforcement decides that a missing momentum tag warrants synthetic scene pressure even when the resolver has just supplied the requested information.

Original request: `{t[0]['request']}`. Current scene: frontier_gate / Cinderwatch Gate District. The visible board lists taxes, curfew rules and a missing-patrol warning. The previous NPC answer concerns a patrol missing near the old milestone; T04 approaches the board locally without completing touch or revealing the notice. The parsed contract is inquiry / inspect / Notice board, explicit player target; the resolver selects discover_clue, interactable notice_board, clue notice_patrol_route. Full history, available surfaces, contract construction, resolver metadata and state are in t05_before.json.

The deterministic `resolved_clue_discovery` candidate (provider_narration_skipped, zero calls) is:

> {t[0]['initial_candidate']}

When scene momentum is due and the candidate has no momentum tag, enforcement calls `render_scene_momentum_diegetic_append(scene_envelope, seed_key='frontier_gate')`. Its scene-wide notice/patrol template returns the jab sentence. It has no selected-clue or resolved-event input. The output is appended as a separate paragraph and tagged scene_momentum:consequence_or_opportunity. The semantic write-site record names `_apply_scene_momentum_enforcement` / scene_momentum_enforced_fallback. This is demonstrated by captured inputs, nested renderer result and enforcement output, not inferred from wording.

`continuation_preserves_resolution` retains the combined text because the selected answer survives and no recognized repeat splice appears. Subsequent presentation removes the generic inspection lead and joins the paragraphs; it does not introduce the jab. The pre-seal candidate already contains both sentences. Normal hard validation passes; seal_accepted_response adopts attempt 1 / initial_generation; downstream mutators preserve it. There is no publication-stage append or provider fallback responsible for the contamination.

Authorized disclosure contract: resolver-selected public information must be delivered and may be paraphrased or supplemented by the existing information owner. Relevant notice description, presentation, supported observation or NPC reaction can remain in candidate narration, including multiple sentences and multiple authorized facts. The request resolves an information inquiry, not a new physical event. Scene-wide synthetic crowd pressure is not a required resolved outcome. Multiple components are legal when their sources support them; this stock renderer is independent of the selected disclosure. Immutable acceptance begins only after assembly and hard validation.

An initial correction omitted both the stock append and its tag. The full twelve-turn run exposed T07 entering the existing scene_stall:momentum_due_without_progress terminal fallback. Inspection of storage.SCENE_MOMENTUM_KINDS established the existing new_information kind. The final correction tags the real clue disclosure with that kind, preserving cadence without inventing a pressure event. The complete final scenario is rerun; this does not repair T07 narration itself. Intermediate traces/results remain preserved, including intermediate_t07_investigation.json.

The narrow correction is at the proven source-selection/append boundary. It never tries to classify arbitrary sentences or remove material from a sealed response. Raw before/after traces and compact composition/publication comparisons are cycle-owned evidence under artifacts/{ID}/.
""")
write("IMPLEMENTATION.md",f"""# Implementation

Only `game/response_policy_enforcement.py::enforce_scene_momentum` changes, by 18 lines. Existing prerequisites remain: valid GM dict, scene id, momentum due, and no existing momentum tag. Immediately before invoking the stock renderer, query the existing `revealed_information` owner. A selected disclosure requires successful discover_clue/investigate/observe, nonempty clue_text/discovered_clues and no already_searched flag.

When selected information exists, return a detached copy preserving every existing candidate field and all text. Internal emission_debug.scene_momentum_composition records appended=false, selected_information_takes_precedence and the excluded renderer source. The existing scene_momentum:new_information tag identifies the actual clue disclosure, satisfying momentum cadence without inventing pressure or an event. The stock component has not yet been assembled, so no prose deletion is needed. The stock renderer has no resolver-specific information and therefore cannot supply an authorized physical result or selected clue in this branch.

Selected clue, player-requested information, resolved physical outcomes, state changes and existing descriptive elaboration all survive unchanged. Existing tagged momentum remains intact. Failed/unselected/already-searched information, NPC dialogue, travel, physical actions and ordinary atmosphere use their existing paths. This does not sanitize unrelated content already present in a candidate or block other atmosphere owners.

The unchanged parent policy entry guard skips immutable responses; the change happens during initial assembly before normal hard validation and sealing. No public HTTP field, accepted-response logic, authority projection, claim extraction, prompt, provider budget or retry changes. `game/api.py`, immutable_valid_response.py and referenced_surface.py are byte-identical to entry.

Tests: tests/test_pr_play_t05_composition.py (15 cases). Seven original unaffected controls and eight demonstrations of stock contamination run unchanged before/after. The original HTTP test captures the actual sealed record, verifies normal hard validity/digest, checks published/pointer equality and re-enters policy enforcement to verify immutability. Existing 17 pre-seal tests cover hidden inspections, item acquisition, physical-result precedence, travel, dialogue, sensory improvisation and validation failure behavior.

Cycle-only diff: artifacts/{ID}/production.diff, relative to preserved dirty entry bytes, not Git HEAD.
""")
write("T05_BEFORE_AFTER.md",f"""# Original HTTP T05 before and after

Request: {t[0]['request']}

Authorized notice_patrol_route clue: {t[0]['authorized_clue']}

| Stage | Before | After |
|---|---|---|
| Initial candidate | {t[0]['initial_candidate']} | {t[1]['initial_candidate']} |
| Composed candidate | {t[0]['composed_candidate'].replace(chr(10),' ')} | {t[1]['composed_candidate'].replace(chr(10),' ')} |
| Pre-seal candidate | {t[0]['preseal_candidate']} | {t[1]['preseal_candidate']} |
| Accepted and published | {t[0]['published_text']} | {t[1]['published_text']} |
| Stock renderer invoked | Yes | No |
| Hard validation / digest | Pass / verified | Pass / verified |
| Publication pointer | Exact accepted text above | Exact accepted text above |

Both runs use the same seed and all twelve original utterances. T05 stays in frontier_gate, character/inventory byte-equivalent in state comparison; it reveals the same selected clue, sets the same resolver state changes and advances the same turn. Full session/world/log changes include ordinary simulation and conversation/publication bookkeeping, not invented acquisition or travel. Momentum bookkeeping records new_information instead of synthetic consequence_or_opportunity, retaining the established cadence. The selected clue itself is the new information beat.

Before/after accepted text equals HTTP player-facing text and last_publication.visible; each accepted integrity digest independently verifies. t05_before.json and t05_after.json preserve full authority, scene/history, response, stages and state. t05_comparison.json is the compact comparison. No accepted response is changed after sealing.
""")
write("NEGATIVE_CONTROLS.md",f"""# Negative controls

| Control | Evidence and outcome |
|---|---|
| Relevant elaboration | Three composition cases preserve full multi-sentence notice appearance, paraphrase and contextual NPC-reaction candidates; no stock renderer called. This establishes retention, not a new authority grant for arbitrary prose. |
| Multiple facts and physical event | Both selected facts and an existing resolved unfold outcome remain verbatim; resolver metadata untouched. |
| Existing momentum | Candidate already bearing an authorized momentum tag remains intact. |
| NPC dialogue and follow-ups | Boundary control retains old composition; seven unchanged post-NPC HTTP tests pass, including explicit repetition and returning to captain. |
| Genuine travel | Boundary control, existing pre-seal test, conversational HTTP test and original T11 preserve Old Milestone travel. |
| Physical action / acquisition | Boundary physical control plus unchanged pre-seal resolved action/acquisition precedence pass; T04/T06 remain their existing incomplete/unsupported outcomes. |
| Sensory atmosphere | Unselected observe keeps the stock renderer and original sensory candidate; pre-seal rain control passes. |
| Closed inspection | Three original HTTP cases and all 17 pre-seal tests pass; no token acquisition/reveal, eight Glassport crews or four overseers. |
| Hidden information | Existing notice hidden-detail and patrol-color HTTP controls pass; no new hidden grant. |
| Immutable identity | Original T05 HTTP test verifies digest, accepted/published/pointer equality and unchanged text after policy re-entry. |

Fresh results: 15 composition tests and 17 pre-seal tests pass. Closed HTTP evidence: closed_inspection_results.json and focused_final/http_capture.json. These are bounded authored variations/regression controls, not independent held-out generalization.
""")
commands=[]
for run in r["runs"]:
    commands.append("### "+run["directory"]+"\n\n```text\n"+json.dumps(run["command"],indent=2)+"\n```\n")
write("REGRESSION_RESULTS.md",f"""# Regression results

| Selection | Before pass/fail | After pass/fail |
|---|---:|---:|
| Main, 235 | 222/13 | 222/13 |
| Authority, 146 | 139/7 | 139/7 |
| Pre-seal authority, 17 | 17/0 | 17/0 |
| Established baseline, 356 (excludes 25 mechanical cases) | 336/20 | 336/20 |
| Expanded audit, 381 | 361/20 | 361/20 |
| Expanded plus pre-seal, 398 | 378/20 | 378/20 |
| New composition, 15 | 7/8 | 15/0 |
| Combined post-repair, 413 | — | 393/20 |

Current entry hashes match all 1,294 predecessor hashes, including requirements.txt and pytest.ini. The fresh baseline matches the historical 378/20; it was not assumed. No changed old test outcomes, resolved old failures, new old-test failures, collection errors or skips. Failure identities and normalized diagnostics match; normalization only removes hyphenated UUIDs, generated 32-hex turn_id fields and hexadecimal object addresses. Full tracebacks and commands are preserved. The initial 15-test draft assumed no momentum tag. Scenario verification exposed the cadence dependency, so two assertions now require the existing new_information tag for the real clue. Final identical test bytes run against this cycle's preserved pre-edit enforcement function in memory (7/8) and final production (15/0); no historical files are checked out or overwritten. All intermediate results and the initial test draft remain preserved. This is a current-entry function replay, not a reopened historical provenance investigation. No old/frozen assertion is relabeled to excuse a regression.

Known failure identities:

"""+"\n".join("- `"+n+"`" for n in r["unchanged_known_failures"])+f"""

The before authority runner was invoked with before/authority, and its existing /authority suffix produced before/authority/authority. This naming discrepancy does not change selection or results. A new test module was added while that pre-edit run was executing; its integrity log records only the addition, no preexisting-file mutation, and the collected historical nodes do not include it. The original focused/new-test before runs finish before production edits. The final new-test-source before replay loads only the preserved current-entry enforcement function in memory; final HTTP and all regression after runs use production unchanged.

All runners set provider-disable flags, block external sockets and isolate storage. Live provider calls **0**; network attempts **0**. Commands from repository root, .venv/Scripts/python.exe:

```powershell
.venv/Scripts/python.exe artifacts/{ID}/run_sequence.py traced_before
.venv/Scripts/python.exe artifacts/{ID}/run_sequence.py after_final
.venv/Scripts/python.exe artifacts/{ID}/run_audit.py before
.venv/Scripts/python.exe artifacts/{ID}/run_audit.py after_final
.venv/Scripts/python.exe artifacts/{ID}/run_controls.py before/authority
.venv/Scripts/python.exe artifacts/{ID}/run_controls.py after_final
.venv/Scripts/python.exe artifacts/{ID}/run_focused.py focused_before
.venv/Scripts/python.exe artifacts/{ID}/run_focused.py focused_final
.venv/Scripts/python.exe artifacts/{ID}/run_composition.py new_before_final
.venv/Scripts/python.exe artifacts/{ID}/run_composition.py new_after_final
```

Exact pytest argument arrays and executable paths follow (also each command.json):

"""+"\n".join(commands))
write("TWELVE_TURN_COMPARISON.md","# Twelve-turn original HTTP comparison\n\nAll original requests/seed retained; provider requests and live calls zero, all twelve HTTP 200.\n\n| Turn | Before | After |\n|---|---|---|\n"+"\n".join(f"| {x['id']} | {x['before']} | {x['after']} |" for x in turns)+"\n\nOnly T05 text changes. All turn intent kinds, routing fields, authorized discoveries, resolver state changes, scene results and refusal categories match. T04 stays local without completing touch; T06 refuses copying; T09 recalls the same clue; T11 genuinely travels. T06 retains the preceding successful publication, so its pointer inherits T05's corrected text; it still does not publish the refused action. No publication mismatch. Full conversation histories naturally contain the corrected T05 and momentum bookkeeping records the selected new information beat. Separate unchanged controls preserve explicit NPC repetition, genuine follow-up and hidden-information protection.\n\n"+limitations+"\n\nMachine comparison: twelve_turn_comparison.json. Full requests, state/log snapshots and publication traces: traced_before/twelve_turn and after_final/twelve_turn. No scenario edit manufactured the result.")
write("PERFORMANCE.md",f"""# Performance and token efficiency

Live provider calls: **0**. All gameplay request ledgers remain zero; no network/client attempt. No new dispatch, retry, prompt instruction, model pass or token usage. Existing selected-information extraction and a detached GM dictionary copy replace a stock rendering/append on eligible due-momentum turns; this is bounded local work, not per-sentence scoring or full-context reconstruction.

Observed T05 TestClient time: {turns[4]['ms_before']} ms before, {turns[4]['ms_after']} ms after. These single guarded instrumentation runs do not isolate overhead and are not a performance/savings claim. No material new processing path warrants expensive benchmarking. Captured per-turn elapsed time and zero-provider accounting are in the sequence artifacts. Emission diagnostics add a small fixed internal record, outside the player DTO.
""")
write("NEXT_STEP_DECISION.md",f"""# Next step decision

**A/PASS for the bounded composition repair.** Original T05 HTTP reproduction improves, authorized disclosure and immutable publication agree, relevant existing elaboration/multiple facts survive, closed-authority protections and existing regression outcomes hold. Archive verification is recorded independently in artifacts/{ID}/archive_verification.json.

Exactly one proposed next action: investigate T04 notice-board physical-action completion through its existing local-interaction owner, preserving the repaired T05 information route. This is a proposed future bounded cycle, not authorization to implement it now.

Deferred: {limitations} No historical-baseline investigation, PR-PLAY-80, AT-OPT-07 or live play is reopened. Stop after verification and handoff.
""")
write("INTEGRITY.md",f"""# Integrity

Milestone `{ID}`. Branch feature/product-realization; HEAD d40f1ed198236c604085f1c842ead267a8104ce2. Entry status and source manifest preserved before edits; all 1,294 predecessor source/test/data/config hashes match. Existing dirty changes remain; no reset, clean, stash, revert, historical checkout, commit or push.

Only preexisting source changed: game/response_policy_enforcement.py, relative to preserved entry bytes in production.diff. Added tests/test_pr_play_t05_composition.py, 15 cases; it is byte-identical across new_before_final/new_after_final. No game/api.py, immutable_valid_response.py, referenced_surface.py, prompt/provider or frozen fixture change. {changes['frozen_checked']} frozen/validation input hashes unchanged. Before/after manifests and runner execution_integrity.json distinguish this repair from prior dirty edits.

Test evidence captures no preexisting protected mutation or external network attempt. One new test module was added during the before authority run and is explicitly recorded as an addition; the collection remained unchanged. All selected baseline failure identities and normalized assertion diagnostics match after repair.

Ten reports are in development/campaigns/product_realization/{ID}/. Scripts, commands, JUnit, raw HTTP/stage/state evidence, source manifests, comparisons and cycle-only diff are in artifacts/{ID}/. NEXT_SESSION is prepended from retained entry bytes; historical entries remain an exact suffix. No temporary root artifacts created.

Standard handoff generation uses an explicit cycle config and canonical evidence manifest. Full raw twelve-turn states remain canonical evidence; selected T05 traces, compact twelve-turn comparisons, regressions, source/test bytes and all ten reports form the review surface. Prior dated archives are hash-checked and preserved. The fresh stable and New York timestamped ZIP are independently reopened and checked for CRC, milestone, before/after publications, test totals, updated handoff/history and canonical member/source/evidence hashes.

Final archive path and SHA-256: artifacts/{ID}/archive_sha256.txt. Verification: archive_verification.json. These final external seal files avoid circular archive hashing; do not infer completion from this protocol text alone.
""")
head=f"""# NEXT_SESSION — PR-PLAY T05 Authorized Clue Publication Composition Repair (2026-11-08)

**A/PASS for the bounded repair; the game remains incomplete.** Milestone `{ID}`. Branch feature/product-realization; HEAD d40f1ed198236c604085f1c842ead267a8104ce2. Dirty work preserved; no commits/pushes. Live provider calls: **0**.

Traced T05's unrelated jab to enforce_scene_momentum's synthetic stock append. Only response_policy_enforcement.py changes: resolver-selected public information declines that append before validation/sealing; all existing candidate description, authorized facts and resolved events survive. No sentence limit, prose classifier, prompt/provider/API or pre-seal authority change. Original HTTP T05 now publishes the northwest mud-track clue without the stock jab; accepted text, digest and publication pointer agree, inventory/location unchanged. Other eleven turns, intent/routes/disclosures/resolver state changes/scenes/refusals preserved.

Fresh same-source selection: 378/20 before and after; new composition tests 7/8 → 15/0. Combined 393 passed / 20 known failures; no new identities/normalized diagnostics, collection errors or skips. All 17 pre-seal tests, three closed-inspection HTTP cases, seven conversational handoff controls and AT-OPT-06 controls pass. Relevant elaboration and multiple facts remain publishable. No full-suite/held-out/live-provider/Gameplay Benchmark acceptance claim.

**Exactly one proposed next action: investigate T04 notice-board physical-action completion through its existing local-interaction owner**, preserving T05. Do not begin automatically. Defer remaining physical/generic/NPC/trading/refusal deficiencies and all twenty baseline failures; do not reopen historical provenance, PR-PLAY-80, AT-OPT-07 or live play.

Reports: development/campaigns/product_realization/{ID}/. Evidence: artifacts/{ID}/. Minimum: SUMMARY, ROOT_CAUSE, IMPLEMENTATION, T05_BEFORE_AFTER, REGRESSION_RESULTS, NEXT_STEP_DECISION; t05_comparison.json, closed_inspection_results.json, twelve_turn_comparison.json, test_results.json, source_changes.json. Fresh stable/dated review archive and reopened seal: archive_sha256.txt / archive_verification.json. Review surface: handoff/CURRENT_REVIEW.md.

---

"""
(ROOT/"docs/NEXT_SESSION.md").write_bytes(head.encode()+ (OUT/"entry/docs/NEXT_SESSION.md").read_bytes())
print("Ten reports and canonical session handoff written.")
