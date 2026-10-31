from pathlib import Path
import json

out=Path('artifacts/atgb/atgb_r1_02')
reports=Path('development/reports/atgb_r1_02'); reports.mkdir(parents=True,exist_ok=True)
summary=json.loads((out/'test_summary.json').read_text())
existing='tests/test_pr_ef_r4_authorization.py tests/test_pr_ea_conversational_orchestration.py tests/test_pr_ef_gm_authority.py tests/test_pr_ef_r1_semantic_handoff.py tests/test_pr_ef_r2_social_authority.py tests/test_state_authority.py tests/test_pr_eg_r1_continuity.py tests/test_pr_eg_r6_r1_disclosure_boundary.py tests/test_pr_eg_r6_r1_r1_provenance.py tests/test_pr_eg_r6_r2_r1_referents.py tests/test_pr_eg_r6_r2_r2_operations.py tests/test_pr_eg_r6_r5_diagnostic.py'
args={'targeted':'-m pytest tests/test_atgb_r1_02_revision_boundary.py tests/test_pr_ef_r4_authorization.py',
      'final':'-m pytest tests/test_atgb_r1_02_revision_boundary.py '+existing,
      'pre_repair':'artifacts/atgb/atgb_r1_02/run_pre_repair_regression.py '+existing}
commands={}
for name,arg in args.items():
 temp='targeted' if name=='targeted' else name
 commands[name]="$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' "+arg+f' -q --tb=short --basetemp=development/tmp/atgb_r1_02_{temp} --junitxml=artifacts/atgb/atgb_r1_02/{name}.xml *> artifacts/atgb/atgb_r1_02/{name}.txt; $code=$LASTEXITCODE; $code | Set-Content artifacts/atgb/atgb_r1_02/{name}_exit.txt'
(out/'test_commands.json').write_text(json.dumps({'commands':commands,'working_directory':str(Path.cwd()),'execution_environment':'Outside sandbox for Windows local socketpair support; pytest autouse live-model guard active.','interrupted_runs':[{'name':'focused','exit_code':1,'reason':'Interrupted: Starlette asyncio socketpair accept hung; no completed suite count.'},{'name':'regression','exit_code':1,'reason':'Same socketpair environment hang.'},{'name':'diagnose','exit_code':1,'reason':'Interrupted after faulthandler captured local socketpair hang.'}],'initial_verified_run':{'tests':452,'passed':440,'failed':12,'exit_code':1,'new_test_assertion_errors':3,'pre_existing_failures':9,'resolution':'Corrected overly broad new session-equality assertion to preserve gameplay/intention invariants while allowing existing conversation-memory/save metadata writes.'}},indent=2))
texts={
'01_implementation_summary.md':'''# 01 — Implementation Summary

ATGB-R1-02, 2026-10-18. Failure class: contract, as established by ATGB-R1-01. Implementation authority: mechanical revision routing only.

The prior investigation establishes the mechanism in the verified current source. Its S08.2 trace, mechanical counterexample, causal comparison, minimal recommendation, validation proposal and verdict were read before editing. `support/docs/NEXT_SESSION.md` is a bundle-relative path; repository orientation is `docs/NEXT_SESSION.md`. PR-EG-R6-R5 artifacts 11, 32 and 36 were reviewed. R5's bind/witness repair remains a different mechanism and was not integrated.

Production changes are limited to `game/conversational_orchestration.py`:

- `_REVISION_RE` keeps the established explicit `instead`, `make that`, and `revise` cues, recognizes `change my/the pending`, and no longer treats `i meant` or bare `change that` as sufficient by themselves.
- `_pending_revision_decision` accepts existing interpreted action components. Without an explicit cue, correction language requires both an existing intention referent (pending, clarification, or last executed) and an action component. Existing scene, status, no-pending, and executed-action checks then run unchanged.
- `_communication_decision` passes those components and reserves the set-aside/clear-context branch for WITHDRAWAL. A nonmechanical CORRECTION continues through ordinary public-evidence answering rather than clearing an intention.

The distinction uses existing state and interpretation signals. It contains no scenario IDs or calibration nouns, no new classifier, no prompt change and no new model call. Unrelated observatory/astronomer fixtures exercise the same condition; these authored variations are not independent held-out generalization.

Legitimate revisions remain pending, explicit requests with no pending action remain safeguarded, and executed actions remain immutable. A correction purpose is no longer itself authorization to control an intention.

Other authored files: `tests/test_atgb_r1_02_revision_boundary.py`; these eight reports and index; `docs/NEXT_SESSION.md`; campaign evidence scripts/JSON/logs/diff under `artifacts/atgb/atgb_r1_02/`; validation evidence packet; review configuration and generated exports. Extensive pre-existing dirty worktree changes were retained. No commit or push.
''',
'02_routing_contract.md':'''# 02 — Routing Contract

| Input/state | Result |
| --- | --- |
| Ordinary correction, including “I meant the people, not the weather.” | Correction phrase or CORRECTION label alone does not select mechanical revision. Existing ordinary communication retains prior context and selected public evidence. No intention update is emitted. |
| Explicit pending movement/attack revision | Mechanical revision owner retains scene/status checks. An eligible intention receives revised_text and stays pending; no action executes. |
| Explicit request with no eligible pending intention | Existing no_pending_intention clarification; no invented intention. |
| Explicit request after execution | Existing executed_intention_not_reversible answer; no rollback. |
| “I meant to move east” with a pending intention and interpreted MOVE | Mechanical revision, including when the phrase contains no “instead”. |
| Ambiguous correction with no action proposal | Ordinary communication or its existing clarification/fallback; no mechanical authority is acquired. |
| Established conversational referent | Available context and evidence continue to existing owners; no new referent binding or sufficiency logic is added. |

“I meant” is not categorically conversational. It may participate in action control when existing action/state signals establish that reading. Conversely a pending record by itself does not make a correction mechanical.

Existing explicit instead/make-that/revise cues remain conservative safeguards to preserve frozen PR-EF holdouts. This bounded repair is not a complete natural-language distinction for every usage of those words. Unrelated “instead” statements and bad upstream action labels remain limitations, not newly solved cases.

Pending-action validation remains authoritative. Interpreted action components at this gate identify revision relevance; they do not execute an action or grant a new world-writing permission. Revised intentions must still pass the established continuation/resolution checks when later attempted.
''',
'03_regression_evidence.md':'''# 03 — Regression Evidence

No live provider calls. All tests use the repository's autouse live-model guard, which blocks OpenAI constructors and known model entry points. Existing tests install deterministic stubs. Local socket access was required only for Starlette TestClient.

| Run | Tests | Passed | Failed | Exit |
| --- | ---: | ---: | ---: | ---: |
| New boundary tests + frozen PR-EF-R4 authorization suite | 133 | 133 | 0 | 0 |
| Final relevant slice | 452 | 443 | 9 | 1 |
| Matched existing slice, saved pre-repair source loaded in memory | 347 | 338 | 9 | 1 |

New tests: 105 passing. Existing focused authorization tests: 28 passing, including correction_pending, correction_already_executed, correction_nothing_pending. The broad existing outcome set matches the pre-repair run exactly. Full suite not run; no full-suite-green claim.

Coverage includes all requested correction and ambiguous wordings, DESCRIPTION/CORRECTION labels, absent/pending/executed contexts, movement and attack revisions, implicit action revisions, pending_clarification fallback, stale-scene rejection, nonexecution, selected public evidence, original S08.2 context and direct API gameplay-state integrity. Related observatory/astronomer vocabulary is authored scenario-independent coverage, not unseen evaluation.

Nine pre-existing failures are in test_pr_eg_r6_r2_r1_referents: eight test_untrusted_operations_fail_closed_without_losing_focus parameters expect clarification but get unknown, and test_unqualified_historical_id_cannot_override_focus lacks bound_referent_id. Both runs have precisely these IDs. No production change was made to repair them. `test_summary.json` retains every failure ID; XML and text logs retain exact assertions.

Initial sandbox focused and broader runs were interrupted (exit 1, incomplete counts) because Python's socket._fallback_socketpair blocked on accept during TestClient loop initialization. `diagnose.txt` preserves the 15-second faulthandler stack. The outside-sandbox rerun completed. The first completed run had three new-test assertion failures from requiring the entire session to remain equal: normal delivered-history/save metadata changed. Assertions were corrected to check gameplay stores and pending/executed records explicitly. That run remains preserved as verified.txt/xml (440 pass, 12 fail).

One existing Starlette/httpx deprecation warning. No test expectation in an existing test or frozen fixture was changed.

## Exact commands

Commands below use the repository cwd and bundled runtime. Their exit codes are pytest exits, retained in *_exit.txt; the enclosing PowerShell command can itself exit 0 after recording a failed pytest exit.
''',
'04_s08_2_before_after_trace.md':'''# 04 — S08.2 Before/After Trace

Source: frozen ATGB-03C S08 trial 1, `artifacts/atgb/atgb_03c/S08/result.json` and transcript.md. The raw historical model record and selected evidence refs are unavailable. This pass replays the interpretation-to-orchestration seam; it is not a new live ATGB trial.

Player: “I meant the people, not the weather.”

Prior player: “What's in front of me right now?” The delivered description names rain/choke traffic as well as the gate serjeant, tavern runner, watchers and refugees. Relevant pre-turn context is reconstructed from that delivered exchange and captured state: frontier_gate, no pending_intention, pending_clarification or last_executed_intention, no active interlocutor. The final store is not claimed to be a pre-turn snapshot. Full exact prior response, reconstructed seam state, both complete decisions and provenance are in s08_2_trace.json.

| Stage | Before | After |
| --- | --- | --- |
| Controlled interpretation | GM/DESCRIPTION or GM/CORRECTION; empty components/evidence | Identical stub |
| Routing reason | no_pending_intention | communication_before_execution |
| Mechanical handling selected | Yes, both stubs | No, both stubs; gate consulted and abstains |
| Response plan | “I don't have an unexecuted intention to revise. What do you want to change?” | “That has not been established in the information available to you.” |
| Context update | None | None |
| State changes / action execution | None | None |
| Provider calls in this replay | 0 | 0 |

The before result is observed both in the historical capture and by executing the saved pre-repair source. The after result is observed from current code with controlled empty-evidence records. No historical provider purpose is inferred from the host-overwritten purpose.

**Routing correctness: PASS.** Neither label triggers mechanical revision from conversational correction alone.

**Conversational adequacy of the empty-evidence deterministic fixture: FAIL.** The fallback does not describe the people despite the preserved prior description. The next observed boundary is ordinary GM evidence answering: it has no selected evidence and does not itself recover the requested subject from the stored reply. No downstream repair was attempted.

**Conversational adequacy of a production/live S08.2 replay: NOT EVALUABLE.** A live model call is prohibited and historical evidence selection was not retained. The selected-public-evidence unit control demonstrates only that this existing path can emit supplied public evidence. It does not prove the production model will select the people or justify a successful response claim.

Behavioral packet: `artifacts/validation_evidence/atgb_r1_02/`. Two controlled response-plan runs, two turns; UNREVIEWED. No representative semantic success, evaluator disagreement or stress probe was observed. No gameplay benchmark performance result.
''',
'05_authority_preservation.md':'''# 05 — Authority Preservation

- Pending intention: eligible pending/clarification records are copied with revised_text and pending status, with no executable proposal. Status and scene checks are unchanged; stale scenes retain the no-pending safeguard.
- Executed action: existing refusal remains; tests assert unchanged input records and no context update. Frozen executed-action holdout still passes without social resolution or world mutation.
- World ownership: only entry selection changed. No resolver, bridge, world writer, validator, gameplay permission or state owner changed. API tests preserve world, active scene and character plus gameplay session fields, inventory/clocks/scene/turn and pending/executed records. Normal delivered-history and save metadata writes remain allowed.
- No fabrication: explicit revision without pending state returns the existing clarification and no context update. Ambiguous/conversational corrections emit no intention update and do not clear unrelated pending context.
- Disclosure: public-evidence selection and existing addressee/disclosure owners are unchanged. New API assertions do not reveal a hidden maker's mark; existing disclosure/provenance suites pass. This is scoped regression evidence, not a proof over every possible provider output.
- Existing authorization holdouts: all 28 pass. Existing PR-EG referent failures remain unchanged and separate; no witness or bind predicate was relaxed to obtain green results.

Baseline/fixture/experiment preservation: 3,564 files hashed before repair; zero missing or changed on final check. baseline_hashes.json and preservation_check.json retain details. Protected scopes include ATGB definitions, frozen capture/assessment artifacts, tests/fixtures, PR-EG-R6-R5 evidence and experimental candidates. No authority was granted to the model; no experimental candidate was merged.
''',
'06_performance_assessment.md':'''# 06 — Performance Assessment

| Dimension | Assessment |
| --- | --- |
| Model invocations | No call site or count added; deterministic trace has zero calls. Historical S08.2 used one interpretation call and no narration call. A repaired live call count was not measured. |
| Context payload construction | No prompt, retrieval payload or context builder changed. Existing context is retained. |
| Token consumption | No intentional payload enlargement. Actual response/output-token consumption may differ by downstream route; unmeasured. |
| Retry behavior | Unchanged; no added retry. |
| Persistent state | No new schema, store or memory subsystem. Ordinary corrections no longer clear intention records in the correction fallback. Existing delivered-exchange memory remains active. |
| Routing complexity | Same owner, regex, state lookups and one scan of existing action components for implicit revisions. Bounded local work proportional to input/components; no network stage. |
| Expected latency | Small local predicate cost expected; no measured improvement or live latency claim. Downstream branch behavior may differ. |

No live provider calls were made in this pass. Test execution durations measure deterministic tests, not production latency or cost.
''',
'07_remaining_conversational_limitations.md':'''# 07 — Remaining Conversational Limitations

The original inappropriate intention prompt is repaired at the demonstrated routing boundary. The empty-evidence S08.2 stub still produces a nonresponsive established-information fallback. Public evidence/referent selection and response sufficiency require a separate observed investigation; they were not repaired here.

The original raw provider interpretation was not retained. This pass establishes behavior for two controlled purpose labels rather than claiming reconstruction of that missing label. Production adequacy is NOT EVALUABLE without a separately authorized live trial.

A provider's action-component interpretation remains an upstream signal; this repair is not a universal correction classifier. Preserved explicit revision cues such as instead/revise can still be broad. Ambiguous utterances use existing clarification/fallback behavior; this pass does not improve referent resolution or guarantee a useful clarification.

PR-EG bind/witness corrections, addressee grounding, session-ruling responses, withdrawal behavior, response sufficiency and the other ATGB failures remain outside scope. PR-EG-R6-R5 correction tag 0/25 and its historical 59/164 success measurement are unchanged historical results. R4-R1 remains do-not-integrate; R5 remains diagnosis only. No unseen generalization, benchmark performance or overall playability result is established.

The nine matched existing PR-EG referent regression failures remain unresolved. Authenticated human review remains pending. Extensive pre-existing worktree changes remain preserved. No ATGB-R1-03 work began.
''',
'08_final_verdict.md':'''# 08 — Final Verdict

**B — Conditional.**

The scoped routing repair is demonstrated: S08.2 leaves mechanical revision handling under both controlled labels; all 105 new regressions and all 28 frozen authorization tests pass. World/action/disclosure boundaries remain intact in the tested slice. The broader slice has 443 passes and nine failures; the same nine failures occur with saved pre-repair source (338 passes among 347 existing tests), so no new failures were observed in that matched slice. The broader requested regression surface is not wholly green.

Response adequacy is separate: empty-evidence stub FAIL; production replay NOT EVALUABLE. These limitations preclude a claim that the people-description interaction is repaired end to end. The grade is for bounded implementation and its validation limits, not conversational competence.

Recommend external review of this ZIP first. After review, a separately authorized controlled live S08.2 trial could determine actual downstream evidence selection; do not rerun or overwrite the frozen trial. A separate investigation may then address an observed downstream insufficiency. Do not expand this repair into PR-EG bind/witness work or ATGB-R1-03 during this pass.

Confirmed: no live provider calls; frozen ATGB baseline unchanged; no unrelated production changes authored; no additional model authority; no experimental PR-EG candidates merged. No commit/push. Stop at the review ZIP and await external review.
'''}
for name,text in texts.items():
 if name.startswith('03_'):
  for n,c in commands.items():text+=f'\n### {n}\n\n```powershell\n{c}\n```\n\nExit {summary[n]["exit_code"]}; {summary[n]["passed"]} passed, {summary[n]["failed"]} failed.\n'
 (reports/name).write_text(text,encoding='utf-8')
index='# ATGB-R1-02 — Mechanical Revision Boundary Repair\n\n2026-10-18. Bounded implementation; no live provider calls. **B — Conditional.** Routing PASS, empty-evidence response stub FAIL, production adequacy NOT EVALUABLE.\n\n'
index+='\n'.join(f'- [{name[3:-3].replace("_"," ").title()}](atgb_r1_02/{name})' for name in texts)
index+='\n\nEvidence: `artifacts/atgb/atgb_r1_02/`; behavioral packet: `artifacts/validation_evidence/atgb_r1_02/`; review: `handoff/CURRENT_REVIEW.md` and ZIP. Exact commands, test counts, preserved baseline hashes and trace are included. No full-suite or ATGB performance claim. Stop for external review.\n'
Path('development/reports/atgb_r1_02_mechanical_revision_boundary.md').write_text(index,encoding='utf-8')
# Preserve the handoff's other current facts and replace only the completed-work pointer.
p=Path('docs/NEXT_SESSION.md'); text=p.read_text(encoding='utf-8')
text=text.replace('Updated 2026-10-18 / ATGB-R1-01.','Updated 2026-10-18 / ATGB-R1-02.')
a=text.index('ATGB-R1-01 investigated S08.2 only.'); b=text.index('ATGB-05A remains',a)
text=text[:a]+'''ATGB-R1-02 implemented the bounded mechanical revision-entry repair authorized
by the user after ATGB-R1-01. Report:
`development/reports/atgb_r1_02_mechanical_revision_boundary.md`; eight detailed
reports under `development/reports/atgb_r1_02/`; evidence under
`artifacts/atgb/atgb_r1_02/`. Standard review: `handoff/CURRENT_REVIEW.md` and ZIP.

Verdict **B — Conditional**. Routing PASS under GM/DESCRIPTION and GM/CORRECTION
stubs; 105 new tests plus 28 frozen authorization tests pass. Broader slice:
443 passed, 9 failed; saved pre-repair source reproduces the same 9 PR-EG
referent failures (338 passed / 347 existing tests). No new failures in the
matched slice. Full suite not run. No live provider calls.

Empty-evidence S08.2 response-plan adequacy FAIL: ordinary communication says
“That has not been established in the information available to you.” Production
adequacy NOT EVALUABLE: original interpretation/evidence refs were not retained.
No downstream sufficiency repair. Frozen baseline/fixtures/experiments: 3,564
hashed files unchanged. No bind/witness, addressee or experimental integration.

Await external review. Only after review and separate live authorization,
consider a controlled new S08.2 trial to inspect downstream evidence selection.
Do not begin ATGB-R1-03 automatically. The R1-01 mechanism and different-mechanism
PR-EG comparison remain established in its causal-trace report.

'''+text[b:]
text=text.replace('Stop for review: ATGB-R1-01 implemented no repair. No gameplay change, live\nprovider call, baseline edit, or authority change in this pass.','Stop for external review: ATGB-R1-02 changed only mechanical revision routing.\nNo live provider call, frozen-baseline edit, added model authority, commit or push.\nDo not begin ATGB-R1-03 until external review.')
p.write_text(text,encoding='utf-8')
print('Eight reports, report index, exact commands and session handoff written.')
