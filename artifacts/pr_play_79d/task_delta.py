"""Reconstruct pre-edit source from entry diff and the recorded patch preimages."""
import difflib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
TEMP=ROOT/'development/tmp/pr79d_entry_source'
tracked=['game/api.py','game/exploration.py','game/bounded_improvisation.py']
entry=(OUT/'entry.diff').read_text(encoding='utf-8')
patch=[]
for path in tracked:
    target=TEMP/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT))
    chunk=next(c for c in entry.split('diff --git ') if c.startswith('a/'+path+' '))
    relocated='development/tmp/pr79d_entry_source/'+path
    chunk=('diff --git '+chunk).replace('a/'+path,'a/'+relocated).replace('b/'+path,'b/'+relocated)
    patch.append(chunk)
patch_path=OUT/'entry_reconstruction.patch'
patch_path.write_text(''.join(patch),encoding='utf-8')
subprocess.run(['git','apply','--ignore-space-change',str(patch_path)],cwd=ROOT,check=True)
before={p:(TEMP/p).read_text(encoding='utf-8') for p in tracked}
p='game/publication_contract.py'
s=(ROOT/p).read_text(encoding='utf-8')
start=s.index('\ndef record_completed_publication(')
end=s.index('# These already have',start)
s=s[:start]+'\n'+s[end:]
s=s.replace('        meta = {}\n    contract =', '        meta = {}\n        resolution["metadata"] = meta\n    contract =')
s=s.replace('        line = published or KNOWN_REPEAT_LINE\n        return', '        line = published or KNOWN_REPEAT_LINE\n        stamp(meta, FINAL_ENGINE_RESPONSE, publication=line)\n        return')
before[p]=s
p='game/quarantined_investigation_narration.py'
s=(ROOT/p).read_text(encoding='utf-8')
start=s.index('def verify_engine_publication(');end=s.index('def verify_authoritative_publication(',start)
before[p]=s[:start]+s[end:]
p='game/player_http_boundary.py'
s=(ROOT/p).read_text(encoding='utf-8')
start=s.index('            if (request.url.path in')
end=s.index('\n        return handle',start)
s=s[:start]+s[end:]
s=s.replace('final = JSONResponse','return JSONResponse')
before[p]=s
for p in ['tests/test_pr_play_61_player_facing.py','tests/test_pr_play_62_investigation_quality.py','tests/test_pr_play_69_target_references.py']:
    s=(ROOT/p).read_text(encoding='utf-8')
    if '61_player' in p:
        start=s.index('    # A repeat is a direct engine recall')
        end=s.index('    decisions =', start)
        s=s[:start]+'    assert published == [True, True, True, True]\n'+s[end:]
        s=s.replace('    assert continued["gm_output"]["player_facing_text"].startswith("You examine the notice board again")\n    assert ROUTE in continued["gm_output"]["player_facing_text"]',
                    '    assert continued["gm_output"]["player_facing_text"].startswith("You examine the board again")')
    elif '62_investigation' in p:
        s=s.replace("    assert texts[2].startswith('You examine the notice board again.')\n    assert ROUTE in texts[2] and 'nothing new' in texts[2]",
                    "    assert texts[2] == ('You examine the notice board again. '\n                        'The examination adds nothing new to what you already know.')")
        s=s.replace('    assert all(ROUTE not in texts[index] for index in (1, 3, 4))', '    assert all(ROUTE not in t for t in texts[1:])')
    else:
        start=s.index("        assert text.startswith('You examine the weathered milestone again.')")
        end=s.index('    assert calls==',start)
        s=s[:start]+"        assert text=='You examine the weathered milestone again. The examination adds nothing new to what you already know.'\n"+s[end:]
    before[p]=s
result=[]
for path, original in before.items():
    current=(ROOT/path).read_text(encoding='utf-8')
    result.extend(difflib.unified_diff(original.splitlines(True),current.splitlines(True),fromfile='a/'+path,tofile='b/'+path))
for path in ['tests/test_pr_play_79d_closeout.py','tests/test_pr_play_79d_holdout.py']:
    result.extend(difflib.unified_diff([], (ROOT/path).read_text(encoding='utf-8').splitlines(True),fromfile='/dev/null',tofile='b/'+path))
(OUT/'task_source.diff').write_text(''.join(result),encoding='utf-8')
print('Task diff reconstructed. Tracked preimages use entry git diff; untracked preimages reverse recorded edits.')
