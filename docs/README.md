# Ashen Thrones AI GM

A local, browser-based solo PF1e-inspired AI GM toolkit built for chat-first play with persistent scenes, world state, faction pressures, projects, and optional action helpers.

## Features
- Chat-first solo campaign play in the browser
- Persistent campaign, scene, character, world, and combat state
- World layer with factions, projects, assets, and event log
- GPT can draft and auto-save new scenes
- Optional combat action helpers for initiative, attacks, spells, and skill checks
- Character sheet import optimized for the exported JSON format used in this project
- One-command startup

## Requirements
- Python 3.9+
- OpenAI API key in `OPENAI_API_KEY`

## Setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="your_key_here"
# Optional: override the model (defaults to gpt-4o-mini)
# $env:MODEL_NAME="gpt-4o-mini"
python run.py
```

Alternatively, use a local `.env` file for development:

```powershell
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY (never commit the real .env)
python run.py
```

Open:
`http://127.0.0.1:8000`

## Notes
- The engine owns mechanics and persistence.
- GPT owns narration, scene drafting, world suggestions, and narrative consequences.
- Scene drafting is auto-saved when GPT returns `new_scene_draft`.
- The app starts with the `Ashen Thrones` campaign seed, but the Campaign tab can rewrite it.

## Current Supported Mechanics
- Initiative
- End turn
- Basic attacks
- Daze
- Magic Missile
- Shield
- Risky Strike
- Defensive Stance
- Basic condition framework

## Project Layout
- `game/` backend modules
- `data/` runtime state
- `data/scenes/` scene registry
- `static/` browser UI
- `docs/README.md` this file
