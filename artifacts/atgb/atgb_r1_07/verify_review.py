"""Verify selected review payload without printing possible sensitive content."""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'handoff/CURRENT_REVIEW.zip'
with zipfile.ZipFile(path) as archive:
    assert archive.testzip() is None
    manifest = json.loads(archive.read('REVIEW_MANIFEST.json'))
    verified = 0
    for entry in manifest['included_files']:
        if entry['sha256'] is None:
            continue  # Manifest intentionally has no self hash.
        assert hashlib.sha256(archive.read(entry['bundle_path'])).hexdigest() == entry['sha256']
        verified += 1
    reports = [n for n in archive.namelist() if n.startswith('support/development/reports/atgb_r1_07/') and n.endswith('.md')]
    assert len(reports) == 8
    findings = []
    patterns = [rb'\bsk-[A-Za-z0-9_-]{16,}', rb'Bearer\s+[A-Za-z0-9_.-]{16,}', rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    for name in archive.namelist():
        data = archive.read(name)
        if any(re.search(pattern, data) for pattern in patterns):
            findings.append(name)
    assert not findings, 'Potential sensitive payload; inspect affected files without printing values.'
result = {'zip': path.name, 'crc_valid': True, 'payload_hashes_verified': verified, 'reports': len(reports), 'sensitive_value_pattern_findings': findings, 'policy': 'Explicit source selection; no environment/config/account data exports. Pattern scan is supplementary.', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
print(json.dumps(result, indent=2))
