# Interpretation Contract Audit

Current live production interpretation contract:

- Input: player text, scene summary, visible catalog rows, and up to two recent visible turns (`game/live_chat_interpretation.py:222`).
- Provider output: strict PR-DR interpretation JSON, adapted into a bridge record.
- Acceptance: structurally valid, `IN_WORLD_ACTION`, `INTERPRETED`, no unresolved references, exactly one action component, connected operation, visible compatible target.
- Output: normalized action for existing pipeline, or a blocked non-mutating clarification response.

Supported bridge operations (`game/player_interpretation_bridge.py:14`): `PERCEIVE`, `INSPECT`, `ASK`, `MOVE`.

Unsupported outcomes include: answer OOC as helpful text, answer IC knowledge without target, continue dialogue from implicit focus after unbound ASK, represent emotional/incidental behavior, represent primary intention plus setup, represent ordered plans, establish intended destination, or acknowledge correction.

Why this exists: it protects authority by preventing invented targets, unsupported operations, unresolved references, and unsafe fall-through. The cost is that understood but non-bridgeable intent becomes failure.

Smallest coherent contract change: add a pre-execution envelope with `response_intent`, `primary_goal`, `execution_plan`, `missing_slots`, and `incidental_context`. Keep operation validation unchanged for actual mutation.
