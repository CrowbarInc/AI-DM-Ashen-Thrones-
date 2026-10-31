# Automated playtest guide

Run an isolated campaign opening, collect diagnostics, and export evidence with
one PowerShell command from the repository root. Your ordinary campaign is never
used as the test store. Each run copies the pinned `frontier-gate-v1` fixture.

## Requirements

Windows PowerShell or PowerShell 7, Python 3.12+, and the repository's
`requirements.txt` installed in `.venv`. No additional testing framework or browser
download is required. The command supports paths containing spaces and resolves
the repository from its own location. If the local virtual environment cannot
run, it can use the installed Codex bundled Python with local environment packages.
You may explicitly select an interpreter with `-PythonExecutable <path>`.

Localhost networking must be permitted. A sandbox that blocks loopback can cause
startup timeouts inside Python's event-loop initialization. Run from ordinary
PowerShell, or allow localhost execution in your automation environment. Do not
disable provider safety controls to address a networking failure.

## Deterministic opening — default, zero live provider calls

```powershell
.\scripts\run_live_playtest.ps1 -Scenario CampaignOpening -Mode Deterministic
```

The worker substitutes synthetic SDK transport and denies external socket
connections. It exercises the real HTTP endpoints, provider admission, parser,
semantic validation, opening acceptance, and persistence. Reported provider
attempts in this mode are synthetic attempts. This tests infrastructure and
contracts; it does not measure live generation or conversational quality.

Optionally preserve the existing bounded response artifact:

```powershell
.\scripts\run_live_playtest.ps1 -CaptureResponse
```

Capture is disabled by default. Captures can contain campaign content; review
before sharing. The production capture owner limits each artifact to 64 KiB and
six per diagnostic scope. Unparsed/empty responses may have no capture; reports
state that limitation explicitly.

Exercise a negative control, with exactly one opening submission:

```powershell
.\scripts\run_live_playtest.ps1 -FixtureResponse truncation
```

Other fixtures: `invalid_json`, `envelope`, `semantic`, `safe_nonresolution`,
`exception`, `admission`, `empty`, `incomplete`, and `success`. Negative controls
normally produce FAIL and exit 2. Their failure is an intended fixture outcome.

## Scripted deterministic scenario

```powershell
.\scripts\run_live_playtest.ps1 -Scenario ScriptedObservation -Mode ScriptedGameplay
```

This opens once, observes the scene, verifies the started flag, and captures state.
The dispatcher also defines NPC interaction, examination, rules-action, and
movement steps using existing chat/action request contracts. There is no autonomous
player, unbounded scenario loop, or live multi-turn mode. Future scenarios require
reviewed request fixtures, appropriate invariants, and bounded limits.

## Live opening — only after separate review and authorization

PR-PLAY-08 does **not** authorize running this command. After external review and
separate authorization, the exact command is:

```powershell
.\scripts\run_live_playtest.ps1 -Scenario CampaignOpening -Mode Live -AuthorizeLiveProvider -CaptureResponse
```

Both `-Mode Live` and `-AuthorizeLiveProvider` are required at invocation time.
Existing credentials must already be configured through the application's normal
environment or `.env`. Never put credentials on the command line. Provider calls
must be enabled in existing settings; disabled flags block Live mode. Credentials
are checked for presence, never tested with a connectivity request or stored in
the report.

This permits **at most one provider admission/attempt**, with SDK and host retries
disabled. A failure ends the scenario; Start Campaign is never automatically
submitted again. Existing model routing and opening output allowance remain
unchanged (normally 3,000). Scenario aggregate ceilings are 200,000 input, 20,000
output, 220,000 total, matching the prior controlled manual scope. Any inherited
stricter limit is retained. The one-request limit is stricter than that manual
scope's six admissions. Admission uses the application's existing input estimates;
usage after completion can still establish exhaustion. Unavailable usage remains
unknown. No pricing table is maintained here; reports show tokens without a dollar
estimate. Live execution can incur provider charges even when opening fails.

Connectivity preflight is intentionally skipped to reserve the sole admission for
opening generation. A skipped health probe is not proof of upstream health.

## Results and evidence

Every command prints the verdict, absolute summary path, and exact ZIP path.
The default output directory is:

```text
artifacts/atgb/automated_playtests/<UTC timestamp>-<unique suffix>/
  configuration/          effective safe configuration and scenario
  data/                   fresh isolated campaign; never ordinary saves
  baseline/               API-visible and persistent state before Start
  after/                  API-visible and persistent state after Start
  diagnostics/            journal, worker attestation, bounded stdout/stderr,
                          usage snapshot, optional response, execution log
  screenshots/            reserved for a future browser adapter
  reports/result.json     machine-readable results
  reports/SUMMARY.md      human-readable results
  evidence/manifest.json  selected artifact sizes and SHA-256 hashes
  evidence/evidence.zip   complete selected diagnostic package
```

All timestamps in run IDs are UTC. The unique suffix prevents overwrites.
Prior runs are retained. Only the worker process started for this run is stopped.
The log ceiling is 256 KiB, each API/file capture is bounded at 2 MiB, and evidence
selection at 32 MiB. ZIP generation is bounded at 30 seconds. The manifest hashes
every selected member except itself. Live response evidence is sensitive game
content even when it contains no credentials.

View the latest verdict, summary path, and evidence ZIP location:

```powershell
.\scripts\run_live_playtest.ps1 -Latest
```

Use `-Port 8765` to select a localhost port; the default asks the OS for a free
port. An occupied explicit port produces BLOCKED and leaves the existing server
alone. The harness never attaches to or terminates an existing development server.

## Reading a result

| Verdict | Meaning |
| --- | --- |
| PASS | Required observed acceptance, state, commit, diagnostic, and budget-accounting invariants hold. |
| FAIL | An observed scenario invariant failed. Failed opening may still have PASS state integrity. |
| BLOCKED | Authorization, preflight, port binding, or startup prevented execution. |
| INCONCLUSIVE | Execution or evidence collection was interrupted or required evidence is missing. |

HTTP 200 alone cannot produce PASS. Failure classification identifies the observed
stage and evidence field. Root causes remain unestablished unless investigated
separately. An explicit incomplete/max-output finish outranks JSON parsing errors.
Safe nonresolution can parse correctly and still fail opening acceptance.
The UI is always reported `NOT_TESTED` until a browser adapter is installed.

## Troubleshooting and limitations

- BLOCKED before steps: inspect `reports/result.json`, `diagnostics/worker_failure.json`
  if present, and `diagnostics/application.log`. Missing dependencies, altered
  pinned fixtures, credentials, and unsafe directories must be resolved before
  dispatch. Exception type and stage are retained without copying private messages.
- Startup timeout: the bound is 30 seconds; check localhost permissions and the
  selected port. No provider request is used for readiness polling.
- API/step timeout: request ceiling 90 seconds, scenario ceiling 180 seconds;
  the harness stops its worker and preserves evidence. It does not retry gameplay.
- Output exhaustion or semantic failure: inspect journal provenance and optional
  response artifact. The tool does not change prompts, budgets, models, or game code.
- Missing artifact or unknown usage: treat the report's uncertainty as unresolved.
  Captured persistent after-state can survive interruption even when a final API
  projection is unavailable.
- API automation does not prove rendered browser behavior. No Playwright/Selenium
  dependency or registered browser runner exists in this repository. The adapter
  contract is `tools/playtest/browser.py`.
- The comparator recognizes opening-owned state roots and explicit bookkeeping;
  it is conservative about new fields. It is not a general gameplay evaluator.
  No ATGB score or frozen corpus judgment is changed by these runs.

Run the bounded deterministic verification lanes:

```powershell
.\.venv\Scripts\python.exe -m tools.validate_pr_play_08
```

Lane logs, JUnit XML, exact commands, and preservation hashes are written under
`artifacts/pr_play_08/`. This command runs no live provider operations.
