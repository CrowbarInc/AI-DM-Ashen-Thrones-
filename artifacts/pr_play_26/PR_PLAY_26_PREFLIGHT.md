# PR-PLAY-26 preflight

PASS. Exactly one offline preflight; zero live requests and no campaign initialization. Repository branch/revision and full pre-existing dirty status are in repository_status.json. No AGENTS.md was found in repository or immediate parent directories. Existing changes preserved.

Uses scripts/run_live_playtest.ps1 infrastructure through tools.playtest.runner/worker with an evidence-only bounded controller; no standalone provider client. Production HTTP /api/new_campaign, /api/start_campaign and /api/chat; all calls explicitly Player. Existing FiveTurnGameplay fixture provides storage and worker compatibility; its five-turn action loop is never run.

Configured gpt-4.1-mini, credentials present but not serialized, no alternate model settings. ASHEN_OPENING_RENDERER=1. SDK retries 0, host retries disabled, provider request ceiling 5, no judges/fallback models. Token limits unchanged (200000 input, 20000 output, 220000 total). Production admission accepted five synthetic invocations and refused a sixth without provider contact.

Loopback round-trip, HTTP readiness, Player state 200, snapshot capture, diagnostics and cleanup/port release verified. Privileged reads remain rejected by unchanged resolve_requested_ui_mode, exercised offline for author/debug; no privileged HTTP calls. Readiness credentials_present=false refers to the deliberately disabled offline worker; safe_configuration.json confirms live credentials configured.

PR-PLAY-23 normalization is present in game/local_interaction.py and invoked by conversational_orchestration.py; classify_turn/evaluate preserve structural semantic-stop distinctions. PR-PLAY-25 public_fact_dialogue.select_public_offering is called by dialogue_authority.build_dialogue_authority. Source hashes preserve exact versions. Owned worker termination/wait verifies process cleanup; no graceful ASGI shutdown handshake is claimed.
