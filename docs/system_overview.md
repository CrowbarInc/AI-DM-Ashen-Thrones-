# System Overview

## Core Loop

1. Player input
2. Intent normalization
3. Engine resolution
4. State update
5. GPT narration

---

## Core Systems

### Scene State
- Tracks location, entities, and environmental context
- Must be explicit and machine-readable

### Interaction State
- Tracks active interaction target
- Tracks conversation privacy and player positioning
- Provides continuity across turns

### Affordance Generation
- Produces a small set of actionable choices
- Must be deduplicated, ranked, and pruned
- Outputs 3–5 options

### Prompt Construction
- Converts engine state into a narration payload
- Includes scene + interaction context
- Enforces narration constraints

---

## Ownership Boundaries

Each system owns a responsibility, not an implementation.

| System | Responsibility |
|------|------|
| Engine | State transitions, outcomes |
| Affordances | Player options (generation, dedupe, pruning) |
| Interaction State | Conversation continuity |
| Prompt Layer | Narration constraints and context |
| GPT | Narrative expression only |

---

## Ownership Rules

- Responsibilities must not be duplicated across systems.
- Systems may be refactored, but ownership boundaries must remain clear.
- If a new system is introduced, its ownership must be explicitly defined.

---

## Design Priorities

- Playability > completeness
- Clarity > cleverness
- Determinism > interpretation
- Small, inspectable systems over complex abstractions
