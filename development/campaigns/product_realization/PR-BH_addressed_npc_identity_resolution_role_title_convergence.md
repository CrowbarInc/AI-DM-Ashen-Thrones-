# PR-BH — AI Experience / Gameplay: Addressed-NPC Identity Resolution and Role-Title Convergence

Date: 2026-09-22
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Probe artifacts: `artifacts/prbh_addressed_npc_identity/isolation/`

---

## 1. Executive Summary

`"Gate Serjeant" -> gate_guard` is **not** an authored alias. It is a genuine identity-resolution defect.

The recovered PR-AI utterance:

```text
I turn to the Gate Serjeant. "Did the census choke change the route?"
```

addressed an authored `gate_serjeant` NPC who owns `route_change`. Directed-prep matching bound `gate_guard` because the short token `gate` appears in `to the Gate Serjeant`. The first roster hit won. Downstream social resolution then treated the guard as the speaker and could voice `watch_command`.

The same first incorrect decision is general:

* leftover identity words were not required to belong to the selected NPC;
* unsupported explicit addressees could then fall through to sole-NPC information-seeking bind;
* vocative `captain` was hardcoded as a synonym of `guard`.

The repair stays inside existing addressed-NPC resolution. It does not add rank synonym lists, embeddings, an LLM entity resolver, invented NPCs, or a second router.

Addressed-NPC identity resolution is now sufficiently converged for Product Realization. Do not open another NPC-name/title paraphrase cycle.

---

## 2. Recovered Failure

Source: `artifacts/prai_bound_speaker_knowledge/freeform_probe/20260920T112834Z_probe.md` Turn 12.

| Stage | Result |
| --- | --- |
| Player utterance | `I turn to the Gate Serjeant. "Did the census choke change the route?"` |
| Scene | `frontier_gate` |
| Present/addressable NPCs (PR-AI / golden-replay fixture) | world: `gate_guard`, `gate_serjeant`, `tavern_runner`; scene addressables: `guard_captain`, `tavern_runner`, `refugee`, `threadbare_watcher` |
| Extracted addressee | declared-switch phrase `the gate serjeant` |
| Candidate evidence | `gate_guard` matches `gate`; `gate_serjeant` matches `gate` and `gate serjeant` |
| Fallback | first roster directed-prep hit, not sole-NPC |
| Selected NPC | `gate_guard` |
| Social action | `kind=question`; interlocutor `gate_guard` |
| Final response | `Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."` |
| Authored topic that should have been eligible | `gate_serjeant.route_change` |

Before-repair isolation: `artifacts/prbh_addressed_npc_identity/isolation/20260922T110000Z_before.md`

Current persisted `data/world.json` contains only `tavern_runner`. On that roster the recovered line already fail-closes. The defect reproduces on the authored fixture roster that tests and the PR-AI probe still use. Scene flavor still mentions a gate serjeant; that prose is not an alias of `gate_guard`.

---

## 3. Authored NPC Identity Data

### Current persisted world

| Field | `tavern_runner` |
| --- | --- |
| Canonical ID | `tavern_runner` |
| Player-facing name | `Tavern Runner` |
| Role / aliases | empty |

No `gate_guard` or `gate_serjeant` row.

### PR-AI / golden-replay fixture (`tests/helpers/golden_replay_fixtures.py`)

| Field | `gate_guard` | `gate_serjeant` |
| --- | --- | --- |
| Canonical ID | `gate_guard` | `gate_serjeant` |
| Player-facing name | `Gate Guard` | `Gate Serjeant` |
| Role | `guard` | none |
| Aliases | `guard`, `watch`, `watch guard` | `serjeant`, `watch serjeant`, `gate serjeant` |
| Topics | `watch_command` | `route_change` |

### Frontier Gate scene addressables (`data/scenes/frontier_gate.json`)

`guard_captain` / Guard Captain with `address_roles` including `guard` and `captain`. No `gate_serjeant` addressable. Visible fact: `"A gate serjeant manages the crowd..."` is scene prose, not identity metadata.

**Is "Gate Serjeant" an authored identity for `gate_guard`?**

**No.**

A guard being able to be a serjeant is not data authority. The fixture authors a distinct `gate_serjeant` with its own name, aliases, and topic.

---

## 4. Addressed-NPC Resolution Order

Owner: `game/interaction_context.py`.

| Rank | Mechanism | Authority |
| --- | --- | --- |
| A | Exact canonical ID slug | Authoritative |
| B | Exact authored name | Authoritative |
| C | Exact authored alias | Authoritative |
| D | Exact `address_roles` / ordinary generic role (`guard`, `runner`, `watchman`) | Authoritative when unique or priority-unique |
| E | Title tokens listed in `_NPC_REFERENCE_TITLES` if present in the name | Authoritative surface, not a rank ontology |
| F | Directed-prep / leading phrase with leftover-token ownership | Authoritative after repair |
| G | Normalized token overlap / first short-token hit | Heuristic; no longer sufficient alone |
| H | Sole-present-NPC + information-seeking / hailing | Intended only when no explicit addressee was supplied |
| I | Active-interlocutor pronoun continuity | Conversational; must not override an unresolved explicit name |
| J | Spoken comma vocative / declared-action switch | Authoritative when the extracted phrase resolves |

Before repair, G ran as first-roster-wins inside `_explicit_addressed_npc_id_leading_or_directed` and the trailing substring loop of `_resolve_social_address_phrase_to_roster_id`. That outranked B/C for `to the Gate Serjeant`.

---

## 5. First Incorrect Decision

**Prefix-token directed-prep bind, then cooperating sole-NPC substitution.**

1. Declared switch extracts `the gate serjeant`.
2. `_explicit_addressed_npc_id_leading_or_directed` / `extract_npc_reference_tokens` treat `gate` from `gate_guard` as enough for `to the gate …`.
3. Roster order returns `gate_guard` before the longer exact match `gate serjeant`.
4. If that prefix bind is later refused, sole-NPC information-seeking in `find_addressed_npc_id_for_turn` could still attach the only present NPC.
5. `_VOCATIVE_TOKEN_TO_GENERIC_ROLE["captain"] = "guard"` was a separate rank synonym on the same identity owner.

Not a missing serjeant NPC in content. Not speaker-label quality. Not PR-AZ observe steal.

---

## 6. Compact Identity Matrix

Authoritative fixture unless labeled sole/kiln. After-repair: `artifacts/prbh_addressed_npc_identity/isolation/20260922T120000Z_after.md`.

| Class | Example | Before | After |
| --- | --- | --- | --- |
| Recovered declared switch | `I turn to the Gate Serjeant. "Did the census…"` | `gate_guard` | `gate_serjeant` |
| Canonical name | `I turn to the Gate Guard.` | `gate_guard` | unchanged |
| Ordinary role | `Guard, what happened?` (only guard present) | `gate_guard` | unchanged |
| Authored alias | `Serjeant,` / `I turn to the serjeant.` | `gate_serjeant` | unchanged |
| Authored full alias | `I turn to the gate serjeant.` | `gate_guard` | `gate_serjeant` |
| Supported vocative | `Gate Serjeant,` / `Captain,` with captain present | serjeant / captain | unchanged |
| Unsupported rank | `Captain,` with only `gate_guard` | `gate_guard` | unbound |
| Unsupported title | `I turn to the Commander.` | prefix/continuity steal | unbound |
| Unknown name | `Lord Aldric,` | sole-NPC / continuity | unbound |
| Sole-NPC unsupported | recovered serjeant / `Foreman,` / `Clerk` | sole present NPC | unbound |
| Sole-NPC undirected | `What happened here?` | sole NPC | unchanged |
| Sole-NPC supported | `Gate Guard,` / `Porter,` | bind | unchanged |
| Multiple-NPC contrast | `I turn to the Guard Captain.` vs `Gate Guard` | find_addressed could steal via `guard`/`gate` | each exact identity |
| Kiln generalization | `Night Porter,` / `Porter,` vs `Foreman,` / `Clerk` | unsupported bound porter | unsupported unbound |
| No invented NPC | unauthored names | no new row | unchanged |
| Directed social | vocative / `ask X` | remains directed when resolved | unchanged |
| Undirected social | `What happened here?` with one NPC | still may bind | unchanged |

---

## 7. Explicit vs Undirected

`What happened here?` and `Where did the missing patrol go?` remain undirected information-seeking. Sole-NPC bind is still allowed.

`Serjeant, what happened here?` and `I turn to the Clerk.` contain explicit identity evidence. If that evidence cannot be authorized, the system now leaves the addressee unresolved instead of substituting the person who happens to be present.

---

## 8. Sole-NPC Fallback Findings

Intended meaning, preserved:

```text
No explicit addressee was supplied, but only one conversational partner is available.
```

Previously also implemented:

```text
An explicit addressee was supplied but could not be resolved, so use the only NPC anyway.
```

That second meaning was the general defect for unknown vocatives and leftover titles in sole-NPC scenes. It is no longer used.

Hailing (`hey you`, `excuse me`) is unchanged.

---

## 9. Downstream Identity Implications

Selected NPC ID is consumed by:

* `resolve_authoritative_social_target` / dialogue-lock `target_id`
* `resolve_social_action` speaker and topic reveal
* `authoritative_knowledge_npc_ids_for_speaker`
* relationship / social-state attachment
* speaker label and memory attribution

Diagnostic only. Those owners were not redesigned.

After repair, the recovered line binds `gate_serjeant` and knowledge ids are `['gate_serjeant']`, not `gate_guard`. Wrong-NPC `watch_command` attribution no longer follows this addressing path.

`"The guard says"` generic labeling remains a separate speaker-render residue.

---

## 10. Repair-Threshold Decision

Repair **was** warranted.

* Incorrect substitution reproduced on the authored fixture.
* Explicit addressee evidence was lost (`serjeant` discarded; `gate` kept).
* Multiple natural cases shared one first decision: recovered wording, `I turn to the gate serjeant`, `I turn to the Guard Captain` find_addressed steal, sole-NPC `Captain`/`Foreman`/`Clerk`/`Aldric`.
* Existing authored identity fields were enough to resolve or reject them.
* The repair is deterministic and preserves legitimate aliases, titles, and roles.

Not repaired by inventing a serjeant in `data/world.json`, hardcoding the recovered string, or adding a rank dictionary.

---

## 11. Production Changes

All in `game/interaction_context.py`:

1. `_best_roster_id_for_address_phrase` — exact id/name/alias/role first; otherwise require the phrase's identity tokens to be a subset of the NPC's authored tokens; longest unique match; priority only to break a remaining tie.
2. `_explicit_addressed_npc_id_leading_or_directed` uses the last non-pronoun directed phrase, not the first `at him`.
3. `_resolve_social_address_phrase_to_roster_id` asks that owner before first-token / unconstrained substring steal.
4. `find_world_npc_reference_id_in_text` uses the same leftover rule for directed phrases.
5. Sole-NPC information-seeking bind is skipped when an explicit addressee phrase is present and unresolved.
6. Vocative map no longer treats `captain` as `guard`. `watchman` / `guardsman` / `sentry` remain ordinary guard-role synonyms.

`tests/test_directed_social_routing.py`: `Well, Captain,` on a guard-only roster was expecting the old rank collapse. It now uses `Well, Guard,` so the vocative-override contract is preserved with a legitimate identity.

No Frontier Gate hardcode. No invented NPC metadata. No second router.

---

## 12. Generalization Evidence

The invariant is `unresolved explicit addressee != arbitrary present NPC`, not `"Gate Serjeant" != gate_guard`.

Demonstrated beyond the recovered wording:

* legitimate exact identity: `Gate Guard`, `Night Porter`, `Guard Captain`
* legitimate alias/title: `serjeant`, `porter`, `Captain` when `guard_captain` authors it
* unsupported explicit identity in a sole-NPC scene: `Gate Serjeant` with only `gate_guard`; `Foreman` / `Clerk` with only `night_porter`
* unrelated unsupported identity: `Lord Aldric`, `Commander`
* multiple-NPC contrast: `Gate Guard` vs `Guard Captain`; `Serjeant` does not pick either when unauthored

---

## 13. Preserved Legitimate Addressing

* Exact names and canonical IDs
* Authored aliases (`serjeant`, `gate serjeant`, `porter`, `ragged stranger`)
* Ordinary role addressing (`guard`, `runner`) where unique or priority-unique
* Undirected sole-NPC questions and hailing
* PR-AZ: `"What's nearby?"` still does not sole-NPC-bind; `"Where did the missing patrol go?"` still may
* PR-BC: directed vocative / `ask X` remain social
* PR-BG: follow-up continuity owner untouched

---

## 14. Validation

| Suite | Result |
| --- | --- |
| New PR-BH tests (`tests/test_addressed_npc_identity_resolution_role_title.py`) | 11 passed |
| After-repair isolation | recovered line binds `gate_serjeant`; sole-NPC unsupported unbound; kiln Foreman/Clerk unbound |
| Directed social routing | passed after `Well, Guard,` contract correction |
| Dialogue establishment | 8 passed; 1 pre-existing red (`I look back at him, then to the guard`) blocked by world-action `look back at`, not this owner. `find_addressed` on that line is `gate_guard` |
| PR-AZ question-form observe | passed |
| PR-AY / PR-BB local observation | passed |
| PR-BA place-existence | passed |
| PR-BC agent-history | passed |
| PR-BG follow-up continuity | passed |
| PR-BD interactable aliases | passed |
| PR-AI bound-speaker knowledge | passed |
| Social target authority | passed |
| Emergent scene actors | passed |
| BX5 speaker identity | passed |
| Social-exchange emission | one documented unrelated social-pressure red (`test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere`) |

Requested cycle coverage:

1. Recovered `"Gate Serjeant"` — now `gate_serjeant` on the authored fixture; fail-closed on current persisted world
2. Canonical `gate_guard` — binds
3. Ordinary guard-role — binds when authority is clear
4. Authored alias/title — `serjeant`, `porter`, `Captain` with captain present
5. Unsupported rank/title — `Captain` with only a guard; `Commander`; `Foreman` unbound
6. Unrelated unknown name — `Lord Aldric` unbound
7. Unsupported explicit + one NPC — unbound
8. Undirected + one NPC — still binds
9. Supported explicit + one NPC — binds
10. Multiple-NPC contrast — exact identities distinguished
11. No invented NPC
12. No invented title/rank metadata
13. No wrong-NPC knowledge attribution on the recovered path
14. Directed social remains directed when resolved
15. Undirected social unchanged
16. PR-BC vocative / ask-X preserved
17. PR-AZ sole-NPC observe protections preserved
18. PR-BG continuity suite preserved
19. Relevant social-routing tests preserved except the rank-collapse wording correction
20. Relevant addressability tests preserved

Do not treat structural PASS as live-model playability. Full 6,450-test suite was not re-run.

---

## 15. Explicit Convergence Assessment

### A. Is `"Gate Serjeant" -> gate_guard` authoritatively correct?

**No.**

### B. What data defines player-addressable NPC identity?

`world.npcs[].id` / `name` / `aliases` / `role`, merged with scene `addressables[]` `name` / `aliases` / `address_roles`. Consumed by `canonical_scene_addressable_roster` and `_best_roster_id_for_address_phrase`. Scene prose is not identity authority.

### C. Does unsupported explicit addressing silently fall back to another NPC?

**No** after repair. **Yes** before repair, via prefix-token bind and/or sole-NPC information-seeking.

### D. What was the first incorrect decision?

Directed-prep / first-roster short-token match (`gate` inside `to the Gate Serjeant`) without requiring leftover identity words to be authored for that NPC.

### E. Was production code changed?

**Yes.**

### F. If changed, what general identity invariant was repaired?

An explicit addressee binds only when authored identity tokens cover that phrase. An unresolved explicit addressee is not the sole present NPC.

### G. What legitimate addressing behavior was preserved?

Exact names, authored aliases/titles, ordinary unique roles, undirected sole-NPC questions, hailing, and declared-switch / vocative routing for resolvable identities.

### H. Is addressed-NPC identity resolution sufficiently converged?

**YES** — explicit identities and fallback boundaries are adequate for Product Realization.

**DEFER** richer entity resolution that would need semantic similarity, embeddings, an LLM identity inference, or a rank/title ontology. Do not approximate those with more synonym heuristics.

---

## 16. Accepted / Deferred Residue

Accepted on this owner:

* Current persisted `data/world.json` not containing `gate_guard` / `gate_serjeant`. That is content state, not a resolver defect. This cycle did not invent those rows.
* Scene flavor mentioning a gate serjeant without a matching persisted world NPC. Prose is not identity authority.
* Ambiguous bare `guard` among multiple guard-role NPCs still uses `address_priority` (Frontier Gate prefers `guard_captain`).
* `test_generic_to_the_guard_redirects_from_prior_stranger_target` still fails at establishment because `_line_blocks_dialogue_addressing` treats `I look back at` as a world-action blocker. Addressing itself now resolves `to the guard`. Out of scope.

Sibling residue, do not absorb:

* Opening `Gate Guard mutters` / `"Word is,"`
* Evaluator lexical false negatives on quiet listen and nothing-new
* `"The guard says"` generic absent-speaker label
* Richer follow-up discourse
* Wait / time-passage
* Unresolved travel (closed on its owner)
* Interactable aliases (closed)
* Agent-history residue (closed)
* Observation passive residue
* Compound-intent execution
* Unrelated social-pressure reds

Do not reopen PR-BG through PR-AI settled owners unless new causal evidence appears.

---

## 17. Recommended Next Action

Addressed-NPC identity resolution is closed enough for Product Realization.

Do not select another Gate Serjeant / rank-title paraphrase as the next cycle. Do not start embeddings, an LLM identity inferencer, or a rank ontology.

If the next slice stays in AI Experience, pick a **different** remaining sibling owner. Candidates of that kind, none automatically selected:

* Replay / opening `Gate Guard mutters` / `"Word is,"` (do not reopen PR-AI without new causal evidence)
* Evaluator lexical false negatives on quiet listen and nothing-new
* `"The guard says"` generic absent-speaker label

Primary lane: AI Experience. Secondary lane: Gameplay.

No user decision is required.

---

## 18. Git / Worktree State

The worktree was dirty before PR-BH and remains dirty.

PR-BH production:

* `game/interaction_context.py`

PR-BH tests / artifacts / report / handoff:

* `tests/test_addressed_npc_identity_resolution_role_title.py`
* `tests/test_directed_social_routing.py` (legitimate-role wording only)
* `artifacts/prbh_addressed_npc_identity/`
* `development/tmp/prbh_addressed_npc_identity_probe.py`
* this report
* `docs/NEXT_SESSION.md`

Do not commit or push unless explicitly asked.
