"""ATGB-04: offline presentation of preserved evidence; no gameplay imports."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/atgb/atgb_04'
DIMENSIONS = ('interpretation', 'response', 'authority', 'failure_severity',
              'clarification', 'continuity', 'reviewer_explanation')
OPTIONS = {
    'interpretation': ['', 'pass', 'fail', 'uncertain', 'not_evaluated', 'unchecked'],
    'response': ['', 'pass', 'fail', 'uncertain', 'not_evaluated', 'unchecked'],
    'authority': ['', 'pass', 'fail', 'uncertain', 'not_evaluated', 'unchecked'],
    'failure_severity': ['', 'minor', 'major', 'critical', 'uncertain', 'not_evaluated'],
    'clarification': ['', 'none', 'necessary_pass', 'unnecessary_fail',
                      'missing_when_needed_fail', 'uncertain', 'not_evaluated'],
    'continuity': ['', 'not_applicable', 'preserved', 'lost', 'uncertain', 'not_evaluated'],
}
GUIDE = """# Independent human review — ATGB-04

Start with `review.html` in a browser (offline). Read the instructions and each
conversation in order; all 37 baseline exchanges are included verbatim. Its blank
fields export `human_judgments.json`. Save that export before closing; this form
does not automatically save. Import an earlier export to continue. An optional
plain-text form is in `blank_scoring_forms.md`; transfer it into a copy of
`blank_judgments.json` for reporting. Keep each reviewer's file separate and retain
disagreements; do not average reviewers or silently adjudicate them.

Authority: ATGB-02 / ATGB-01 / atgb-rubric-01 / ATGB-02-s07-held-out.
Approved definitions and behavioral criteria are reproduced, not amended.
Interpretation, response adequacy, and authority each use pass/fail/uncertain;
unchecked means the dimension was not judged. `not_evaluated` explicitly records
that no supported judgment was made. Blank means still pending. Neither is pass.
These are review statuses, not new gameplay scoring categories.

Failure severity uses only minor, major, critical. Leave it blank when no defect
is assigned; blank is not a finding of no defect. Minor: usable reply with stiff
or repetitive wording. Major: communicative job missed, wrong addressee, lost
referent, evasive restatement or needless clarification; response fails. Critical:
consequential invented/hidden fact or unauthorized state; authority fails.
Explain failures, uncertainty, skipped criteria, and any setup dependence in the
reviewer explanation. An explanation is requested for each entered judgment.

Clarification: none (no question needed), necessary_pass (one focused question
for a real ambiguity), unnecessary_fail (already specific enough), or
missing_when_needed_fail (needed but guessed/evaded/refused without asking).
Continuity: not_applicable, preserved, or lost. S02.4, S03.4, S05.2, S08.4 and
S10.2 require context older than the last sentence. All earlier exchanges in the
same trial are linked in the index and shown immediately above each later turn.

Response and authority both passing define acceptability under the approved
rubric; interpretation remains separate. Major/critical defects cannot be
acceptable. No universal score is calculated. Conversation observations cover
repetition, phrasing, clarification, pacing, sustained initiative and mechanical
or validation-like dialogue without a new numerical category.

S07/S09 require special review: authored facts in state were not delivered as an
opening before turn 1. Browser/journal delivery is unverified. Do not presume
player knowledge or score missing setup as conversational failure. Explain which
criteria remain supported by explicit lines and actual preceding replies; use
uncertain/not_evaluated for unsupported judgments. Preserve independently
evaluable interpretation, text, clarification, continuity and state evidence.
See `scenario_qualifications.md` for turn-specific review questions.

Technical capture is not human scoring. Individual replies may be host-owned
despite live-enabled execution. State snapshots show scene, clue IDs, flag names,
interlocutor and transcript count; they are bounded projections, not proof that
all hidden values were unchanged. Raw results and final state are available in
the ZIP for deeper inspection. Raw harness diagnostic zeros are not human
findings. Do not use the old worksheet placeholders as judgments.

Original S04 trial 1 is a separate two-turn historical observation, excluded
from all 37-turn reporting. It is retained in `historical_S04_trial_1.md` and
its original evidence files. Do not splice it into trial 2.

Reporting (Python standard library only, no provider or gameplay imports):

`python support/tools/atgb/report_human_review.py --index support/artifacts/atgb/atgb_04/review_index.json --judgments human_judgments.json --output report.json`

Run that command from the extracted ZIP root. In the repository, omit `support/`.
Rates use pass/(pass+fail) separately per dimension, capability and partition;
raw numerators, denominators, pending/uncertain/not-evaluated/unchecked counts
remain alongside them. Continuity loss uses lost/(preserved+lost), with
not_applicable separate. Clarification counts retain all four approved tags.
Partial judgments produce explicitly partial reports. Critical and major
exchanges appear before aggregate data. With no human judgments, rates are null.
Review metadata is human-entered attribution, not authentication of identity.

One environment, single selected trial per scenario, uncontrolled sampling,
API-only delivery, differing original/continuation accounting, and previously
exposed held-out material limit claims. No independent unseen generalization,
gameplay improvement, browser validation or completed performance baseline is
established by this preparation. Stop and await independent human evaluation.
"""


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    corpus = read('data/validation/atgb/corpus.json')
    fixtures = {p.stem: json.loads(p.read_text(encoding='utf-8'))
                for folder in ('visible', 'held_out')
                for p in (ROOT / 'data/validation/atgb' / folder).glob('S*.json')}
    combined = read('artifacts/atgb/atgb_03c/combined_baseline_worksheet.json')
    worksheet = {t['turn_id']: t for c in combined['conversations'] for t in c['turns']}
    rows, conversations, sources = [], [], set()
    for sid, fixture in sorted(fixtures.items()):
        base = f"artifacts/atgb/{'atgb_03' if sid <= 'S03' else 'atgb_03c'}/{sid}"
        result_path = base + '/result.json'
        result = read(result_path)
        trial = result['trial_number']
        assert trial == (2 if sid == 'S04' else 1)
        assert len(result['turns']) == len(fixture['turns'])
        prior = []
        conv = {'scenario_id': sid, 'trial': trial, 'title': fixture['title'],
                'partition': fixture['partition'], 'evidence_status': fixture['evidence_status'],
                'objective': fixture['expected_outcomes'], 'fixture': fixture,
                'readiness': result['scenario_records'][0]['preflight'],
                'source_result': result_path, 'source_transcript': base + '/transcript.md'}
        conversations.append(conv)
        sources.update([result_path, base + '/transcript.md', base + '/worksheet.json'])
        for original, expected in zip(result['turns'], fixture['turns']):
            tid = original['turn_id']
            assert (tid, original['player_input']) == (expected['turn_id'], expected['player_input'])
            assert worksheet[tid]['ai_dm_response'] == original['response_text']
            assert worksheet[tid]['player_input'] == original['player_input']
            qualification = (
                'Special review: opening-dependent criteria require eligibility assessment. '
                'World-state presence does not establish delivery to player. '
                'Use only actual prior exchanges and explicit player wording; explain unsupported criteria.'
                if sid in ('S07', 'S09') else
                'Machine prerequisites verified; naturalness and scenario assumptions still require human review. '
                'Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.')
            row = {'review_id': f'{tid}/trial-{trial}', 'scenario_id': sid,
                   'turn_id': tid, 'trial': trial, 'partition': original['partition'],
                   'evidence_status': original['evidence_status'],
                   'primary_capability': original['primary_capability'],
                   'player_input': original['player_input'], 'ai_dm_response': original['response_text'],
                   'preceding_conversation': list(prior),
                   'authoritative_context': original['turn_context'],
                   'behavioral_expectations': expected, 'state_evidence': original['state_evidence'],
                   'resolution_evidence': {k: original.get(k) for k in
                       ('resolution_kind', 'communication_mode', 'conversational_decision', 'addressee')},
                   'telemetry': original['telemetry'],
                   'setup_limitations': qualification,
                   'special_review_required': sid in ('S07', 'S09'),
                   'source_result': result_path, 'source_turn_pointer': f"/turns/{len(prior)}",
                   'source_transcript': base + '/transcript.md'}
            rows.append(row)
            prior.append({k: row[k] for k in ('review_id', 'player_input', 'ai_dm_response')})
    assert len(rows) == len({r['turn_id'] for r in rows}) == 37
    assert {p: sum(r['partition'] == p for r in rows) for p in
            ('development_visible', 'related_variation', 'held_out')} == {
                'development_visible': 25, 'related_variation': 4, 'held_out': 8}
    index = {k: corpus[k] for k in ('benchmark_version', 'scenario_version', 'rubric_version', 'partition_revision')}
    index.update({'review_package': 'ATGB-04', 'lane': 'live_provider',
                  'human_review_complete': False, 'gameplay_performance_claim': False,
                  'conversations': conversations, 'turns': rows,
                  'excluded_historical_trial': {'scenario_id': 'S04', 'trial': 1, 'captured_turns': 2,
                      'source_result': 'artifacts/atgb/atgb_03/S04/result.json'}})
    write('review_index.json', index)
    blank = {'review_package': 'ATGB-04', 'rubric_version': corpus['rubric_version'],
             'reviewer': '', 'reviewed_at': '', 'human_review_attestation': False,
             'turns': [dict(review_id=r['review_id'], **{k: '' for k in DIMENSIONS}) for r in rows],
             'conversations': [{'scenario_id': c['scenario_id'], 'trial': c['trial'],
                                'qualitative_observations': ''} for c in conversations]}
    write('blank_judgments.json', blank)
    (OUT / 'README.md').write_text(GUIDE, encoding='utf-8')
    rubric = (ROOT / 'development/reports/atgb_01_conversational_benchmark_design.md').read_text(encoding='utf-8')
    rubric = rubric[rubric.index('## 5. Three results per turn'):rubric.index('## 7.')]
    (OUT / 'approved_rubric_excerpt.md').write_text(rubric, encoding='utf-8')
    qualifications = (OUT / 'scenario_qualifications.md').read_text(encoding='utf-8')
    md = [GUIDE, qualifications, '\n# Shared authoritative facts (reviewer knowledge, not assumed player knowledge)\n']
    md += ['- ' + f['text'] for f in corpus['environments']['frontier_gate']['shared_facts']]
    cards = []
    esc = lambda v: html.escape(str(v))
    for c in conversations:
        sid, f = c['scenario_id'], c['fixture']
        title = f"{sid} — {c['title']} — trial {c['trial']}"
        notes = ['\n## ' + title, f"\nPartition: {c['partition']}; {c['evidence_status']}."]
        for label, key in [('Scenario objective', 'expected_outcomes'), ('Required context', 'initial_context'),
                           ('Authoritative facts', 'authoritative_facts'), ('NPC knowledge', 'npc_knowledge'),
                           ('Acceptable variations', 'acceptable_variations'),
                           ('Unacceptable behavior', 'unacceptable_behaviors'),
                           ('Setup dependencies', 'setup_dependencies'), ('Required evidence', 'required_evidence')]:
            value = f[key]
            notes += [f'\n**{label}**', '\n'.join('- ' + x for x in value) if isinstance(value, list) else value]
        notes += ['\nEach turn below retains every previous exchange in this trial above it. '
                  'No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.']
        card = ['<section><h2>' + esc(title) + '</h2>', '<pre>' + esc('\n'.join(notes[1:])) + '</pre>']
        for r in (r for r in rows if r['scenario_id'] == sid):
            e = r['behavioral_expectations']
            before, after = r['state_evidence']['before'], r['state_evidence']['after']
            state_lines = [f"{key}: {before.get(key)!r} → {after.get(key)!r}" for key in sorted(set(before) | set(after))]
            text = [f"\n### {r['review_id']} ({r['primary_capability']})",
                    '\n**Player**\n\n' + r['player_input'], '\n**AI-DM**\n\n' + r['ai_dm_response'],
                    '\n**Setup qualification** ' + r['setup_limitations'],
                    '\n**Prior turns** ' + (', '.join(t['review_id'] for t in r['preceding_conversation']) or 'None; empty history.'),
                    '\n**Approved behavioral expectations**']
            for key in ('communicative_act', 'interpretation_pass', 'response_pass', 'authority_pass',
                        'clarification_expected', 'clarification_notes', 'continuity_expected', 'continuity_notes',
                        'acceptable_variations', 'unacceptable_behaviors', 'required_evidence'):
                text.append(f"- {key}: {e[key]}")
            text += ['\n**State before → after**\n', *['- ' + x for x in state_lines],
                     f"\nResolution: {r['resolution_evidence']['resolution_kind']}; mode: {r['resolution_evidence']['communication_mode']}; "
                     f"addressee: {r['resolution_evidence']['addressee']}.",
                     f"\nEvidence: `{r['source_result']}` {r['source_turn_pointer']}; `{r['source_transcript']}`."]
            md += notes if r['turn_id'].endswith('.1') else []
            md += text
            md += ['\n| Human judgment | Entry |', '| --- | --- |'] + [f'| {d} | __________ |' for d in DIMENSIONS]
            card += [f'<article data-review-id="{esc(r["review_id"])}"><h3>{esc(r["review_id"])}</h3>',
                     '<p><b>Player</b></p><div class="verbatim">' + esc(r['player_input']) + '</div>',
                     '<p><b>AI-DM</b></p><div class="verbatim">' + esc(r['ai_dm_response']) + '</div>',
                     '<p class="qualification">' + esc(r['setup_limitations']) + '</p>',
                     '<pre>' + esc('\n'.join(text[4:])) + '</pre><div class="fields">']
            for d in DIMENSIONS:
                card += ['<label>' + esc(d.replace('_', ' '))]
                if d == 'reviewer_explanation':
                    card += [f'<textarea name="{d}" rows="3"></textarea>']
                else:
                    card += [f'<select name="{d}">'] + [f'<option value="{x}">{esc(x or "— pending —")}</option>' for x in OPTIONS[d]] + ['</select>']
                card += ['</label>']
            card += ['</div></article>']
        md += ['\nConversation qualitative observations: __________________________________\n']
        card += [f'<label>Conversation qualitative observations<textarea data-conversation="{sid}" rows="3"></textarea></label></section>']
        cards += card
    (OUT / 'conversational_review.md').write_text('\n'.join(md), encoding='utf-8')
    form = ['# Blank scoring forms', '\nSee README.md for allowed values and approved definitions. No judgments are prepopulated.\n']
    for r in rows:
        form += [f"## {r['review_id']}"] + [f'- {d}: ' for d in DIMENSIONS]
    form += ['## Conversation observations'] + [f"- {c['scenario_id']} trial {c['trial']}: " for c in conversations]
    (OUT / 'blank_scoring_forms.md').write_text('\n'.join(form) + '\n', encoding='utf-8')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>ATGB-04 Independent human review</title>
<style>body{font:16px/1.5 system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#20232a}pre,.verbatim{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}.verbatim{padding:1rem;background:#f2f3f5;border-left:3px solid #53617a}article{border-top:1px solid #aaa;padding:1rem 0}section{margin:3rem 0}.qualification{background:#fff2ce;padding:.7rem}.fields{display:grid;grid-template-columns:1fr 1fr;gap:.7rem}label{display:block}textarea,select,input{display:block;width:95%;font:inherit}button{padding:.5rem;margin:.5rem}header{border-bottom:2px solid #555}@media print{button,input[type=file]{display:none}article{break-inside:avoid}body{font-size:11pt}}</style>
<header><h1>ATGB-04 — Independent human review</h1><p>37 turns; all human judgments blank. No gameplay-performance baseline established.</p>
<label>Reviewer<input id="reviewer"></label><label>Review date / time<input id="reviewed_at"></label>
<label><input type="checkbox" id="attestation" style="display:inline;width:auto"> These entries are my human judgments.</label>
<button id="export">Download judgments</button><label>Resume from exported judgments<input id="import" type="file" accept=".json"></label><p id="status" aria-live="polite">Save your export before closing. No automatic saving.</p></header>'''
    page += '<details><summary>Review instructions and reporting</summary><pre>' + esc(GUIDE) + '</pre></details>'
    page += '<details><summary>Approved rubric, reproduced verbatim</summary><pre>' + esc(rubric) + '</pre></details>'
    page += '<details><summary>Scenario and turn-specific setup qualifications</summary><pre>' + esc(qualifications) + '</pre></details>'
    page += '<details><summary>Shared facts — reviewer authority, not presumed player knowledge</summary><ul>'
    page += ''.join('<li>' + esc(f['text']) + '</li>' for f in corpus['environments']['frontier_gate']['shared_facts']) + '</ul></details>'
    page += ''.join(cards)
    page += '<script type="application/json" id="blank">' + json.dumps(blank).replace('<', '\\u003c') + '</script>'
    page += '''<script>
const template=JSON.parse(document.querySelector('#blank').textContent);
function collect(){const j=structuredClone(template);j.reviewer=document.querySelector('#reviewer').value;j.reviewed_at=document.querySelector('#reviewed_at').value;j.human_review_attestation=document.querySelector('#attestation').checked;j.turns.forEach(t=>{const a=[...document.querySelectorAll('article')].find(a=>a.dataset.reviewId===t.review_id);a.querySelectorAll('[name]').forEach(e=>t[e.name]=e.value)});j.conversations.forEach(c=>c.qualitative_observations=document.querySelector(`[data-conversation="${c.scenario_id}"]`).value);return j}
document.querySelector('#export').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(collect(),null,2)],{type:'application/json'}));a.download='human_judgments.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);document.querySelector('#status').textContent='Judgments exported. Retain your saved file.'};
document.querySelector('#import').onchange=async e=>{try{const j=JSON.parse(await e.target.files[0].text());if(j.review_package!==template.review_package||j.rubric_version!==template.rubric_version||j.turns.length!==37||new Set(j.turns.map(t=>t.review_id)).size!==37)throw Error('Wrong package or duplicate/missing turns');for(const t of j.turns){const base=template.turns.find(x=>x.review_id===t.review_id);if(!base)throw Error('Unknown trial/turn');const a=[...document.querySelectorAll('article')].find(a=>a.dataset.reviewId===t.review_id);for(const e of a.querySelectorAll('select'))if(![...e.options].some(o=>o.value===t[e.name]))throw Error('Unknown judgment value')};if(j.conversations.length!==10||new Set(j.conversations.map(c=>c.scenario_id)).size!==10||j.conversations.some(c=>!template.conversations.some(x=>x.scenario_id===c.scenario_id&&x.trial===c.trial)))throw Error('Wrong conversations');document.querySelector('#reviewer').value=j.reviewer;document.querySelector('#reviewed_at').value=j.reviewed_at;document.querySelector('#attestation').checked=j.human_review_attestation===true;j.turns.forEach(t=>{const a=[...document.querySelectorAll('article')].find(a=>a.dataset.reviewId===t.review_id);a.querySelectorAll('[name]').forEach(e=>e.value=t[e.name])});j.conversations.forEach(c=>document.querySelector(`[data-conversation="${c.scenario_id}"]`).value=c.qualitative_observations);document.querySelector('#status').textContent='Imported. Export again to save changes.'}catch(err){document.querySelector('#status').textContent='Import refused: '+err.message}};
</script></html>'''
    (OUT / 'review.html').write_text(page, encoding='utf-8')
    index_md = ['# Authoritative review index — 37 unique turns',
                '\nSelection: original S01–S03; continuation S04 trial 2 and S05–S10 trial 1. '
                'Historical S04 trial 1 is excluded. Full text, context and state: review_index.json and review.html.',
                '\n| Review ID | Partition | Primary capability | Source | Prior turns in same trial |',
                '| --- | --- | --- | --- | --- |']
    index_md += [f"| {r['review_id']} | {r['partition']} | {r['primary_capability']} | "
                 f"{r['source_result']} {r['source_turn_pointer']} | "
                 + (', '.join(t['review_id'] for t in r['preceding_conversation']) or 'none') + ' |' for r in rows]
    (OUT / 'review_index.md').write_text('\n'.join(index_md) + '\n', encoding='utf-8')
    historical = read('artifacts/atgb/atgb_03/S04/result.json')
    hist = ['# Original S04 trial 1 — historical, excluded from baseline',
            'Two captured turns; stopped before turn 3 by unavailable provider accounting. '
            'Not a gameplay judgment. Do not merge with trial 2. Human judgments remain pending.']
    for t in historical['turns']:
        if t['capture_status'] == 'captured':
            hist += [f"## {t['turn_id']} / trial 1", '\nPlayer: ' + t['player_input'], '\nAI-DM: ' + t['response_text']]
    hist += ['Evidence: artifacts/atgb/atgb_03/S04/result.json and transcript.md, packaged separately.']
    (OUT / 'historical_S04_trial_1.md').write_text('\n\n'.join(hist), encoding='utf-8')
    sources.update(['artifacts/atgb/atgb_03/S04/result.json', 'artifacts/atgb/atgb_03/S04/transcript.md',
                    'artifacts/atgb/atgb_03c/combined_baseline_worksheet.json'])
    write('evidence_sources.json', [{'path': p, 'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest()} for p in sorted(sources)])
    print('Prepared 37 unique baseline turns; 25 visible / 4 related / 8 held-out; judgments blank.')


if __name__ == '__main__':
    prepare()
