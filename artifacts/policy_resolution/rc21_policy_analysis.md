# RC-21 Policy Analysis

Campaign: RC-10 / RC-21 Policy Resolution  
Identifier: `rc10_rc21_policy_resolution_20260919`  
Status: analysis only; no policy chosen; no implementation

## 1. Plain English

A **destination redirect** is an NPC telling the player where to go next: a person, a landmark, or a path.

In the live fixture, the tavern runner says the player will find **Lirael** near the **notice board**.

The unresolved question is:

> After that line is spoken, what official record should the game keep so later turns know the party has something to follow?

Three stores are involved:

| Store | Ordinary meaning | Current role |
|---|---|---|
| NPC pending-lead state | a scene-local sticky note: “talk to this person next” | `scene_runtime.pending_leads` with `leads_to_npc` |
| Discoverable-clue state | authored scene secrets/landmarks the party can uncover | `data/scenes/*.json` `discoverable_clues`, plus `clue_knowledge` after reveal |
| Lead registry | the session’s official case file of leads | `session.lead_registry`, written by `apply_engine_lead_signal` |

The prior shorthand “pending versus clue” is close but incomplete. Current code already writes **clue knowledge, a rumor-style pending row, and a registry row**. What it does **not** write is an NPC pending row targeting `emergent_town_crier`.

## 2. Concrete Gameplay Example

The player asks the tavern runner who posted the missing-patrol notice.

The runner answers: “Check with Lirael—you’ll find her near the notice board.”

What should happen?

**If NPC pending-lead is official:**  
Later the player can say “follow the lead to Lirael.” The engine already knows how to pursue an NPC pending row (`tests/test_qualified_pursuit_parser.py`). The party has an actionable person-target.

**If authored-clue / landmark evidence is official:**  
The engine records “Check the notice board.” Lirael remains a name in spoken text unless the scene already authors her as a crier/discoverable. “Follow Lirael” has no NPC lead to pursue.

**Current runtime, confirmed this campaign:**  
The second thing happens. Lirael is dropped. The notice board becomes an actionable location/rumor.

## 3. Current Runtime Behavior

```text
social interaction / test resolution
        ↓
apply_socially_revealed_leads
        ↓
extract_actionable_social_leads
        ↓
_scan_scene_anchored_destination_leads
        ↓
named-crier bind requires:
    authored discoverable crier name
    AND crier id from addressables / active_entities
        ↓
current frontier_gate canon has neither
        ↓
fallback: scene_anchor:notice_board
        ↓
apply_engine_lead_signal → lead_registry  (declared source of truth)
        ↓
reveal_clue / clue_knowledge
        ↓
pending_leads rumor mirror  (declared compatibility only)
        ↓
later pursuit / minimum-lead / routing reads pending + registry
```

Actual symbols:

| Role | Symbol |
|---|---|
| First landing | `game.clues.apply_socially_revealed_leads` |
| Narration second pass | `game.clues.apply_social_narration_lead_supplements` |
| Destination extraction | `game.clues._scan_scene_anchored_destination_leads` |
| Crier name evidence | `game.clues._discoverable_crier_names` |
| Crier id bind | `game.clues._crier_npc_id_from_addressables` |
| Authoritative write | `game.leads.apply_engine_lead_signal` |
| Compatibility mirror | `game.storage.add_pending_lead` |
| Scene canon used by the tests | `game.storage.load_scene("frontier_gate")` → `data/scenes/frontier_gate.json` |
| Player pursuit consumer | `game.intent_parser.parse_freeform_to_action` |

Campaign diagnostic (`artifacts/policy_resolution/rc21_runtime_snapshot.json`):

- `CRIER_ID = None`
- `CRIER_NAMES = []`
- extracted lead: `lead_frontier_gate_notice_board` / `scene_anchor:notice_board`
- pending: rumor-only “Check the notice board”
- registry related NPCs: `tavern_runner` (speaker), not `emergent_town_crier`
- Lirael is absent from official state

Evidence class: **CONFIRMED BY CURRENT CODE**.

## 4. Current Test Expectation

The three red tests in `tests/test_social_destination_redirect_leads.py` all require:

```text
pending_leads contains exactly one row with leads_to_npc == "emergent_town_crier"
```

They also expect:

- an `authoritative_lead_id`
- a registry social row related to `emergent_town_crier`
- repeat redirects to merge rather than duplicate
- that NPC row to stay distinct from an existing old-milestone pending row

The same file’s passing fourth test says flavor travel text must **not** invent a crier lead. Both sides already agree that mere directional flavor is not enough.

Focused failures:

```text
assert len(npc_pending) == 1
assert 0 == 1
```

Stdout shows the runtime discovering `narration_ctx_frontier_gate_notice_board` and `lead_frontier_gate_notice_board` instead.

Evidence class: **CONFIRMED BY CURRENT TEST**.

## 5. Architectural Context

Current code comments already declare a third model:

```text
Authoritative registry row (registry_id) is source of truth;
pending_leads is compatibility mirror only.
```

`apply_engine_lead_signal` is the engine-owned write. `compat_pending_lead_needed` is true only when a **scene** target exists, not when only an NPC target exists.

Architecture doctrine (Campaigns 1–6 / AR-AD / AR-CA):

- runtime truth before narration
- domain modules own simulation truth
- GPT authors prose, not authoritative state
- derived/compatibility stores must not become second owners

State authority:

- `discoverable_clues` begin as unpublished/authored scene content (`hidden_state` adjacent)
- reveal writes into `scene_state` / clue knowledge through named operations
- `merge_pending_lead_runtime` is an allow-listed hidden → scene write, not a license for narration to invent entities

AI GM contract:

- engine owns state transitions
- GPT must not invent or override state
- a new named entity may appear in **narration** only with an explicit source and marked certainty
- that narration rule is not the same as creating an official NPC lead

Lead/clue cleanup is still **explicitly deferred** in `docs/current_focus.md`. RC-21 is the deferred ownership question, not a forgotten bug.

Evidence class: **CONFIRMED BY CURRENT ARCHITECTURE DOC** plus **CONFIRMED BY CURRENT CODE**.

## 6. Historical Context

| Fact | Class |
|---|---|
| RC-21 tests were added 2026-04-03 (`fc73bc8`) | **CONFIRMED BY HISTORICAL ARTIFACT** |
| `frontier_gate.json` still authored Lirael / town-crier discoverables at that time | **CONFIRMED BY HISTORICAL ARTIFACT** (replay copies and `game/defaults.py` fallback text) |
| Scene canon was cleaned 2026-04-25 (`4d3d71a`); `frontier_gate.json` lost 540 lines | **CONFIRMED BY HISTORICAL ARTIFACT** |
| Current canon discoverable is only the patrol-route clue | **CONFIRMED BY CURRENT CODE** |
| Extraction comments still say frontier_gate authors Lirael beside `emergent_town_crier` | **CONFIRMED BY CURRENT CODE** (stale comment vs current file) |
| `game/defaults.py` still contains the old Lirael discoverable rumor | **CONFIRMED BY CURRENT CODE** |
| Tests load canon via `load_scene`, not the defaults fallback | **CONFIRMED BY CURRENT CODE** |

Inference: the tests encode the **pre-cleanup** world, in which mentioning Lirael could bind to an authored crier. After canon cleanup, the extractor still requires that authorship and therefore degrades to the notice board.

RC-21 is therefore:

- partly a leftover of cleaned scene canon
- partly an unresolved authority choice among registry, pending, and clue/landmark evidence
- not a random extractor crash
- not proof that current production is “broken” unless the user wants Lirael to remain a follow-up target

## 7. NPC Pending-Lead Model

If redirect authority belongs to NPC pending-lead state:

- **Owns the lead:** `scene_runtime[scene].pending_leads` row with `leads_to_npc`.
- **Becomes authoritative:** as soon as the redirect is extracted and a pending row is written.
- **Represents:** player-facing follow-up more than NPC belief or world truth. The speaker’s claim is turned into an actionable person-target.
- **Lifecycle:** created/merged by `add_pending_lead`; later consumed by intent/pursuit and social discussion tracking.
- **Persistence:** scene-runtime local. If the scene overlay is dropped, the sticky note can vanish unless a registry id remains.
- **Consumption:** `game.intent_parser` reads `pending_leads` for “follow the lead to Lirael.”
- **Deduplication:** merge by `authoritative_lead_id`.
- **Invalidation:** not modeled as “the runner was lying.” The row stays until resolved/superseded elsewhere.
- **Replay:** deterministic if extraction inputs are deterministic.
- **Provenance:** weaker unless `authoritative_lead_id` points at a registry row.
- **Future interactions:** best for person-pursuit. Poor at distinguishing rumor from presence.

This is what the three red tests want.

## 8. Discoverable-Clue / Landmark Model

If redirect authority belongs to authored discoverable-clue / landmark state:

- **Owns the lead:** scene-authored `discoverable_clues` plus revealed `clue_knowledge`.
- **Becomes authoritative:** only when the scene already authored the person or landmark, and the spoken line matches that evidence.
- **Represents:** world/scene authorship first. Player knowledge is a reveal of existing content, not invention of a new NPC.
- **Lifecycle:** authored at content time; revealed at play time.
- **Persistence:** scene canon persists independently of the speaker living or dying.
- **Consumption:** minimum-actionable-lead already prefers authored discoverables, then exits, then extracted social.
- **Deduplication:** clue id / compare-id.
- **Invalidation:** changing canon changes what can be realized. A lying NPC cannot create a person who is not authored.
- **Replay:** strongest, because the evidence is in the scene file.
- **Provenance:** “this destination exists because the scene authored it.”
- **Future interactions:** cleanest engine-first model. Weaker at honoring a named person the NPC just invented in speech.

This matches current `frontier_gate` extraction: no authored Lirael, therefore notice-board landmark only.

## 9. Third Model Already In The Repository

The apparent binary is false. Existing architecture already names a third model:

**The lead registry is canonical. Pending leads are a compatibility projection. Discoverable clues are evidence that gate NPC binding.**

Support:

- `SESSION_LEAD_REGISTRY_KEY` comment
- `_apply_extracted_social_leads` comment
- `apply_engine_lead_signal`
- extraction requiring authored crier name + entity id
- AR-AD: runtime truth before narration; no second owner
- deferred lead/clue cleanup rather than a second pending-lead engine

This third model does **not** by itself decide whether Lirael becomes an NPC target. It decides **where the official record lives** and **what evidence is required before an NPC target may be bound**.

Include this model because the repository already implements it. Do not treat it as a new elegant invention.

## 10. Simulationist Consequences

### Knowledge

Who actually knows the destination?

- The tavern runner claims to.
- The current engine does not know Lirael as a gate entity.
- The player has heard a name.

### World truth

Does the destination exist independently of the mention?

- The notice board does. It is visible, interactable, and authored.
- Lirael does not, in current `frontier_gate` canon.
- Historical canon and `defaults.py` still remember her. That is leftover content, not current scene truth.

### Player knowledge

Hearing the redirect makes Lirael **player-known speech**, not automatically an official follow-up target.

### NPC reliability

Current extraction does not model mistaken, lying, uncertain, rumored, or misleading speakers. It pattern-matches text against authored evidence.

- If the runner is lying about Lirael, Policy A still creates an NPC follow-up.
- Policy B/C create only the authored landmark, which exists regardless of the lie.
- None of the current options store “this is the runner’s claim, confidence=rumor.”

### Discoverability

Mentioning a destination does **not** currently make a new person discoverable. It can make an authored landmark actionable.

### Persistence

The notice-board registry/clue row survives the runner leaving. An NPC pending row would also survive in scene runtime, but would still not prove Lirael exists in the world.

If the runner dies, Policy A keeps a person-target that the world may not contain. Policy B keeps a board that is still there.

### Contradiction

A second NPC giving a conflicting redirect would create or merge another extracted lead. Registry merge is monotonic and does not currently record competing claims as competing claims.

### Provenance

Today the game can answer “why does the board matter?”: social extraction from the runner, source `scene_anchor:notice_board`.

It cannot answer “why does the party believe Lirael matters?” because Lirael was never stored.

### Replay

Reconstruction is deterministic from scene + narration + resolution. The missing piece is policy, not non-determinism.

### Future AI reasoning

Cleanest distinction if the registry remains official:

| Need | Best current field |
|---|---|
| world fact | authored scene / world entity |
| NPC belief | not modeled; would need claim/provenance |
| player-known information | clue_knowledge / journal publication |
| actionable lead | lead_registry lifecycle/presentation |
| rumor | `LeadConfidence` / `rumor_text` |
| clue | `clue_knowledge` + `evidence_clue_ids` |

Pending-only NPC rows collapse those distinctions into one sticky note.

## 11. Policy Options

### POLICY A — Spoken redirect creates an NPC follow-up

Meaning: “Find Lirael near the notice board” writes an official actionable lead targeting `emergent_town_crier`.

Current support: the three red tests; qualified pursuit already understands that shape; older scene canon authored Lirael; extraction comments still assume that authorship.

Contradicting evidence: current canon has no Lirael; extractor requires authored name+id; runtime writes notice-board instead; engine-authority doctrine; scene-clean commit.

Runtime consequence: players can pursue Lirael by name.

Architecture consequence: either restore authored Lirael/crier content, or let narration instantiate an NPC lead. The second path weakens “truth before narration.”

Compatibility consequence: pending remains a live authority surface, against the current “mirror only” comment.

Player-facing consequence: the spoken name becomes a follow-up option.

Migration cost: **moderate**. Product and/or content change, plus pending/registry alignment. Not a one-line test edit if the user wants real Lirael pursuit.

### POLICY B — Spoken redirect follows authored scene evidence

Meaning: a named person becomes an official NPC lead only if the scene already authors that person. Otherwise the authored landmark/clue is what becomes actionable.

Current support: current extractor; current `frontier_gate.json`; AI GM / AR-AD engine-first rules; minimum-lead preference for authored discoverables.

Contradicting evidence: the three red tests; player-facing quality of “Find Lirael”; historical Lirael content.

Runtime consequence: current behavior stands.

Architecture consequence: pending stays a mirror; clues stay evidence; registry stays official.

Compatibility consequence: tests must be modernized to assert notice-board/registry/clue outcomes rather than `leads_to_npc`.

Player-facing consequence: the runner’s name-drop does not become a person-target unless content authors her.

Migration cost: **localized** if only tests/docs change; **moderate** if content is also reconciled (`defaults.py` still has Lirael).

### POLICY C — Registry canonical; pending and clues are projections

Meaning: choose the official store first. `lead_registry` is the case file. `pending_leads` may surface follow-ups. Discoverable clues gate what may be realized. This is already declared.

Current support: current write path and comments.

Contradicting evidence: the red tests still treat pending NPC rows as the assertion surface; `compat_pending_lead_needed` ignores NPC-only targets; intent parsing still reads pending.

This is the architectural frame, not a complete gameplay answer. A later implementation should keep C even if the user also chooses A or B.

Migration cost: already mostly present. Remaining work is expectation alignment and leftover comment/content drift.

## 12. Decision Consequences

### If we choose A

- Conceptually: a spoken person-redirect is enough to create a follow-up person.
- Authoritative: NPC pending, or registry rows that carry `related_npc_ids=["emergent_town_crier"]` plus a pending mirror.
- Evidence-only: discoverable clues become optional color unless used as bind evidence.
- Transitional: pending becomes live again unless C is kept.
- Future developers preserve: Lirael-style redirects must create person-targets.
- Bugs prevented: “the NPC told me who to find, but the game forgot the person.”
- Legitimate behavior constrained: the engine can no longer refuse to instantiate an unauthored person.
- Duplicate ownership: increases if pending and registry both stay authoritative.
- Implementation: moderate; architectural if narration alone may create entities.

### If we choose B

- Conceptually: speech reveals authored world, it does not author people.
- Authoritative: authored scene evidence + registry realization.
- Evidence-only: narration text.
- Transitional: pending remains a mirror.
- Future developers preserve: do not bind NPC leads without authored name/entity evidence.
- Bugs prevented: GPT/narration inventing pursueable people.
- Legitimate behavior constrained: good spoken redirects may not become person-pursuit options.
- Duplicate ownership: decreases if tests stop treating pending as authority.
- Implementation: localized to tests/docs, or moderate if leftover Lirael content is cleaned.

### If we choose C explicitly

- Same store model the code already claims.
- Still requires A or B for the Lirael gameplay question.
- Strengthens reconciled boundaries.
- Implementation: mostly documentation/expectation; tiny if comments/tests only.

## 13. Evidence Table

| Category | Evidence | Stance |
|---|---|---|
| Current runtime behavior | Notice-board location/rumor lead; no `emergent_town_crier` pending | SUPPORTS_OPTION_B |
| Current runtime behavior | Registry write declared authoritative; pending labeled compatibility | SUPPORTS_OTHER (C) |
| Current tests | Three red NPC-pending assertions | SUPPORTS_OPTION_A |
| Current tests | Flavor-text negative still passes | NEUTRAL |
| Current tests | Qualified pursuit of Lirael requires an NPC pending row | SUPPORTS_OPTION_A |
| Current architecture | AR-AD runtime truth before narration; GPT not a truth owner | SUPPORTS_OPTION_B |
| Current architecture | State-authority reveal/merge seams | SUPPORTS_OTHER (C) |
| Current governance | Lead/clue cleanup deferred, not decided | AMBIGUOUS |
| Historical design intent | Tests predating 2026-04-25 canon cleanup | SUPPORTS_OPTION_A |
| Historical design intent | Explicit scene-canon cleaning of Lirael sprawl | SUPPORTS_OPTION_B |
| Simulationist/gameplay | Named-person follow-up quality | SUPPORTS_OPTION_A |
| Simulationist/gameplay | Lying/rumor/unauthored-person integrity | SUPPORTS_OPTION_B |
| Future extensibility | Distinct world / belief / player-known / lead fields | SUPPORTS_OTHER (C) |
| Migration/implementation | A needs product/content; B can be test-side | SUPPORTS_OPTION_B |

## 14. Repository-Supported Recommendation

```text
Repository-supported recommendation: POLICY B, keeping POLICY C as the store model
Confidence: MEDIUM-HIGH
Reason: Current canon, extractor gates, registry comments, and Campaign 1–6 doctrine all refuse to let narration invent an NPC lead. The red tests remember a world in which Lirael was authored. If the user wants Lirael pursuit, restore her as authored content rather than making pending_leads a second authority.
```

This is advisory. The policy has **not** been decided.

The remaining human question is gameplay, not a hidden technical defect:

> Should “Find Lirael” become an official follow-up when an NPC says it, even though current scene canon does not author Lirael?

## 15. User Decision

```text
RC-21

Plain-English question:
When an NPC points the player at a named person or landmark, what official follow-up should the game record?

Option A:
Record an NPC follow-up (Find Lirael / town crier), even if she is not currently authored at the scene.

Option B:
Record only what the scene already authors (here: Check the notice board) unless Lirael is restored as content.

Option C:
Keep the lead registry as the official case file; pending and clues are projections. This can accompany A or B and is already declared.

Existing architecture leans:
B + C

Important consequence:
A makes “follow Lirael” work. B prevents spoken text from inventing people. Choosing A without restoring authored Lirael weakens engine-first simulation.

Cursor recommendation:
B, keep C

USER DECISION REQUIRED:
[A / B / B+C / A+C / Other]
```
