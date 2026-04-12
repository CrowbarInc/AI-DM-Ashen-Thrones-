# Current Focus

## Active Goals

- Reduce affordance clutter
- Improve social interaction continuity
- Strengthen implied action handling
- Improve cause-and-effect clarity in narration
- Keep one authoritative turn pipeline across `/api/action` and `/api/chat`
- Keep a compact, developer-facing resolved-turn trace in `debug_traces` so ownership/timing drift can be diagnosed from logs
- Distinguish social exchange (`social_exchange`) from deliberate pressure (`social_maneuver`) so ordinary dialogue is not over-mechanized
- Keep check prompting engine-owned (`requires_check`/`check_request`) with a clear player-facing prompt in response payloads
- Keep prompt-context output obligations explicit and machine-readable (`narration_obligations`) from authoritative turn state so GPT acts as active narrator without gaining state/mechanics authority
- Let social resolution mark explicit active-NPC reply expectation (`npc_reply_expected` / `reply_kind`) so prompt-context can prevent dead-air turns without scripting dialogue
- Keep raw player text in prompt context as interpretive evidence, while steering GM narration to continue from resolved state and structured turn summaries instead of echoing player wording
- Ensure campaign start and successful travel/arrival turns emit explicit scene-advancement signals in authoritative resolution state and prompt-context (`scene_advancement` / `must_advance_scene`)
- During active interaction context, route NPC-directed in-character dialogue/questions to social exchange by default; only explicit OOC/procedural/mechanical asks should route to adjudication

---

## Known Issues

- NPC speaker drift in social scenes
- Missed implied actions (sitting, moving, lowering voice)
- Occasional narrative stall loops
- UI can still present ambiguous or redundant choices

---

## Constraints

- Do NOT add new systems
- Do NOT expand mechanics
- Do NOT increase UI complexity
- Focus on consolidation and clarity
- Turn trace scope remains lightweight and developer-facing (compact stage summary, no large telemetry subsystem)
- Preserve engine-first ownership: engine resolves and mutates; GPT narrates only after resolution
- GPT does not decide whether a check is required; engine adjudication/check routing is authoritative
- Adjudication questions are a first-class engine route (distinct from narration fallback and distinct from normal action resolution), with engine-owned procedural answers/check requirements
- Default player action style is third person (for example: `Galinor examines the altar.`)
- Quoted speech is allowed inside action declarations (for example: `Galinor asks, "Who paid for this?"`)
- Preserve the user's expression format through normalization/prompt context; avoid gratuitous first-person rewrites
- Clue mutation ownership remains centralized in engine clue gateways; GPT narration must not create or mutate clue state
- Clue state and clue presentation are distinct:
  - state tracks whether a clue is known in authoritative runtime (`discovered` / `inferred`)
  - presentation tracks player-facing readiness (`implicit` / `explicit` / `actionable`)
  - presentation may change only via deterministic engine-owned paths (never narration text)
- Interaction-state mutation has a single owner: `game/interaction_context.py`
- Implied-action handling runs during normalized turn preparation (before prompt-context assembly and affordance derivation) and is limited to narrow deterministic continuity/context updates
- Interaction continuity must remain explicit in runtime state via:
  - `active_interaction_target_id`
  - `active_interaction_kind`
  - `interaction_mode`
  - `engagement_level`
  - `conversation_privacy`
  - `player_position_context`

---

## Authoritative Turn Order

1. player input
2. intent normalization / expansion
   - includes narrow implied-action continuity preparation (deterministic, conservative, no speculative target invention)
   - includes lightweight mixed-turn segmentation (declared action, embedded question, observation intent, contingency, spoken text) before dominant action classification
3. action classification
4. engine resolution
5. authoritative state mutation
6. prompt-context construction
7. GPT narration
8. affordance derivation
9. response/debug packaging
   - includes compact authoritative `turn_trace` in `debug_traces` (input -> normalization/classification -> resolution path -> post-resolution state snapshot)

---

## Success Criteria

- Player always understands available actions
- Conversations maintain clear continuity
- Outcomes feel deterministic and legible
- UI supports decision-making, not exploration overload
- Ordinary conversational turns can proceed without unnecessary roll prompts
- When a check is required, the engine surfaces a clear check prompt in payload (`requires_check`, `check_request`) without relying on GPT to infer or announce rolls

---

## Final validation layer

### Playability Validation Pass

Final validation that the system behaves like a competent human DM.

This is a **validation and observability** layer, not a new runtime system.

Backed by:

- Deterministic evaluator (`game/playability_eval.py`)
- Transcript-backed integration tests (`tests/test_playability_smoke.py`)
- Scenario runner and artifacts (`tools/run_playability_validation.py`)

**Evaluation scope:** turn-level behavioral quality (not system architecture).

**Pass criteria:**

- answers questions directly
- respects player intent
- escalates logically
- maintains immersion

**Important:**

- Evaluation is **turn-scoped**
- Session-level summaries are **derived** from per-turn evaluations
- No runtime behavior changes are introduced at this stage
