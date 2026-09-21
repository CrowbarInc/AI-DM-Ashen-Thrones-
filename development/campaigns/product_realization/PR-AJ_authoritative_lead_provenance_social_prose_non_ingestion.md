# PR-AJ — Gameplay / State Authority: Authoritative Lead Provenance and Social-Prose Non-Ingestion

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/praj_authoritative_lead_provenance/`

---

## 1. Executive Summary

PR-AJ repaired the highest-leverage ordinary-play failure after PR-AI: a legitimate bound-NPC answer was being ingested as a generated `narration_ctx_…` lead, letting narration wording mint gameplay authority.

The representative Guard Captain / Frontier Gate case is repaired. It is not the proof of the contract.

The recovered authority direction is:

```text
authoritative world / social / clue / lead outcome
    → structured state consequence, where authorized
    → narration communicates that outcome
```

The inverse is rejected:

```text
narration wording
    → inferred mechanical consequence
    → authoritative state
```

`narration_ctx_…` creation was a transitional/compatibility fallback in `reconcile_final_text_with_structured_state`. It existed to recover structured leads from freeform AI narration when the social engine reported an empty payload. RC-21 = B + C already supplies the intended replacement for official follow-up: authored-scene evidence plus the canonical lead registry.

PR-AJ does not delete extraction. Contextual extraction remains a non-authoritative continuity hint. When no authorized structured or scene-anchored lead exists, prose-to-lead promotion now fails closed.

No new lead architecture. No new knowledge store. No Cinderwatch-specific filter.

---

## 2. Starting Failure

PR-AI extended replay T9:

> Player: I turn to the Guard Captain. "What's being done about the missing patrol?"
> GM: "We're maintaining a strict watch along the northwest mud track..."
> Interlocutor: `guard_captain`
> New registry row: `narration_ctx_frontier_gate_were_maintaining_a_strict`
> Title: `"we're maintaining a strict`
> `discovery_source`: `clue_explicit`
> Side effect: `minlead_exit_frontier_gate_old_milestone` entered `pending_leads`

The NPC answer was legitimate. The authority direction was not.

---

## 3. End-to-End False Lead Trace

Traced before production changes.

| Stage | Result |
| --- | --- |
| Original fact | Authored notice / watch material. Captain may communicate it. |
| Bound speaker | `guard_captain` |
| Structured social result | Empty. Addressable has no topics. PR-AI late realization writes **player-facing text only**. |
| Raw / finalized prose | Live model or realization line, e.g. `"We're maintaining a strict..."` |
| Extractor input | Final `player_facing_text` in `reconcile_final_text_with_structured_state` |
| Extraction decision | `_resolution_claims_no_information` true; text has operational hooks (`patrol` / directional color); `extract_actionable_social_leads` empty |
| Generated lead | `narration_ctx_{scene}_{slug(first words)}` from the `contextual_lead_clues` branch |
| Provenance | None. Slug from prose. Later stamped `clue_explicit` by clue discovery. |
| Destination | None on the ctx row. `ensure_scene_has_minimum_actionable_lead` then added `minlead_exit_…` because the fabricated payload made the turn look information-bearing. |
| Registry / pending / clues | Ctx row entered lead registry + clue_knowledge. Pending gained the exit safety-rail row. |
| Persistence | Saved with session/world. |
| Later consumers | Intent parser reads `pending_leads` as pursuit; registry titles can feed follow/pursue matching. |

---

## 4. First Prose-to-Authority Promotion Point

**Confirmed:** `game/narration_state_consistency.py` → `reconcile_final_text_with_structured_state` → `contextual_lead_clues` fallback.

This is the first point where ordinary prose became gameplay authority. Not “a `narration_ctx_…` id existed,” but:

1. empty social payload
2. narration judged to contain hooks
3. no authorized extracted lead
4. raw text / contextual subject used as `clue_id`
5. `apply_socially_revealed_leads` landed that id as a canonical clue/lead

Creator of the id: that fallback branch, format `narration_ctx_{slugify(scene)}_{slugify(primary)[:48]}`.

PR-AI realization is upstream of this only as a text writer. It did not create the lead.

---

## 5. `narration_ctx_…` History and Purpose

| Question | Evidence |
| --- | --- |
| Where created? | Only `reconcile_final_text_with_structured_state` contextual fallback. |
| Intended purpose? | Block 5 narration/state consistency: if the model narrated hooks while the social engine claimed “no new information,” recover a structured topic/clue so later landing and the frontier-gate minimum-lead rail could fire. |
| Documented? | Function docstring and tests in `tests/test_narration_state_consistency.py`. Not a canonical lead-registry contract. |
| Tests? | Yes. Several expected empty-payload + hooky prose to upgrade structured state. |
| Canonical? | No. Ids are prose slugs. |
| Predates RC-21? | Yes. RC-21 later required authored-scene follow-up + registry ownership. |
| Recover leads from freeform narration? | Yes. That was the purpose. |
| Legitimate current content? | No authored content depends on a `narration_ctx_…` id. RC-21 tests reuse one as a historical fixture clue_id, then assert the authored notice-board lead. |
| Can it create destinations/entities? | The ctx row itself is a rumor/clue. Combined with `ensure_scene_has_minimum_actionable_lead` it could open an authored-exit pursuit surface the turn did not grant. It does not invent a new scene file. |
| Provenance? | Insufficient. `clue_explicit` after landing hides that the source was narration. |

---

## 6. Current Classification / Authority Status

Classification from repository evidence, not invented to justify deletion:

| Layer | Status |
| --- | --- |
| `narration_ctx_…` authority mint | **Transitional / compatibility fallback.** Obsolete as an authority writer after RC-21. |
| `extract_actionable_social_leads` (topic hooks, structured facts, scene anchors, existing text-hook specs) | **Compatibility / authorized extraction.** Kept. This is the RC-21-adjacent path. |
| `remember_recent_contextual_leads` | **Non-authoritative continuity / prompt hint.** Kept. |
| Canonical lead registry | **Canonical lead identity.** Unchanged. |
| `pending_leads` | **Compatibility projection.** Unchanged contract. |
| Clue knowledge | **Projection / player-knowledge surface.** Unchanged contract. |

PR-AJ removed the obsolete **authority role** of unsourced contextual ingestion. It did not delete extraction.

---

## 7. Existing Consumers and Dependencies

| Consumer | Role after PR-AJ |
| --- | --- |
| `apply_socially_revealed_leads` | Still lands structured/extracted leads. No longer receives a fabricated ctx payload from reconcile. |
| `apply_social_narration_lead_supplements` | Still runs authorized extraction on final narration. |
| `ensure_scene_has_minimum_actionable_lead` | Still requires an information-bearing social payload. Informational prose no longer unlocks it. |
| Lead registry / clue_knowledge | Unchanged APIs. |
| Intent parser | Still reads `pending_leads` as the pursuit surface. Deferred consumer-alignment. |
| `remember_recent_contextual_leads` / prompt / passive-scene pressure | Still may remember mentioned figures/objects. Not canonical leads. |
| Tests that expected ctx mint from unanchored prose | Updated to the fail-closed contract. |

Legitimate gameplay that still depends on narration **mentioning** an authored landmark (notice board, exit label, `_TEXT_LEAD_SPECS` hook) continues through `extract_actionable_social_leads`.

---

## 8. Existing Lead Provenance Contracts

Documented from the repository, not invented:

| Path | Source authority → structured consequence → identity → projection → narration |
| --- | --- |
| Authored scene follow-up / RC-21 | Scene evidence (notice board, named crier if authored, exit label) → extracted social lead → registry id → pending/clue projection → narration may mention it |
| Authored NPC/topic consequence | `world.npcs[].topics` with `clue_id` / `leads_to_*` → `topic_revealed` → `apply_socially_revealed_leads` → registry / pending → narration |
| Clue discovery | Interactable / discoverable clue → `apply_authoritative_clue_discovery` → registry + clue_knowledge → narration |
| Explicit interaction outcome | Resolution `clue_id` / `discovered_clues` → same landing path |
| Canonical registry insertion | `game.leads` create/upsert |
| Compatibility text-hook | `_TEXT_LEAD_SPECS` / scene-anchor scans on topic or narration text → labeled lead, not a prose slug |

Owners:

- Lead identity: canonical lead registry
- Target/destination: authored `leads_to_scene` / scene exits / scene-anchor extraction
- Availability / discovery: clue + registry lifecycle
- Provenance: `discovery_source` on the registry row
- Player knowledge: clue_knowledge / journal projections
- Pursuit surface: `pending_leads` (compatibility; deferred realignment)

---

## 9. RC-21 Relationship

RC-21 = B + C is settled and was not reopened.

Yes: authored-scene follow-up + canonical lead registry already provide the authoritative path that `narration_ctx_…` was approximating.

PR-AJ therefore narrowed the obsolete authority role of unsourced contextual ingestion. Residual compatibility (`pending_leads` as pursuit, `compat_pending_lead_needed` scene-target keying, `_TEXT_LEAD_SPECS`) is not an open RC-21 policy question.

---

## 10. Authority-Direction Contract

A. Authority may produce narration. Paraphrase is allowed.

B. Narration alone must not produce authority.

C. A social answer is not automatically a lead.

D. Legitimate structured social/follow-up leads still work.

E. Harmless paraphrase must not change mechanics.

F. Mentioning an existing lead must not mint a duplicate prose-derived lead.

G. Fail closed when provenance cannot be established.

---

## 11. Implementation

Generic engine: `game/narration_state_consistency.py`.

When `extract_actionable_social_leads` is empty, reconcile now:

- records the mismatch diagnostically
- sets `mismatch_repair_applied = fail_closed_no_authoritative_provenance`
- does **not** mint `narration_ctx_…`
- does **not** fabricate `topic_revealed` / `clue_id`
- does **not** call `apply_socially_revealed_leads`
- does **not** upgrade reply_kind or success from prose

When extraction finds an authorized lead, the previous structured upgrade remains.

Doctrine note added under lead-store authority in `docs/state_authority_model.md`.

Canonical scene/world content was not modified. `game/social.py` was not modified.

---

## 12. Social-Prose Non-Ingestion

Informational or suggestive social prose with no authorized extraction no longer becomes a canonical lead.

The Captain `"We're maintaining a strict..."` class is covered both by the HTTP calibration test and by the general Salt Harbor fixtures.

---

## 13. Legitimate Structured Lead Preservation

Existing contract: NPC topic with `clue_id` + `leads_to_scene` → `apply_socially_revealed_leads`.

Synthetic Harbor Clerk topic `kelp_shed_key` → `kelp_shed` still lands:

- registry row `kelp_shed_key`
- pending `authoritative_lead_id=kelp_shed_key`, `leads_to_scene=kelp_shed`
- production pursuit helper `_actionable_pending_with_registry_rows` sees it

This is structured authority → lead → narration, not “the sentence sounded like a quest.”

---

## 14. Paraphrase Invariance

Same empty structured outcome, two suggestive wordings: no lead in either.

Same structured `kelp_shed_key`, two wordings: same canonical id, no ctx duplicate.

Same informational tide-mark topic, three wordings: no ctx leads; no extra destination pending.

---

## 15. Duplicate / Projection Analysis

The targeted path no longer becomes:

```text
canonical lead A
+
prose-derived narration_ctx lead B
```

Existing-lead mention HTTP test: first reveal creates `kelp_shed_key`; a later mention does not add a ctx row or a second id.

Broader lead/clue overlap reduction remains deferred. `pending_leads` remains a projection.

---

## 16. Guard Captain Before / After

| Surface | Before | After |
| --- | --- | --- |
| Bound first-ask answer | Legitimate (PR-AI) | Intact. Replay T9: bound `guard_captain`; not `"I don't know."` |
| `narration_ctx_frontier_gate_were_maintaining_a_strict` | Minted from speech | Absent |
| `minlead_exit_…` side-effect from that mint | Created | Absent on the informational answer |
| HTTP calibration with the exact maintaining speech | Would mint ctx | No ctx; answer remains |

Replay T9 used the authored `mutters` / `"Word is,"` envelope rather than the longer live-model sentence. That is known dialogue-envelope residue, not a return of first-ask ignorance.

---

## 17. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is Salt Harbor / kelp shed / trestle / coal loft. Scene `salt_harbor`. NPCs `harbor_clerk`, `net_mender`. Destination `kelp_shed`.

| Test | Result |
| --- | --- |
| 1. Informational social prose | PASS — no ctx / no pending from prose |
| 2. Paraphrased information | PASS — identical empty authority |
| 3. Legitimate structured lead | PASS — `kelp_shed_key` exists and is narrated |
| 4. Structured lead paraphrase | PASS — same id, no extra ctx |
| 5. Existing lead mention | PASS — no duplicate |
| 6. Suggestive non-authoritative prose | PASS — no destination/entity minted |
| 7. No false pursuit surface | PASS — next-turn pending/registry empty; no resolved travel |
| 8. Authorized pursuit surface | PASS — pending helper sees `kelp_shed_key` |
| 9. Provenance survives persistence | PASS — save/load keeps structured lead; prose-only does not reappear |
| 10. No model-wording dependence | PASS — three tide-mark realizations, same mechanics |

HTTP tests exercise `/api/chat` with stubbed GPT.

---

## 18. Anti-Overfitting Audit

Searched PR-AJ generic production changes (`game/narration_state_consistency.py` fail-closed branch; new doctrine paragraph) for:

`guard_captain`, `Captain Thoran`, `frontier_gate`, `Cinderwatch`, `old_milestone`, `patrol`, `watch_command`, `were_maintaining_a_strict`, `narration_ctx_frontier_gate_were_maintaining_a_strict`.

| Surface | Result |
| --- | --- |
| New fail-closed branch | No calibration identifiers |
| Doctrine paragraph | No calibration identifiers |
| Pre-existing `_OPERATIONAL_TOKENS` | Still contains `patrol` / `notice board`. Not introduced here. Used only as a mismatch **probe**, not as a lead id. |
| Phrase suppression | None |
| Captain-only filter | None |
| Prefix-only deletion | No. The authority write is gone, not renamed. |
| Synthetic fixtures | Different nouns and syntax from Frontier Gate |

Calibration identifiers appear only in the allowed Captain HTTP regression test.

---

## 19. Tests Added or Updated

Added: `tests/test_authoritative_lead_provenance_social_prose_non_ingestion.py`

Updated: `tests/test_narration_state_consistency.py`

- `test_explanation_with_directional_hook_not_left_as_empty_payload` now expects fail-closed, not a ctx/clue mint
- `test_named_figure_sets_emergent_actor_hint_flag` keeps the diagnostic hint flag; no longer requires structured information

Extractable authored-hook tests (`old milestone`, `old trading crossroads`, House Verevin spec) still use the extracted-actionable path.

No existing RC-21 or social-lead-landing expectations were weakened.

---

## 20. Continued Multi-Turn Replay

Scenario: `data/validation/praj_authoritative_lead_provenance/scenarios.json` (`R2-MT01-AJ`)

After: `artifacts/praj_authoritative_lead_provenance/extended_replay/runs/20260920T115017Z_R2-MT01-AJ/transcript.md`

| Turn | Player | Result |
| --- | --- | --- |
| T2 | read notice | `notice_patrol_route` |
| T3 | follow northwest track | `frontier_gate` → `old_milestone` |
| T5 | examine milestone | `milestone_mud_prints` |
| T6 | head back | authoritative return; evaluator FAIL on stock leave line is known residue |
| T7 | look around | grounded gate; no invented confrontation |
| T8 | reread board | authored notice |
| T9 | first captain ask | bound `guard_captain`; not ignorance; **no `narration_ctx_…`**; pending empty |
| T10 | check roster board | investigate collapses to observe stock; no invented names this run |
| T11 | look around again | same observe stock repeated |

State after T9:

- canonical leads: `notice_patrol_route`, `milestone_mud_prints`
- pending: `[]`
- narration_ctx: none
- next-turn pursuit from the captain speech: none

---

## 21. Freeform Provenance Probe

Artifact: `artifacts/praj_authoritative_lead_provenance/freeform_probe/20260920T115111Z_probe.md`

| Turn | Player | Result |
| --- | --- | --- |
| 1 | roster / watch-keeper paraphrase | messy mutters + ignorance; **no ctx** |
| 2 | closed western carts (suggestive) | refusal; **no lead** |
| 3 | who commands the watch | Thoran; **no ctx** |
| 4 | paraphrase the commander | Thoran again; **no ctx** |
| 5 | mention Thoran again | no duplicate lead |
| 6 | pursue the prose-only western road | `travel` but `resolved_transition=False`, no target; **no dest minted**; scene stayed `frontier_gate` |
| 7 | look around | still at the gate |
| 8 | read notice | legitimate `notice_patrol_route` |
| 9 | follow that rumor | legitimate travel to `old_milestone` |

T6 narration still described walking west while state did not move. That is residual State ↔ Narration on unresolved travel, not lead ingestion. Not absorbed.

---

## 22. Validation Results

| Gate | Result |
| --- | --- |
| New PR-AJ tests | Pass (13) |
| Scenario-independent fixtures | Pass |
| Existing narration-consistency | Pass |
| Existing lead-registry / clue / social-lead / RC-21 redirect | Pass |
| Existing pursuit / start-campaign | Pass |
| Existing state-authority / narrative-authority | Pass |
| Mixed-state recovery | Pass |
| PR-AD authored knowledge | Pass |
| PR-AE stay/leave | Pass |
| PR-AF arrival | Pass |
| PR-AG generalized exit | Pass |
| PR-AH grounded observation | Pass |
| PR-AI bound speaker | Pass |
| Round #1 calibration | 13/13 (`artifacts/praj_authoritative_lead_provenance/round1_calibration/`) |
| Extended R2-MT01-AJ replay | Captain answer intact; no ctx; continuation taken |
| Freeform provenance probe | Diagnostic; Thoran and notice/follow paths hold; prose-only road does not become a dest |
| Full authoritative suite | Not re-run as a complete 6,450-test pass |

Structural PASS is not semantic playability. Known protected-replay / mutation-attribution reds were not refreshed.

---

## 23. Remaining Semantic Failures

- Roster-board investigate still collapses to generic observe stock (T10). Previously this class also invented names.
- Local observe can repeat the same stock line (T11 / probe T7).
- Authored `mutters` / `"Word is,"` envelope remains; T9 answer was thinner than the earlier live-model sentence.
- Follow-up paraphrases that miss owned topic / landed clue can still refuse (probe T1).
- Unresolved travel can still be narrated as departure (probe T6).
- Evaluator FAIL on stock leave / some observe lines remains.
- T1 observe can still voice an NPC topic through the mutters envelope.

---

## 24. Deferred Findings

Unchanged unless noted:

- Absent-speaker `"The guard says"` default label.
- `compat_pending_lead_needed` still keys off a scene target only.
- Intent parsing still reads `pending_leads` as the pursuit surface.
- Broader lead/clue overlap reduction.
- `_TEXT_LEAD_SPECS` remains a compatibility text-hook library. Not the ctx fallback. Not absorbed.
- House Verevin / rooftop invention.
- Filling other stub scenes.
- New authoritative knowledge store.
- Project-wide State ↔ Narration.
- Protected-replay baseline refresh.
- General prompt rewrite or NPC personality redesign.

---

## 25. Recommended Next Product Slice

**Mentioned-but-unstubbed surface realization, starting with the roster board / repeated observe-stock collapse.**

Chosen from ordinary-play evidence after the repaired captain exchange. T10 tried to inspect the serjeant's roster and received the same generic gate-line stock as T11's “look around.” That is now the dominant playability break. It is not a leftover `narration_ctx_…` problem.

Do not start a general State ↔ Narration campaign because probe T6 narrated an unresolved walk. Do not reopen PR-AI speaker/topic ownership or PR-AJ provenance.

---

## 26. Git / Worktree State

The worktree was dirty before PR-AJ and remains dirty.

PR-AJ production files:

- `game/narration_state_consistency.py` (fail-closed contextual fallback; file also carried pre-existing PR-AE/AF helpers)
- `docs/state_authority_model.md` (lead-store paragraph; file also carried pre-existing dirt)

PR-AJ tests / report / handoff / artifacts:

- `tests/test_authoritative_lead_provenance_social_prose_non_ingestion.py` (new)
- `tests/test_narration_state_consistency.py` (updated)
- `tools/run_praj_freeform_probe.py` (new)
- `data/validation/praj_authoritative_lead_provenance/` (new)
- `PR-AJ_authoritative_lead_provenance_social_prose_non_ingestion.md` (new)
- `docs/NEXT_SESSION.md` (updated)
- `artifacts/praj_authoritative_lead_provenance/` (new)

Canonical scene JSON was not modified.

Replay and the freeform probe reset local runtime documents (`data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`).

Pre-existing dirt from earlier validation, policy, replay, and PR-AC through PR-AI was not erased.

No commit or push.

---

## 27. Confidence

**Medium-high** on the targeted failure class.

High that the first prose-to-authority promotion was the contextual `narration_ctx_…` mint, that RC-21 already owned official follow-up, and that fail-closed plus the Salt Harbor HTTP fixtures prove the general contract. High that structured `leads_to_*` landing and notice-board RC-21 tests remain green. Medium that every compatibility text-hook in `_TEXT_LEAD_SPECS` is the long-term right remaining extraction surface — it was left in place because it is not the targeted ctx fallback and is used by existing authorized-hook tests. Medium that the next-slice recommendation will remain correct after more play — roster/observe-stock collapse is the strongest new ordinary-play contaminant after the repaired captain turn.
