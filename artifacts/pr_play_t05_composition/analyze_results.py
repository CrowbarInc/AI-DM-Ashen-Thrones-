import json, hashlib, re, difflib
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ID = "pr_play_t05_composition"
def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding="utf-8")
def run(d,xml):
    suite=ET.parse(OUT/d/xml).getroot()[0]
    rows=[]
    for c in suite.findall("testcase"):
        status=next((x for x in ["failure","error","skipped"] if c.find(x) is not None),"passed")
        rows.append({"nodeid":c.get("classname").replace(".","/")+".py::"+c.get("name"),"status":status,"seconds":c.get("time")})
    return {"directory":d,"counts":{k:sum(c["status"]==s for c in rows) for k,s in [("passed","passed"),("failed","failure"),("errors","error"),("skipped","skipped")]},"nodes":rows,"command":read(OUT/d/"command.json"),"failures":read(OUT/d/"failures.json")}
runs=[run(d,x) for d,x in [("before","baseline_junit.xml"),("before/authority/authority","recovery_junit.xml"),("focused_before","baseline_junit.xml"),("after_final","baseline_junit.xml"),("after_final/authority","recovery_junit.xml"),("focused_final","baseline_junit.xml"),("new_before_final","baseline_junit.xml"),("new_after_final","baseline_junit.xml")]]
def totals(rs): return {k:sum(r["counts"][k] for r in rs) for k in runs[0]["counts"]}
b={r["nodeid"]:r["status"] for run_ in runs[:3] for r in run_["nodes"]};a={r["nodeid"]:r["status"] for run_ in runs[3:6] for r in run_["nodes"]}
assert b.keys()==a.keys()
new=[k for k in a if a[k]!=b[k]]
def norm(s):
    s=re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}","<UUID>",s)
    s=re.sub(r'(\"turn_id\": \"?)[0-9a-f]{32}',r'\1<TURN_ID>',s)
    return re.sub(r"0x[0-9A-Fa-f]+","<ADDRESS>",s)
bf={f["nodeid"]:norm(f["traceback"]) for run_ in runs[:3] for f in run_["failures"]};af={f["nodeid"]:norm(f["traceback"]) for run_ in runs[3:6] for f in run_["failures"]}
results={"milestone":ID,"runs":runs,"baseline_before":totals(runs[:3]),"baseline_after":totals(runs[3:6]),"expanded_without_preseal_before":totals(runs[:2]),"expanded_without_preseal_after":totals(runs[3:5]),"new_tests_before":runs[6]["counts"],"new_tests_after":runs[7]["counts"],"combined_after":totals(runs[3:6]+[runs[7]]),"changed_outcomes":new,"newly_failing":[k for k in new if a[k]!="passed"],"unchanged_known_failures":sorted(af),"normalized_failure_differences":[k for k in bf if bf[k]!=af.get(k)],"live_provider_calls":0}
save("test_results.json",results)

def find(v,key):
    if isinstance(v,dict):
        if key in v: return v[key]
        for val in v.values():
            hit=find(val,key)
            if hit is not None: return hit
    if isinstance(v,list):
        for val in v:
            hit=find(val,key)
            if hit is not None: return hit

def digest(record):
    payload={k:v for k,v in record.items() if k not in {"integrity_digest","skipped_mutators"}}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()==record["integrity_digest"]
comparison=[]
for side,d in [("before","traced_before"),("after","after_final")]:
    seq=read(OUT/d/"twelve_turn/turns.json");events=read(OUT/d/"twelve_turn/stage_trace.json")
    t=next(r for r in seq if r["id"]=="T05");te=[e for e in events if e["turn"]=="T05"]
    m=next(e for e in te if e["function"].endswith(".enforce_scene_momentum"))
    seal=next(e for e in te if e["function"].endswith(".seal_accepted_response"))
    record=seal["result"]["metadata"]["accepted_response"]
    assert digest(record) and record["text"]==t["visible"]==t["after"]["publication_visible"]
    assert t["full_before"]["character"]==t["full_after"]["character"]
    assert t["before"]["scene_id"]==t["after"]["scene_id"]
    save("t05_"+side+".json",{"milestone":ID,"turn":t,"stage_events":te})
    comparison.append({"side":side,"request":t["player_text"],"initial_candidate":m["args"][0]["player_facing_text"],"composed_candidate":m["result"]["player_facing_text"],"preseal_candidate":next(e for e in te if e["function"].endswith(".run_preserve_if_valid"))["args"][0]["player_facing_text"],"authorized_clue":m["kwargs"]["resolution"]["clue_text"],"composition":m["result"].get("metadata",{}).get("emission_debug",{}).get("scene_momentum_composition"),"stock_renderer_called":any(e["function"].endswith(".render_scene_momentum_diegetic_append") for e in te),"accepted_text":record["text"],"hard_valid":record["hard_validation"]["hard_valid"],"digest_verified":digest(record),"published_text":t["visible"],"publication_pointer":t["after"]["publication_visible"],"before":t["before"],"after":t["after"],"character_unchanged":True})
save("t05_comparison.json",comparison)
before=read(OUT/"traced_before/twelve_turn/turns.json");after=read(OUT/"after_final/twelve_turn/turns.json")
turns=[]
for b,a in zip(before,after):
    # Session histories/UUIDs and derived momentum bookkeeping can differ after T05.
    def resolution(r): return r["full_after"]["log"][-1].get("resolution",{})
    br,ar=resolution(b),resolution(a)
    turns.append({"id":b["id"],"request":b["player_text"],"before":b["visible"],"after":a["visible"],"text_identical":b["visible"]==a["visible"],"intent_before":br.get("kind"),"intent_after":ar.get("kind"),"disclosures_equal":br.get("discovered_clues")==ar.get("discovered_clues"),"state_changes_equal":br.get("state_changes")==ar.get("state_changes"),"scene_equal":b["after"]["scene_id"]==a["after"]["scene_id"],"refusal_before":b["log"].get("refusal_category"),"refusal_after":a["log"].get("refusal_category"),"pointer_before":b["after"]["publication_visible"],"pointer_after":a["after"]["publication_visible"],"route_before":b["log"].get("route"),"route_after":a["log"].get("route"),"ms_before":b["elapsed_ms"],"ms_after":a["elapsed_ms"]})
save("twelve_turn_comparison.json",turns)
cases=[]
for n,rows in read(OUT/"focused_final/http_capture.json").items():
    if "test_http_publication_matches_prepared_authority" not in n: continue
    r=rows[-1];gm=r["raw_before_projection"];record=find(gm,"accepted_response");note=find(gm,"closed_surface_preparation");line=r["response"]["gm_output"]["player_facing_text"]
    assert record["text"]==line==r["after"]["session"]["last_publication"]["visible"] and digest(record)
    cases.append({"nodeid":n,"request":r["request"],"published":line,"authority":note["classification"],"hard_valid":record["hard_validation"]["hard_valid"],"digest_verified":True,"character_unchanged":r["before"]["character"]==r["after"]["character"],"passed":not any(f["nodeid"]==n for f in runs[5]["failures"])})
save("closed_inspection_results.json",cases)
manifest={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ["game","tests","data","static","prompts"] for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc"}
manifest={str(Path(k).relative_to(ROOT)).replace("\\","/"):v for k,v in manifest.items()}
for name in ["requirements.txt","pytest.ini"]: manifest[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
save("after_source_manifest.json",manifest)
old=read(OUT/"before_source_manifest.json")
save("source_changes.json",{"changed":[k for k,v in old.items() if manifest.get(k)!=v],"added":sorted(set(manifest)-set(old)),"frozen_checked":sum(k.startswith(("tests/fixtures/","data/validation/")) for k in old),"frozen_changed":[k for k in old if k.startswith(("tests/fixtures/","data/validation/")) and old[k]!=manifest.get(k)]})
source="game/response_policy_enforcement.py"
(OUT/"production.diff").write_text("".join(difflib.unified_diff((OUT/"entry"/source).read_text(encoding="utf-8").splitlines(True),(ROOT/source).read_text(encoding="utf-8").splitlines(True),fromfile="before/"+source,tofile="after/"+source)))
print(json.dumps({k:v for k,v in results.items() if k!="runs"},indent=2))
