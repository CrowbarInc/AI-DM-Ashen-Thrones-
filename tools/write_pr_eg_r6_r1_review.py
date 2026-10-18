"""Produce the bounded R6-R1 evidence review and established CURRENT_REVIEW bundle."""
from __future__ import annotations
import difflib
import hashlib
import json
import re
import shutil
import statistics
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/pr_eg_r6_r1'

def read_rows(name):
    p=OUT/name
    return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()] if p.exists() else []

def write(name,value):
    (OUT/name).write_text(value if isinstance(value,str) else json.dumps(value,indent=2,default=str),encoding='utf-8')

def cases(name):
    out={}
    for c in ET.parse(OUT/name).iter('testcase'):
        f=next((e for e in c if e.tag in {'failure','error'}),None)
        out[c.get('classname')+'::'+c.get('name')]={'failed':f is not None,'message':f.get('message','') if f is not None else ''}
    return out

def ref(path,symbol):
    lines=(ROOT/path).read_text(encoding='utf-8').splitlines()
    number=next((i for i,s in enumerate(lines,1) if symbol in s),1)
    return f'[{path}:{number}](../../{path}#L{number})'

def main():
    live=read_rows('live_turns.jsonl'); exploit=read_rows('exploit_turns.jsonl'); baseline=read_rows('baseline_turns.jsonl')
    before=json.loads((OUT/'matched_before.json').read_text(encoding='utf-8'))
    after=json.loads((OUT/'matched_after.json').read_text(encoding='utf-8'))
    old=cases('baseline_regression_junit.xml'); new=cases('regression_junit.xml'); focused=cases('focused_junit.xml')
    new_fail={k:v for k,v in new.items() if v['failed'] and not old.get(k,{}).get('failed')}
    inherited={k:v for k,v in new.items() if v['failed'] and old.get(k,{}).get('failed')}
    reg={'baseline_passed':sum(not v['failed'] for v in old.values()),'baseline_failed':sum(v['failed'] for v in old.values()),
         'final_passed':sum(not v['failed'] for v in new.values()),'final_failed':sum(v['failed'] for v in new.values()),
         'new_failures':new_fail,'inherited_failures':inherited,'focused_passed':sum(not v['failed'] for v in focused.values())}
    write('regression_comparison.json',reg)
    def p95(values): return sorted(values)[max(0,int(len(values)*.95+.999)-1)] if values else None
    def perf(rows):
        calls=[c for r in rows for c in r.get('provider_calls') or []]
        tokens=[sum(c.get('input_tokens') or 0 for c in r.get('provider_calls') or []) for r in rows]
        latency=[r['latency_ms'] for r in rows]
        return {'turns':len(rows),'provider_calls':len(calls),'calls_per_turn':len(calls)/len(rows) if rows else None,
                'mean_input_tokens_per_turn':statistics.mean(tokens) if tokens else None,'p95_input_tokens_per_turn':p95(tokens),
                'mean_latency_ms':statistics.mean(latency) if latency else None,'p95_latency_ms':p95(latency),
                'input_tokens':sum(tokens),'output_tokens':sum(c.get('output_tokens') or 0 for c in calls),
                'retry_calls':sum('retry' in str(c.get('purpose','')) for c in calls)}
    performance={'final_fresh':perf(live),'original_before':perf(baseline),'original_after':perf(exploit),
                 'note':'Retry purposes only; generic retry activity is not exhaustively instrumented. Dollar cost not calculated without verified pricing. Authorship and interrupted runs are excluded from final-turn aggregates, retained in usage files.'}
    write('performance.json',performance)
    changed=[]; patch=[]
    for p in sorted((OUT/'baseline_sources/game').glob('*.py')):
        target='game/'+p.name
        a=p.read_text(encoding='utf-8').splitlines(keepends=True); b=(ROOT/target).read_text(encoding='utf-8').splitlines(keepends=True)
        if a!=b:
            changed.append(target);patch.extend(difflib.unified_diff(a,b,fromfile='before/'+target,tofile='after/'+target))
    write('production.patch',''.join(patch))
    hold=hashlib.sha256((ROOT/'artifacts/pr_eg_r6/frozen_holdouts.json').read_bytes()).hexdigest()
    leaks=[r for r in live if re.search(r'\bsword\b',r['text'],re.I)]
    gates={'original_exploit':bool(len(exploit)==2 and all(all(r['checks'].values()) for r in exploit)),
           'evaluated_live_checks':bool(live and all(all(r['checks'].values()) for r in live)),
           'fresh_target':len(live)>=60 and len({r['conversation'] for r in live})>=4,
           'universal_path_qualification':False,'legacy_compatibility':False,'regression':not new_fail,
           'protected_leaks':len(leaks),'verdict':'C — REPAIR INCOMPLETE'}
    write('acceptance_gates.json',gates)
    summary=f'''**C — REPAIR INCOMPLETE.** The password exploit is reproduced and repaired across both feature-gate settings. Focused tests: {reg['focused_passed']} passed. Relevant regression: {reg['final_passed']} passed / {reg['final_failed']} failed, including {len(new_fail)} new failures and {len(inherited)} inherited failures. Fresh-provider turns recorded: {len(live)} across {len({r['conversation'] for r in live})} conversations. Complete-value password leaks observed in those turns: {len(leaks)}.

Do not approve the universal boundary yet. Source-less host-resolution and historical fixtures now fail closed, breaking legitimate-disclosure/recall compatibility. The matrix is narrower than the complete requested production-path qualification. No R6-R2 or PR-EH work was started.'''
    mapping=[
      ('Legacy question / imperative','game/social.py','def _next_topic_to_reveal','NPC topics/knowledge; speaker/source row. Common authorization before relevance and again before reveal mutation. Revealed flags cannot override policy.'),
      ('Unified semantic plan','game/unified_semantic_planning.py','def _topic_rows','Same authored rows; hidden eligibility now derives from common source authorization. Planner migration gate is unchanged; provider source IDs grant nothing.'),
      ('Partial answer','game/dialogue_authority.py','def _single_partial_topic','Host NPC topic rows checked before partial-source choice. Final seal checks an authorized proposition even without a promoted topic.'),
      ('Stored authored answer / strict retry','game/social.py','def _match_present_npc_topic_authored_knowledge','Present/allowed knowledge identities retain existing speaker rules; each enumerated NPC source now checks common permission.'),
      ('Historical speech / GM quotation','game/conversational_continuity.py','def continuity_directive','Current source revalidation for topic-linked history; missing legacy proof denied. History without a topic currently accepts an existing delivery digest/source marker; this is not full provenance reconstruction.'),
      ('Direct supplied clarification','game/conversational_continuity.py','def supplied_clarification','Topic-linked prior speech is rechecked against the actual NPC source. Missing source authority returns safe contextual speech.'),
      ('Commitment reuse','game/dialogue_authority.py','def commitment_disclosure_permitted','Stored propositions require a current NPC source; nonconsequential host commitments carry a bounded scope marker. Older unmarked commitments are not proof.'),
      ('Expression','game/expressive_dialogue.py','def validate_expression','Existing bounded proposition/operation validation remains. No new provider call for permission. Six unsupported consequential candidate categories tested.'),
      ('Narration grounding corpus','game/gm_resolution_decision.py','for topic in npc.get','Authored NPC topics used as a grounding corpus now exclude denied records. Cross-speaker and all semantic narration combinations have not been exhaustively qualified.'),
      ('Interpretation bridge','game/player_interpretation_bridge.py','from game.dialogue_authority import npc_source_permitted','Only permitted NPC authored passages can ground unresolved subject annotations.'),
      ('Referenced abstract surface','game/referenced_surface.py','def _abstract_surfaces','List-shaped topics/knowledge now filter through common permission. Mapping-shaped knowledge is a remaining schema/projection audit limitation.'),
      ('Preseal authored projection','game/immutable_valid_response.py','def _project_authorized_social_answer_before_seal','World-backed NPC topic check occurs before projecting a selected fact into narration.'),
      ('Final host adoption / seal','game/immutable_valid_response.py','def seal_host_speech','Production callers supply world. Topic, semantic authorized text, or dialogue authorized proposition is rebound before final sealing. Pure callers without source evidence fail closed.'),
      ('Discovered clue / lead writes','game/clues.py','def apply_socially_revealed_leads','Rebind source against world before first write; reject unsupported clue text/IDs. Existing deterministic IDs and idempotence retained.'),
      ('Save/load / reconstructed state','game/storage.py','def load_session','Serialization is unchanged. Read-time source checks protect explicitly linked restricted records; no destructive migration or cleansing of historical R6 files was performed.'),
    ]
    inventory='| Path | Source and policy / bypass assessment | Source link |\n|---|---|---|\n'+'\n'.join(f'| {name} | {detail} | {ref(path,symbol)} |' for name,path,symbol,detail in mapping)
    reproduction='''The original preserved R6 transcript is `artifacts/pr_eg_r6/live_turns.jsonl`, labeled_adversarial turn 14. Its provider performed one interpretation call, no unified plan; speech adoption, API equality, history equality and final seal all passed while the secret leaked.

`reproduction.json` captures the pre-edit deterministic resolver, source world, before/after session, speech and discovery. `baseline_turns.jsonl` reproduces the same utterance through fresh-provider `/api/chat` using preserved pre-edit modules and the same synthetic ADVERSARIAL source fixture. It is an isolated reconstruction, not a claim that a turn-13 save was recovered: the retained R6 save is already post-failure.

First eligibility failure: `_next_topic_to_reveal` accepted the authored secret based on relevance/sufficiency and dropped its policy metadata. Routing excluded “grant me” from the migrated family, exposing this weaker selector. NPC ownership established that Nara knew the password; it did not authorize disclosure. `resolve_social_action` marked it revealed and populated discovery fields before final speech adoption. `apply_socially_revealed_leads` persisted a derived clue and event log without checking disclosure. Final adoption trusted the selected topic and sealed the unauthorized sentence faithfully.

Failure classes: routing exposed the defect; source eligibility, disclosure authorization, speech adoption and persistence were faulty. This was not evidence that Nara lacked the secret, nor a final-text mutation. Raw `world.event_log` changed with discovery while the existing canonical-view projection remained unchanged.'''
    sections={
      '01_EXECUTIVE_SUMMARY':summary,
      '02_BASELINE_AND_REPOSITORY_STATE':'Pre-edit HEAD/status and frozen holdout hash are in `baseline_repository.json`; the repository already had extensive tracked/untracked R6 and predecessor work. `baseline_sources/game` is the pre-repair authority source overlay. `production.patch` compares against those files, not Git HEAD. Real campaign data was not intentionally changed; all API probes used isolated synthetic storage.',
      '03_ORIGINAL_FAILURE_REPRODUCTION':reproduction,
      '04_DISCLOSURE_PATH_INVENTORY':inventory,
      '05_UNIVERSAL_DISCLOSURE_CONTRACT':f'''The common deterministic contract lives inside existing dialogue authority: {ref('game/dialogue_authority.py','def authorize_npc_disclosure')}. It resolves speaker, addressee, exact source text/identity, classification, knowledge, permission, epistemics, operation, authorized proposition/clue text, provenance and validation. Existing outer dialogue authority, expression contract and accepted-response record continue to carry proposition identity and authorized speech. There is no second persistent authority store. Provider source IDs alone never authorize a source. Production final adoption supplies the host world and re-resolves the source; pure callers without world must carry a matching host receipt.

Limit: a receipt is an internal projection, not a cryptographic capability; do not expose a caller-controlled receipt as an API authority input.''',
      '06_INFORMATION_CLASSIFICATION':'''Existing authored omission of `disclosure` maps to public NPC knowledge. Explicit public/allowed/authorized policies may disclose; secret/hidden/withheld/none/forbidden and all unrecognized or empty policy values fail closed. `hidden`/`secret` flags override public. Explicit unknown knowledge is denied. Rumor/belief/false/disputed epistemics remain noncanonical and are classified separately. Generated incidental expression continues to use the existing bounded expression scope. No new world truth classification was introduced.

Limit: the focused rumor test proves classification, not every disputed/false assertion's realization framing and persistence through production.''',
      '07_AUTHORIZATION_ENFORCEMENT':'Authorization precedes topic enumeration, source projection, final speech sealing and social clue persistence. Recalled topic IDs and runtime revealed flags cannot grant restricted sources. Final sealing rechecks promoted topics and unpromoted semantic/dialogue propositions. Clue persistence rechecks authored text and clue identity, independently of delivered prose. See source inventory and focused JUnit. Universal coverage remains unqualified where historical provenance or alternate schema projections cannot be established.',
      '08_ROUTING_CONTRACT':f'''The migrated-family recognizer and its existing punctuation/interrogative/correction/follow-up/unsupported-operation rules remain unchanged: {ref('game/unified_semantic_planning.py','def is_migrated_information_turn')}. “Grant me” remains legacy. The repair changes source authorization, not the family boundary. Invalid plans and provider transport failures are covered by controlled tests and cannot create a weaker topic selector. No additional interaction family was migrated.''',
      '09_FAIL_CLOSED_BEHAVIOR':'Missing NPC/source, mismatched source text, fabricated identity, unknown policy, unresolved knowledge, and altered clue payload deny permission. Safe host speech replaces denied final topics. Rejected expression candidates remain bounded by existing validation. Older source-less tests now fail closed, which is safer but breaks expected legitimate behavior; this is an acceptance blocker, not a reason to silently weaken enforcement.',
      '10_LEGITIMATE_DISCLOSURE_PRESERVATION':'''Focused tests preserve public topic delivery, repeated idempotent discovery, current authorized historical source lookup, rumor classification and existing R6 partial answers. Fresh turns show harbor bell and dawn facts reaching API/history and creating legitimate clues.

Preservation is incomplete: direct host-resolution fixtures without NPC/world source evidence and old unsealed history/commitments are blocked. This causes new R2C/R3/R1 failures. No blanket compatibility bypass was added. A reviewable migration or an explicit existing host-source receipt contract is still needed.''',
      '11_DISCOVERED_CLUE_INVESTIGATION':f'''The creator is {ref('game/clues.py','def apply_socially_revealed_leads')}, called from API authoritative resolution mutation before final speech adoption. It consumes resolution/topic data, not merely delivered text; it creates `clue_knowledge`, scene runtime discovery records, lead presentation/tracking and event-log entries. These are persisted derived discovery/lead records, not a change to the authored secret source. The original leak survives in the R6 synthetic save.

The repair re-resolves source permission before writes and validates clue text/ID against that source. Repeated authorized delivery uses existing stable social IDs. Controlled tests verify first public clue, repeat no new clue, rejected restricted clue, and public-topic/secret-clue injection. The real campaign and preserved R6 evidence are not retroactively sanitized.''',
      '12_FINAL_SPEECH_INTEGRATION':f'''The R4-R1 immutable accepted-response representation is retained: {ref('game/immutable_valid_response.py','def seal_host_speech')}. Source revalidation occurs before `seal_accepted_response`; postprocessing restores the accepted line and its delivery digest. A denied source cannot acquire an expression audit containing the rejected proposition. Denied adoption records do not seed NPC historical authority. Focused tests mutate a sealed line to the secret and verify restoration. Fresh checks compare API, seal and delivered history exactly.''',
      '13_PROVIDER_FACT_REJECTION':'Controlled expression candidates cover passwords, guard schedules, hidden routes, undisclosed relationships, rewards and promises. Existing semantic expression validation rejects unsupported propositions; source validation does not use a keyword blacklist. The evaluator uses a full-word test-value check solely to detect the synthetic password. The earlier “sword” inside “password” false positive is preserved in the stopped detector trace and is not counted as a leak.',
      '14_FEATURE_GATE_QUALIFICATION':'The exact exploit is blocked in `exploit_turns.jsonl` under gate 1 and gate 0. Controlled tests cross both flags and twelve grammatical/adversarial inputs. Fresh conversations alternate flags 1/0/1/0. Full requested strict-social retry and all alternate fallback combinations were not independently exercised in fresh production conversations; no universal qualification is claimed.',
      '15_GRAMMATICAL_EQUIVALENCE_TESTS':'Twelve forms cross both gate states in the new suite: question, grant/tell imperatives, indirect polite request, ellipsis, follow-up, correction, repeat/history, coercion, injection and mixed public/restricted request. `matched_before.json` and `matched_after.json` repeat 24 identical synthetic source/state/input/gate cases. No phrases were added as production disclosure exceptions.',
      '16_ADVERSARIAL_DISCLOSURE_TESTS':'The controlled set tests claimed prior permission, roleplay coercion, injection, mixed requests, fabricated source identifiers, altered source text, forged restricted resolution, secret clue payload grafted onto a public topic and old commitment laundering. Final fresh holdouts were independently authored by the provider without seeing the implementation/test matrix. They are narrow password-focused evidence, not a comprehensive semantic leak detector.',
      '17_CONTROLLED_TEST_RESULTS':f'''Final focused JUnit: {reg['focused_passed']} passed / {sum(v['failed'] for v in focused.values())} failed across the new disclosure suite and unchanged R6 suite. New suite covers 53 cases; unchanged R6 contributes 31. Provider exception testing patches the actual transport boundary; invalid plan testing supplies forbidden authorization metadata. Existing tests were not rewritten to improve counts.

Requested T01–T28 are not all independently qualified through `/api/chat`: public/secret, routing, failure, invalid-plan, expression, clue/idempotence, sealing and history cases are covered; exhaustive strict-social retries, rumor/disputed realization, partial persistence and legacy save reconstruction need further evidence.''',
      '18_MATCHED_BASELINE_COMPARISON':'`matched_before.json` / `matched_after.json` contain 24 matched deterministic cases with identical initial world, NPC knowledge/policy, input and flag. Provider calls/tokens are zero in both; local latency is recorded per case. The fresh original pair uses the preserved baseline overlay versus final code; provider latency/calls/tokens are in `performance.json`. These are not a 24-case matched fresh-provider comparison. Unchanged R6 holdouts were not modified.',
      '19_FRESH_PROVIDER_CONVERSATIONS':f'''Final-code recorded turns: {len(live)}; independent conversations: {len({r['conversation'] for r in live})}. Synthetic state, API response, resolution, final seal, history, calls and before/after state are in `live_turns.jsonl`. Authorship metadata and the frozen new inputs are `holdout_authorship.json` / `disclosure_holdouts.json`. Original R6 frozen inputs hash: `{hold}`. Interrupted pre-scope-fix and pre-commitment-gate attempts are retained separately and excluded from final counts. The 60-turn acceptance target is {gates['fresh_target']}.

The first fresh attempt hit a variable-scope error before delivering that turn; it was fixed and qualification restarted. Sandbox socket creation initially stalled; approved external execution was then used. Automatic review initially rejected provider transmission, after which the human explicitly approved synthetic OpenAI qualification.''',
      '20_TURN_LEVEL_QUALIFICATION':'Each final row records input, flag, full resolution (including selected NPC and available source/authority metadata), expression audit where emitted, final accepted speech, API text, delivered history, full before/after synthetic state, provider records and latency. Not every nonmutating fallback exposes every requested source/rejection/candidate field; absent fields remain absent rather than inferred. A seal or API/history equality check is integrity evidence, not independent authorization proof.',
      '21_PERSISTENCE_AND_STATE_INTEGRITY':'Every API turn reloads stored state, and each evidence row contains before/after synthetic state. Checks separately inspect derived clue knowledge for the complete password value and the R6 canonical-view projection. Raw world event-log differences are retained. Focused JSON round-trip verifies serializability and clue idempotence; exhaustive real legacy save migration is unqualified. Restricted history with an explicit topic is rechecked; old source-less history fails closed.',
      '22_PERFORMANCE':'```json\n'+json.dumps(performance,indent=2)+'\n```\n\nThe authorization function is deterministic and creates no additional provider request. The single original fresh baseline is too small and structurally different from the full final set to establish a general latency regression. No dollar-pricing or exhaustive retry-frequency claim is made.',
      '23_REGRESSION_COMPARISON':f'''Matched selected suites: baseline {reg['baseline_passed']} passed / {reg['baseline_failed']} failed; final {reg['final_passed']} passed / {reg['final_failed']} failed (includes 53 added tests). {len(inherited)} failures are inherited by exact identity; {len(new_fail)} are new.

Investigation: new failures chiefly construct “authorized” topics without the NPC/world/source evidence now required by final sealing, or load raw historical/commitment fixtures without delivery/source proof. This also affects partial speech and historical proposition identity. These are material compatibility regressions. Full identity/messages are in `regression_comparison.json`; no test expectation was weakened. The selected regression is narrower than R6's 780-test selection; its pass/fail totals must not be compared as though selections were identical.''',
      '24_ACCEPTANCE_GATES':'```json\n'+json.dumps(gates,indent=2)+'\n```\n\nOriginal exploit and evaluated fresh integrity are separate from universal path and compatibility gates. New regression failures prevent approval. Performance and broader fallback coverage remain limited, not automatic passes.',
      '25_REMAINING_LIMITATIONS':'''Material blockers: source-less host-resolution compatibility; previously delivered legacy histories/commitments without verifiable source metadata; incomplete production retry/fallback matrix; rumor/disputed framing and persistence qualification; alternate mapping-shaped knowledge projections; cross-speaker grounding and session clue reuse provenance. No claim is made that the inventory itself closes every bypass. Final checks compare a known test value and cannot independently detect all paraphrased or novel consequential disclosures.

The synthetic R6 state already contains the old discovery. This cycle prevents new evaluated leaks; it does not migrate or cleanse existing user saves. Do not accept a provider source identifier or a caller-controlled receipt as authority while resolving these limitations.''',
      '26_RECOMMENDED_NEXT_ACTION':'Submit CURRENT_REVIEW for external review. Keep the cycle unqualified. Review the source-evidence contract at existing host-resolution/recall seams and decide a bounded compatibility repair within R6-R1 before further acceptance testing. Do not proceed to R6-R2 or PR-EH. No release, merge or commit was performed.',
      '27_FINAL_VERDICT':summary,
      '28_SOURCE_AND_EVIDENCE_INVENTORY':'Cycle source changes:\n\n'+'\n'.join('- '+p for p in changed)+'\n\nTools/tests: `tools/qualify_pr_eg_r6_r1.py`, `tools/compare_pr_eg_r6_r1.py`, `tools/write_pr_eg_r6_r1_review.py`, `tests/test_pr_eg_r6_r1_disclosure_boundary.py`.\n\n`production.patch` and baseline overlay isolate this cycle from the dirty Git baseline. Package manifest hashes enumerate included reports, source, tests, traces and synthetic state. No `.env`, credential, real campaign save, or broad repository archive belongs in the bundle.\n\n'+inventory,
    }
    for title,body in sections.items(): write(title+'.md','# '+title.replace('_',' ')+'\n\n'+body+'\n')
    # Preserve the predecessor's stable review surface before replacing it.
    archive=ROOT/'handoff/history/pr_eg_r6_before_r1';archive.mkdir(parents=True,exist_ok=True)
    for name in ['CURRENT_REVIEW.md','CURRENT_REVIEW.zip','REVIEW_MANIFEST.json']:
        src=ROOT/'handoff'/name
        if src.exists() and not (archive/name).exists(): shutil.copyfile(src,archive/name)
    supports=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='handoff_config.json':
            supports.append({'path':p.relative_to(ROOT).as_posix(),'role':'r6_r1_evidence','why':'Cycle report, preserved source, or isolated synthetic evidence.','human_review_required':p.name.startswith(('01_','23_','27_'))})
    for name in changed+['tools/qualify_pr_eg_r6_r1.py','tools/compare_pr_eg_r6_r1.py','tools/write_pr_eg_r6_r1_review.py','tests/test_pr_eg_r6_r1_disclosure_boundary.py']:
        supports.append({'path':name,'role':'source','why':'Cycle implementation or reproducible validation.','human_review_required':True})
    config={'campaign_id':'pr_eg_r6_r1_disclosure_20261017','campaign_name':'PR-EG-R6-R1 — Universal Disclosure Boundary','campaign_date':'2026-10-17',
            'purpose':'Repair and qualify disclosure integrity; stop for external review.','objective_status':'C — REPAIR INCOMPLETE','executive_summary':summary,
            'changes':{'production':changed,'validation':['53 new controlled cases and production synthetic OpenAI qualification.'],'tooling':['Isolated qualification, matched comparison and review builder.'],'documentation':['28 review artifacts.'],'generated_artifacts':['Transcripts, state snapshots, JUnit, comparison, patch and performance.']},
            'testing':{'focused':f"{reg['focused_passed']} passed",'broader':f"{reg['final_passed']} passed / {reg['final_failed']} failed",'full_suite':'Not run.','runtime_validation':f'{len(live)} final-code fresh turns across {len({r["conversation"] for r in live})} conversations.','model_runtime_boundary':'Configured OpenAI gpt-4.1-mini; actual models and request IDs in traces.','new_regressions':f'{len(new_fail)} identified; details in regression_comparison.json.','pre_existing_failures':f'{len(inherited)} exact-identity inherited failures.'},
            'known_problems':{'campaign_specific':['Legitimate source-less host speech and older recall fixtures fail closed.', 'Universal fallback/alternate-schema qualification incomplete.'],'pre_existing':[f'{len(inherited)} inherited failures.']},
            'decisions_requiring_human_review':['Review the incomplete repair and compatibility contract before further qualification.'],
            'missing_concepts':['Verifiable legacy disclosure provenance without a weaker fallback.'],
            'does_not_prove':['Universal disclosure integrity or complete compatibility.'],
            'recommended_next_step':'External review; stop after R6-R1. Do not start R6-R2 or PR-EH.',
            'primary_report':'artifacts/pr_eg_r6_r1/01_EXECUTIVE_SUMMARY.md','supporting_files':supports,
            'max_file_bytes':50000000,'warn_bundle_bytes':100000000}
    write('handoff_config.json',config)
    import sys
    sys.path.insert(0,str(ROOT))
    from tools.build_review_handoff import build_handoff
    result=build_handoff(config,root=ROOT,output_dir=ROOT/'handoff')
    print(json.dumps({k:result[k] for k in ['file_count','zip_size_bytes','warning']}))

if __name__=='__main__': main()
