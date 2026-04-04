# NPC lead continuity — practical testing

Compact checklist for re-validating **NPC lead continuity** after social or prompt-context changes. Architecture and prompt-contract intent live in code comments (Block C); this file is **procedural** only. Full pytest lanes and markers: `tests/README_TESTS.md`.

## Validation layers

**Unit/integration** — Storage, prompt export, behavior hints, and grounding invariants (targeted modules under `tests/`). **Synthetic transcript regression** — Deterministic multi-turn sessions that lock the exported continuity / repeat-suppression contract, not narration wording. **Manual gauntlets** — Spot-check conversational feel and obvious repetition or speaker bleed.

## Commands

From repo root (on Windows, use `py -m pytest` if `pytest` is not on your `PATH`; see `tests/README_TESTS.md`).

| Lane | Command |
|------|---------|
| Default full run | `py -m pytest -q` |
| Synthetic-focused | `py -m pytest tests/test_synthetic_sessions.py -q` |
| Prompt-context | `py -m pytest tests/test_prompt_context.py -q` |
| Fast lane | `pytest -m "not transcript and not slow"` |

- **Default** `py -m pytest -q` includes synthetic-player tests (`pytest.ini` only adds `-q`; no marker filter).
- **Fast lane** skips slow smoke (e.g. `tests/test_synthetic_smoke.py`) but still runs the lighter synthetic modules (`tests/README_TESTS.md` → Synthetic-player harness).

**Synthetic and manual:** Continuity can stay correct even when a later same-NPC follow-up does not create a fresh discussion write (for example, no new `mention_count` increment), because prompt/export continuity can still come from existing discussion rows.

## Manual continuity gauntlets

Repeat each in the live UI (or your usual play harness). Adjust scene/NPC names to whatever you have loaded.

### A. Same NPC should advance, not restate

- **Setup:** One NPC with a lead you can follow up on in-scene.
- **Player inputs:** First line that invites the topic; then a second line that assumes the lead is already on the table.
- **Expected:** First mention may introduce or hint the lead; the follow-up advances, clarifies, or narrows — not a full reintroduction as if new.
- **Common failure mode:** Same premise repeated like a first introduction.

### B. Hint upgrades to explicit cleanly

- **Setup:** A lead that can start hinted and become explicit over turns.
- **Player inputs:** Draw the NPC out across several exchanges until the lead is clearly stated.
- **Expected:** Hint → explicit is allowed; after it is explicit, later turns do not reset to “first time you hear this.”
- **Common failure mode:** Explicit disclosure never lands, or later responses reset the thread.

### C. Acknowledged lead becomes shared context

- **Setup:** NPC states a lead; you acknowledge clearly in-character.
- **Player inputs:** Acknowledge, then ask a next-step question or change subtopic within the same thread.
- **Expected:** NPC moves past basic re-explanation toward next beats.
- **Common failure mode:** NPC keeps re-explaining the same premise.

### D. Same lead across different NPCs does not bleed memory

- **Setup:** Two different NPCs who could plausibly discuss the same lead; talk to A, then B.
- **Player inputs:** Surface the lead with A (including acknowledgement if needed); then raise it with B.
- **Expected:** B can discuss the same lead with their own posture; A’s private acknowledgement/disclosure state does not become B’s.
- **Common failure mode:** B acts as if A’s continuity state belongs to them.

### E. Absent lead-salient NPC does not override grounded speaker

- **Setup:** Grounded active speaker in scene; another NPC exists in lore or context but is not the addressed / present speaker.
- **Player inputs:** Lines that mention leads tied to the absent NPC while addressing the grounded NPC.
- **Expected:** Reply stays with the grounded active NPC.
- **Common failure mode:** Off-scene or absent NPC “steals” the reply because the lead is salient to them.
