"""Assemble baseline evidence and authorized reports/handoff; no runtime edits."""
import hashlib, json, subprocess, xml.etree.ElementTree as ET, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
ID='pr_play_baseline_provenance'; RP=ROOT/'development/campaigns/product_realization'/ID
AP=OUT.relative_to(ROOT).as_posix(); RPR=RP.relative_to(ROOT).as_posix()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(n,d): (OUT/n).write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def report(n,text): (RP/n).write_text(text.strip()+'\n',encoding='utf-8')
manifest=read(OUT/'source_manifest.json')
manifest['snapshot']={'path':AP+'/current_source_snapshot.zip','sha256':sha(OUT/'current_source_snapshot.zip'),
 'scope':'Executable game, tests, static, prompts and dependency/test configs. Data is hash-only in source_manifest.json; synthetic test fixtures construct runtime state. Not a full campaign backup.'}
with zipfile.ZipFile(OUT/'current_source_snapshot.zip') as z:
    assert z.testzip() is None
    for n in z.namelist(): assert hashlib.sha256(z.read(n)).hexdigest()==manifest['files'][n],n
    manifest['snapshot']['verified_members']=len(z.namelist())
dump('source_manifest.json',manifest)
changed=[p for p,h in manifest['files'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
assert not changed,changed
prior=read(ROOT/'artifacts/pr_play_adjacent_regression_recovery/failures.json')
priorids={r['nodeid'] for r in prior}
oldmatrix=read(ROOT/'artifacts/pr_play_adjacent_regression_recovery/classification_matrix.json')
oldrows={r['test']:r for r in oldmatrix['failures']}
runs=[]; classifications=[]
for label,folder,junit in [('focused_expanded',OUT,'baseline_junit.xml'),('authority_and_known_failures',OUT/'authority','recovery_junit.xml')]:
    root=ET.parse(folder/junit).getroot().find('testsuite')
    cases=root.findall('testcase'); failures=read(folder/'failures.json')
    nodes=read(folder/'collected_nodes.json')
    assert len(cases)==len(nodes)
    failing={r['nodeid']:r for r in failures}
    results=[{'nodeid':n,'outcome':'failed' if c.find('failure') is not None or c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed','duration_seconds':float(c.get('time','0'))} for n,c in zip(nodes,cases)]
    integrity=read(folder/'execution_integrity.json')
    assert not integrity['changed'] and not integrity['added'] and not integrity['network_attempts_blocked']
    runs.append({'name':label,'command':read(folder/'command.json'),'junit':str((folder/junit).relative_to(ROOT)).replace('\\','/'),
      'counts':{'tests':int(root.get('tests')),'passed':len(cases)-len(failures)-int(root.get('skipped')),'failed':len(failures),'errors':int(root.get('errors')),'skipped':int(root.get('skipped'))},'results':results,'integrity':integrity})
    for node,f in failing.items():
        if node in priorids:
            category='known obsolete assertion' if oldrows[node]['classification'].startswith('C') else 'known publication-authority defect'
        elif 'perception_narration_authority' in node:
            category='newly observed obsolete assertion (PR-PLAY-67 public resolution)'
        elif 'test_raw_chat_stub_preserves_valid' in node:
            category='newly observed response mismatch; historical origin unverified'
        elif 'test_pr_play_79df3_classification.py' in node:
            category='newly observed authority/publication mismatch; historical origin unverified' if 'This portal is not running' not in f['traceback'] else 'newly observed TestClient portal exception; follow-up recorded separately'
        else: category='known unrelated failure (AT-OPT-06 recorded KeyError)'
        classifications.append({'nodeid':node,'classification':category,'phase':f['phase'],'traceback':f['traceback']})
followdir=OUT/'authority_followup'
fr=ET.parse(followdir/'recovery_junit.xml').getroot().find('testsuite')
followup={'command':read(followdir/'command.json'),'counts':dict(fr.attrib),'failures':read(followdir/'failures.json'),'integrity':read(followdir/'execution_integrity.json')}
assert not followup['integrity']['changed'] and not followup['integrity']['network_attempts_blocked']
dump('test_results.json',{'milestone':ID,'source_manifest_identity':manifest['manifest_identity_sha256'],'runs':runs,'failure_classifications':classifications,'targeted_followup':followup,
 'same_original_twelve':set(read(OUT/'failures.json')[i]['nodeid'] for i in range(12))==priorids,
 'live_provider_calls':0,'not_run':['full suite','live gameplay','Gameplay Benchmark','independent generalization','frozen holdout (existing fixtures not rewritten)']})
events=read(OUT/'http_capture.json')
specs=[('hidden_brass_token','test_general_hidden_object_is_not_revealed_by_naming','A brass token is sealed under the grain hopper; naming does not disclose or retrieve it.'),
 ('shipping_record','test_general_abstract_reference_does_not_become_physical','Only the abstract statement: I checked the shipping records this morning. No inspectable ledger, crews, or Glassport destination is established.'),
 ('schedule','test_general_failed_inspection_creates_no_world_facts','No authored glass kiln schedule exists. The mill-loft scene establishes a hopper, skylight, maize sacks and tariff slate; no four-overseer roster.')]
defects=[]
for ident,suffix,facts in specs:
    node=next(n for n in events if n.endswith('::'+suffix)); ev=events[node][0]; raw=ev['raw_before_projection'][0]
    gm=raw['gm_output']; res=raw['resolution']; before=ev['before']; after=ev['after']
    state={}
    for domain,keys in [('character',['inventory']),('world',['npcs','clues','world_state']),('session',['scene_runtime','lead_registry','clue_knowledge','last_publication'])]:
        state[domain]={k:{'before':before.get(domain,{}).get(k),'after':after.get(domain,{}).get(k)} for k in keys}
    defects.append({'id':ident,'nodeid':node,'established_facts':facts,'request':ev['request'],'published_text':ev['response']['gm_output']['player_facing_text'],
      'resolution':res,'accepted_response':gm.get('metadata',{}).get('accepted_response'),
      'skipped_semantic_mutators':gm.get('metadata',{}).get('skipped_semantic_mutators'),
      'state_before_after':state,'character_unchanged':before['character']==after['character'],
      'world_npcs_unchanged':before['world'].get('npcs')==after['world'].get('npcs'),
      'capture_reference':AP+'/http_capture.json#'+node+'[0]','capture_sha256':sha(OUT/'http_capture.json'),
      'fixture_path':'tests/test_referenced_surface_grounding_inspection_resolution.py','fixture_sha256':manifest['files']['tests/test_referenced_surface_grounding_inspection_resolution.py'],
      'historical_classification':'Historical origin unresolved — closed','attribution_possible':False,
      'confidence':'High in demonstrated current defect and evidence insufficiency; no confidence assigned to a causal origin.',
      'historical_evidence_available':['post-repair matching captures and JUnit','reconstructed overlay equality','partial archives and implementation diff','pre-repair conversational trace unrelated to these three inputs'],
      'historical_evidence_missing':['coherent complete pre-repair dirty source/test/dependency snapshot','authenticated pre-repair execution of this fixture'],
      'production_path':['game/api.py','game/conversational_orchestration.py','game/referenced_surface.py','game/exploration.py','game/immutable_valid_response.py','game/perception_grounding.py','game/player_http_projection.py']})
    assert res['state_changes']=={} and defects[-1]['character_unchanged']
dump('publication_defects.json',{'provider_free':True,'existing_fixtures_preserved':True,'defects':defects})
dump('historical_attribution.json',{'milestone':ID,'snapshot':'unavailable (surviving evidence incomplete)','stopping_condition':'B',
 'decision':'Historical attribution unresolvable from available evidence. Closed; do not initiate another reconstruction cycle.',
 'defects':[{k:r[k] for k in ['id','nodeid','published_text','historical_classification','attribution_possible','confidence','historical_evidence_available','historical_evidence_missing']} for r in defects]})
controls={n:e for n,e in events.items() if 'test_pr_play_post_npc_handoff.py' in n}
dump('conversational_controls.json',{'passed_tests':7,'captures':controls,'limitations':['T04/T06 do not complete physical actions','T05 stock jab sentence remains','Other twelve-turn scenario inadequacies remain; full scenario not rerun']})
counts=[r['counts'] for r in runs]; total=sum(c['tests'] for c in counts); passed=sum(c['passed'] for c in counts); failed=sum(c['failed'] for c in counts)
result_line=f"{total} tests: {passed} passed, {failed} failed, zero errors/skips."
assert len(controls)==7
repair='T04 local-object approach, T05 authorized notice disclosure, T06 unsupported physical-action routing and T09 grounded notice recall pass. Explicit NPC repetition, genuine NPC follow-up, unknown destination, hidden information, genuine travel and publication refusal remain verified in seven unchanged focused HTTP tests.'
limits='T04/T06 lack meaningful physical completion. T05 still appends the unrelated stock jab sentence. Other turns in the twelve-turn scenario remain inadequate; that full scenario was not rerun. No playability, full-suite, live-model or independent-generalization claim is made.'
report('SUMMARY.md',f'''# PR-PLAY Baseline Provenance Closure & Current-State Freeze

Milestone: `{ID}`. Client date: 2026-11-08. **Cycle verdict: A/PASS for bounded provenance closure and current baseline capture.** This is not gameplay acceptance.

Historical snapshot unavailable: surviving evidence is incomplete. Condition B reached after 32 archive copies and 11 Git candidates; no coherent authenticated pre-repair dirty source/test/dependency state. Historical attribution is **unresolvable from available evidence** and closed. Do not initiate another reconstruction cycle.

| Defect | Final historical classification | Current status |
|---|---|---|
| Hidden brass token | Historical origin unresolved — closed | Retrieval prose contradicts authoritative non-retrieval |
| Shipping record | Historical origin unresolved — closed | Unsupported eight crews / Glassport published |
| Schedule | Historical origin unresolved — closed | Unsupported four new overseers published |

**Current baseline established.** Branch `{manifest['branch']}`, HEAD `{manifest['head']}`, dirty state preserved. {len(manifest['files'])} source/test/data/configuration hashes; executable source/test snapshot and local dependency versions retained. {result_line} Main expanded run: {counts[0]}; authority/known-failure run: {counts[1]}. Same original twelve failures: nine obsolete assertions and three publication defects. Expanded selection additionally exposes three obsolete public-resolution assertions, one response mismatch and four authority-slice failures (one initially a TestClient portal exception); three documented unrelated KeyErrors recur. A targeted four-test follow-up is separately recorded, without inflating the unique-test total.

{repair}

{limits}

**Exactly one next action: Option A — Publication-authority boundary investigation.** Investigate consequential-claim acceptance before immutable sealing, with structured-resolution/visibility/commit signals and descriptive-improvisation negative controls. No repair implemented or authorized by this recommendation. Live provider calls: **0**. No campaigns, commits or pushes. Stop after verified handoff. Reports and machine evidence listed in INTEGRITY.md; final archive seal recorded externally in `{AP}/archive_verification.json` and `archive_sha256.txt`.
''')
report('PROVENANCE_SEARCH.md',f'''# Bounded provenance search

Milestone `{ID}`. **Condition B: no authentic sufficiently complete pre-repair development snapshot. Search closed.**

Examined only repository review archives, named historical handoff packages, preserved repair diff/source-comparison manifests, predecessor test/capture evidence, local Git references/reflogs/unreachable-object inventory, and the explicitly named `%TEMP%/pr_play_adj_audit` path. No unrelated user-directory search, network recovery, branch reconstruction, historical execution or mixed-source execution occurred.

Machine inventory: `{AP}/historical_archives.json` records 32 archive copies (some duplicates), full SHA-256, internal campaign summary and presence/hash of eight required source/test modules. Every archive lacks at least one of this minimum set, so none meets completeness. Names and ZIP timestamps were not used as proof. Immediate pre-repair post-optimization and AT-OPT-06 packages contain reports/measurements, not complete source. Post-NPC packages contain an implementation diff and after-edit test file/results, not a pre-edit dirty-tree capture. Recovery archives are later evidence.

`git_provenance.json` contains exact read-only commands: show-ref, log -12, reflog --all, stash list, fsck --full --no-reflogs --unreachable. No current stash exists. `git_candidate_assessment.json` examines eight unreachable commits, two Codex checkpoint refs and HEAD. All lack the later player HTTP projection and authored-travel definition required by the current imports. The unreachable inventory contains 14,946 blobs, 61 trees and eight commits. Unattached blobs/trees have no capture time or binding to a coherent pre-repair development state. Do not assemble them into a historical hybrid. Codex checkpoint refs are tree objects rather than normal dated commits; blank commit-time fields do not establish a capture time.

`local_snapshot_inventory.json` records whether the exact earlier temporary package survives. Its saved overlay manifest expressly describes current source plus selected HEAD files and manual deletion of handoff insertions. Even if present, it is a reconstructed approximation. Equality of its three failure responses supports a hypothesis, not authenticated preexisting attribution.

| Authentication requirement | Finding |
|---|---|
| Source-state identity | HEAD identifies a much older committed state; no exact dirty pre-repair identity |
| Capture time | Dated archives/commits identify their artifacts, not a complete pre-repair working tree |
| Relationship to repair | Diff identifies edits; traces distinguish before/after intent behavior |
| Relevant production files | No surviving pre-repair coherent complete set |
| Relevant tests | Current and post-repair tests/results survive; exact historical environment missing |
| Dependencies | Current versions captured; no complete compatible historical dependency/source binding |
| Coherent state | No authenticated aggregate manifest for the pre-repair dirty tree |
| Predates repair | Some evidence predates repair, but does not capture all required files |
| Integrity | ZIP/diff hashes establish surviving bytes only |

Relevant earlier evidence read: recovery SUMMARY, FAILURE_INVENTORY, BASELINE_RECONSTRUCTION, CONTRACT_ANALYSIS, NEXT_STEP_DECISION, HANDOFF_RECOVERY and targeted verification; previous audit reports/overlay/captures; post-NPC SUMMARY, ROOT_CAUSE, REGRESSION_RESULTS, INTEGRITY, routing contract, diff and JUnit; PR-PLAY-67 public-response contract; AT-OPT-06 regression/CI definitions. Local CI configuration is generic replay/governance evidence, not a pre-repair dirty-worktree run. Earlier 118 passing tests are a different selection from the twelve failures.

Stopping decision: all bounded source classes reasonably capable of preserving this state have been evaluated. Authentic baseline requirements are unmet. Historical attribution is unresolvable from available evidence; no further historical-reconstruction cycle is warranted. The new current baseline permits future development comparison.
''')
hist=['# Historical attribution — final closure','',f'Milestone `{ID}`. Current manifestations are demonstrated, historical origins are closed as unresolved. No newly introduced or preexisting cause is confirmed.']
for r in defects:
    hist += ['',f"## {r['id']}",'',f"Published: {r['published_text']}",f"Established authority: {r['established_facts']}",f"Current resolution: investigate; authority `{r['resolution']['metadata']['referenced_surface_authority']}`; `state_changes={{}}`; character unchanged. NPC roster unchanged: {r['world_npcs_unchanged']}.",
      'Historical evidence: post-repair reproduction, partial archives/diff and matching reconstructed-overlay capture. Missing: authenticated complete pre-repair dirty source/test/dependency snapshot and a tied run of this input.',
      '**Final classification: Historical origin unresolved — closed.** Attribution impossible from available evidence. Confidence high in current reproduction and evidentiary insufficiency; causal origin unknown. Temporal correlation and reconstructed equality do not prove causation.']
hist += ['',f'Exact fixture nodes, acceptance records, state before/after, full published text and references: `{AP}/publication_defects.json`; machine decision: `historical_attribution.json`. No historical execution was justified.']
report('HISTORICAL_ATTRIBUTION.md','\n\n'.join(hist))
selections='\n\n'.join('```json\n'+json.dumps(r['command'],indent=2)+'\n```' for r in runs)
failure_table='\n'.join(f"| `{r['nodeid']}` | {r['classification']} |" for r in classifications)
report('CURRENT_BASELINE.md',f'''# Current development baseline

Milestone `{ID}`. **Established for the exact selections below.** Capture `{manifest['captured_at_utc']}`; branch `{manifest['branch']}`; HEAD `{manifest['head']}`. Worktree dirty. Source aggregate SHA-256 `{manifest['manifest_identity_sha256']}`. Source snapshot SHA-256 `{manifest['snapshot']['sha256']}`. Local dependency versions recorded; no installation or provider changes.

{result_line} First run {counts[0]['passed']}/{counts[0]['tests']} passed, {counts[0]['failed']} failed. Second run {counts[1]['passed']}/{counts[1]['tests']} passed, {counts[1]['failed']} failed. Exact collected node IDs/outcomes/durations and source binding are in `test_results.json`; failures retain complete tracebacks. Sequential pytest execution, isolated runtime storage, test fixture model stubs, production provider dispatch disabled, nonloopback network blocked. Loopback remains available for Windows asyncio/TestClient. Both runs report no protected changes, additions or external connection attempts.

## Selections and commands

Run from repository root with `.\\.venv\\Scripts\\python.exe artifacts/{ID}/run_baseline.py`, then `run_authority.py`. These evidence scripts apply the recorded flags and guards before imports and call pytest with these exact arguments. Basetemp directories are cycle-owned disposable paths; historical output paths must not be reused as basetemp.

{selections}

The original 176 adjacent tests remain 164 passed / 12 failed; all seven post-NPC controls pass. The two expanded immutability/perception modules add 52 tests: 48 pass / four fail. The separate formerly green 118-test authority/publication selection is now 114 passed / four failed; three explicitly selected known KeyError tests also fail, making 114/121 passing in that run. One call-phase failure is a TestClient portal exception. The four newly failing authority nodes were rerun once sequentially with captures; all four failed again, including the repeated TestClient portal exception; exact results: `{json.dumps(followup['counts'])}`. Follow-up commands/results/captures are under authority_followup and in test_results.json. This is current baseline evidence, not proof of which prior edit caused the differences. AT-OPT-06 same-scene/real-transition protection remains covered by the original focused slice. Accepted-text retry/fallback/preservation and sensory-grounding unit controls pass in their exercised cases, subject to the failures listed below.

## Failure classifications

| Exact assertion/test identity | Baseline classification |
|---|---|
{failure_table}

The nine original and three newly observed public-resolution failures concern stopping assertions conflicting with PR-PLAY-67. Assertions after those stopping points remain unexecuted; prose quality is not accepted by classification. The new raw-chat mismatch expects a stew-cost inability sentence and receives `Tavern Runner mutters, "Word is, hot stew and rumors for coin."` Historical origin and full semantic implications are unverified; it is not attributed to this cycle or the conversational repair. Additional authority failures involve duplicate-refusal publication, two-refusal progression (initial portal exception), save/reload refusal-log classification, and fallback last-publication behavior. The follow-up preserves exact responses/state and distinguishes repeated mismatches from the initial transport exception; these are unresolved current-baseline findings, not confirmed new regressions. The three known unrelated failures are the recorded provider_context_projection, gm_only and social_context KeyErrors. No expectation was changed.

## Current behavior and limits

{repair}

{limits}

Passing behavior, obsolete assertions, known publication defects, known unrelated failures, newly observed failures and unverified behavior are separate categories in machine evidence. Provider-free stubs demonstrate production publication-path behavior, not the frequency of live-model invention. No full frozen holdout rerun is claimed; frozen fixtures/results remain preserved. A failing baseline is usable when source identities and exact failure identities are preserved; it is not acceptance of those defects.
''')
relevant=['game/api.py','game/gm.py','game/conversational_orchestration.py','game/conversational_continuity.py','game/intent_parser.py','game/referenced_surface.py','game/exploration.py','game/perception_grounding.py','game/immutable_valid_response.py','game/player_http_projection.py','game/narrative_planning.py','game/state_authority.py','tests/test_pr_play_post_npc_handoff.py','tests/test_referenced_surface_grounding_inspection_resolution.py','tests/test_pr_br_continuation18_immutable_boundary.py','tests/test_perception_narration_authority_audible_non_invention.py']
relevant += manifest['configuration_paths']
table='\n'.join(f'| `{p}` | `{manifest["files"][p]}` |' for p in relevant if p in manifest['files'])
report('SOURCE_MANIFEST.md',f'''# Source manifest

Milestone `{ID}`. Branch `{manifest['branch']}`. HEAD `{manifest['head']}`. Capture time `{manifest['captured_at_utc']}`. Dirty working tree preserved, not reset to HEAD.

Complete machine manifest: `{AP}/source_manifest.json`, {len(manifest['files'])} file hashes; aggregate sorted-path/hash identity `{manifest['manifest_identity_sha256']}`. Complete modified-tracked/untracked path status: `entry_git_status.txt`; post-cycle status in `final_git_status.txt`. Relevant untracked game/tests/config files are included in the hash map; the status file disambiguates them from tracked modifications. The existing configuration/dependency files are hashed, local installed versions recorded in `dependency_versions.json`.

| Relevant file | SHA-256 |
|---|---|
{table}

Executable source/test snapshot: `{AP}/current_source_snapshot.zip`, {manifest['snapshot']['verified_members']} members verified against the manifest, SHA-256 `{manifest['snapshot']['sha256']}`. This external evidence snapshot is intentionally not recursively nested in the standard review ZIP; selected canonical modules and complete source manifest are packaged. Retain the snapshot alongside the evidence. Runtime data is hash-only; tests seed their own synthetic states. No environment/credential files, virtualenv or Git database were copied. This is a current comparison baseline, not an authenticated historical state or full campaign backup.

Both test runs hash-check 1,292 game/test/data/static/prompt files unchanged; final seal also rechecks all {len(manifest['files'])} manifest paths including configuration. Existing historical archives remain at entry SHA-256. Only new cycle evidence/reports and authorized handoff surfaces change.
''')
report('PUBLICATION_AUTHORITY_RISK.md','''# Publication-authority risk

The three production HTTP reproductions publish accepted initial-generation stubs: hidden-token retrieval, eight shipping crews bound for Glassport, and four new overseers. Each authoritative resolution has empty state_changes. Character/inventory remains unchanged. Schedule NPC/lead assertions pass before the prose assertion; there is no demonstrated canonical acquisition or new roster. The demonstrated failure is consequential player-facing prose diverging from structured authority. Future player decisions may rely on the prose; actual inventory grant, world-fact promotion, later cascading corruption and live-model frequency are not demonstrated here.

`publication_defects.json` retains authoritative resolution/hints, accepted_response, skipped mutators, published text and relevant state before/after. The three acceptance records report initial_generation, immutable=true, candidate_accepted, authority_result=accepted, hard_valid=true, empty reasons/claim results/proposed facts, and grounding_result=not_a_replacement_trigger. That is evidence of insufficient rejection in these exercised cases, not proof that every unsupported claim bypasses all validators.

`game/immutable_valid_response.py:run_preserve_if_valid` validates a candidate, then `seal_accepted_response` binds accepted text when hard_valid. `leave_text_unchanged` and the seal preserve that text downstream. `game/perception_grounding.py:apply_perception_non_invention_to_gm` checks leave_text_unchanged before building correction evidence. The captured accepted-response metadata records this skipped mutator. `game/api.py` restores accepted text, processes separately authorized effects, gates/records publication and projects the final player body with `game/player_http_projection.py`. Empty public resolution is a privacy contract, so internal resolution/log/capture fields—not public DTO metadata—are the authority evidence. `effects_allowed` is not item-acquisition proof; structured resolution/world/inventory commit owners remain necessary.

Descriptive improvisation includes mundane light, texture, gestures, cadence, ordinary dialogue and incidental sensory description when it makes no consequential state claim. It need not all be authored in advance. By contrast, pocketing a hidden item asserts acquisition; named crews/destination or an overseer count in inspected records purports to establish actionable world facts. These examples conflict with explicit hidden/abstract/unsupported target authority. They are not excused as flavor.

Narrowest plausible next boundary: candidate consequential-claim acceptance immediately before immutable adoption/sealing, using existing resolution, visibility/discovery, target authority, declared-claim/decision audit and committed-outcome signals. Investigate why a candidate with these contradictions is accepted and how rejection/regeneration or an authorized response can occur before publication while preserving accepted-text immutability. Do not add an unconditional downstream rewrite or universal refusal policy.

Negative controls should retain harmless sensory improvisation, authorized clue disclosure, supported world facts, legitimate speech/repetition, real travel, failed mechanics without invented success, sealed valid-response identity and operational-refusal last-publication protection. Existing fixtures suffice to preserve the three defects; no new production mechanism, prompt change or repair is implemented in this cycle. Upstream ownership and a minimal remedy remain investigative questions for Option A.
''')
report('BASELINE_PROCEDURE.md',f'''# Lightweight future baseline procedure

Use existing Git/file-hash tools, pytest JUnit and standard review generator. This cycle's capture scripts are evidence, not a new baseline framework.

Before production edits:

1. Read latest NEXT_SESSION and source authority. Record branch, HEAD, full porcelain status; preserve dirty work.
2. Hash the relevant production/test/config dependency closure, including relevant untracked source. Save current source bytes or an explicit scoped snapshot without environment values; record capture time and aggregate hash.
3. Save the exact node/module selection, Python/dependency versions, relevant nonsecret flags and isolated storage paths. Run provider-free focused baseline tests sequentially under live-model/network/storage guards.
4. Preserve JUnit, node outcomes, stopping assertions/tracebacks and any relevant state-before/after/published text. Classify known defects, obsolete assertions, unrelated/newly observed failures and unverified behavior separately.
5. Seal source/evidence hashes before editing. HEAD alone and a partial implementation diff are insufficient when the worktree is dirty.

After production edits:

1. Run the identical focused selection and flags; compare exact assertion identities and authority/publication behavior, not only failed counts.
2. Identify additions/disappearances in failure identities. Do not label a failure preexisting solely because an invented hybrid reproduces it. Preserve limitations and never silently update frozen fixtures or expectations.
3. Preserve post-edit source hashes, scoped diff and relevant untracked source, dependency compatibility and before/after evidence. Distinguish focused reproduction, related controls, independent generalization, regression and gameplay acceptance.

Handoff integrity:

1. Prepend concise outcome to authoritative docs/NEXT_SESSION.md, retaining all prior entries. Point to canonical reports/evidence and exactly one next action.
2. Generate the standard Markdown/manifest/ZIP together directly to handoff using explicit configuration; do not reuse a stale ZIP or copy only one surface from another export.
3. Copy the just-generated ZIP to CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip using America/New_York time. Reopen that exact file and verify cycle identity, all required reports, internal manifest member hashes, source/evidence identities and packaged NEXT_SESSION bytes.
4. Compare stable ZIP to timestamped ZIP; check exclusions/omissions. Save validation evidence and SHA-256 externally after sealing. A final archive cannot contain its own final cryptographic hash without circularity. Include a pre-seal validation protocol in the package and retain the final seal beside it.
5. Record the exact archive path/hash and stop at the authorized scope. A current reproducible red baseline permits comparison; it does not normalize known gameplay defects. This historical attribution question is closed and must not trigger another reconstruction cycle.
''')
report('NEXT_STEP_DECISION.md','''# Next development action

**Exactly one selected action: Option A — Publication-authority boundary investigation.**

The three demonstrated consequential publication defects remain the highest-priority concern, particularly retrieval prose without inventory authority. Current source/behavior can now be captured and compared, so historical incompleteness does not justify Option C. No authenticated before/after evidence establishes a repair-induced regression, so Option B is not selected.

Investigate candidate acceptance and immutable adoption: where unsupported consequential claims pass, which existing resolution/discovery/commit/claim signals can reject or correct them before publication, and how legitimate descriptive improvisation and accepted-text identity remain protected. Preserve the three unchanged HTTP reproductions and the relevant negative controls. This is a recommendation, not implementation of that investigation or a repair.

Historical origin of all three defects is unresolved — closed. The targeted conversational improvements remain verified within their existing fixtures, but this closure does not upgrade the game to playable or erase publication defects. Newly observed raw-chat stew response mismatch is recorded separately; causal origin unverified.

Deferred: T05 stock-sentence correction, meaningful T04/T06 physical completion, other twelve-turn shortcomings, obsolete expectation migration, unrelated KeyErrors, new response mismatch investigation, full suite, independent generalization, live evaluation, prompt/model/budget changes, PR-PLAY-80 and AT-OPT-07. Stop after baseline closure and verified archive; do not automatically begin another cycle.
''')
report('INTEGRITY.md',f'''# Integrity

Milestone `{ID}`. A/PASS for evidence closure. Existing dirty source, tests, runtime data, prompts, configs and historical evidence preserved. Branch/HEAD unchanged. Both sequential executions report 1,292 protected files unchanged, zero protected additions and zero external network attempts. Final seal rechecks all {len(manifest['files'])} source manifest paths and entry archive hashes. Source snapshot contents independently match manifest hashes.

Production changes: none. Test/expectation/frozen-fixture changes: none. Live provider calls: **0**. No campaign openings, live gameplay, network recovery, dependency installation, prompt/model/budget changes, commits, pushes, resets, clean, stash or revert. Synthetic already-started test sessions are isolated beneath development/tmp. The working tree was never used as a historical checkout.

Created reports under `{RPR}/`: SUMMARY.md, PROVENANCE_SEARCH.md, HISTORICAL_ATTRIBUTION.md, CURRENT_BASELINE.md, SOURCE_MANIFEST.md, PUBLICATION_AUTHORITY_RISK.md, BASELINE_PROCEDURE.md, NEXT_STEP_DECISION.md, INTEGRITY.md.

Created evidence under `{AP}/`: source manifest/status/source snapshot/dependency versions; archive and Git provenance/candidate assessment/local snapshot inventory; exact commands, collected nodes, JUnit and complete test failures for both runs; full HTTP before/after/pre-projection captures; publication-defect references, authority and inventory summaries; historical attribution JSON; conversational controls; test-result JSON; execution/source preservation records; review configuration and capture/report/seal scripts. Exact file inventory is `files_created.json` after sealing. No broad tooling framework was added.

Authorized updates: prepend docs/NEXT_SESSION.md preserving the entire former content; regenerate handoff/CURRENT_REVIEW.md, REVIEW_MANIFEST.json and CURRENT_REVIEW.zip; create a fresh timestamped handoff archive. No existing dated archive is overwritten. Final verification opens both stable and dated ZIPs, validates internal cycle/reports/handoffs/source manifests and canonical member hashes, checks no unrequested/sensitive payload or unexplained omissions (identical-content deduplication is recorded), and records external `archive_verification.json`, `archive_contents.txt`, `archive_sha256.txt`. Final seal files are external to avoid circular self-hashing. A packaged validation protocol describes these checks.
''')
entry=(OUT/'entry_next_session.md').read_bytes()
header=f'''# NEXT_SESSION — PR-PLAY Baseline Provenance Closure (2026-11-08)

**A/PASS for provenance closure and current-state baseline.** Milestone `{ID}`. Branch `{manifest['branch']}`; HEAD `{manifest['head']}`; dirty work preserved. No production/test edits, campaigns, commits or pushes. Live provider calls: **0**.

Bounded search closed under Condition B: 32 archive copies and 11 Git candidates do not authenticate a complete pre-repair dirty source/test/dependency state. All three publication defects (hidden-token retrieval, Glassport crews, four overseers) are **Historical origin unresolved — closed**. Do not initiate another historical reconstruction cycle. This supersedes the prior handoff's baseline prerequisite; it does not relabel the defects as harmless or prove a causal origin.

Current baseline established: {len(manifest['files'])} source/test/data/config hashes, executable source/test snapshot, local dependency versions and exact provider-free test selections. {result_line} Original adjacent slice remains 164/176 passing with the same nine obsolete assertions and three publication defects; seven handoff controls pass. Expanded selection adds three obsolete resolution assertions, one raw-chat stew-response mismatch and four authority-slice failures (one initial portal exception), all with unverified historical origin; three known unrelated KeyErrors recur. A four-test follow-up is recorded separately. Exact IDs, assertions and categories are in test_results.json and CURRENT_BASELINE.md.

{repair} {limits}

**Exactly one next action: Option A — Publication-authority boundary investigation.** Examine consequential-claim acceptance before immutable sealing, preserving descriptive improvisation and valid-response identity. Do not implement it from this handoff. Defer T05 repair and other gameplay/expectation fixes. Do not open PR-PLAY-80, AT-OPT-07 or live play.

Reports: `{RPR}/`. Evidence: `{AP}/`. Minimum reading: SUMMARY, HISTORICAL_ATTRIBUTION, CURRENT_BASELINE, PUBLICATION_AUTHORITY_RISK, NEXT_STEP_DECISION; source_manifest.json, test_results.json and publication_defects.json. Source snapshot is retained alongside evidence (not nested in the review ZIP). Final verified archive path and SHA-256: `{AP}/archive_sha256.txt`; verification: archive_verification.json.

---

'''
(ROOT/'docs/NEXT_SESSION.md').write_bytes(header.encode('utf-8')+entry)
dump('archive_validation_protocol.json',{'milestone':ID,'phase':'pre-seal protocol; final outcome is in external archive_verification.json',
 'required_checks':['open exact new timestamped and stable ZIP','internal campaign identity','nine required reports','source/evidence manifest hashes','packaged NEXT_SESSION current cycle and preserved suffix','every canonical member byte/hash','no unexplained omissions (identical-content deduplication allowed)','entry source and historical ZIP preservation','stable ZIP identity','external SHA-256 seal'],
 'source_snapshot':manifest['snapshot']})
config=read(ROOT/'artifacts/pr_play_adjacent_regression_recovery/review_handoff.json')
config.update({'campaign_id':ID,'campaign_name':'PR-PLAY Baseline Provenance Closure & Current-State Freeze','campaign_date':'2026-11-08',
 'purpose':'Close historical attribution and freeze a trustworthy provider-free current baseline without production changes.','objective_status':'A/PASS',
 'executive_summary':f'Historical snapshot unavailable; all three publication origins unresolved — closed. Current baseline established. {result_line} Same original twelve failures retained; newly observed failures separately classified. No production/test changes; live provider calls 0.',
 'changes':{'production':[],'validation':['Unchanged provider-free focused/authority tests; exact failures preserved.'],'tooling':[],'documentation':['Nine closure reports; NEXT_SESSION prepended.'],'generated_artifacts':['Current source/behavior baseline and independently sealed review bundle.']},
 'testing':{'focused':str(counts[0]),'broader':str(counts[1]),'full_suite':'Not run','runtime_validation':'Provider-free synthetic already-started TestClient sessions. Seven repair controls pass.','model_runtime_boundary':'Live calls 0; nonlocal network blocked.','new_regressions':'None attributed; newly observed stew/authority mismatches, one initial portal exception and three additional obsolete assertions recorded. Four-test follow-up retained.','pre_existing_failures':'Nine original obsolete assertions, three publication defects of closed unresolved origin; three known unrelated KeyErrors.'},
 'decisions_requiring_human_review':['No human decision required to close provenance. Option A is the sole recommended future action; no repair begun.'],
 'known_problems':{'campaign_specific':['Historical source cannot be authenticated; attribution closed.'],'pre_existing':['Three consequential publication defects; T05 stock text; incomplete physical actions; unrelated KeyErrors; newly observed response mismatch.']},
 'missing_concepts':['Complete authenticated pre-repair dirty source capture unavailable; current baseline now recorded.'],
 'does_not_prove':['Historical causal origin; broad gameplay acceptance; live-model frequency; full suite; independent generalization.'],
 'recommended_next_step':'Option A — Publication-authority boundary investigation. Stop after baseline closure.',
 'self_contained_review_test':'Reopen new archive; verify cycle, nine reports, source/evidence identities and all canonical bytes. External archive seal is retained after packaging.',
 'primary_report':RPR+'/SUMMARY.md','supporting_files':[],'max_file_bytes':41943040})
supports=[p for p in RP.glob('*.md') if p.name!='SUMMARY.md']
supports += [p for p in OUT.rglob('*') if p.is_file() and 'review_export' not in p.parts and p.suffix in ('.json','.xml','.txt','.py') and p.name not in ('review_handoff.json','archive_verification.json','files_created.json')]
supports += [ROOT/'docs/NEXT_SESSION.md',ROOT/'docs/state_authority_model.md',ROOT/'development/campaigns/product_realization/pr_play_67/05_PLAYER_SAFE_RESPONSE_CONTRACT.md']
supports += [ROOT/p for p in relevant if p.startswith(('game/','tests/')) and (ROOT/p).exists()]
for p in sorted(set(supports)):
    config['supporting_files'].append({'path':p.relative_to(ROOT).as_posix(),'role':'baseline_evidence','why':'Supports source identity, exact baseline behavior or provenance closure.','behavioral_evidence':p.suffix in ('.json','.xml'),'human_review_required':False})
config['supporting_files'].append({'path':AP+'/review_handoff.json','role':'configuration','why':'Exact packaging selection and cycle configuration.','behavioral_evidence':False,'human_review_required':False})
dump('review_handoff.json',config)
print(json.dumps({'counts':counts,'total':result_line,'source_files':len(manifest['files']),'reports':len(list(RP.glob('*.md'))),'supporting_files':len(config['supporting_files'])}))
