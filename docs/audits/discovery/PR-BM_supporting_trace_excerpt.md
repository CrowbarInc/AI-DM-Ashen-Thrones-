# PR-BM Supporting Trace Excerpt

Date: 2026-09-26
Target session: `6010c8dfe3c0dcae2ea49469`
HEAD: `a5bfdd9e0376173c5aeb4fc762ada259e24bd638`

## Latest Playtest Turn Summary

Extracted from `data/session_log.jsonl`.

| Turn | Player | Final AI-DM emission | Tags / FEM |
| --- | --- | --- | --- |
| 1 | campaign start | Rain-spattered Cinderwatch gate opening; includes refugees, tavern runner, notice board, watcher, townhouse. | `final_emission_gate_replaced`; FEM route `replaced`, source `opening_deterministic_fallback` |
| 2 | Investigate where refugees came from / what they flee | "On closer inspection, a gate serjeant manages the crowd and keeps one eye on the roster board. Closer looking yields nothing further." | `final_emission_gate_replaced`, `final_emission_gate:narrative_safe_fallback` |
| 3 | Sit near tavern runner expecting stew | "As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board." | `final_emission_gate_replaced`, `final_emission_gate:passive_scene_pressure_grounded_observe`; response-type candidate not OK |
| 4 | Ask runner for rumors | `Tavern Runner says, "No. I cannot answer that from what I know."` | FEM route `accept_candidate`, source `normalized_social_candidate` |
| 5 | Offer silver | `Tavern Runner grimaces. "Not something I can say here."` | `retry_escape_hatch`, `forced_retry_fallback`, `retry_exhausted`, `final_emission_gate:emergency_social_minimal`, `terminal_strict_social_emission` |
| 6 | Ask guard about work | `Gate Guard says, "I do not know enough to answer that."` | FEM route `accept_candidate`, source `generated_candidate` |
| 7 | Ask who can answer | `Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."` | `authored_knowledge_realization`; source `structured_fact_candidate_emission` |
| 8 | Ask for audience with Thoran | `Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."` | `authored_knowledge_realization`; debug `topic_pressure:last_answer`; source `structured_fact_candidate_emission` |

## Notable Runtime State Evidence

`data/session.json` contains richer Thoran follow-up material in topic-pressure state:

- last answer: the guard cannot arrange the audience; Thoran holds the cards; the player needs another way inside.
- authoritative text: `Captain Thoran commands the gate watch tonight.`

The final emitted player-visible turn used only the authoritative text.

## Key Source Anchors

- `game/api.py`: request routing, authoritative resolution mutation, GPT narration construction, retry loop, finalization, post-GM structured update adoption, persistence.
- `game/gm.py`: system prompt and GM JSON shape including `scene_update`, `world_updates`, `new_scene_draft`, `player_facing_text`.
- `game/state_authority.py`: state-domain ownership and explicit rule that model output is never an authoritative mutator.
- `game/narrative_authority.py`: visible observation vs bounded inference vs hidden fact assertion vs adjudicated outcome.
- `game/gm_retry.py`: retry failure detection, deterministic retry fallback, terminal retry fallback, `retry_escape_hatch`, `forced_retry_fallback`, `retry_exhausted`.
- `game/final_emission_gate.py`: final-emission orchestration.
- `game/final_emission_strict_social_stack.py`: strict-social candidate normalization and replacement.
- `game/final_emission_terminal_pipeline.py`: terminal visibility / fallback / narrative-mode / acceptance-quality enforcement.
- `game/social.py`: unauthored social fact invention detection and authored knowledge realization.
- `game/defaults.py`, `data/scenes/frontier_gate.json`, `data/world.json`: tavern runner affordance source.

## Git History Signals

Relevant safety/accretion commits observed:

- `1d3580d Unified State Authority Model`
- `e7bd8c2 Narrative Authority Boundaries`
- `02ab9b0 Final Emission Boundary Hardening`
- `6c00e6e D: Final Emission Gate Pressure Reduction`
- `2469338 Extract final emission gate authority boundaries`
- `dcbcefe AI: Response Policy Authority Extraction`
- `59c14aa AP: Fallback Authorship Resolution`
- `11ff282 BJ: Final Emission Gate Responsibility Extraction`
- `683c8df BK: Fallback Ownership Compression`
- `c45cfe0 Finalize strict social fallback ownership extraction`
- `4460543 CK: Fallback Authorship Contraction`
- `ec9c7c8 CN: Final-Emission Adjacency Compression`

## Commands Recorded

- `git status --short`
- `rg --files`
- targeted `rg` searches for final-emission, retry, grounding, authority, and playtest terms
- targeted source reads with `Get-Content` / `Select-String`
- `git log --oneline` for final-emission/retry/social/state-authority paths
- session-log summary extraction from `data/session_log.jsonl`
- `git rev-parse HEAD`
