from pathlib import Path
import ast,difflib,json,shutil,xml.etree.ElementTree as ET,hashlib,zipfile,re
from datetime import datetime
import subprocess
P=Path('artifacts/pr_play_27')
def write(n,s): (P/n).write_text(s,encoding='utf8')
def xml(n):
 r=ET.parse(P/n).getroot(); rows={}
 for t in r.iter('testcase'):
  fail=t.find('failure');error=t.find('error');node=fail if fail is not None else error
  rows[t.attrib['classname'].replace('.', '/')+'.py::'+t.attrib['name']]={'status':'error' if error is not None else 'failed' if fail is not None else 'skipped' if t.find('skipped') is not None else 'passed','message':node.attrib.get('message','') if node is not None else ''}
 return rows
def counts(rows): return {s:sum(x['status']==s for x in rows.values()) for s in ('passed','failed','error','skipped')}
def locations(file,names):
 tree=ast.parse(Path(file).read_text(encoding='utf8'))
 return ', '.join(f'{n.name}:{n.lineno}' for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names)
# Only prior-pass material needed for this investigation; no historical bundle.
root=Path('artifacts/pr_play_26'); dest=P/'pr_play_26_trace';dest.mkdir(exist_ok=True)
for n in ['PR_PLAY_26_TRANSCRIPT.md','followup_decision.json','stop_and_quality_analysis.json','expression_token_analysis.json']:
 shutil.copyfile(root/n,dest/n)
for n in ['request_03.json','response_03.json','trace_018_build_dialogue_authority_output.json','trace_019_select_public_offering_output.json','trace_022_select_host_speech_output.json','trace_023_request_expression_input.json','trace_023_request_expression_output.json','trace_024_validate_expression_input.json','trace_024_validate_expression_output.json','trace_008_normalize_local_approach_output.json']:
 shutil.copyfile(root/'live/diagnostics'/n,dest/n)
write('PR_PLAY_27_FAILURE_RECONSTRUCTION.md','''# PR-PLAY-27 failure reconstruction

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
''')
source=P/'source_snapshot/game/expressive_dialogue.py'
write('PR_PLAY_27_EXPRESSION_CONTRACT.md',f'''# PR-PLAY-27 expression contract

Source: game/expressive_dialogue.py ({locations(source,{'build_expression_contract','build_expression_prompt','_faithful_reasons','_offering_reasons','validate_expression','_attempt','apply_expression','attach_expression_audit'})}).

The host selects authority before any wording request. game/dialogue_authority.py:build_dialogue_authority, attach_dialogue_authority and select_host_speech determine the proposition and fallback; game/public_fact_dialogue.py:select_public_offering projects already eligible public facts. No change to eligibility, source selection, attribution or disclosure policy.

build_expression_contract represents authorized_propositions as a list of host strings, with source_identity, proposition_id, source_revision, speaker_identity, entity_identities, epistemic/disclosure posture, answer_sufficiency and permitted_meaning. Public offerings get relation=own_offerings. The provider receives the compact system/user prompt built from this contract. It is expected to reword, never establish new consequences.

Before repair: bounded lexical coverage with function-word exclusion and a few synonym classes, plus scoped offering-verb replacement. _plain folds typographic quotes; _tokens extracts words; _content removes grammar/framing; _faithful_reasons checks missing anchors and uncovered tokens, hedge loss/strengthening, exact repetition and proper names. It is near-verbatim for most other content; it is not a semantic entailment engine. Adjectives such as hot are mandatory anchors. Case B remains rejected; dropping hot conflicts with the existing preserve-every-item-description contract.

Repair: only the existing own_offerings relation enters _offering_reasons. Full source frames are first person or the exact contract speaker name; other subjects fail closed. Whole item phrases, including adjectives, must match as a multiset. Whole items can reorder; internal item word order cannot. Supported frames: I offer, I can offer you, I serve, I've got/I have got, optional Well, optional terminal to share, and items—that's what I've got. Sale authority supports I sell and I've got ... for sale; a generic offering cannot become a sale commitment. Rooms/a room has one scoped service-unit normalization. No own/give/pay/free or arbitrary synonym substitutions.

Shared length, sentence, number and internal-voice checks still run. The closed grammar excludes negation, new actors, locations, prices, quantities, inventory promises, extra items and embedded claims. The grammar applies only to an already authorized offering; hidden campaign text never becomes authority. Other operations retain their original validation.

_attempt makes one expression request, sanitizes spoken text, validates it, and wraps accepted wording in the host speaker frame. On rejection it returns the original deterministic host line and records candidate/reasons/fallback_used/provider outcome and contract. No retry or judge. attach_expression_audit records expression_decision/adoption and reseals delivery through game.immutable_valid_response:seal_delivery_contract. game/immutable_valid_response.py:adopt_host_speech selects host speech, calls apply_expression, then seal_host_speech and attach_expression_audit; seal_delivery_contract seals final publication. game/api.py:_nonmutating_conversational_decision_response also uses maybe_reword_continuity_line and attach_expression_audit for eligible continuity answers. Player projection remains authoritative.

Limitations: this handles a small offering grammar, not broad paraphrase/entailment. Item synonyms, adjective omissions, general third-person transformations, arbitrary possession, sale/gift equivalence, separately authorized location combinations and complex clauses remain unsupported. Existing non-offering lexical validators are unchanged. Hidden disclosures are prevented by closed source matching here and existing projection; the harness's exact restricted-string scan alone cannot prove absence of paraphrased leakage.
''')
write('PR_PLAY_27_REPAIR_REPORT.md','''# PR-PLAY-27 repair report

Confirmed root cause: a terminal to share is outside lexical coverage despite preserving the authorized offering. The expression contract was already bounded; extending its existing own_offerings branch is sufficient.

Production files modified in this pass:
- game/expressive_dialogue.py: replace global-in-sentence offering verb substitution with a scoped full-sentence grammar, preserve whole item phrases and seller identity, align offering prompt with allowed frames.
- tools/playtest/gameplay.py: derive four expression outcomes from existing audit/accepted response; validate published wording separately; exact host proposition counts as recovery even though generated exact repetition is intentionally rejected; require correct published speaker frame; generic uncertainty with answer material fails; missing/unauthorized response fails. evaluate retains state, confidentiality, parser, binding, hard-validation and overlay gates. Experiments can set requires_substantive_answer on an action to stop generic uncertainty when that experiment requires an answer. Legitimate uncertainty in other scenarios is unchanged.
- tools/playtest/runner.py: use can_start_interaction to reserve two remaining request slots (interpretation and possible expression) before submitting a turn. Existing ceilings, token admission, refusal, deadline and transport logic are unchanged.
- tests/test_pr_play_27_expression_recovery.py: matrix, recovery/failure controls, real-controller budget gate, mocked harness continuity and HTTP opening/conversation/state evidence.

Four derived outcomes: EXPRESSION_ACCEPTED; EXPRESSION_REJECTED_RECOVERED; EXPRESSION_REJECTED_UNRECOVERED; EXPRESSION_NOT_INVOKED. These are harness observations, not new persisted gameplay fields. Rejection reason, candidate, fallback and authority remain in the existing expression audit. Projection-only recovery requires an exact authorized proposition and native hard_valid=true; missing evidence fails closed.

A useful, authorized fallback permits continuation only if all existing semantic and integrity checks pass and a full next interaction fits the request budget. A parser/transport/binding/target/social failure, final hard-invalid response, missing answer, unauthorized mutation, disclosure, explicit substantive-answer dead end or exhausted budget still stops. No provider retry, regenerated turn or increased budget.

Important discovery: the historical shared classifier already permitted the exact PR-PLAY-26 fallback. The fatal rejection rule was in that experiment's manual continuation instructions, not a blanket production classifier branch. This pass makes the distinction explicit and testable in the shared harness; it does not rewrite archived evidence/controllers or override instructions in future experiments.

Compatibility: stricter offering frames intentionally exclude sell/for sale when the actual proposition only authorizes offer. This avoids the old broad replacement's ambiguity. Mandatory descriptors are retained. Other operations and authority selection are untouched. The workspace had substantial existing changes; per-pass before/after snapshots and diffs distinguish this repair from prior uncommitted work.

Remaining continuity: the exact rumors follow-up does not select patrol_rumor. An explicit patrol follow-up selects and publishes the existing authored answer without another expression call. The full evaluator still flags its discovered-clues overlay as authority unavailable. These are recorded limitations; neither topic selection nor overlay authority was redesigned. baseline_explicit_overlay_replay.json confirms the saved pre-pass evaluator flags the same overlay authority limitation.
''')
rows=[]
for path in sorted(P.glob('matrix_*.json')):
 d=json.loads(path.read_text(encoding='utf8')); v=d['actual']; rows.append('| '+ ' | '.join([d['key'],d['authority'],d['candidate'],'ACCEPT' if d['expected'] else 'REJECT','ACCEPT' if v['adopt'] else 'REJECT',', '.join(v['reasons']) or '—','PASS' if v['adopt']==d['expected'] else 'FAIL'])+' |')
write('PR_PLAY_27_VALIDATOR_MATRIX.md','# PR-PLAY-27 validator matrix\n\nB retains REJECT because hot is a required item descriptor; this is the explicitly permitted contract-conflict exception. D uses the Innkeeper identity and existing own_offerings relation; it does not change authority eligibility. All cases call the real deterministic validator.\n\n| Case | Authority | Candidate | Expected | Actual | Reasons | Result |\n|---|---|---|---|---|---|---|\n'+'\n'.join(rows)+'\n')
write('PR_PLAY_27_HARNESS_VALIDATION.md','''# PR-PLAY-27 harness validation

Deterministic scenarios and detailed results: harness_accepted.json (adopted/useful/complete/continue), harness_recovered.json (unsupported candidate rejected, exact authorized fallback complete/continue), harness_generic.json (authorized answer available, uncertainty unhelpful/stop), harness_missing.json (unrecoverable/stop), harness_unauthorized.json (unsupported price/integrity stop), harness_hidden.json (exact restricted sentinel/confidentiality stop). _attempt is tested to retain fallback with exactly one expression request and no retry. The four expression classifications are derived from existing audit evidence.

Budget: test_budget covers two-slot admission including stopped budgets; budget_controller.json exercises the real runner with a mocked recovered turn, then one remaining slot. Only one ordinary turn is attempted and the next turn is not submitted. Stop provider_budget_exhaustion; no budget increase. Existing provider ledger still enforces token ceilings and dispatch limits.

Two-turn mocked harness control: two_turn_mocked_harness.json. A rejected price expression recovers to the public offering, then the real authored-topic selector supplies patrol_rumor for an explicit patrol question. Both mocked published turns complete; same runner, source transition scene:frontier_gate:visible:2 -> npc:tavern_runner:patrol_rumor, no additional expression call. This component-level positive control does not stand in for the exact requested HTTP follow-up.

Full application pipeline: two_turn_accepted.json and two_turn_recovered.json preserve initialization, each player response, internal resolution, authority, mock call counts, before/after state and full evaluator results. The original approach/ASK resolves correctly. Original paraphrase is adopted and published without fallback; deliberately unsupported price expression recovers to the deterministic offering and permits the second submission. The requested follow-up resolves the same NPC but topic_selection is empty, authorized_proposition is empty, and generic uncertainty is published. With requires_substantive_answer=true this experiment stops for decisive_conversational_dead_end. We did not force a topic or invent an answer. Two interpretation mocks and two expression mocks per exact-question conversation; zero live calls.

Additional full HTTP controls: *_explicit.json changes only follow-up wording to What have you heard about the patrol? The real selector picks patrol_rumor and publishes its authored answer. Two interpretations, one expression total. Native turn classification completes. Full evaluator conservatively stops for unauthorized_overlay_mutation because discovered_clues changes lack its recognized ordinary-turn authority evidence (opening_not_accepted_or_ordinary_turn_authority_unavailable). Explicit source/state assertions verify authored clue IDs and corresponding engine log events; this pass does not relax the overlay check. Thus successful shared-classification controls are established, but unrestricted full-harness two-turn success is not claimed.

State checks: character/campaign/combat/conditions unchanged; world matches advance_world_tick exactly for offering/exact generic conversations. Explicit authored disclosure adds exactly social_lead_revealed(muddy_footprints_northwest) and social_extracted_lead(lead_frontier_gate_old_trading_crossroads), with all other world fields matching expected tick. Full before/after data retained. No assertion of arbitrary world immutability during engine-owned progression.
''')
# Final test comparison requires completed authoritative runs.
if not (P/'existing_final.xml').exists():
 print('Static reports written; waiting for exact test comparison.');raise SystemExit(0)
baseline=xml('baseline_exact.xml'); current=xml('existing_final.xml'); focused=xml('focused_final.xml')
changes=[]
for key in sorted(set(baseline)|set(current)):
 b=baseline.get(key,{});c=current.get(key,{})
 if b.get('status') in {'failed','error'} or c.get('status') in {'failed','error'}:
  classification='preexisting' if b.get('status') in {'failed','error'} and c.get('status') in {'failed','error'} else 'resolved_by_repair' if b.get('status') in {'failed','error'} else 'newly_introduced'
  changes.append(dict(test_id=key,classification=classification,before=b,after=c))
write('test_comparison.json',json.dumps(dict(baseline=counts(baseline),current=counts(current),focused=counts(focused),failures=changes),indent=2))
new=[r for r in changes if r['classification']=='newly_introduced']; resolved=[r for r in changes if r['classification']=='resolved_by_repair']
write('PR_PLAY_27_TEST_RESULTS.md',f'''# PR-PLAY-27 test results

Exact pre-repair baseline: {counts(baseline)}. Repaired existing tests: {counts(current)}. Final focused: {counts(focused)}. Existing test IDs: {len(current)}. Newly failing: {len(new)}; resolved: {len(resolved)}. Exact identifiers, statuses and assertion messages are in test_comparison.json; full logs/XML retained. The repository-wide suite is not green.

Method: baseline_exact and existing_final use the identical test_files.json list/order, including previous expression tests, dialogue authority, social resolution, ordinary turn/local interaction and harness coverage. run_comparison.py temporarily restores exact saved pre-pass modules on disk for the baseline, then restores the repair in finally and runs the same files. Distinct --basetemp roots isolate both runs. No baseline is inferred from HEAD, which predates existing workspace repairs. Existing PR-PLAY-25 reported 109 failures in its combined scopes; this scope adds harness/ordinary-turn coverage and uses current pre-pass state, so exact current baseline IDs take precedence over historical totals.

Initial development runs are retained for transparency: new_tests.xml/new_debug.txt contain test-authoring assertion corrections (legitimate authored clue log effects were initially omitted), plus environmental shared pytest temporary-directory collisions. Preliminary broad logs are superseded by baseline_exact/existing_final. Final runs use isolated directories. No production change was made to mask those errors. The full-pipeline requested follow-up limitation is asserted as observed behavior, documented as partial product outcome, not represented as a successful conversation.

Commands: .venv/Scripts/python.exe -m pytest <test_files.json> -q --tb=short --basetemp=development/tmp/pr_play_27_[baseline_exact|existing_final] --junitxml=artifacts/pr_play_27/[baseline_exact|existing_final].xml. Focused files: test_pr_play_27_expression_recovery.py, test_pr_play_25_public_fact_dialogue.py, test_pr_play_23_harness.py with a distinct focused_final temporary root. Pytest autouse live_model_guard blocks unmocked model transports; deterministic workers use SDK stubs and deny external connects. Live-provider requests: **0**. Provider-shaped mock counts are explicitly separate from historical PR-PLAY-26 usage.
''')
answers=[
'Yes; exact contract yields unsupported_addition before repair.',
'_faithful_reasons uncovered-candidate-token check; share is not covered after got -> offer normalization.',
'Yes; original paraphrase adopted in deterministic validator and HTTP publication.',
'Yes; merchant, innkeeper, potter and cook offering controls, with the same bounded grammar.',
'Yes; I\'ve/I have got are supported in offering frames.',
'Yes; offering verbs and sale-qualified frames are constrained by source relation/verb.',
'Yes; unsupported prices rejected.', 'Yes; unsupported rewards rejected.', 'Yes; unsupported locations rejected.',
'Yes; unsupported inventory/quantities rejected.', 'Yes; hidden additions fail closed and exact disclosure stops the harness.',
'Yes; negated/changed offering frames rejected.', 'Yes; unchanged deterministic fallback and one-call/no-retry regression.',
'Yes; four derived expression outcomes, separate gameplay assessment.', 'Yes, subject to semantic/integrity/budget gates.',
'Yes; known answer replaced by generic uncertainty stops; explicit substantive-answer experiments also stop on uncertainty.',
'Yes; complete-next-interaction admission reserves two slots; actual controller regression passes.',
'Component mocked control completes. Exact requested HTTP follow-up does not: no authored topic selected. Explicit patrol HTTP wording selects the topic, but full evaluator conservatively flags discovered-clues overlay authority.',
f'New failing existing tests: {len(new)}; exact comparisons and messages are preserved.',
'No; zero live-provider requests.',
'Not ready to claim successful live testing of the exact two-turn script. Investigate the recorded follow-up selection limitation offline first; separately review the preexisting overlay-authority stop. No PR-PLAY-28 started.'
]
write('PR_PLAY_27_FINAL_VERDICT.md','# PR-PLAY-27 final verdict\n\n**B — PARTIALLY REPAIRED / PARTIAL**\n\nOriginal expression and recovery classification repaired, with a remaining exact-follow-up continuity limitation and conservative overlay stop.\n\n'+'\n\n'.join(f'{i}. {a}' for i,a in enumerate(answers,1))+'\n\nStop for external review. No commit, push, live requests or automatic next pass.\n')
# Per-pass diffs, not cumulative dirty-worktree diffs.
for source,before in [('game/expressive_dialogue.py','expressive_dialogue.before.py'),('tools/playtest/gameplay.py','gameplay.before.py'),('tools/playtest/runner.py','runner.before.py')]:
 target=P/'source_diffs'/Path(source+'.diff');target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(''.join(difflib.unified_diff((P/before).read_text(encoding='utf8').splitlines(True),Path(source).read_text(encoding='utf8').splitlines(True),fromfile='before/'+source,tofile='after/'+source)),encoding='utf8')
 target=P/'source_snapshot'/source;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
target=P/'source_snapshot/tests/test_pr_play_27_expression_recovery.py';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile('tests/test_pr_play_27_expression_recovery.py',target)
new_test=Path('tests/test_pr_play_27_expression_recovery.py')
target=P/'source_diffs/tests/test_pr_play_27_expression_recovery.py.diff';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(''.join(difflib.unified_diff([],new_test.read_text(encoding='utf8').splitlines(True),fromfile='/dev/null',tofile=str(new_test))),encoding='utf8')
# Deliberately selected evidence only: no .env, credentials, repository or old archives.
files=[f for f in P.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix not in {'.zip','.pyc'}]
secret_hits=[]
for f in files:
 text=f.read_text(encoding='utf8',errors='replace')
 if re.search(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}',text): secret_hits.append(str(f))
if secret_hits: raise RuntimeError('Credential-like values found: '+str(secret_hits))
write('credential_scan.json',json.dumps({'files_scanned':len(files),'credential_like_hits':secret_hits,'excluded':['.env','authentication material','unrelated repository files','unrelated historical artifacts']},indent=2))
files=[f for f in P.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix not in {'.zip','.pyc'} and f.name not in {'archive_path.txt','archive_verification.json','MANIFEST.json'}]
write('MANIFEST.json',json.dumps({'pass':'PR-PLAY-27','live_provider_requests':0,'files':[{ 'path':str(f.relative_to(P)), 'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]},indent=2))
stamp=subprocess.check_output(['powershell','-NoProfile','-Command',"[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow, 'Eastern Standard Time').ToString('yyyyMMdd-HHmmss')"],text=True).strip()
archive=Path('handoff')/f'CURRENT_REVIEW({stamp}).zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in [*files,P/'MANIFEST.json']: z.write(f,str(Path('pr_play_27')/f.relative_to(P)))
with zipfile.ZipFile(archive) as z:
 bad=z.testzip();names=z.namelist()
 if bad:raise RuntimeError(bad)
write('archive_path.txt',str(archive.resolve()))
write('archive_verification.json',json.dumps({'path':str(archive.resolve()),'exists':archive.exists(),'entries':len(names),'testzip':bad,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2))
print(json.dumps({'baseline':counts(baseline),'existing':counts(current),'focused':counts(focused),'new_regressions':len(new),'archive':str(archive.resolve())},indent=2))
