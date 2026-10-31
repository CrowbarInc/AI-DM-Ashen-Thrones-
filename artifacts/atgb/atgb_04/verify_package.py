"""Verify review sufficiency from a ZIP extraction, without runtime/provider imports."""
import hashlib
import html.parser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent


class FormParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.verbatim = []
        self.current = None
        self.selects = 0
        self.articles = []
        self.selected = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article':
            self.articles.append(attrs['data-review-id'])
        if tag == 'select':
            self.selects += 1
        if tag == 'option' and 'selected' in attrs:
            self.selected += 1
        if tag == 'div' and attrs.get('class') == 'verbatim':
            self.current = ''

    def handle_data(self, data):
        if self.current is not None:
            self.current += data

    def handle_endtag(self, tag):
        if tag == 'div' and self.current is not None:
            self.verbatim.append(self.current)
            self.current = None


def verify():
    checked = 0
    with zipfile.ZipFile(ROOT / 'handoff/CURRENT_REVIEW.zip') as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('REVIEW_MANIFEST.json'))
        assert manifest['campaign_id'] == 'atgb_04_human_evaluation_preparation'
        for row in manifest['included_files']:
            if row.get('canonical_source_path'):
                data = z.read(row['bundle_path'])
                assert hashlib.sha256(data).hexdigest() == row['sha256']
                assert data == (ROOT / row['canonical_source_path']).read_bytes()
                checked += 1
        assert all('duplicate' in str(row).lower() for row in manifest['omitted_artifacts'])
        summary = z.read('CURRENT_REVIEW.md').decode('utf-8')
        sections = ['Campaign', 'Executive Summary', 'Changes Made', 'What Was Tested',
                    'Behavioral Evidence', 'Decisions Requiring Human Review',
                    'Known Problems / Unresolved Findings', 'Missing Concepts / Future Capabilities',
                    'What This Campaign Does NOT Prove', 'Recommended Next Step', 'Review Bundle Contents']
        assert all('# ' + s in summary for s in sections)
        prefix = 'support/artifacts/atgb/atgb_04/'
        index = json.loads(z.read(prefix + 'review_index.json'))
        blank = json.loads(z.read(prefix + 'blank_judgments.json'))
        rows = index['turns']
        assert len(rows) == len({r['turn_id'] for r in rows}) == 37
        assert len({r['review_id'] for r in rows}) == 37
        assert all(not v for r in blank['turns'] for k, v in r.items() if k != 'review_id')
        for row in rows:
            raw = json.loads(z.read('support/' + row['source_result']))
            original = raw['turns'][int(row['source_turn_pointer'].split('/')[-1])]
            assert row['trial'] == raw['trial_number'] == (2 if row['scenario_id'] == 'S04' else 1)
            assert (row['turn_id'], row['player_input'], row['ai_dm_response']) == (
                original['turn_id'], original['player_input'], original['response_text'])
            assert row['state_evidence'] == original['state_evidence']
            previous = [r for r in rows if r['scenario_id'] == row['scenario_id'] and
                        int(r['turn_id'].split('.')[1]) < int(row['turn_id'].split('.')[1])]
            assert row['preceding_conversation'] == [{k: r[k] for k in
                ('review_id', 'player_input', 'ai_dm_response')} for r in previous]
        assert sum(r['special_review_required'] for r in rows) == 6
        original_s04 = json.loads(z.read('support/artifacts/atgb/atgb_03/S04/result.json'))
        assert original_s04['trial_number'] == 1
        assert sum(t['capture_status'] == 'captured' for t in original_s04['turns']) == 2
        parser = FormParser()
        parser.feed(z.read(prefix + 'review.html').decode('utf-8'))
        assert parser.verbatim == [v for r in rows for v in (r['player_input'], r['ai_dm_response'])]
        assert parser.articles == [r['review_id'] for r in rows]
        assert parser.selects == 222 and parser.selected == 0
        scratch = ROOT / 'development/tmp'
        scratch.mkdir(exist_ok=True, parents=True)
        with tempfile.TemporaryDirectory(prefix='atgb04_bundle_', dir=scratch) as folder:
            z.extractall(folder)
            base = Path(folder)
            result = subprocess.run([sys.executable, 'support/tools/atgb/report_human_review.py',
                '--index', prefix + 'review_index.json', '--judgments', prefix + 'blank_judgments.json',
                '--output', 'pending.json'], cwd=base, capture_output=True, text=True, check=True)
            pending = json.loads((base / 'pending.json').read_text(encoding='utf-8'))
            assert pending['coverage_only']['evaluated_turns_all_three_dimensions'] == 0
            assert not pending['gameplay_performance_claim']
            assert all(d['percent'] is None for p in pending['by_partition'].values() for d in p['dimensions'].values())
            assert pending == json.loads(z.read(prefix + 'pending_report.json'))
    before = json.loads((OUT / 'preservation_before.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest for p, digest in before.items())
    result = {'status': 'PASS', 'packaged_source_hashes_verified': checked,
              'protected_files_unchanged': len(before), 'baseline_turns_exactly_once': 37,
              'historical_observations_separate': 2, 'html_verbatim_exchanges': 37,
              'blank_selects': 222, 'bundle_only_blank_report': 'PASS',
              'human_judgments': 'blank; pending', 'rendered_browser_layout': 'unverified; file: URL blocked',
              'provider_requests': 0}
    (OUT / 'bundle_verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
