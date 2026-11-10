"""Classify surviving Git snapshot candidates without executing their source."""
import collections, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
data=json.loads((OUT/'git_provenance.json').read_text())
rows=[r.split() for r in data['unreachable']['stdout'].splitlines() if r.startswith('unreachable ')]
commits=[r[2] for r in rows if r[1]=='commit']
refs=[r.split() for r in data['refs']['stdout'].splitlines()]
commits += [r[0] for r in refs if r[1].startswith('refs/codex/')]
commits += [subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()]
paths=['game/conversational_orchestration.py','game/player_http_projection.py','game/immutable_valid_response.py','game/perception_grounding.py','tests/test_referenced_surface_grounding_inspection_resolution.py','tests/test_pr_play_post_npc_handoff.py','requirements.txt']
result=[]
for oid in commits:
    meta=subprocess.check_output(['git','show','-s','--format=%H%n%cI%n%s',oid],cwd=ROOT,text=True).splitlines()
    files={}
    for path in paths:
        r=subprocess.run(['git','show',oid+':'+path],cwd=ROOT,capture_output=True)
        files[path]={'exists':r.returncode==0,'sha256':hashlib.sha256(r.stdout).hexdigest() if r.returncode==0 else None,
          'authored_travel_admission':b'def authored_travel_admission' in r.stdout if path.endswith('orchestration.py') else None}
    result.append({'object':oid,'commit_time':meta[1],'subject':meta[2],'files':files,
      'authentication':'Not the Nov 8 pre-repair dirty environment: missing later player projection and/or authored-travel dependency; no capture binding to repair entry.'})
(OUT/'git_candidate_assessment.json').write_text(json.dumps({'object_counts':dict(collections.Counter(r[1] for r in rows)),
 'candidates':result,'loose_blob_tree_limit':'Unattached blobs/trees have no creation time or coherent working-source/test/dependency capture binding. No historical branch reconstruction attempted.',
 'verdict':'No authenticated pre-repair development snapshot; Condition B after bounded sources examined.'},indent=2))
print(json.dumps({'candidates':len(result),'object_counts':dict(collections.Counter(r[1] for r in rows))}))
