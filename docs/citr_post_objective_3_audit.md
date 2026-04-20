# CITR audit — post Objective #3 (Unified State Authority)

**Scope:** Static audit of narration, clues, journal publication, allow-listed interaction → scene writes, and the GM post-update seam (`game.api._apply_post_gm_updates` and neighbors). **Not** a redesign of GM trust, global guard expansion, or architecture.

**Verdict (summary):** Objective #3’s **guarded domain seams** (journal publication, interaction_context allow-list, API-orchestrated owner checks on scene/world mutation) are **aligned with CITR** as documented. Several **pre-existing product seams** still carry CITR tension: GM-proposed scene/world patches, bounded **narration→resolution repair** that promotes text hooks into structured lead/clue state, and **infrastructure for hidden-fact journal reveals** without a live engine caller for `mark_hidden_fact_revealed`. These are classified below; none negate Objective #3’s stated goal of **representative** guard adoption.

---

## 1. Hidden → player-visible publication (journal)

### Confirmed safe

- **Derived journal only:** `build_player_journal` composes a snapshot; module docstring states it must not back-write `hidden_state` or `world_state`.
- **Allow-listed cross-domain merge:** When runtime reveals are present, `merge_player_journal_known_facts_publication` calls `assert_cross_domain_write_allowed(..., operation="journal_merge_revealed_hidden_facts")` and `assert_owner_can_mutate_domain(..., PLAYER_VISIBLE_STATE, ...)`, and optional mutation traces are appended.

```273:327:game/journal.py
def merge_player_journal_known_facts_publication(
    bootstrap: List[str],
    revealed_hidden_runtime: List[str],
) -> List[str]:
    """Publication seam: merge ``scene_runtime.revealed_hidden_facts`` into journal ``known_facts``.
    ...
    """
    rev = [x for x in revealed_hidden_runtime if isinstance(x, str) and x.strip()]
    if rev:
        assert_cross_domain_write_allowed(
            HIDDEN_STATE,
            PLAYER_VISIBLE_STATE,
            operation="journal_merge_revealed_hidden_facts",
        )
    assert_owner_can_mutate_domain(__name__, PLAYER_VISIBLE_STATE, operation="journal_known_facts_merge")
    return _merge_known_fact_lines(bootstrap, rev)
```

- **No journal back-write:** No code path in `game/journal.py` mutates `session['scene_runtime']`, scene templates, or `world` for merges.

### Risky / needs tightening

- **`known_facts` bootstrap is not “hidden-only”:** `_journal_bootstrap_known_facts` uses `journal_seed_facts` or a capped prefix of **`visible_facts`**, which are scene-facing lines (and can be extended by GM `scene_update`; see §5). So the **full** `known_facts` list is **not** exclusively “earned hidden reveals”; only the **post-bootstrap merge slice** is tied to `revealed_hidden_facts`.

- **Provenance of `revealed_hidden_facts`:** The intended writer is `mark_hidden_fact_revealed` in `game.storage`, which performs no membership check against `scene['hidden_facts']`.

```496:499:game/storage.py
def mark_hidden_fact_revealed(session: Dict[str, Any], scene_id: str, hidden_text: str) -> bool:
    """Mark a hidden fact as explicitly revealed; return True only if newly added."""
    rt = get_scene_runtime(session, scene_id)
    return _add_unique_to_list(rt['revealed_hidden_facts'], hidden_text)
```

- **Observation:** Repository-wide search shows **no production caller** of `mark_hidden_fact_revealed` outside `game/storage.py` itself (only tests import it). So the **guarded journal merge seam is real**, but the **authoritative hidden→runtime reveal seam is not exercised** by current engine paths—journal “earned” lines will stay empty unless another mechanism populates `revealed_hidden_facts` (e.g. persistence hand-edits). **Classification:** **future objective (not blocking Objective #3)** — wire reveal from deterministic resolution when hidden text is actually published, with optional template membership check and `reveal_hidden_fact_runtime` guard at the mutation site.

### Player-visible → hidden/world back-write

- **Not observed** in `game/journal.py` or `build_player_journal` consumers for journal construction in `compose_state` paths reviewed.

---

## 2. Narration → state alignment

### Confirmed safe

- **Turn order (CTIR documented):** `_run_resolved_turn_pipeline` applies `_apply_authoritative_resolution_state_mutation` **before** building GPT narration from post-mutation state.

```1530:1533:game/api.py
    """Shared resolved-turn flow for both `/api/action` and `/api/chat`.

    Stage 5: authoritative engine mutation is applied first.
    Stage 6-7: prompt context and GPT narration are built only from that post-resolution state.
```

- **Final emission + narrative authority:** Strict-social paths use `apply_final_emission_gate`; `game/narrative_authority.py` and `game/narration_visibility.py` support **forbidding invented hidden facts** in player-facing text relative to visibility contracts (enforcement lives in the emission stack, not in state_authority guards alone).

- **Sanitization:** Non–strict-social paths run `sanitize_player_facing_output` before the emission gate (`game/api_turn_support.py`).

### Risky / needs tightening (explicit CITR tradeoff)

- **`reconcile_final_text_with_structured_state` (`game/narration_state_consistency.py`):** When a social resolution claims **no information** but finalized narration shows **investigative hooks**, the engine **mutates `resolution`** (adds `discovered_clues`, synthetic/`extracted` clue ids, `topic_revealed`, may set `success` True) and calls **`apply_socially_revealed_leads`** so session/world lead state **matches** narration. This is **engine-authored** repair, not raw GPT JSON, but it **does derive structured “facts” from narration text** under narrow predicates.

- **`apply_social_narration_lead_supplements` (`game/clues.py`):** After final player-facing text exists, social turns can run a **second-pass** extraction (`extraction_pass="narration"`) into `_apply_extracted_social_leads`. Again: bounded, idempotent, but **narration-shaped**.

**Classification:** **needs tightening** *if* product CITR is defined as “zero structured state may ever be inferred from player-facing text.” Under the repo’s existing **anti-drift / consistency** posture (documented CTIR comments in `game/api.py`), this is **consistent** with shipped behavior—treat as **documented tension**, not an Objective #3 regression.

### Minimal fix ideas (not implemented)

- **A (narrow):** Add a single policy flag (session or campaign) to disable `reconcile_final_text_with_structured_state` and/or `apply_social_narration_lead_supplements` for strict playtests; default remains current behavior.

- **B (narrow):** Tighten `_text_indicates_new_information` / extraction eligibility so fewer narration phrases trigger repair (reduce false promotion) without removing the seam.

---

## 3. Clue integrity

### Confirmed safe

- **Single authoritative mutation gateway** for discovery lists: `apply_authoritative_clue_discovery` documents that GPT narration detection must not call it; resolution paths use `_apply_authoritative_clues_from_resolution` → that gateway.

```622:635:game/clues.py
def apply_authoritative_clue_discovery(
    session: Dict[str, Any],
    scene_id: str,
    *,
    clue_id: str | None = None,
    clue_text: str | None = None,
    discovered_clues: List[str] | None = None,
    world: Dict[str, Any] | None = None,
    structured_clue: Dict[str, Any] | None = None,
) -> List[str]:
    """Single authoritative clue mutation gateway.

    This is the only engine-owned path that should mutate clue discovery state.
    GPT narration text detection can still exist for telemetry, but must not call this.
```

- **Surfaced-clue scan is telemetry-only:** `_apply_post_gm_updates` calls `detect_surfaced_clues` on `player_facing_text` and collects `surfaced_in_text` **without** passing through `apply_authoritative_clue_discovery`.

```527:531:game/api.py
    surfaced_in_text: list = []
    if isinstance(gm.get('player_facing_text'), str):
        from game.gm import detect_surfaced_clues  # local import to avoid cycles
        for clue_text in detect_surfaced_clues(gm['player_facing_text'], scene):
            surfaced_in_text.append(clue_text)
```

- **Journal `discovered_clues`:** Built from `get_all_known_clue_texts(session)` (clue knowledge layer), not from narration string parsing in `journal.py`.

### Risky / needs tightening

- **Narration repair & supplements (§2)** can change clue/lead **presentation** and registry via **`apply_socially_revealed_leads` / `_apply_extracted_social_leads`** after the main resolution mutation—still **engine-governed**, but not exclusively “resolution JSON at stage 5.”

- **Registry vs allow-list documentation drift:** `game/state_authority.py` lists `reveal_clue_runtime`, `reveal_hidden_fact_runtime`, and `merge_pending_lead_runtime` under **HIDDEN_STATE → SCENE_STATE**, but repository search shows **no** `assert_cross_domain_write_allowed(..., operation="reveal_clue_runtime")` (or the sibling ops) at clue/runtime mutation sites. **Classification:** **future objective** — align either call sites with the registry names or narrow the documented allow-list to match wired guards (no behavior change required for this audit).

---

## 4. Interaction → scene cross-domain writes

### Confirmed safe

- **Allow-listed operations** (`interlocutor_binding`, `exchange_interruption_tracker_slot`, etc.) are invoked with `assert_cross_domain_write_allowed` from `game/interaction_context.py` (e.g. `set_social_target`, `set_social_exchange_interruption_tracker`, `clear_for_scene_change`, `synchronize_scene_addressability` when mirroring `current_interlocutor`).

```1103:1121:game/interaction_context.py
def set_social_target(session: Dict[str, Any], target_id: Optional[str]) -> Dict[str, Any]:
    """Set or clear the active social target; marks interaction kind as social."""
    assert_owner_can_mutate_domain(__name__, INTERACTION_STATE, operation="set_social_target")
    assert_cross_domain_write_allowed(
        INTERACTION_STATE,
        SCENE_STATE,
        operation="interlocutor_binding",
    )
    ...
    st = _scene_state(session)
    ...
    st["current_interlocutor"] = tid if tid else None
```

- **`synchronize_scene_addressability`:** Uses `assert_owner_can_mutate_domain` for `SCENE_STATE` and guarded cross-domain write when setting `current_interlocutor` from a validated target universe—reduces **stale interlocutor drift** rather than introducing unconstrained new truth.

### Risky / needs tightening

- **`apply_conservative_emergent_enrollment_from_gm_output`** (`game/interaction_context.py`), invoked from `_apply_post_gm_updates`, can enroll **scene_state** emergent addressables from **final GM narration text** using a **conservative** hint table. This is intentional roster hygiene but is **narration-sourced scene addressability** (not world truth). **Classification:** **needs tightening** only if emergent figures must never affect addressability; otherwise **safe under current conservative design**.

---

## 5. GM update seam (`game.api._apply_post_gm_updates`)

### Confirmed safe

- **Scene transitions from GPT are advisory:** `new_scene_draft` / `activate_scene_id` are ignored here; debug notes record `advisory_only:...`.

- **Owner checks present:** `scene_update` branch asserts `SCENE_STATE` owner for `apply_gm_scene_update_layers`; `world_updates` asserts `WORLD_STATE` for `apply_gm_world_updates`.

- **Policy layer upstream:** `validate_gm_state_update` (e.g. blocks exact promotion of `hidden_facts` strings into `visible_facts_add`) runs inside `apply_response_policy_enforcement` when `forbid_state_invention` is enabled—**before** the GM payload is heavily consumed in the resolved pipeline’s GPT build path (`game/gm.py`).

### Risky / needs tightening

- **`_apply_post_gm_updates` does not re-validate** the GM dict: it applies `gm['scene_update']` / `gm['world_updates']` **as given** at this seam. If any code path produced a GM dict **without** `apply_response_policy_enforcement`, this would be a **defense-in-depth gap**. **Minimal fix (not implemented):** call `validate_gm_state_update(gm, session, scene)` at the top of `_apply_post_gm_updates` (or assert a marker that policy enforcement ran).

- **Ordering vs narration:** `_finalize_player_facing_for_turn` runs **before** `_apply_post_gm_updates` (`game/api.py` action/chat completion paths). `scene_update` can therefore change `visible_facts` / `discoverable_clues` / `hidden_facts` **after** narration was aligned to the pre-update scene envelope—potential **same-turn template drift** between emitted text and persisted scene. **Classification:** **needs tightening** for strict same-turn coherence; **future objective** if rare.

---

## 6. Objective #3 vs CITR — overall classification

| Area | Classification |
|------|----------------|
| Journal publication seam (merge + guards, no back-write) | **safe** |
| `build_player_journal` bootstrap from `visible_facts` / seeds | **safe** under “curated player knowledge” model; **needs tightening** if “every journal line must trace to hidden reveal” |
| Runtime `revealed_hidden_facts` population | **future objective** — API exists; no engine caller located |
| Authoritative resolution → clue discovery gateway | **safe** |
| `detect_surfaced_clues` telemetry | **safe** |
| Narration consistency repair + narration lead supplements | **needs tightening** vs strict “no text-derived state” CITR; **safe** under shipped anti-drift policy |
| Interaction allow-listed scene writes | **safe** |
| Emergent enrollment from narration | **needs tightening** / product discretion |
| `_apply_post_gm_updates` | **needs tightening** (re-validate; optional ordering review) |
| Registry ops `reveal_*_runtime` without matching guards at clue/hidden writers | **future objective** (documentation / guard alignment) |

### Explicit statement

**Objective #3 remains CITR-compatible under its documented scope:** guards are correctly placed at **representative** publication and orchestration seams; GPT output is still not treated as an unguarded mutator of registry domains. **Strict** interpretations of “no narration-created facts,” “all journal lines from hidden_state,” or “no GM-shaped scene patches after narration” are **not fully satisfied** by the broader product seams above—those gaps are **mostly pre-existing** or **intentional reconciliation**, not regressions introduced by the unified authority model itself.

---

## 7. Minimal fix proposals (not implemented)

Each targets one seam; avoids global guard expansion.

1. **Hidden reveal → runtime:** From the deterministic resolution path that truly publishes a hidden template line, call `mark_hidden_fact_revealed` only after verifying the string is in `scene['hidden_facts']` (normalized), then optionally `assert_cross_domain_write_allowed(HIDDEN_STATE, SCENE_STATE, operation="reveal_hidden_fact_runtime")` at that single new caller.

2. **GM post-update hardening:** At the start of `_apply_post_gm_updates`, run `validate_gm_state_update` on a shallow copy of `gm` and merge cleaned `scene_update` / `world_updates` back (or no-op if invalid).

3. **Same-turn scene drift:** Move `scene_update` application **before** final narration build, **or** re-run a narrow visibility/narration check after `scene_update` (larger change—flag as **future objective** if chosen).

4. **Allow-list truth:** Either add `assert_cross_domain_write_allowed` to `mark_clue_discovered` / related storage helpers with `reveal_clue_runtime`, or trim the documented operations in `docs/state_authority_model.md` / registry to match reality.

5. **Strict CITR mode:** Feature-flag `reconcile_final_text_with_structured_state` and `apply_social_narration_lead_supplements` for audit builds only.

---

## 8. Tests run

- `py -3 -m pytest tests/test_state_authority.py tests/test_validation_journal_affordances.py -q` — **pass** (local environment).

---

## References

- `docs/state_authority_model.md` — domain definitions, allow-list, Objective #3 adoption table.
- `game/state_authority.py` — registry and guard primitives.
- `game/journal.py`, `game/api.py`, `game/api_turn_support.py`, `game/narration_state_consistency.py`, `game/clues.py`, `game/interaction_context.py`, `game/storage.py`, `game/gm.py` — cited above.
