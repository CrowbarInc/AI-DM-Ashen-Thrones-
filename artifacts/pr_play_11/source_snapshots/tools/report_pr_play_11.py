"""Explicit PR-PLAY-11 reports and secret-scanned standard review export."""
from datetime import datetime, timezone, timedelta
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from tools.build_review_handoff import build_handoff
from tools.validate_pr_play_09 import protected_hashes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/pr_play_11'
REPORTS = ROOT/'development/campaigns/product_realization/pr_play_11'
COMMAND = '.\\scripts\\run_live_playtest.ps1 -Scenario FiveTurnGameplay -Mode Live -AuthorizeLiveProvider -CaptureResponse'
SOURCES = ['game/gm.py','tests/test_pr_play_11_claim_authority.py',
    'tests/helpers/pr_play_11_entry_source.py',
    'tests/fixtures/pr_play_11/opening_context.json','tests/fixtures/pr_play_11/rejected_opening.json',
    'tools/validate_pr_play_11.py','tools/analyze_pr_play_11.py','tools/report_pr_play_11.py','docs/NEXT_SESSION.md']
CONFIRM = '''No live provider calls. No provider connectivity tests. No model changes.
No output-budget increases. No automatic retries. No broad semantic-validation relaxation.
No unsupported claim authorization. No unrelated gameplay changes. No unauthorized state mutations.
No new persistent gameplay structures. No experimental PR-EG integration.
Frozen ATGB baseline unchanged. No secrets included. No commit or push performed.'''


def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def report(name, title, body):
    (REPORTS/(name+'.md')).write_text('# '+title+'\n\nPR-PLAY-11 · 2026-10-30 America/New_York · evidence_scope: structural_only.\n\n'+body.strip()+'\n', encoding='utf-8')


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = {}
    runs = read('regression_runs.json')
    for lane in runs:
        p = OUT/(lane+'_regression.xml')
        if not p.exists():
            results[lane] = dict(classification='environment-blocked', timeout=runs[lane]['timeout'])
            continue
        suite = next(ET.parse(p).getroot().iter('testsuite'))
        counts = {k:int(suite.get(k,0)) for k in ('tests','failures','errors','skipped')}
        counts['passed'] = counts['tests']-counts['failures']-counts['errors']-counts['skipped']
        counts['failure_cases'] = [c.get('classname')+'::'+c.get('name') for c in suite if c.find('failure') is not None or c.find('error') is not None]
        results[lane] = counts
    write('test_summary.json', results)
    prior=json.loads((ROOT/'artifacts/pr_play_10/test_summary.json').read_text())
    prior_ids={n for v in prior.values() for n in v['failure_cases']}
    entry_ids=set(results['entry_claim_authority']['failure_cases'])
    prior_ids.update(entry_ids)
    failures=[dict(lane=k,test=n,classification='preexisting_failure' if n in prior_ids else 'unresolved')
        for k,v in results.items() for n in v.get('failure_cases',[])]
    write('failure_classification.json',dict(failures=failures,
        new_regressions=[f for f in failures if f['classification']!='preexisting_failure'],
        environment_blocked=['Two sandbox attempts interrupted before obtaining regression results; localhost-capable run is authoritative.'],
        comparison='Exact failure IDs against PR-PLAY-10; no frozen source attestation rewritten.'))
    assert all(f['classification']=='preexisting_failure' for f in failures), failures
    assert not any(r['timeout'] for r in runs.values()), runs
    assert set(results['claim_authority']['failure_cases']) == entry_ids
    for lane in ('overlay','diagnostics','harness','gameplay','hidden_faction'):
        assert results[lane]['failures']==results[lane]['errors']==0, (lane,results[lane])
    passed=sum(v.get('passed',0) for k,v in results.items() if k!='entry_claim_authority')
    failed=sum(v.get('failures',0) for k,v in results.items() if k!='entry_claim_authority')
    analysis=read('declaration_analysis.json')
    corpus=read('historical_corpus.json')
    authority=[
        dict(category='Authored-world facts',owner='gm_resolution_decision / authored scene, world, resolution',rule='Match existing realization claim by ID, semantic identity, exact text or bounded lexical coverage; preserve ceilings'),
        dict(category='Environmental realization',owner='authored evidence and narration audit',rule='Descriptive text is not automatically a resolution outcome. Authored content still needs coverage when consequential patterns match.'),
        dict(category='Bounded improvisation',owner='bounded_improvisation',rule='Existing low-consequence proposal policy; rumors remain claims, not world truth. No new authority.'),
        dict(category='Player-action outcomes',owner='resolution_contract and engine resolution',rule='Narration cannot resolve success, movement or player agency without engine evidence.'),
        dict(category='Mechanical decisions',owner='noncombat_resolution / combat / world',rule='Checks, damage, resources and movement require engine outcomes.'),
        dict(category='Consequential world changes',owner='world / state_authority',rule='NPC/faction/access/quest changes require existing authorized mutations; structured declarations cannot self-authorize.')]
    write('claim_authority_matrix.json',authority)
    bindings={
      'C1':('PASS','before_repair_replay.json; baseline.xml: historical production replay returned 422'),
      'C2':('PASS','Historical unchanged JSON remains 422 after guidance; conservative_generation.json returns 200 with source sentence'),
      'C3':('PASS','Both PR-PLAY-08 and 09 unchanged parsed captures replay with 200'),
      'C4':('PASS','C4.json: valid claim with source reference'),
      'C5':('PASS_WITH_CONTRACT_CLARIFICATION','C5.json: unsupported fact without evidence rejected; source ID is not mandatory if authored text matches'),
      'C6':('PASS_WITH_CONTRACT_CLARIFICATION','C6.json: nonexistent ID plus unsupported text rejected; source_id_fallback.json proves invalid ID alone is not fatal with exact authored evidence'),
      'C7':('PASS','C7.json: contradictory authored claim rejected'),
      'C8':('PASS','C8.json: existing authored environmental realization accepted'),
      'C9':('PASS','C9.json: sensory incidental accepted; hidden_faction regression includes bounded proposal acceptance/promotion controls'),
      'C10':('PASS','C10.json: unauthorized action outcome rejected'),
      'C11':('PASS','C11.json: unauthorized mechanical/resource decision rejected'),
      'C12':('PASS','C12.json: unauthorized consequential gate/faction change rejected'),
      'C13':('PASS','C13.json and narrative-authority/hidden regressions'),
      'C14':('PASS','C14.json: established authored provenance requested in proposal rejected'),
      'C15':('PASS','C15.json: exact authored text with empty premises and no source ID accepted'),
      'C16':('PASS','C16.json and mixed-opening endpoint rollback/retry test'),
      'C17':('PASS','C17.json: both invalid declaration IDs captured'),
      'C18':('PASS','Historical endpoint replay before==after gameplay snapshot; PR04 rollback controls'),
      'C19':('PASS','Accepted endpoint replay advances one turn/log; PR04 exactly-once controls'),
      'C20':('PASS','Mixed-opening test fails without progression then succeeds on explicit new Start'),
      'C21':('PASS','Accepted historical replay repeat returns 409 and no extra transport dispatch'),
      'C22':('PASS','PR04 and PR10 concurrent endpoint tests pass in diagnostics/overlay lanes'),
      'C23':('PARTIAL_EVIDENCE_LIMIT','Original capture bytes hashed and copied unchanged; parsed JSON equal. Original provider wire bytes and original request payload were not captured; cannot claim byte-exact transport replay.'),
      'C24':('PASS','Pytest live-model guard, SDK synthetic transport, H15/G23 external socket refusal controls'),
      'C25':('PASS','Existing nested decision audit plus declaration_analysis.json and lexical_failure.json identify accepted declarations and sole narration rule'),
      'C26':('PASS','Explicit export selection, no environment dumps, configured-secret scan and ZIP scan'),
      'C27':('PASS','Overlay lane including O1-O15, production replay, rollback and concurrency'),
      'C28':('PASS_WITH_EXISTING_LIMIT','Gameplay HTTP synthetic pipeline proceeds past opening through T1-T4 and safely skips T5 at unchanged six-request ceiling; no all-five completion claim')}
    write('C1_C28_results.json',{k:dict(status=v[0],evidence=v[1]) for k,v in bindings.items()})
    table='\n'.join(f"| {k} | {v[0]} | {v[1]} |" for k,v in bindings.items())
    report('01_BASELINE_AND_HISTORICAL_EVIDENCE','01 — Baseline and Historical Evidence',f'''
Revision: `{(OUT/'revision.txt').read_text(encoding='utf-8-sig').strip()}`. Extensive tracked and untracked entry changes are preserved in entry_status.txt; this is not a clean-tree investigation. Incremental diff uses saved entry sources, not git HEAD. No unrelated work reverted.

Primary archive evidence(3).zip was not located in the workspace. Corresponding complete local run **20261031T015747Z-5a6c03c902e3** matches the requested 26593 input / 1352 output tokens, one completed GPT-4.1-mini dispatch, structured validity, HTTP 422, zero player turns and unchanged gameplay. Original evidence remains untouched. historical/rejected_capture.json is an unchanged byte copy of the bounded parsed-response capture; original provider wire bytes are unavailable.

Authorities reviewed: DEVELOPMENT_CONSTITUTION, NEXT_SESSION, Product Realization portfolio bootstrap/validation, state_authority_model, validation_layer_separation, validation_evidence_standard (ATGB), realization_provenance_audit, PR-BN bounded authority, source structured-envelope/claim contracts and PR-PLAY-04–10 handoffs and relevant tests. No benchmark score is claimed.

Relevant owners: game/gm.py (transport/extraction/schema), structured_player_output, gm_resolution_decision (declaration and prose authority), immutable_valid_response (hard validation/sealing), api (acceptance/rollback), provider_budget (observations), tools/playtest (isolated harness). Existing tests include PR04 opening integrity, PR07 semantic acceptance, PR10 overlay replay, structured realization, claim-control, provenance, bounded improvisation and narrative authority suites.

Existing replay capability preserved parsed JSON via SDK transport through production API owners. PR11 adds two accepted historical captures and the rejected capture to that capability. Source claims and prompt requests are observed by delegating wrappers, without replacing validators or commit logic. Opening scene comes from the historical baseline and remaining campaign state from the existing isolated seed; relevant authored facts/claim IDs are confirmed in actual outgoing context. Original live request payload was not saved, so exact original full-context equivalence cannot be proved.
''')
    report('02_DECLARATION_LEVEL_FAILURE_ANALYSIS','02 — Declaration-Level Failure Analysis',f'''
**No structured declaration is rejected.** All seven exact authored-text matches pass validate_declared_claims_against_decision, despite source_claim_id=null and semantic_identity={{}}. The requested declaration-level rejection table is artifacts/pr_play_11/declaration_rejection_table.md; original fields and accepted source claims are preserved in declaration_analysis.json.

The sole offending narration is: “The board itself lists grim new taxes, curfew regulations, and a posted warning about a patrol that has gone missing.” Related accepted declaration: rc_a83c5bcfc65e, “The notice board lists taxes, curfew rules, and a warning about a missing patrol.” Subject/predicate/object fields are **absent**, not inferred replacements for the empty semantic_identity. Every actual field and null/empty value remains in the capture.

Path: call_gpt completed output_text → _safe_json / structured envelope → run_preserve_if_valid._check → validate_generated_response → audit_realization_envelope_against_decision → declarations pass → audit_narration_against_decision → audit_narrated_claims / classify_narrated_fact → _classify_narrated_fact_legacy → no _authorized_rows_for_sentence coverage → consequential pattern notice_roster_history → unauthorized narration → unauthorized_resolution_decision_fact → host safe_nonresolution → api._opening_response_rejection → 422 and rollback.

_empty_identity_covers rejects more than one added content token. Relative to the first authored source, the narration adds gone/grim/itself/posted/regulations; the alternative opening-seed wording also fails. No synonym/entailment authority exists. This is correct under the executable conservative coverage contract, even though the sentence reads as an ordinary paraphrase. The notice/patrol pattern conservatively treats posting assertions as potentially consequential; it does not establish that the model made a mechanical decision.

Existing nested audits already report all seven accepted claims and the rejected narration with specific reason codes. No production diagnostics relaxation or raw-response ledger extension is necessary. PR11 exports that existing audit and bounded (32-item) declaration/narration analysis; omitted counts are explicit. Aggregate ledger error alone must not be used to accuse a declaration.
''')
    report('03_CLAIM_AND_RESOLUTION_AUTHORITY','03 — Claim and Resolution Authority','''
The decision is a pre-narration authority boundary, not merely a dice-result classifier. It covers authored facts, epistemic limits, incidental texture, action outcomes, mechanics and persistent consequences. claim_authority_matrix.json identifies existing owners and limits. GPT expressions never become state truth by assertion.

authored_world_fact does not self-authorize. A realize declaration must match a supplied authorized realization_claim and preserve modality/premise ceilings. source_claim_id is **not mandatory**: _declared_identity_matches_realization also accepts semantic identity, exact text and bounded lexical compatibility. Exact authored environmental facts can use authored provenance; premises may be empty when no uncertain dependency exists. No special opening exemption exists. Scene context is usable only through the host's actual decision/evidence, not a model-invented authority claim.

Missing provenance defaults to generated_proposal during coercion, but realized output provenance is taken from the matched host claim. Requested provenance is not independently equality-checked in the realize branch; contradictions in *requested labels* alone do not necessarily reject. Proposal world-truth requests are explicitly prohibited. Invalid source IDs may fall back to exact text matching: C6 rejects unsupported content with an invalid ID, while source_id_fallback.json documents that a bogus ID with independently matched authored text remains accepted. This preexisting contract is not silently strengthened or relaxed here. Source ID matching itself is permissive; broad assurance about all malformed metadata is not claimed.

MUST_STATE is host presentation priority derived from authorized world claims. It is not an authority grant or resolution flag. Declared roles and ordinary_predicate do not by themselves reject this opening. established modality is valid for these established facts. The historical combination is valid for all seven declarations. Correct source IDs, changed role, or changed requested provenance leave the original narrated sentence rejected. Same semantic subject can pass declaration validation and fail prose validation because each surface is checked separately.

Consequential player-action, mechanical and persistent-world outcomes remain engine-owned. Ordinary prose can trigger a consequential lexical restriction when it asserts posted information, evidence, historical causes or other guarded content. Sounding mundane does not bypass that check. Bounded incidental details and NPC rumors retain their existing separate policy and persistence limits.
''')
    report('04_GENERATION_CONTRACT_ANALYSIS','04 — Generation Contract Analysis','''
Actual model input is saved in before_repair_replay.json.requests (reconstructed pre-change production request), with actual post-change SDK requests in each replay. Full system JSON example permits source_claim_id=null, semantic_identity={}, established status and MUST_STATE. These are permitted options, not a requirement to use that combination. The system requires consequential declarations, forbids self-authorization, and permits plain sensory texture. decision_facing_answer_recipe requests source references and provenance. Opening guidance requests sensory/spatial details and natural language; vivid mode emphasizes mood.

The confirmed mismatch is narrower than missing evidence: the model receives authored claim texts and stable rc_ identifiers, can reference them in the schema, and all historical declarations match supplied texts. No identifier fabrication or missing-context repair is justified. Existing guidance does not explain that free-text claims without semantic identities have a conservative lexical prose check that cannot authorize expanded synonym paraphrases. A valid declaration does not make its elaborated narration valid.

Compliant generation is feasible: keep an authorized source fact sentence intact and place texture separately. An unchanged-metadata response with only the notice sentence replaced passes the complete production opening path and commits once. The general system example is a field catalog rather than a concrete positive/negative opening pair; the recipe supplies real valid rows but no explicit lexical counterexample. Empty identity means there is no typed subject/relation/value supplied for that fact. The model must not invent one to broaden prose acceptance.

Repair: one opening-only system instruction in call_gpt explains this existing lexical constraint before input estimation/admission/dispatch. Use exact supplied text as a separate sentence for empty-identity authored claims; preserve references/status/premises; keep texture separate; do not fabricate identities or IDs. The outgoing-request assertion verifies delivery and source claim availability. Ordinary-turn prompts and all authority validators are unchanged. Additional prompt input is small but unmeasured in live tokens; no claim of prompt-size reduction or output-budget increase.
''')
    corpus_table='\n'.join(f"| {c['pass_name']} | {c['source_run']} | {c['declaration_count']} | {c['opening_acceptance']} | {c['replay_status']} |" for c in corpus)
    report('05_ACCEPTED_REJECTED_OPENING_COMPARISON','05 — Accepted/Rejected Opening Comparison',f'''
| Source | Run | Declarations | Historical accepted | Replay HTTP |
|---|---|---|---|---|
{corpus_table}

All three use GPT-4.1-mini; original capture bytes and parsed JSON are retained under corpus/. historical_corpus.json contains actual declaration metadata, availability, structural/semantic outcomes, original failure reason, model and hashes. No unavailable capture was manufactured. Exact parsed replay is available; exact provider wire-byte replay is not.

The seven rejected-run declaration texts occur as authored evidence; the accepted PR09 response uses nonempty semantic_identity fields and one source ID, whereas rejected declarations have empty identities and null sources. This correlation is **not the cause**: original declarations all pass, and adding all correct source IDs still leaves the same prose rejection. Accepted historical metadata may use model-supplied identities, but acceptance is not evidence that every possible identity/provenance combination is sound.

Smallest confirmed causal change: replace the one notice-board narration sentence (both narration and legacy player_facing_text) with its already supplied authored text. Declarations, field combinations, state, validator and provider transport remain fixed. conservative_generation.json records 200; before_repair_replay.json records 422. Superficial wording matters to this conservative token-coverage gate. No metadata-only authorization repair is indicated, and no predicate-specific production allowlist is added.
''')
    report('06_ROOT_CAUSE_AND_IMPLEMENTATION','06 — Root Cause and Implementation','''
**Classification C — Generation/Validation Contract Mismatch (under-specified realization constraint).** Development-constitution failure class: contract. The first demonstrated mismatch is the prose realization of an authorized untyped fact beyond the existing lexical coverage rule. Structured declarations are valid; parser/provider completion are successful; no missing-claim provenance conclusion is supported. The executable validator conservatively rejects the paraphrase as designed. This is not proof that the model attempted an unauthorized mechanical resolution.

Bounded implementation: game/gm.py appends opening-only guidance before accounting input estimation and dispatch. No validator change, synonym table, retry, additional request, fabricated authority, scene rewrite, output allowance or model change. New tests and offline evidence tools replay both accepted captures and the rejection through production owners and capture existing nested authority diagnostics. Source diff is incremental against dirty entry bytes. No new gameplay subsystem or persistent structure is added.

Rejected alternatives: require source_claim_id everywhere (not existing contract and not causal); trust authored_world_fact labels; exempt ordinary_predicate/MUST_STATE; expand token-overlap allowance; whitelist this historical sentence; attach invented semantic identities; strip declarations; change world content; bypass hard validity; force historical acceptance; spend a live request. All would be unjustified or exceed scope.

The raw historical response correctly remains rejected under the preserved contract. A compliant equivalent is accepted. This fixes the demonstrated missing generation constraint for the class of empty-identity opening facts, conditional on the model following it. It does not prove a stochastic failure-rate reduction or solve every conservative prose false rejection. Broader semantic adequacy is deferred.
''')
    summary_table='\n'.join(f"| {k} | {v.get('passed',0)} | {v.get('failures',0)} | {v.get('errors',0)} |" for k,v in results.items())
    report('07_DETERMINISTIC_VALIDATION','07 — Deterministic Validation',f'''
Actual commands, executable paths, basetemps, exits and durations: regression_runs.json. Entry point: `.venv/Scripts/python.exe -m tools.validate_pr_play_11`; successful outer invocation uses the base Python312 interpreter with repository/.venv site-packages in PYTHONPATH to avoid Windows launcher issues. Every lane executes pytest with explicit selected files, -q --tb=short and JUnit output. Test live-model guard prohibits real SDK construction except explicit synthetic stubs. No live test or connectivity probe ran.

| Lane | Passed | Failures | Errors |
|---|---|---|---|
{summary_table}

Actual current-source total: **{passed} passing executions / {failed} failures**. The same PR10 lanes retain **752 passing / six failures**. The added claim/provenance selection contributes **126 passing / eight additional failures**; all eight reproduce against saved entry GM source (separate entry comparison: 104 passing / eight failures, excluded from the current-source total). Exact failure IDs and comparison are in failure_classification.json. One additional failure is an existing test incompatibility with the deterministic live-model guard; remaining added failures concern old claim/investigation behavior. They are not repaired here. No relevant new regression remains. Initial sandbox child/localhost attempts did not yield usable results and were interrupted; completed localhost-capable run supplies authoritative results. A transient Windows atomic-replace PermissionError passes on rerun. Initial prompt placement after the user message broke seven transport-fixture assumptions; moving the instruction before the user payload restores all diagnostics. Initial results are preserved under initial_regression/.

The first exploratory baseline test also had a mistaken expected structured subject and raised StopIteration; correcting the evidence lookup exposed that actual scene claims have empty identities. That test-authoring error was not a product regression; original baseline XML is retained. Counts are overlapping executions, not unique tests. No acceptance tests were weakened.

| Case | Result | Evidence / limits |
|---|---|---|
{table}

No full-suite, rendered UI, live reliability, semantic gameplay-quality, ATGB score or independent held-out generalization claim. Matrix probes are synthetic positive/negative controls. Historical captures are runtime-discovered evidence; replay is deterministic. C23 is explicitly partial, not fabricated wire fidelity. C5/C6 reflect the actual matching contract rather than imposing a nonexistent mandatory-ID rule. Normal data and frozen baseline hashes are checked at exit; prior fixed evidence sinks restored after regression.
''')
    readiness=f'''
**B — Conditionally ready for external review of the controlled diagnostic.** Historical failure reproduced; exact offending prose and rule identified; conservative generation constraint reconciled; positive/negative, atomicity, overlay and continuation controls pass. No relevant new regression remains. C23's missing wire bytes/original full request cannot be recovered; parsed captures and relevant reconstructed public context remain inspectable. C5/C6's source-ID fallback is a preexisting contract limitation, not repaired or hidden here.

Original reproduction: raw response remains rejected as required by the existing lexical guard; a one-sentence compliant equivalent passes. Failure-class guidance: now explicitly communicates the empty-identity lexical constraint. Reliability: **not established**; no independent live openings run. Do not promise the prompt prevents every future rejection.

Future command, for external review and a separately authorized later run only:

```powershell
{COMMAND}
```

Existing FiveTurnGameplay v1.0.0, same five actions, same configured model and output allowances (normally opening 3000 / ordinary narration 600), maximum six requests, no SDK/host retries, isolated fresh campaign, state-integrity checks, bounded response capture and automatic evidence export retained. Aggregate ceilings remain 200000 input / 20000 output / 220000 total or stricter inherited limits. No connectivity test. Failed-call usage can be unknown. No cost estimate fabricated.

Synthetic normal HTTP pipeline passes opening and T1–T4, then safely skips T5 at the unchanged six-request ceiling. Full five-turn completion in six requests is unproven. Stop on any semantic or state-integrity failure and retain evidence without retry. Live execution is not authorized in PR-PLAY-11 and was not executed. One next action: external review of this archive.
'''
    report('08_LIVE_TEST_READINESS','08 — Live-Test Readiness',readiness)
    (OUT/'future_live_command.md').write_text(readiness,encoding='utf-8')
    verdict=f'''
**B — Conditionally ready.** Root cause C: generation/prose validation constraint mismatch, not rejected declaration provenance. All seven declarations pass; notice-board narration triggers notice_roster_history after lexical coverage fails. Exact original parsed replay returns 422 and preserves gameplay. Two historical accepted openings remain 200. One constrained sentence replacement returns 200 with the original declarations. Opening-only guidance communicates the existing guard without relaxing authority.

Validation: {passed} passing regression executions, {failed} inherited failures, no demonstrated relevant new regression. See report 07 for C1–C28 qualifications. Missing original wire bytes/full live payload, preexisting source-ID fallback/permissive identity matching, conservative prose wording sensitivity, six-request feasibility and unmeasured live compliance remain limitations. No broad reliability, gameplay quality or ATGB improvement is claimed.

Live recommendation: only after external review accepts this bounded package and a separate invocation authorizes the controlled diagnostic. Do not execute it now. One recommended next action: external review of CURRENT_REVIEW and the timestamped ZIP.

{CONFIRM}

Stop after generating the review archive. Await external review before another live gameplay test.
'''
    report('09_FINAL_VERDICT_AND_HANDOFF','09 — Final Verdict and Handoff',verdict)
    entry=read('protected_before.json'); after=protected_hashes()
    changed=[k for k in entry if entry[k]!=after.get(k)]
    integrity=dict(files=len(entry),changed=changed,added=sorted(set(after)-set(entry)),
        normal_data_unchanged=all(entry[k]==after.get(k) for k in entry if k.startswith('data/')),
        only_authorized_production_change=changed==['game/gm.py'])
    assert integrity['normal_data_unchanged'] and integrity['only_authorized_production_change'], integrity
    assert not integrity['added'], integrity
    from tools.atgb.baseline import load_baseline
    load_baseline(ROOT)
    integrity['frozen_baseline_verified']=True
    write('entry_to_exit_integrity.json',integrity)
    (OUT/'exit_status.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),encoding='utf-8')
    diff=[]
    for name in SOURCES:
        path=ROOT/name; dest=OUT/'source_snapshots'/name
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        base=OUT/'entry_sources'/name
        diff.extend(difflib.unified_diff(base.read_text(encoding='utf-8').splitlines(True) if base.exists() else [],
            path.read_text(encoding='utf-8').splitlines(True),fromfile='entry/'+name if base.exists() else '/dev/null',tofile='exit/'+name))
    (OUT/'source_diff.patch').write_text(''.join(diff),encoding='utf-8')
    selected=[ROOT/s for s in SOURCES]+list(REPORTS.glob('*.md'))+[
        p for p in OUT.rglob('*') if p.is_file() and p.name not in {'review_config.json'} and 'entry_sources' not in p.parts]
    from dotenv import dotenv_values
    secrets=[v.encode() for k,v in {**dotenv_values(ROOT/'.env'),**os.environ}.items()
        if any(t in k.upper() for t in ('API_KEY','SECRET','PASSWORD','ACCESS_TOKEN'))
        and isinstance(v,str) and len(v)>=8 and v!='offline-placeholder']
    def check_payload(data, label):
        assert not any(secret in data for secret in secrets), 'Configured secret detected in '+label
        if zipfile.is_zipfile(io.BytesIO(data)):
            with zipfile.ZipFile(io.BytesIO(data)) as nested:
                for name in nested.namelist():
                    if not name.endswith('/'):
                        check_payload(nested.read(name), label+'!'+name)
    for path in selected:
        check_payload(path.read_bytes(), path.name)
    write('diagnostic_safety.json',dict(configured_secret_scan_passed=True,environment_dump_included=False,
        raw_provider_wire_bytes_included=False,existing_nested_audit_exported=True,bounded_violation_count=32))
    selected.append(OUT/'diagnostic_safety.json')
    config=dict(campaign_id='pr_play_11',campaign_name='PR-PLAY-11 — Opening Claim-Authority Reconciliation',
        campaign_date='2026-10-30',purpose='Offline claim-authority investigation and bounded generation repair',
        objective_status='B — Conditionally ready; external review only',
        executive_summary=f'All seven declarations pass; notice-board prose fails conservative lexical authority. Opening guidance reconciled; {passed} passing checks, {failed} inherited failures. No live calls.',
        primary_report='development/campaigns/product_realization/pr_play_11/09_FINAL_VERDICT_AND_HANDOFF.md',
        supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='evidence',why='Explicit PR11 report, source or offline evidence') for p in sorted(set(selected))],
        changes=dict(production=['Opening-only exact source-sentence guidance for untyped authored claims'],tooling=['Offline analysis and replay evidence export'],
            validation=['Three historical replays, authority distinctions and inherited regression lanes'],documentation=['Nine reports and canonical session handoff']),
        testing=dict(focused='Historical and authority controls pass',broader=f'{passed} passed; {failed} inherited failures',full_suite='Not run',
            runtime_validation='Production API / normal HTTP with synthetic SDK',model_runtime_boundary='Zero live providers or connectivity tests',
            new_regressions='None demonstrated',pre_existing_failures='Six PR10 baseline IDs plus eight added-lane entry-reproduced failures'),
        decisions_requiring_human_review=['Review conservative generation repair and qualified readiness before separate live authorization'],
        known_problems=dict(campaign_specific=['No original wire bytes/full historical request; live compliance unproven'],
            pre_existing=['Conservative prose matching; source-ID fallback; six-request limit may skip T5; six PR10 failures plus eight additional entry-reproduced failures']),
        does_not_prove=['Live reliability, broader semantic authority, full five-turn feasibility, ATGB quality or held-out generalization'],
        recommended_next_step='External review only; do not execute live test',deferred_work=['Broad validator/identity/provenance policy repair outside confirmed cause'],
        validation_evidence=dict(evidence_scope='structural_only'))
    write('review_config.json',config)
    build_handoff(config,root=ROOT)
    stamp=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-4))).strftime('%Y%m%d-%H%M%S')
    dest=ROOT/'handoff'/f'CURRENT_REVIEW({stamp}).zip'
    shutil.copy2(ROOT/'handoff/CURRENT_REVIEW.zip',dest)
    with zipfile.ZipFile(dest) as archive:
        assert archive.testzip() is None
        assert all(any(n.endswith(p.relative_to(ROOT).as_posix()) for n in archive.namelist()) for p in REPORTS.glob('*.md'))
        for name in archive.namelist():
            if not name.endswith('/'):
                check_payload(archive.read(name), name)
    print(dest)


if __name__=='__main__':
    main()
