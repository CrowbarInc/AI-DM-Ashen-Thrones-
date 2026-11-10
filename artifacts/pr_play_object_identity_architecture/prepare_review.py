"""Prepare documentation/evidence and explicit standard handoff configuration."""
from pathlib import Path
import json, hashlib, xml.etree.ElementTree as ET, subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
REPORT=ROOT/'development/campaigns/product_realization/pr_play_object_identity_architecture'
MID='pr_play_object_identity_architecture'
def dump(name,value): (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
entry=json.loads((OUT/'before_manifest.json').read_text())
prior=json.loads((ROOT/'artifacts/pr_play_t06_persistent_manipulation/after_manifest.json').read_text())
diff=[p for p,h in prior.items() if entry.get(p)!=h]
assert not diff,diff
suite=ET.parse(OUT/'preservation_junit.xml').getroot().find('testsuite')
counts={k:int(suite.get(k,'0')) for k in ('tests','failures','errors','skipped')}
counts['passed']=counts['tests']-sum(counts[k] for k in ('failures','errors','skipped'))
assert counts['tests']==143 and counts['passed']==143,counts
dump('validation_summary.json',{'fresh_preservation':counts,'predecessor_reference_only':{'established_selection':{'passed':405,'failed':20,'total':425},'diagnostics':6,'physical_persistence_controls':93},'predecessor_source_comparison':{'paths':len(prior),'different':diff},'full_suite_rerun':False,'conceptual_controls_are_execution_tests':False,'live_provider_calls':0,'execution':json.loads((OUT/'validation_execution.json').read_text())})
dump('milestone_identity.json',{'milestone':MID,'predecessor':'pr_play_t06_persistent_manipulation','predecessor_verdict':'BLOCKED','identifier_basis':'Next descriptive PR-PLAY work package following current NEXT_SESSION and CURRENT_REVIEW. No numeric PR-PLAY-80 allocation or reopening.','next_cycle':'pr_play_object_instance_identity','scope':'architecture only'})
source_specs={
 'game/defaults.py':[(53,96)],'game/importers/pf_json_importer.py':[(35,109)],
 'game/models.py':[(44,99),(242,253)],'game/player_http_projection.py':[(1,49)],
 'game/referenced_surface.py':[(1,28)],'game/scene_actions.py':[(1,48)],
 'game/storage.py':[(1,20),(83,110),(120,140),(170,232),(285,294),(1182,1210),(1231,1325)],
 'game/api.py':[(874,900),(2620,2651),(4875,4910),(7125,7143),(7170,7192)],
 'game/physical_adjudication.py':[(1,27),(99,137),(960,992),(1203,1224)],
 'game/local_interaction.py':[(95,138),(170,245)],
 'game/conversational_orchestration.py':[(2856,2905)],
 'game/noncombat_resolution.py':[(1,47),(237,327),(489,545)],
 'game/integrated_play.py':[(48,162)],
 'game/world.py':[(566,588)],'game/state_authority.py':[(1,35),(69,103)],
 'game/bounded_improvisation.py':[(107,136),(500,528)],
 'game/exploration.py':[(262,316)],'game/authored_consequences.py':[(34,77)],
 'game/mechanical_claims.py':[(22,40),(189,214)],
 'game/narration_authorization.py':[(48,86)],'game/offline_investigation_projection.py':[(36,74)],
 'game/immutable_valid_response.py':[(1,38)],
}
excerpts=[]
for path,spans in source_specs.items():
    p=ROOT/path; lines=p.read_text(encoding='utf-8-sig').splitlines()
    excerpts.append({'path':path,'sha256':sha(p),'line_count':len(lines),'excerpts':[{'start':a,'end':min(b,len(lines)),'text':'\n'.join(lines[a-1:b])} for a,b in spans]})
dump('existing_contract_excerpts.json',excerpts)
dump('source_inventory.json',[{'path':p,'sha256':h,'size_bytes':(ROOT/p).stat().st_size} for p,h in entry.items() if p.startswith('game/')])
dump('architecture_comparison.json',{'selected':'B','envelope_used_within_B':'shared validated mutation envelope (C mechanism)','options':[
 {'id':'A','description':'extend inventory only','ruleset_independence':'conditional','migration':'low initially; high fixtures','authority_risk':'pseudo-inventory for world objects','decision':'reject as generic foundation'},
 {'id':'B','description':'lightweight shared instance contract; existing hosts','ruleset_independence':'strong','migration':'bounded explicit promotion','authority_risk':'requires single-host/delegation invariant','decision':'recommend'},
 {'id':'C','description':'shared event/mutation envelope without common identity','ruleset_independence':'good envelope','migration':'low initially','authority_risk':'duplicate IDs and cross-host reconciliation unresolved','decision':'reject alone'}],
 'full_criteria_matrix':'development/campaigns/product_realization/pr_play_object_identity_architecture/ARCHITECTURE_OPTIONS.md'})
port=[]
for system in ('pf1e','rules_light','modern_scifi'):
    port.append({'system':system,'tested':'conceptual only','core_operation':'add_marking','identity':'core UUID','placement':'generic custody/scene/containment','persistence':'existing hosts and snapshots','equipment_slots':'adapter extension','statistics':'versioned definitions/adapter','skill_checks':'adapter','action_costs':'adapter','resource_consumption':'adapter adjudicates, core applies atomic costs','conditions':'namespaced adapter','special_abilities':'adapter; never overrides existence/disclosure','core_pf_fields':[]})
dump('ruleset_portability_matrix.json',port)
deps=[{'phase':1,'cycle':'pr_play_object_instance_identity','depends_on':[],'risk':'low-medium','t06':'unchanged refusal'},
 {'phase':2,'cycle':'one established-object marking','depends_on':[1],'risk':'medium-high','t06':'service capability only'},
 {'phase':3,'cycle':'inspection and removal','depends_on':[2],'risk':'medium-high','t06':'controlled end-to-end only'},
 {'phase':4,'cycle':'equipment/affordances/T06 binding','depends_on':[3],'risk':'high','t06':'original conditional on established facts'},
 {'phase':5,'cycle':'scene/transfer/physical delegation','depends_on':[4],'risk':'high','t06':'state follows transfer'},
 {'phase':6,'cycle':'specific later adapter/lifecycle capability','depends_on':[2,3],'risk':'capability-dependent','t06':'not needed for mundane mark'}]
dump('implementation_dependencies.json',deps)
controls=['touch accessible','mark owned','mark inaccessible','copy hidden','nonexistent equipment','ordinary environmental material','take NPC item','ruleset equipment','transfer modified','save/reload','remove marking','duplicate request','application failure','switch rulesets']
dump('architecture_negative_controls.json',[{'scenario':s,'status':'addressed by design, not executed','contract':'T04_T06_INTEGRATION.md','runtime_support':'existing T04 only; other guarantees require roadmap phases'} for s in controls])
dump('proposed_contract_examples.json',{'status':'illustrative design data, not executable scaffolding','instance':{'id':'legacy_shirt_id','name':'Travel shirt','quantity':1,'usable':False,'instance_id':'<core UUID>','revision':0,'provenance':{'campaign_id':'<campaign>','operation_id':'<explicit migration>','source_binding':'character.inventory singleton'}},'proposal':{'request_id':'<existing client_request_id or server-issued ID>','payload_digest':'<canonical semantic digest>','target':{'campaign_id':'<campaign>','instance_id':'<UUID>','part':'left_sleeve'},'expected_revision':0,'operation':'add_marking','arguments':{'text':'<exact disclosed text>','medium_ref':'<established evidence>'},'preconditions':['positive access','writable part','compatible accessible material','source disclosure','bound adapter decision'],'proposed_delta':'engine generated','validation':'engine result'},'applied_receipt':{'envelope':'ExplorationEngineResult','kind':'custom','success':True,'state_changes':{'object_modifications':[{'operation_id':'<ID>','instance_id':'<UUID>','from_revision':0,'to_revision':1,'marking_id':'<UUID>','delta_digest':'<digest>'}]},'metadata':{'object_action':{'status':'completed','application':'applied','narrative_assertions':['<disclosure-approved result>']}}}})
authorities=['docs/DEVELOPMENT_CONSTITUTION.md','docs/NEXT_SESSION.md','docs/review_handoff_standard.md','docs/state_authority_model.md','docs/ruleset_contract_registry.md','development/campaigns/product_realization/PR-AA_product_realization_portfolio_bootstrap.md']
pre_reports=[]
for folder in ('pr_play_t04_local_action','pr_play_t06_persistent_manipulation'):
    pre_reports.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/'development/campaigns/product_realization'/folder).glob('*.md'))
dump('files_inspected.json',{'authority_documents':authorities,'prior_review_captured':'entry_current_review.md','predecessor_and_T04_reports':pre_reports,'source_excerpts':list(source_specs),'source_term_inventory_scope':'all game/**/*.py; exact matching rows in *_references.json','additional_tests':['tests/conftest.py','tests/helpers/storage_isolation.py','tests/test_pr_play_60_inventory_projection.py'],'review_generator':'tools/build_review_handoff.py'})
# Explicitly add lane references discovered after the initial source term capture.
rows=json.loads((OUT/'state_mutation_references.json').read_text())
for i,line in enumerate((ROOT/'game/integrated_play.py').read_text().splitlines(),1):
    if any(t in line for t in ('class ordered_turn','lane.completed','lane.inflight','request_key','lane.writer =')):
        rows.append({'path':'game/integrated_play.py','line':i,'text':line.strip()})
dump('state_mutation_references.json',rows)
identity=json.loads((OUT/'entry_identity.json').read_text())
dirty=(OUT/'entry_git_status.txt').read_text().splitlines()
integrity=f'''# Integrity and review sealing

Milestone: `{MID}`. Date: 2026-11-09.

Branch `{identity['branch']}`; HEAD `{identity['head']}`. Entry status: {len(dirty)} dirty/untracked status lines. Exact original porcelain status and current review/session bytes are captured in entry_git_status.txt, entry_current_review.md and entry_next_session.md. No reset/clean/stash/revert/historical checkout/commit/push occurred.

Protected manifest covers {len(entry)} source/test/data/static/tool/script files, excluding caches. All {len(prior)} predecessor source/test/data hashes match entry; inherited 405/20 baseline is reference evidence, not a fresh result. Source inventory, line-bearing object/action/mutation/persistence references and exact contract excerpts include original file SHA-256. See files_inspected.json for inspection scope. No repository AGENTS.md was located in the working tree or its immediate parent during instruction discovery.

Production files changed: **None (0)**. Tests/frozen fixtures/data changed: **0**. No production scaffolding. This cycle adds fourteen design reports and bounded cycle-local evidence/config/validation helpers, prepends NEXT_SESSION and regenerates review exports. before_manifest.json / after_manifest.json / source_changes.json prove protected bytes are identical. Historical NEXT_SESSION bytes remain the exact suffix. Prior generated review is preserved in evidence; historical ZIPs/entries are untouched.

Fresh validation: **143 passed / 0 failed / 0 errors / 0 skipped**. Includes original six T06 negative diagnostics, 93 physical/persistence/authority controls, 12 T04, 15 T05 and 17 pre-seal tests. Runtime prerequisites/inscription success and portability are not implemented or proven. Full 425 baseline and full suite were not rerun. Existing Starlette TestClient deprecation warning remains. Live provider calls **0**; test runner disabled providers, forbidden external networking and protected production data. validation_command.json / validation_execution.json / preservation_junit.xml retain exact evidence.

Review is generated by the unchanged standard tools/build_review_handoff.py from this cycle's explicit review_handoff.json. All fourteen reports, machine-readable evidence, prior T04/T06 contracts, selected actual source files and source excerpts are named support. Source/evidence manifests and historical handoff suffix are verified after regeneration. Stable and freshly timestamped ZIPs are independently reopened; packaged canonical hashes, milestone, recommended architecture, portability, roadmap, exactly one next decision and updated handoff are checked by seal_review.py. Results: archive_verification.json.

Archive SHA-256 and absolute dated path are written to archive_sha256.txt **outside the archive after sealing**, avoiding circular self-hashing. This report points to that authoritative final seal rather than embedding a hash of its own containing ZIP. The archive does include the source/evidence manifests and sealing procedure. The external verification/SHA files are final outputs, not stale predecessor artifacts.

Performance: no production overhead introduced, no model calls or token increase. Design complexity estimates are in ARCHITECTURE_OPTIONS.md; test elapsed time is not a gameplay benchmark.
'''
(REPORT/'INTEGRITY.md').write_text(integrity,encoding='utf-8')
summary=REPORT/'SUMMARY.md'
summary.write_text(summary.read_text(encoding='utf-8').replace(', contingent on the accompanying final integrity/archive checks',''),encoding='utf-8')
next_entry=f'''# NEXT_SESSION — PR-PLAY Object Identity Architecture (2026-11-09)

**A/PASS for bounded architecture; no implementation.** Milestone `{MID}`; predecessor `pr_play_t06_persistent_manipulation` remains BLOCKED for original T06. Branch {identity['branch']}; HEAD {identity['head']}. Dirty source/tests/data preserved; no commits/pushes. Live provider calls **0**.

Decision: Option B, lightweight common object-instance contract over existing hosts, with one core validated mutation owner proposed and specialized action owners preserved. Core owns campaign UUID/revision/current state; ruleset adapters own mechanics, never identity. Character inventory is the initial host; no scene-ledger shadow inventory. Definitions, attack rows, knowledge and physical instances remain distinct. Explicit mundane-affordance policy; clothing/material/source evidence is required for T06. Existing FIFO ordered_turn/client_request_id reused with future durable digest validation. Current rollback is exception-oriented, not crash-atomic.

Fresh preservation selection **143/143 passed**, zero errors/skips; all 1,296 predecessor hashes match and expanded protected manifest has {len(entry)} files. Established 425 result **405 passed / 20 failed** is predecessor reference only, not rerun. No inscription, alternate-ruleset runtime, full-suite or Gameplay Benchmark claim.

**Exactly one next implementation cycle:** `pr_play_object_instance_identity` — stable identity for existing inventory singletons. Explicit idempotent migration, distinct IDs for identical old rows, revision/provenance and real save/snapshot round trip. Exclude markings/T06 routing, equipment/material minting, transfer, physics/crafting, experimental activation, new rulesets and baseline repairs. Do not begin automatically.

Minimum reading: development/campaigns/product_realization/{MID}/SUMMARY.md, OBJECT_INSTANCE_CONTRACT.md, MODIFICATION_CONTRACT.md, ACTION_OWNERSHIP_MAP.md, CORE_RULESET_BOUNDARY.md, IMPLEMENTATION_ROADMAP.md, NEXT_STEP_DECISION.md and INTEGRITY.md. Fourteen reports are authoritative design; proposed modules do not exist yet. Evidence: artifacts/{MID}/validation_summary.json, existing_contract_excerpts.json, source_changes.json. Review: handoff/CURRENT_REVIEW.md; fresh dated ZIP/hash/reopen checks in artifacts/{MID}/archive_sha256.txt and archive_verification.json. Preserve T04 transient completion, T05 clue composition, hidden protection/travel/inventory authority and immutable publication. Defer historical baseline defects and full ruleset loader.

---

'''
(ROOT/'docs/NEXT_SESSION.md').write_bytes(next_entry.encode('utf-8')+(OUT/'entry_next_session.md').read_bytes())
dump('evidence_manifest.json',{'milestone':MID,'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'size_bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ('evidence_manifest.json','review_handoff.json','archive_sha256.txt','archive_verification.json','prepare_review.py','seal_review.py','after_manifest.json','source_changes.json','handoff_generation.log')]})
supports=[]
def add(path,role='architecture_evidence'):
    supports.append({'path':path,'role':role,'canonical':True,'why':'Explicit evidence for the architecture decision, persistence boundary, portability or integrity.','behavioral_evidence':False,'human_review_required':False})
for p in sorted(REPORT.glob('*.md')):
    if p.name!='SUMMARY.md': add(p.relative_to(ROOT).as_posix(),'architecture_report')
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name not in ('review_handoff.json','archive_sha256.txt','archive_verification.json','handoff_generation.log'):
        add(p.relative_to(ROOT).as_posix())
for path in ['docs/NEXT_SESSION.md','docs/state_authority_model.md','docs/ruleset_contract_registry.md','docs/review_handoff_standard.md',
             'game/storage.py','game/physical_adjudication.py','game/integrated_play.py','game/models.py','game/defaults.py','game/importers/pf_json_importer.py','game/noncombat_resolution.py','game/local_interaction.py','game/player_http_projection.py',
             'development/campaigns/product_realization/pr_play_t06_persistent_manipulation/SUMMARY.md','development/campaigns/product_realization/pr_play_t06_persistent_manipulation/MANIPULATION_CONTRACT.md','development/campaigns/product_realization/pr_play_t06_persistent_manipulation/REGRESSION_RESULTS.md','development/campaigns/product_realization/pr_play_t04_local_action/ACTION_CONTRACT.md']:
    add(path,'authoritative_context_or_source')
config={'campaign_id':MID,'campaign_name':'PR-PLAY — System-Agnostic Object Identity and Manipulation Architecture','campaign_date':'2026-11-09','purpose':'Bounded implementation-ready architectural design; no production implementation.','objective_status':'A/PASS — architecture only',
 'executive_summary':(REPORT/'SUMMARY.md').read_text(encoding='utf-8'),
 'changes':{'production':['None (0).'],'validation':['No tests/fixtures modified; existing 143-test preservation selection executed.'],'tooling':['Cycle-local evidence/validation/seal helpers only.'],'documentation':['Fourteen architecture reports; NEXT_SESSION prepended with history preserved.'],'generated_artifacts':['Source/evidence inventories, conceptual matrices and standard fresh stable/dated review archives.']},
 'testing':{'focused':'143 passed / 0 failed / 0 errors / 0 skipped, provider-free preservation.','broader':'425-test predecessor reference 405/20; 1,296 predecessor hashes identical. Full baseline not rerun.','full_suite':'Not run.','runtime_validation':'Existing T04/T05/pre-seal/persistence and negative T06 controls only; no implemented marking.','model_runtime_boundary':'0 live provider calls; fail-closed external network and production-data write guards.','new_regressions':'No failures in selected 143 existing controls; no broader regression claim.','pre_existing_failures':'20 in predecessor 425 selection; unchanged byte provenance, not repaired or freshly rerun.'},
 'decisions_requiring_human_review':['Review the Option B architecture and narrow next implementation scope. No approval is required to finish this design/handoff; implementation remains outside this request.'],
 'known_problems':{'campaign_specific':['Original T06 still unsupported; proposed identity/marking/inspection/adapter contracts unimplemented.','Existing file-backed rollback is best-effort on exceptions, not crash-atomic or multi-process.'],'pre_existing':['Twenty baseline failures and T01/T02/T07/T08/T10/T12 gameplay limitations remain.']},
 'missing_concepts':['Persistent instance identity, carried-item mutation/inspection, durable operation dedupe and equipment/material binding await phased implementation.'],
 'does_not_prove':['Successful original or controlled inscription; transfer/removal/reload of a modified object; implemented alternate rulesets; broad playability; full suite; live-model or benchmark acceptance.'],
 'recommended_next_step':'Exactly one: pr_play_object_instance_identity — Stable Identity for Existing Inventory Singletons. See NEXT_STEP_DECISION.md; do not begin implementation automatically.',
 'self_contained_review_test':'Independently reopen stable and dated ZIPs; verify canonical hashes and manifests, all 14 reports, Option B, portability, roadmap, single next milestone and preserved handoff history. Final evidence is archive_verification.json.',
 'primary_report':(REPORT/'SUMMARY.md').relative_to(ROOT).as_posix(),'supporting_files':supports}
dump('review_handoff.json',config)
print('Prepared',len(list(REPORT.glob('*.md'))),'reports;',len(supports),'explicit supports;',counts)
