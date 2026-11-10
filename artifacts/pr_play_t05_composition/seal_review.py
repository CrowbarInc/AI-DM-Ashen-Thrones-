import hashlib,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
ID="pr_play_t05_composition";AP="artifacts/"+ID+"/";RP="development/campaigns/product_realization/"+ID+"/"
REPORTS=["SUMMARY.md","ROOT_CAUSE.md","IMPLEMENTATION.md","T05_BEFORE_AFTER.md","NEGATIVE_CONTROLS.md","REGRESSION_RESULTS.md","TWELVE_TURN_COMPARISON.md","PERFORMANCE.md","NEXT_STEP_DECISION.md","INTEGRITY.md"]
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v): (OUT/n).write_text(json.dumps(v,indent=2),encoding="utf-8")
def check():
    m=read(OUT/"after_source_manifest.json")
    assert all(sha(ROOT/p)==h for p,h in m.items())
    assert read(OUT/"source_changes.json")["changed"]==["game/response_policy_enforcement.py"]
    assert not read(OUT/"source_changes.json")["frozen_changed"]
    assert (ROOT/"docs/NEXT_SESSION.md").read_bytes().endswith((OUT/"entry/docs/NEXT_SESSION.md").read_bytes())
    assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()==read(OUT/"entry_identity.json")["head"]
    assert subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()==read(OUT/"entry_identity.json")["branch"]
check()
if sys.argv[1]=="prepare":
    save("prior_dated_archives.json",{p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/"handoff").glob("CURRENT_REVIEW(*).zip")})
    files=[RP+n for n in REPORTS]+["game/response_policy_enforcement.py","tests/test_pr_play_t05_composition.py","tests/test_pr_play_preseal_authority.py","docs/NEXT_SESSION.md","docs/DEVELOPMENT_CONSTITUTION.md","docs/review_handoff_standard.md"]
    names=["baseline_provenance.json","intermediate_t07_investigation.json","intermediate_twelve_turn_comparison.json","composition_tests_initial.py","before_source_manifest.json","after_source_manifest.json","source_changes.json","production.diff","entry_identity.json","entry_git_status.txt","entry/game/response_policy_enforcement.py","entry/docs/NEXT_SESSION.md","t05_before.json","t05_after.json","t05_comparison.json","test_results.json","twelve_turn_comparison.json","closed_inspection_results.json","prior_dated_archives.json","analyze_results.py","write_reports.py","seal_review.py","run_sequence.py","run_audit.py","run_controls.py","run_focused.py","run_composition.py"]
    for d in ["before","before/authority/authority","focused_before","after_final","after_final/authority","focused_final","new_before_final","new_after_final"]:
        names += [d+"/"+n for n in ["command.json","execution_integrity.json","entry_hashes.json","collected_nodes.json","failures.json"]]
        names += [d+"/"+p.name for p in (OUT/d).glob("*junit.xml")]
    names += ["focused_final/http_capture.json","focused_final/stage_events.json","traced_before/twelve_turn/sequence_summary.json","after_final/twelve_turn/sequence_summary.json"]
    files+= [AP+n for n in names]
    files+= [AP+"review_handoff.json",AP+"evidence_manifest.json"]
    files=sorted(set(files))
    comparison=read(OUT/"t05_comparison.json")
    config={"campaign_id":ID,"campaign_name":"PR-PLAY T05 Authorized Clue Publication Composition Repair","campaign_date":"2026-11-08","purpose":"Prevent unrelated synthetic momentum filler after resolver-selected information, preserving candidate elaboration and immutable acceptance.","objective_status":"A/PASS",
    "executive_summary":"Original T05 HTTP publication improves: "+comparison[0]["published_text"]+" → "+comparison[1]["published_text"]+" Traced source: scene-momentum stock append, now declined for selected disclosures. Only response_policy_enforcement.py changes. Same 398 tests: 378 passed / 20 known failures before and after; 15 new tests pass; combined 393/20. All three closed inspections pass; other eleven turn publications unchanged. Zero live provider calls. Bounded implementation repair, not broad gameplay acceptance.",
    "changes":{"production":["game/response_policy_enforcement.py::enforce_scene_momentum only; existing selected-information metadata declines synthetic stock append before hard validation/sealing."],"validation":["15 new composition cases; same historical selections and 17 pre-seal tests; unchanged original twelve-turn HTTP scenario."],"tooling":["Cycle-owned guarded runners, raw stage/state captures, result comparison and archive seal."],"documentation":["Ten reports and prepended NEXT_SESSION with exact historical suffix."],"generated_artifacts":["Before/after evidence, source hashes, cycle-only diff and fresh review archive."]},
    "testing":{"focused":"New tests 7 pass / 8 fail before to 15/0 after, same test source. Three closed inspections and 17 authority tests pass.","broader":"Same 398: 378/20 before and after. Existing expanded 381: 361/20. Combined 413: 393/20. No collection errors/skips.","full_suite":"Not run","runtime_validation":"Original T05 HTTP path: clue intact, no stock append, normal hard validity, digest and accepted/published/pointer identity. Other eleven published turns unchanged; all routing/disclosures/resolver state/scenes/refusal outcomes preserved. Seven conversational handoff controls and AT-OPT-06 controls pass.","model_runtime_boundary":"Zero live calls, retries or provider token additions. External network blocked; isolated storage.","new_regressions":"None. Twenty baseline failure identities and normalized diagnostics match.","pre_existing_failures":"Twelve obsolete public-resolution assertions, stew mismatch, four refusal/publication cases including portal exception, three unrelated KeyErrors."},
    "decisions_requiring_human_review":[],"known_problems":{"campaign_specific":["Only synthetic momentum selection for resolver-selected new information is repaired; arbitrary existing candidate prose is not reclassified."],"pre_existing":["T01/T07 missing narration; T02 unhelpful NPC; T04/T06 physical completion; T08 generic acknowledgment; T10 trade; T12 operational refusal and twenty baseline failures remain."]},"missing_concepts":["No general relevance classifier or new narrative subsystem introduced."],"does_not_prove":["Broad playability, independent held-out generalization, full-suite acceptance, live-provider behavior or Gameplay Benchmark improvement."],"recommended_next_step":"Exactly one proposed next action: investigate T04 notice-board physical-action completion through its existing local-interaction owner; preserve T05. Do not begin automatically.","self_contained_review_test":"Independently reopen archive; verify ten reports, original T05 before/after traces and publication, same regression failures, source/evidence manifest hashes and preserved NEXT_SESSION history.","primary_report":RP+"SUMMARY.md","supporting_files":[{"path":f,"role":"repair_evidence","canonical":True,"why":"Supports the bounded composition repair, publication/authority regression or provenance.","behavioral_evidence":f.endswith(("t05_before.json","t05_after.json","t05_comparison.json","twelve_turn_comparison.json","closed_inspection_results.json","test_results.json")),"human_review_required":False} for f in files if f!=RP+"SUMMARY.md"],"max_file_bytes":50*1024*1024}
    save("review_handoff.json",config)
    save("evidence_manifest.json",{"milestone":ID,"entries":[{"path":f,"sha256":sha(ROOT/f),"bytes":(ROOT/f).stat().st_size} for f in files if f!=AP+"evidence_manifest.json"],"excluded":"Full raw twelve-turn state/capture trees remain canonical; selected T05 trace/state and compact all-turn comparison are packaged. No runtime storage/cache/prior ZIP.","final_seal_external":True})
    print("Prepared explicit handoff configuration and evidence manifest.")
    sys.exit()
export=OUT/"review_export"
for n in ["CURRENT_REVIEW.md","REVIEW_MANIFEST.json","CURRENT_REVIEW.zip"]:
    tmp=ROOT/"handoff"/(ID+"_"+n+".tmp");shutil.copyfile(export/n,tmp)
    try: os.replace(tmp,ROOT/"handoff"/n)
    except PermissionError:
        shutil.copyfile(tmp,ROOT/"handoff"/n);tmp.unlink()
stamp=datetime.now(timezone(timedelta(hours=-5))).strftime("%Y%m%d-%H%M%S")
archive=ROOT/"handoff"/("CURRENT_REVIEW("+stamp+").zip");assert not archive.exists();shutil.copyfile(ROOT/"handoff/CURRENT_REVIEW.zip",archive)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names=z.namelist();manifest=json.loads(z.read("REVIEW_MANIFEST.json"))
    assert manifest["campaign_id"]==ID and ID in z.read("CURRENT_REVIEW.md").decode()
    assert all("support/"+RP+n in names for n in REPORTS)
    assert all(o["reason"].startswith("duplicate content of ") for o in manifest["omitted_artifacts"])
    for row in manifest["included_files"]:
        data=z.read(row["bundle_path"])
        if row.get("sha256"): assert hashlib.sha256(data).hexdigest()==row["sha256"]
        if row.get("canonical_source_path"): assert data==(ROOT/row["canonical_source_path"]).read_bytes()
    for row in json.loads(z.read("support/"+AP+"evidence_manifest.json"))["entries"]:
        assert sha(ROOT/row["path"])==row["sha256"]
        if "support/"+row["path"] in names: assert hashlib.sha256(z.read("support/"+row["path"])).hexdigest()==row["sha256"]
        else: assert any(o.get("sha256")==row["sha256"] for o in manifest["omitted_artifacts"])
    handoff=z.read("support/docs/NEXT_SESSION.md");assert handoff==(ROOT/"docs/NEXT_SESSION.md").read_bytes() and handoff.endswith((OUT/"entry/docs/NEXT_SESSION.md").read_bytes())
    t=json.loads(z.read("support/"+AP+"t05_comparison.json"))
    assert t[0]["stock_renderer_called"] and not t[1]["stock_renderer_called"] and t[0]["authorized_clue"]==t[1]["authorized_clue"]
    assert t[0]["published_text"]!=t[1]["published_text"] and t[1]["published_text"]==t[1]["accepted_text"]==t[1]["publication_pointer"] and t[1]["digest_verified"]
    r=json.loads(z.read("support/"+AP+"test_results.json"));assert r["baseline_before"]==r["baseline_after"]=={"passed":378,"failed":20,"errors":0,"skipped":0} and not r["changed_outcomes"] and not r["normalized_failure_differences"] and r["new_tests_after"]["passed"]==15
    assert len(json.loads(z.read("support/"+AP+"closed_inspection_results.json")))==3
    assert [x["id"] for x in json.loads(z.read("support/"+AP+"twelve_turn_comparison.json")) if not x["text_identical"]]==["T05"]
    assert not any("/.git/" in n.lower() or "/.env" in n.lower() or n.lower().endswith(".zip") for n in names)
assert sha(archive)==sha(ROOT/"handoff/CURRENT_REVIEW.zip")
with zipfile.ZipFile(ROOT/"handoff/CURRENT_REVIEW.zip") as z: assert z.testzip() is None and z.namelist()==names
for f,h in read(OUT/"prior_dated_archives.json").items(): assert sha(ROOT/f)==h
for d in ["before","before/authority/authority","focused_before","new_before_final","new_after_final","after_final","after_final/authority","focused_final"]:
    integrity=read(OUT/d/"execution_integrity.json");assert not integrity["changed"] and not integrity["network_attempts_blocked"] and integrity["live_provider_calls"]==0
# New test source was identical across both composition runs.
key="tests\\test_pr_play_t05_composition.py"
assert read(OUT/"new_before_final/entry_hashes.json")[key]==read(OUT/"new_after_final/entry_hashes.json")[key]
check()
digest=sha(archive)
save("archive_verification.json",{"status":"PASS","milestone":ID,"archive_path":str(archive),"sha256":digest,"stable_dated_equal":True,"crc_verified":True,"all_canonical_hashes_verified":True,"evidence_hashes_verified":True,"reports":10,"t05_publication_verified":True,"regression_results_verified":True,"closed_inspections":3,"handoff_history_preserved":True,"prior_archives_preserved":True,"source_changes":["game/response_policy_enforcement.py"],"frozen_unchanged":read(OUT/"source_changes.json")["frozen_checked"],"live_provider_calls":0})
(OUT/"archive_sha256.txt").write_text(str(archive)+"\nSHA-256: "+digest+"\n")
(OUT/"archive_contents.txt").write_text("\n".join(names)+"\n")
(OUT/"final_git_status.txt").write_bytes(subprocess.check_output(["git","status","--short"],cwd=ROOT))
save("files_created.json",{"reports":[RP+n for n in REPORTS],"test":"tests/test_pr_play_t05_composition.py","evidence":AP,"archive":str(archive)})
print(json.dumps({"status":"PASS","archive":str(archive),"sha256":digest}))
