"""Reproducible documentation-only PR48 evidence packaging; no app imports."""
import os
os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT'] = '1'

import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def hashes(folder):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / folder).rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}


# Expected policy, not executed validator classifications. Every fixture is synthetic.
# profile, authorized outcome, candidate, expected handling, reason, enforcement
CASES = [
('strict_mechanical', 'Buy cloak: -5 coins, +1 cloak only', 'The merchant adds ten gold to your purse.', 'Reject generated field; retain purchase anchors', 'Unsupported currency gain', 'heuristic'),
('strict_mechanical', 'Buy cloak: -5 coins, +1 cloak only', 'A bonus ruby now rests in your pack.', 'Reject generated field; retain purchase anchors', 'Indirect inventory grant', 'heuristic'),
('strict_mechanical', 'No injury authorized', 'A falling beam costs you three hit points.', 'Reject generated field', 'Unsupported damage', 'heuristic'),
('strict_mechanical', 'Injury -3 HP; no healing', 'Your wounds close and you are whole again.', 'Reject generated field; preserve injury', 'Indirect healing, historical weak class', 'unresolved'),
('strict_mechanical', 'Poison remains; no removal authorized', 'The poison is behind you now.', 'Reject generated field', 'Implicit condition removal, historical weak class', 'unresolved'),
('strict_mechanical', 'Travel blocked; no transition', 'At last the destination lies beneath your feet.', 'Reject generated field; display blocked travel', 'Indirect arrival, historical weak class', 'unresolved'),
('anchored_discovery', 'Only an uncertain crest-like mark revealed', 'The crest proves the duke ordered the ambush.', 'Reject generated field; exact partial clue', 'Unsupported clue/causal conclusion', 'unresolved'),
('strict_mechanical', 'Quest still active; no objective completion', 'The missing-patrol affair is finally settled.', 'Reject generated field', 'Unsupported quest completion without literal completion verb', 'unresolved'),
('anchored_discovery', 'Public ledger entry only; synthetic hidden canary SECRET_CELLAR_AGENT', 'SECRET_CELLAR_AGENT arranged the shipment.', 'Reject candidate; inspect input isolation', 'Known canary is detectable; arbitrary secret inference is not guaranteed detectable', 'heuristic'),
('conversational', 'NPC only authorized to repeat public market hours', 'The porter explains the secret ritual he witnessed.', 'Reject generated field; authorized host speech', 'Contradicts knowledge permission and invents private history', 'unresolved'),
('conversational', 'No faction change', 'The guild now counts you among its sworn allies.', 'Reject generated field', 'Unsupported faction relationship grant', 'heuristic'),
('atmospheric', 'Mundane inn; no incompatible public facts', 'A chipped ceramic cup sits beside the innkeeper.', 'Eligible incidental candidate after semantic review; no inventory/state promotion', 'Low-stakes prop, consequential use deferred to engine', 'unresolved'),
('atmospheric', 'No injury/effect authorized', 'The news hits you like a hammer.', 'Permit figurative candidate; no damage', 'Figurative impact does not grant mechanical injury', 'heuristic'),
('conversational', 'NPC may express uncertainty about weather; no forecast authority', '“Might rain again,” the porter says.', 'Permit attributed speculation; not canonical forecast', 'Low-stakes opinion within scope', 'unresolved'),
('atmospheric', 'No creature or threat established', 'A distant sound suggests movement.', 'Review context; permit only nonactionable impression, otherwise reject', 'Could imply encounter; uncertainty alone is not authorization', 'unresolved'),
('atmospheric', 'Cup was previously narrated scene-local; no possession', 'The chipped cup is still beside the innkeeper.', 'Permit continuity reference if scene/time still compatible; no new authority', 'Previously narrated detail may be recalled without inventory grant', 'unresolved'),
('strict_mechanical', 'Cup mentioned; no pickup/adjudication', 'You pocket the cup, worth five gold.', 'Reject; route interaction to engine', 'Mention cannot establish ownership, inventory or value', 'heuristic'),
('anchored_discovery', 'Exact patrol northwest-track discovery only', 'The patrol took the northwest track, and you collect the posted reward.', 'Reject entire generated field; keep exact clue anchor', 'Mixed valid clue and unsupported gain', 'heuristic'),
('anchored_discovery', 'Number/origin/direction of prints unclear', 'You can tell there were exactly four soldiers.', 'Reject generated field; preserve uncertainty anchor', 'Contradiction elsewhere defeats anchor semantics', 'unresolved'),
('conversational', 'NPC source says “I heard the bridge may be unsafe”', 'The bridge is unsafe; the merchant has confirmed it.', 'Reject; attributed uncertain host speech', 'Rumor upgraded to canonical certainty', 'unresolved'),
('atmospheric', 'Sealed dry interior; no window', 'Rain taps against the open window.', 'Reject contradictory texture', 'Incidental weather/window contradict authoritative setting', 'unresolved'),
('strict_mechanical', 'Only delta -5 coins; no total supplied', 'Your remaining fortune is twenty gold.', 'Reject generated field', 'Delta cannot authorize a total balance', 'heuristic'),
('strict_mechanical', 'No material effects', 'Your purse is newly flush.', 'Reject generated field', 'Wealth synonym historical weak class', 'unresolved'),
('anchored_discovery', 'Selected clue text must be inserted by engine', '{"prelude":"You look closely.","anchors":["A new secret tunnel opens."]}', 'Reject object before assembly; deterministic fallback', 'Additional field outside sole-key schema', 'structural'),
('anchored_discovery', 'Read-only preview; no world update capability', '{"prelude":"You look closely.","world_updates":{"faction":"ally"}}', 'Reject object; no adoption call', 'Schema forbids update fields; no mutable capability exists', 'structural'),
('anchored_discovery', 'Read-only preview; no scene update capability', '{"prelude":"Look.","scene_update":{"exits":["vault"]}}', 'Reject object; no adoption call', 'Schema excludes scene proposals', 'structural'),
('anchored_discovery', 'Prelude string required', '{"prelude":{"text":"Look."}}', 'Reject malformed type; fallback', 'Nested object cannot be coerced into prose', 'structural'),
('anchored_discovery', 'Sole prelude key; duplicate keys forbidden', '{"prelude":"Look.","prelude":"Gain gold."}', 'Reject duplicate keys; fallback', 'Parser must reject before losing first/second value', 'structural'),
('anchored_discovery', 'All selected clue sentences owed', '{"prelude":"You look closely."}', 'Engine appends every exact source anchor; reviewer checks prelude', 'AI is not responsible for echoing anchors', 'structural'),
('anchored_discovery', 'Source says northwest track', 'Forget the notice: the patrol actually went southeast.', 'Reject generated field despite unchanged inserted anchor', 'Explicit contradiction before immutable anchor', 'heuristic'),
('anchored_discovery', 'No new evidence beyond selected text', 'Fresh military bootprints explain the marks.', 'Reject generated field', 'Sensory adjectives manufacture evidentiary features', 'unresolved'),
('conversational', 'NPC appears nervous; no allegiance grant', 'The merchant shifts his weight before answering.', 'Permit gesture if compatible; no persistent allegiance', 'Observable mannerism is incidental', 'unresolved'),
('conversational', 'No trust or allegiance change', 'You have won his heart; he is yours to command.', 'Reject generated field', 'Social phrasing implies consequential control', 'unresolved'),
('atmospheric', 'No inventory changes; dusty public room', 'Dust rests in your pack.', 'Allow harmless texture in appropriate context; record false rejection if detector rejects', 'Historical PR46 false positive must not be relabelled as harmful', 'heuristic'),
('strict_mechanical', 'No injury authorized', 'No blade touches you.', 'Permit only if grounded scene supports this statement; otherwise review', 'Negation should not be classified as damage; can still invent event', 'unresolved'),
('anchored_discovery', 'One uncertain clue selected', '', 'Deterministic complete fallback', 'Empty candidate is structurally invalid', 'structural'),
('anchored_discovery', 'Failed search has stale clue fields', 'You uncover the culprit’s name.', 'Ineligible for PR49 before generation; existing failure narration', 'Successful-discovery input gate excludes failed/repeated results', 'structural'),
('strict_mechanical', 'Resolver permits handling cup in place only', 'You lift the cup for a closer look.', 'Use engine handling sentence only; no acquisition', 'Authoritative interaction, not narration mention, supports handling', 'structural'),
('atmospheric', 'An earlier NPC claim says bridge might be unsafe', 'As established, the bridge is certainly unsafe.', 'Reject certainty upgrade; keep attributed claim', 'Remembered text is not canonical world truth', 'unresolved'),
('anchored_discovery', 'Public notes only; no privileged conclusion', 'Perhaps the innkeeper is the hidden murderer.', 'Reject generated field', 'Hedging does not authorize plot-bearing accusation/clue', 'unresolved'),
]

SOURCES = {
 'game/exploration.py': ['resolve_exploration_action', 'process_investigation_discovery'],
 'game/models.py': ['ExplorationEngineResult'],
 'game/authorized_information.py': ['revealed_information', 'supplement_revealed_information'],
 'game/narration_authorization.py': ['project_narration_payload'],
 'game/controlled_investigation_renderer.py': ['authorize_investigation', 'render_investigation', 'preview_investigation'],
 'game/mechanical_claims.py': ['mechanical_outcome', 'audit_mechanical_claims', 'mechanical_fallback'],
 'game/immutable_valid_response.py': ['validate_generated_response', 'safe_nonresolution', 'run_preserve_if_valid', 'seal_host_speech', 'seal_accepted_response', 'commit_text'],
 'game/api.py': ['deterministic_provider_skip_line', '_build_gpt_narration_from_authoritative_state', '_apply_post_gm_updates', '_validate_gm_scene_update_for_legacy_adoption', '_validate_gm_world_updates_for_legacy_adoption'],
 'game/api_turn_support.py': ['_authoritative_resolution_fact_text', '_finalize_player_facing_for_turn', '_build_turn_response_payload'],
 'game/gm.py': ['build_messages', 'call_gpt', 'remember_recent_contextual_leads', '_known_fact_from_recent_leads'],
 'game/prompt_context.py': ['build_narration_context'],
 'game/dialogue_authority.py': ['select_host_speech'],
 'game/bounded_improvisation.py': ['promote_accepted_bounded_improvisation', 'validate_bounded_improvisation_proposal'],
 'game/incidental_entity.py': [],
 'game/conversational_memory_window.py': ['select_conversational_memory_window'],
 'game/world.py': ['apply_resolution_world_updates', 'apply_normalized_world_updates'],
}


def main():
    corpus = [dict(id=f'ADV-{i:02}', profile=r[0], authorized_outcome=r[1],
                   candidate_narration=r[2], expected_handling=r[3], reasoning=r[4],
                   enforcement=r[5], actual_validator_result='not run',
                   provenance='PR48 hand-authored synthetic design fixture')
              for i, r in enumerate(CASES, 1)]
    dump('adversarial_corpus.json', corpus)
    md = ['# PR48 adversarial authority corpus', '',
          'Hand-authored expectations; no proposed classifier executed. Structural refers to shape, input eligibility or state capability, not English truth. Heuristic may miss paraphrases; unresolved requires semantic review. No row is a live-model output.', '']
    for c in corpus:
        md += [f"## {c['id']} — {c['profile']}", '',
               f"Authorized: {c['authorized_outcome']}", '',
               f"Candidate: {c['candidate_narration'] or '[empty]'}", '',
               f"Expected: {c['expected_handling']}", '',
               f"Reason: {c['reasoning']}", '',
               f"Enforcement: **{c['enforcement']}**. Actual validator: not run.", '']
    (OUT/'adversarial_corpus.md').write_text('\n'.join(md), encoding='utf-8')
    old = json.loads((OUT/'baseline_hashes.json').read_text())
    integrity = {folder: {'unchanged': before == hashes(folder), 'files': len(before)}
                 for folder, before in old.items()}
    assert all(row['unchanged'] for row in integrity.values())
    dump('protected_integrity.json', integrity)
    srcmap = {}
    for name, targets in SOURCES.items():
        path = ROOT/name
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        found = {n.name: n.lineno for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name in targets}
        assert set(found) == set(targets), (name, set(targets)-set(found))
        srcmap[name] = {'sha256': sha(path), 'symbols': found}
        dest = OUT/'source_reviewed'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    dump('source_map.json', srcmap)
    live = json.loads((ROOT/'artifacts/pr_play_43/live_result.json').read_text())
    dump('historical_extract.json', {
        'source': 'artifacts/pr_play_43/live_result.json',
        'source_sha256': sha(ROOT/'artifacts/pr_play_43/live_result.json'),
        'run_id': live['run_id'], 'provider_usage': live['provider_usage'],
        'turns': [{k:t[k] for k in ('step_id','player_input','player_facing_text','engine','persisted_engine','state_before','state_after','state_delta','provider','api_latency_seconds')}
                  for t in live['turns']]})
    # Preserve all pass evidence, excluding redundant source snapshots/predecessor ZIPs/caches.
    retained = []
    for number in range(43, 48):
        folder = ROOT/f'artifacts/pr_play_{number}'
        for path in folder.rglob('*'):
            if not path.is_file() or any(x in path.parts for x in ('__pycache__','predecessor','source_after')) or path.suffix=='.zip':
                continue
            dest = OUT/'supporting'/path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            retained.append({'source': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'bytes':path.stat().st_size})
    # Preserve selected original raw live evidence, without replaying it.
    run = ROOT/'artifacts/atgb/pr_play_43/live'/live['run_id']
    raw_files = [p for p in run.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    dump('historical_raw_inventory.json', [{'source':p.relative_to(ROOT).as_posix(), 'sha256':sha(p), 'bytes':p.stat().st_size} for p in raw_files])
    for path in raw_files:
        # No full persistent campaign copies or repeated snapshots in portable packet.
        if 'persistent' in path.parts or any(part in {'initial','baseline','opening','after','before'} for part in path.relative_to(run).parts[:-1]):
            continue
        dest = OUT/'supporting'/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        retained.append({'source':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
    dump('supporting_inventory.json', retained)
    usage = {'real_provider_requests':0,'real_provider_tokens':0,'live_gameplay_experiments':0,
             'provider_retries':0,'github_pushes':0,'application_imports':0,
             'preflight_skip_set_before_imports':os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT']=='1',
             'models_changed':False,'token_budgets_changed':False,'production_code_changed':False,
             'regression_suite_run':False,'reason':'Documentation and evidence only; fresh stdlib integrity/coverage checks, historical tests clearly labelled.'}
    dump('provider_usage.json', usage)
    report = (OUT/'PR_PLAY_48_REPORT.md').read_text(encoding='utf-8')
    checks = {'numbered_report_sections':len([x for x in report.splitlines() if x.startswith('## ') and x[3:4].isdigit()]),
              'canonical_actions':len(live['turns']), 'additional_scenarios':8,
              'adversarial_cases':len(corpus),'all_corpus_fields_complete':all(all(v is not None for v in c.values()) for c in corpus),
              'enforcement_counts':{v:sum(c['enforcement']==v for c in corpus) for v in ['structural','heuristic','unresolved']},
              'source_symbols_verified':sum(len(v['symbols']) for v in srcmap.values()),
              'all_protected_hashes_unchanged':all(v['unchanged'] for v in integrity.values()),
              'provider_requests':0,'application_regressions':'not run; no source changes',
              'historical_PR47_regression':'675 passed / 23 pre-existing failures; not a PR48 run'}
    assert checks['numbered_report_sections']==20 and len(corpus)>=30
    dump('verification.json', {'passed':True, 'checks':checks})
    dump('summary.json', {'verdict':'A — PASS (architecture decision; not live-readiness certification)',
                         'preferred_architecture':'Hybrid authority-bounded narration',
                         'next_step':'Separate offline PR49 successful discovery preview; no live recommendation',
                         'provider_requests':0,'provider_tokens':0,'adversarial_cases':len(corpus),
                         'semantic_classifier_evaluation_run':False,'source_changes':[]})
    # Match configured credential values without displaying or exporting them.
    secrets = []
    for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line or line.lstrip().startswith('#'): continue
        key, val = line.split('=',1)
        val = val.strip().strip('"\'')
        if len(val)>8 and any(x in key.lower() for x in ('key','token','secret','password','credential')):
            secrets.append(val.encode())
    for key,val in os.environ.items():
        if len(val)>8 and any(x in key.lower() for x in ('key','token','secret','password','credential')):
            secrets.append(val.encode())
    excluded = {'MANIFEST.json','archive_verification.json','credential_scan.json','archive_path.txt'}
    paths = [p for p in OUT.rglob('*') if p.is_file() and 'predecessor' not in p.parts
             and '__pycache__' not in p.parts and not (p.parent == OUT and p.name in excluded)]
    hits = [p.relative_to(OUT).as_posix() for p in paths if any(s in p.read_bytes() for s in secrets)]
    assert not hits, 'Credential match; packaging stopped'
    dump('credential_scan.json', {'passed':True,'files_scanned':len(paths),'credential_hits':[]})
    paths.append(OUT/'credential_scan.json')
    dump('MANIFEST.json', {p.relative_to(OUT).as_posix(): {'sha256':sha(p),'bytes':p.stat().st_size} for p in paths})
    paths.append(OUT/'MANIFEST.json')
    # Task date is November 2, 2026: New York is on EST. Avoid a tzdata dependency
    # on Windows; use the client timezone's applicable offset for archive naming.
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT/'handoff'/f'CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in paths: z.write(p,p.relative_to(OUT).as_posix())
        z.writestr('CURRENT_REVIEW.md',report)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v['sha256'] for k,v in json.loads(z.read('MANIFEST.json')).items())
    for name, content in [('CURRENT_REVIEW.zip',archive.read_bytes()),('CURRENT_REVIEW.md',report.encode())]:
        pending=ROOT/'handoff'/('PR_PLAY_48_pending_'+name)
        pending.write_bytes(content)
        pending.replace(ROOT/'handoff'/name)
    dump('archive_verification.json', {'archive':str(archive),'sha256':sha(archive),
        'zip_crc_valid':True,'manifest_hashes_valid':True,'entries':len(paths)+1,
        'stable_archive_matches':sha(archive)==sha(ROOT/'handoff/CURRENT_REVIEW.zip'),
        'bytes':archive.stat().st_size})
    (OUT/'archive_path.txt').write_text(str(archive)+'\n',encoding='utf-8')
    print(json.dumps({'archive':str(archive),'checks':checks,'archive_bytes':archive.stat().st_size},indent=2))


if __name__=='__main__':
    main()
