"""Verify portable report links, manifest payloads and untouched protected files."""
import hashlib,json,re,sys,zipfile,posixpath
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(OUT))
from investigate import protected
base=json.loads((OUT/'baseline.json').read_text());now=protected()
changed=[p for p,h in base['protected'].items() if now.get(p)!=h]
added=[p for p in now if p not in base['protected']]
manifest=json.loads((ROOT/'handoff/REVIEW_MANIFEST.json').read_text(encoding='utf-8'))
errors=[];links=0;hashes=0
with zipfile.ZipFile(ROOT/'handoff/CURRENT_REVIEW.zip') as z:
    names=set(z.namelist())
    for item in manifest['included_files']:
        name=item['bundle_path']
        if name not in names:errors.append('missing '+name);continue
        if item.get('sha256'):
            hashes+=1
            if hashlib.sha256(z.read(name)).hexdigest()!=item['sha256']:errors.append('hash '+name)
    reports=[n for n in names if re.search(r'/pr_eg_r5/\d\d_[^/]+\.md$',n)]
    for report in reports:
        for link in re.findall(r'\]\(([^)]+)\)',z.read(report).decode('utf-8')):
            if '://' in link:continue
            links+=1;target,_,anchor=link.partition('#')
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(report),target))
            if resolved not in names:errors.append(f'link {report} -> {resolved}');continue
            if anchor.startswith('L') and resolved.endswith('.py'):
                line=int(anchor[1:])
                if line<1 or line>len(z.read(resolved).splitlines()):errors.append(f'line {resolved}:{line}')
    if len(reports)!=27:errors.append(f'reports={len(reports)}')
    for name in ['CURRENT_REVIEW.md','REVIEW_MANIFEST.json']:
        if z.read(name)!=(ROOT/'handoff'/name).read_bytes():errors.append('handoff mismatch '+name)
result=dict(reports=len(reports),hashes_verified=hashes,report_links_checked=links,protected_files_checked=len(now),protected_changed=changed,protected_added=added,errors=errors,zip_bytes=(ROOT/'handoff/CURRENT_REVIEW.zip').stat().st_size)
(OUT/'bundle_verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
sys.exit(bool(errors or changed or added))
