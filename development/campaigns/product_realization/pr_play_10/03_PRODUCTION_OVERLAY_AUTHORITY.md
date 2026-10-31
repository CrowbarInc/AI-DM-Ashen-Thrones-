# 03 — Production Overlay Authority

PR-PLAY-10 · 2026-10-30 America/New_York · evidence_scope: structural_only.

`production_source_map.json` provides modules/functions/verified line numbers and contracts.

| Operation | Owner / contract | Persistence and tests |
| --- | --- | --- |
| Create / shape | storage.get_runtime_scene_overlay(session, scene_id) returns mutable default overlay | Lazy in-memory root; saved with session; save_load / post_gm tests |
| Read | storage.get_effective_scene → build_effective_scene(canon, overlay) returns merged copy | Canon unchanged; runtime reader may create default shape |
| Runtime clues | storage.get_scene_runtime merges legacy discovered clues into overlay | Session-owned; world_updates_and_clue_normalization |
| Declaration / shape validation | gm.call_gpt parses structured envelope; immutable_valid_response validates candidate; response_policy_enforcement filters exact hidden-fact promotion | No narration-only persistence authority; structured / semantic suites |
| Apply | api._validate_gm_scene_update_for_legacy_adoption returns PostGmSceneUpdateEffect; _apply_post_gm_updates appends visible/discoverable/hidden layers and mode | Engine/API owns application; post_gm_adoption_gateway |
| Persist | storage.save_session and runtime coherency guard | Session envelope; save/load and persistence tests |
| Clear | new_campaign resets runtime using default session | No general arbitrary overlay deletion authority; campaign initialization tests |
| Failure restore | _OpeningScope captures session/world/combat/log and restores uncommitted attempt | Existing process lock serializes starts; PR-PLAY-04 + new rollback/concurrency tests |

Purpose: scene-scoped playthrough additions without editing authored templates. Reads can create
empty shape. Structured scene_update can append overlays during opening or ordinary processing;
ordinary prose alone is not a scene_update. The gateway is transitional: shape enforcement is
active, semantic policy enforcement is observe_only. It does not prove arbitrary proposed facts
are authorized. Declarations do not authorize themselves. Canonical scene templates remain
unchanged, though runtime mode/layers can affect effective views under existing owners.
Hidden layers remain distinct; exact hidden-to-visible promotion is filtered by response policy.
This pass does not claim that filtering proves all paraphrased disclosures impossible.

Instrumentation in replay.json shows in-memory overlay application BEFORE the final opening
acceptance check, then save_session after acceptance. _OpeningScope restores failed attempts,
including a forced save failure after real overlay application (failed_overlay_rollback.json).
This is not a new transaction implementation or a crash-atomicity claim. Repeated Start and
concurrent starts use the existing single-process lock/started gate; no duplicate commits.
Persistent facts require structured/engine authority. Plain sensory presentation can remain
text-only. No new rule promoting prose to world facts was introduced.
