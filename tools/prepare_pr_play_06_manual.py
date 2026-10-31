"""Derive the operator procedure from the reviewed prior procedure, without running it."""
from pathlib import Path

source=Path('development/campaigns/product_realization/pr_play_05/PR_PLAY_05_LIVE_OPENING_TEST.txt').read_text(encoding='utf-8')
source=source.replace('PR-PLAY-05','PR-PLAY-06').replace('pr_play_05','pr_play_06').replace('2026-10-27','2026-10-28')
source=source.replace('Supersedes PR-PLAY-02','Supersedes PR-PLAY-05')
source=source.replace("$playStamp = Get-Date", "$ErrorActionPreference = 'Stop'\n$playStamp = Get-Date")
source=source.replace('Write-Host "ISOLATED OPENING TEST: $playRoot"',
r'''Set-Content -LiteralPath 'artifacts\pr_play_06\active-test-path.txt' -Value $playRoot -Encoding utf8
Write-Host "ISOLATED OPENING TEST: $playRoot"
Write-Host 'Preserve $playRoot in this server window through export.' ''')
source=source.replace("$env:ASHEN_GENERATION_DIAGNOSTICS = '1'", """$env:ASHEN_GENERATION_DIAGNOSTICS = '1'
$env:ASHEN_OPENING_MAX_OUTPUT_TOKENS = '3000'
$env:ASHEN_NARRATION_MAX_OUTPUT_TOKENS = '600'
Write-Host 'Verifying local configuration: opening 3000, ordinary 600, six requests.'""")
source=source.replace("from game.storage import DATA_DIR;", "from game.storage import DATA_DIR; from game.gm import _opening_max_output_tokens;")
source=source.replace("assert int(os.environ.get('ASHEN_NARRATION_MAX_OUTPUT_TOKENS','600'))==600;", "print('OPENING OUTPUT CEILING:',_opening_max_output_tokens()); assert _opening_max_output_tokens()==3000; assert int(os.environ.get('ASHEN_NARRATION_MAX_OUTPUT_TOKENS','600'))==600;")
source=source.replace('& .venv\\Scripts\\python.exe -m uvicorn', "Write-Host 'Launching one server. Next: New Campaign, snapshot, Start once.'\n& .venv\\Scripts\\python.exe -m uvicorn")
source=source.replace('The existing narration limit remains 600; no model pin is introduced.', 'The opening ceiling is 3000; the ordinary narration ceiling remains 600.\nNo model pin is introduced. Aggregate ceilings remain 200000/20000/220000.\nMaximum opening output exposure rises by 2400 tokens (5x the former ceiling).')
source=source.replace("set $playRoot to the full printed path from step 1 (replace MANUAL_FOLDER):", "discover the active test directory with this complete command block.\n$playRoot must remain set independently in BOTH windows through export:")
source=source.replace("$playRoot = 'MANUAL_FOLDER'", """Set-Location -LiteralPath 'C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm'
$ErrorActionPreference = 'Stop'
$playRoot = (Get-Content -LiteralPath 'artifacts\\pr_play_06\\active-test-path.txt' -Raw).Trim()
if (-not (Test-Path -LiteralPath (Join-Path $playRoot 'data'))) { throw 'Active test directory missing. Stop.' }
Write-Host "Capturing BEFORE state and data: $playRoot"
"""
)
source=source.replace("-Uri 'http://127.0.0.1:8765/api/state'", "-Uri 'http://127.0.0.1:8765/api/state' -TimeoutSec 15")
source=source.replace('Get-Content -LiteralPath (Join-Path $playRoot \'provider_usage.jsonl\')', "if (Test-Path -LiteralPath (Join-Path $playRoot 'provider_usage.jsonl')) { Get-Content -LiteralPath (Join-Path $playRoot 'provider_usage.jsonl') } else { Write-Host 'No provider ledger yet; zero admissions expected before Start.' }")
source=source.replace('If responsive, in the SECOND window use this read-only local endpoint:', "If responsive, in the SECOND window use this read-only local endpoint:\n\nWrite-Host 'Capturing AFTER state (15 second timeout). Then stop server with Ctrl+C.'")
source=source.replace("Copy-Item -LiteralPath $env:ASHEN_DATA_DIR -Destination", "Write-Host 'Server stopped. Copying AFTER data and exporting evidence.'\nCopy-Item -LiteralPath $env:ASHEN_DATA_DIR -Destination")
source=source.replace('Do not invent a ledger when startup failed.', 'If the after-state HTTP command times out, record that fact and continue with\nCtrl+C and data/ledger export; do not resend the HTTP request.\nDo not invent a ledger when startup failed.')
source=source.replace('limits()[0]==6', 'limits()==(6,200000,20000,220000)')
source=source[:source.index('6. RESTORE NORMAL ENVIRONMENT')] + '''6. RESTORE NORMAL ENVIRONMENT
After stopping and exporting, close both disposable PowerShell windows and the
test browser tab. Process-local settings disappear. Normal campaign files were
never overwritten. Retain the disposable test folder and evidence ZIP. Do not
launch another server, run provider diagnostics, or retry as part of this test.
Return the evidence ZIP and await external review. A later attempt needs separate
authorization and a new directory/ledger; never restart to continue this budget.
'''
source=source.replace('1. Provider response completes.', '1. Provider response completes.')
source += '''
REVIEW DECISION CRITERIA
Success requires provider_status=completed, JSON parsing true, accepted required
envelope, UI opening visible, campaign_started true, exactly one authorized
turn/time/faction progression, and no retries. Inspect before/after data as well
as the public state. A complete JSON fragment with incomplete provider status
must fail. Failure must be explicit, preserve gameplay values, retain provider
completion/finish/ceiling/usage/extraction/parser/envelope/final-commit diagnostics,
and preserve budget accounting. Compare gameplay separately from existing save
timestamps, debug traces and empty-log initialization bookkeeping.
One success is a functional milestone, not statistical reliability evidence.
Stop after this one attempt and export. Await external review before any retry.
'''
assert 'MANUAL_FOLDER' not in source
Path('development/campaigns/product_realization/pr_play_06/PR_PLAY_06_LIVE_OPENING_TEST.txt').write_text(source,encoding='utf-8')
