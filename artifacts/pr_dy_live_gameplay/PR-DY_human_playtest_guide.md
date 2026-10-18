# PR-DY human playtest guide

HUMAN PLAYTEST: NOT YET PERFORMED

The browser turns in the other reports were automated checks. They are not this playtest. Choose what to do in ordinary language. A useful session is about 10–15 minutes. Prefixes are optional.

Do not edit source to start. Do not type operation names or entity ids. The application reads credentials from the existing local environment file. Do not print, copy, or paste that file into notes.

## Start

From the repository root, in PowerShell:

```powershell
$env:ASHEN_DATA_DIR = "c:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\pr_dy_live_gameplay\disposable_playtest"
$env:ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT = "1"
$env:ASHEN_DISABLE_PROVIDER_RETRIES = "1"
$env:ASHEN_PIN_PROVIDER_MODEL = "gpt-4.1-mini"
$env:ASHEN_PROVIDER_USAGE_PATH = "c:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\pr_dy_live_gameplay\playtest_provider_usage.jsonl"
Remove-Item Env:ASHEN_DISABLE_PROVIDER_CALLS -ErrorAction SilentlyContinue
Remove-Item Env:ASHEN_DISABLE_LIVE_INTERPRETATION -ErrorAction SilentlyContinue
Remove-Item Env:ASHEN_PROVIDER_REQUEST_LIMIT -ErrorAction SilentlyContinue
Remove-Item Env:ASHEN_PROVIDER_INPUT_TOKEN_LIMIT -ErrorAction SilentlyContinue
Remove-Item Env:ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT -ErrorAction SilentlyContinue
Remove-Item Env:ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT -ErrorAction SilentlyContinue
$sceneDir = Join-Path $env:ASHEN_DATA_DIR "scenes"
New-Item -ItemType Directory -Force -Path $sceneDir | Out-Null
Copy-Item -Force "data\scenes\*" $sceneDir
python -m uvicorn game.api:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765/

Leave the request and token ceilings unset for this session. The verification run used a limit of 6 requests and 8,000 input tokens. Narration prompts are larger than that input ceiling, so those calls were refused and the player saw resolver text. A 10–15 minute session with that cap would stop early. If you set the ceilings again, the ledger will refuse calls that would pass them, and missing token fields should be recorded as unavailable.

## Enable and disable providers

Live play, as above: both disable variables unset, model pinned, retries off.

Deterministic play, no model calls:

```powershell
$env:ASHEN_DISABLE_PROVIDER_CALLS = "1"
$env:ASHEN_DISABLE_LIVE_INTERPRETATION = "1"
```

Restart the server after changing them. Explicit `OOC:` still works with providers disabled. Ordinary unmarked actions then use the existing parser instead of live interpretation.

## Reset the test session

Stop the server. Delete the `disposable_playtest` folder, or delete `session.json`, `world.json`, `combat.json`, `session_log.jsonl`, `character.json`, and `campaign.json` inside it. Leave `data\` alone. Start again. Copy `data\scenes` into the new folder before starting if you removed the whole directory, so the opening scene still has its notices and people.

## What to keep

- The on-screen chat, in order.
- `disposable_playtest\session_log.jsonl` for the chronological transcript and resolver results.
- `playtest_provider_usage.jsonl` for request purpose, sent or refused, model, and tokens when the provider supplied them.
- The server window for errors.
- A few notes in your own words: what you tried, what was unclear, and whether the world changed when you expected it to.

Write `unavailable` when a usage field is missing. Do not fill in estimated totals as if they were billed usage.

## Stop

Press Ctrl+C in the server window. Closing the browser does not stop the server.
