# PR-BR Continuation 27 — Structural Resolution-Subject Derivation & Lossless Operative Context

## 1. Purpose

Repair only how `resolution_subject` is derived, and what text contract construction uses as semantic input. Topic words inside an addressed question must not select a direct world resolver. A character cap must not drop the operative clause before the contract exists.

## 2. Authorization basis

C25 made the Resolution Contract the semantic owner. C26 stopped resolver selection from rereading the utterance, and stopped raw JSON envelopes from becoming player text. C26 deterministic matrices passed. C26 live validation was 2/4. Turns 3 and 4 put `place_location` on addressed speech. This cycle repairs that construction defect. It does not reopen C25 routing or C26 post-contract selection.

## 3. Frozen C25/C26 architecture

Preserved path:

raw language → structural preprocessing → authoritative Resolution Contract → resolver selection from the contract → resolution → C19 → C18 → commit → exact emission.

Not restored: peer-parser ownership, resolver-before-contract, post-contract lexical reinterpretation, or gameplay emission without a contract.

`select_resolver_family` still reads only `construction.resolution_subject`. A planted `place_location` subject still selects the place family even when the utterance is an ask. C27 does not repair a bad contract downstream.

## 4. Exact C26 Turn 3 forensic replay

Captured before the edit in `forensic_pre_change.json`.

Utterance, 250 characters after whitespace normalization:

> I approach the lone figure in threadbare clothes cautiously, keeping my voice low to avoid drawing attention. "The patrol near the gate—do you know what happened to them? I've heard unsettling things and seek shelter or guidance for a weary traveler.

The 240-character window dropped only ` traveler.`. Shelter was inside the window.

Segmentation: approach clause, then an unclosed quoted question, then the shelter/guidance clause inside that quote.

Speech structure: player-voiced quote. `_explicit_social_address` did not match (no "I ask" / "speak to"). `_strong_addressed_ask` was false.

Addressee: no bound interlocutor in the stubbed replay. Operation was `ask` because of the question. Commitment was `executed_now`.

`resolution_subject` became `place_location` because `_PLACE_RE` matched `shelter` after the social-address check missed the quote. Resolver selection then obeyed the contract: adjudication / `place_location`.

The quoted ask and `place_location` coexisted at `derive_resolution_subject`. The outranking evidence was the topic pattern for shelter, tavern, inn, lodging, and supplies, applied to any `ask` that had not already matched the narrow address regex.

## 5. Exact C26 Turn 4 forensic replay

Full utterance: 423 characters.

The 240-character cut kept the narrated NPC speech through `Shelter?` and `tavern behind th`, and dropped:

> ose crates—crowded, noisy, but dry. If you're looking for passage or safety, that's where folks gather." I ask if they have any more details about the tunnels or what to expect there.

On the truncated text, `_explicit_social_address` was false and `Shelter` selected `place_location`. On the full text, the same function returned `social` because of `I ask`. The stubbed inspect proposal did not change that, because subject derivation ran on the truncated string either way.

Naïve first-N truncation causally removed the operative ask.

## 6. Structural frame

`structural_interaction_frame` is an implementation label. It is not stored on the contract.

It is computed from the existing operation, commitment, explicit current-turn addressee, addressed-speech patterns, and player-voiced quoted questions. Frames used: `social_ask`, `perception`, `inspection`, `combat_action`, `committed_movement`, `world_action`, `direct_place`, `direct_presence`, `direct_feasibility`, `direct_travel`, `direct_inquiry`, `uncommitted`, `unspecified`.

No second operation system was added.

## 7. Topic versus resolution subject

Topic is what the utterance is about. It stays in the utterance and, when already derived, in `conversational_subject`.

`resolution_subject` is which system resolves the request. Shelter inside "I ask …" or inside the player's own quoted question is topic content. It does not select `place_location`.

## 8. Precedence

Applied inside `resolve_subject_coherence` before the contract is authoritative:

1. Addressed social interaction: explicit ask/tell/speak-to, or a player-voiced quoted question, or `operation=ask` with an explicit current-turn person addressee. Inherited discourse focus does not count.
2. Uncommitted plans stay non-executing, including when they mention place words. Existing commitment rules.
3. Direct questions with no address: presence, state, place (including structural "where is the …"), roll, feasibility, "where does this … lead/go", and "what does the <non-person> say".
4. Topic vocabulary is only that direct-question step. The old shelter/tavern/inn/lodging/supplies pattern still marks a direct place question. It does not outrank step 1.

Speech attributed to someone else (`they speak`, `the figure says`) is not the player's question.

## 9. Social ask sufficiency

`operation=ask` plus an addressed frame canonicalizes a direct-world topical subject to `social`. A topic noun does not select place, presence, feasibility, or travel.

Legitimate non-social asks remain: bare "Is there shelter nearby?", "Who is nearby?", "Can I climb the wall?", "Where is the harbor?", "Where does this road lead?", "What does the inscription say?".

## 10. Non-social controls

H1–H6 passed in `test_h1_through_h6_direct_controls_stay_non_social`.

| Case | Subject | Family |
| --- | --- | --- |
| Is there shelter nearby? | place_location | place_location |
| Who is nearby? | nearby_presence | nearby_presence |
| Can I climb this wall? | feasibility | feasibility |
| Where is the harbor? | place_location | place_location |
| What does the inscription say? | perception | exploration |
| Do I hear movement outside? | perception | exploration |

"Where is the harbor?" is a structural where-is question, not a harbor noun rule. "What does the guard say?" stays social because the nominal is a person.

## 11. Semantic-input truncation audit

| Site | Limit | Consumed by | Semantic for the contract? | C27 |
| --- | --- | --- | --- | --- |
| `construct_resolution_contract` via `_clean(..., limit=240)` | 240 | entire contract construction | yes | removed; full `semantic_input_text` |
| `_echoes_utterance` | 240 | target-echo rejection inside construction | yes | now compares the full normalized utterance |
| `construction.provenance_excerpt` | 240 | logs / telemetry | no | new bounded copy |
| `live_resolution.derive_interaction_obligation` and `_select_resolution_mode_body` | 240 | parallel mode/obligation classification | not the contract text | left in place; routing was not redesigned |
| `semantic_interpreter` history snippets, `gm.py` previous-turn excerpts | 240 | prompt compactness | prior-turn display | unchanged |
| `intent_parser` / `gm.py` / `social_continuity_routing` quote windows | 240 | peer parser or display | not the contract utterance | unchanged |

## 12. Semantic input versus bounded provenance

`semantic_input_text` is the whitespace-normalized full utterance. Contract construction and `raw_input` use it. `construction.provenance_excerpt` is the first 240 characters and is not read by subject derivation or resolver selection.

The persisted contract does not need an unlimited second copy. `raw_input` is the semantic input the selected resolver executes against. The excerpt is the bounded provenance.

## 13. Operative-context architecture

Full utterance in, structural frame and existing operation/commitment/addressee logic, then subject. No first-N or last-N approximation.

## 14. Long-utterance controls

L1–L8 passed. The ask remains available at the start, middle, end, after a long preamble, before a long tail, in a second quoted span, after a conditional, and after a reflective preamble. Each case is longer than 240 characters. Operation `ask`, subject `social`, commitment `executed_now`.

## 15. Multi-clause precedence

M1–M5 passed under existing commitment behavior.

| Case | Operation | Subject | Commitment |
| --- | --- | --- | --- |
| consider harbor, but first ask | ask | social | contemplated |
| ask, then head for the harbor | ask | social | executed_now |
| hope to find shelter and ask | ask | social | executed_now |
| ask about the patrol before deciding on shelter | ask | social | executed_now |
| look toward the harbor while asking | perceive | perception | executed_now |

Shelter does not steal M3 or M4. M5 keeps the existing perceive primary.

## 16. Resolution-subject coherence

`resolve_subject_coherence` compares the topical subject with the structural frame before the contract is returned.

`construction.resolution_subject_coherence` is `accepted` or `canonicalized`. That is validation bookkeeping, not a second subject.

C26 Turn 3 and Turn 4 both canonicalize to `social`. Direct shelter, presence, feasibility, and harbor questions stay `accepted` on their topical subjects.

## 17. Canonicalization and rejection

Unambiguous addressed ask plus a direct-world topical subject canonicalizes to `social`.

A direct question with no address keeps the topical subject.

An existing operation conflict still abstains. "I open the door and ask the guard what is inside." stays `unresolved` / `unspecified` / generation. It is not forced into `place_location` or into a guessed social subject.

## 18. Contract schema

No new semantic field. `resolution_subject` is still the only subject the selector reads.

Added construction bookkeeping only: `resolution_subject_coherence`, `semantic_input_length`, `provenance_excerpt`.

## 19. C26 post-contract closure

`test_post_contract_selection_does_not_repair_a_bad_subject` plants `place_location` on an ask contract. Selection returns `place_location`. C26 `test_pr_br_continuation26_semantic_closure.py` passed.

## 20. C26 structured-output boundary

Structured envelopes still extract `player_facing_text`. A cut-off envelope is malformed and yields empty player text. C26 T-matrix tests passed.

## 21. Player-authored NPC dialogue watch item

C26 Turn 4 replay: the player wrote the threadbare figure's speech, including "Shelter?" and the tavern line, then asked a follow-up. The attributed quote is not treated as the player's question. The player's `I ask` is the operative clause. The contract does not store that quoted speech as a new world fact.

Fresh live session: not encountered. The player asked questions. They did not author an NPC line and then react to it.

POST-GATE / FUTURE WATCH ITEM. Not fixed.

## 22. T1–T10 historical replay

Passed in `test_historical_t1_through_t10`.

| Id | Result |
| --- | --- |
| T1 C26 Turn 3 | ask / social, not place |
| T2 C26 Turn 4 | terminal ask retained, social |
| T3 C25 Turn 1 | ask / social |
| T4 C25 Turn 4 | ask, contemplated, not place |
| T5 C24 nearby | "Who is nearby?" stays presence; ask-about-supplies stays social |
| T6 C22 listen carefully | ask, supporting perceive, sound dimension not primary |
| T7 C22 conditional milestone | not executed, no authored exit |
| T8 C22 serjeant | ask, serjeant requested, not the captain |
| T9 C21 referential head | inspect; "muddy lane" is not a person |
| T10 ten speaker/inspection lines | asks stay social; inspect/perceive stay perception |

No historical API reruns.

## 23. U1–U20

20/20 in `test_u1_through_u20_structural_subject_matrix`. Open "What happened to the patrol?" stays an ordinary ask. There is no specialized patrol resolver, and it is not `place_location`.

## 24. Long-context matrix

12/12. Six nuclei (ask, listen, follow-road, inspect, where-is-harbor, who-is-nearby), each with padding before and after, all longer than 240 characters. Operation, subject, and commitment match the unpadded nucleus.

## 25. Randomized length property

27/27. Nine nuclei × padding before, after, and both. Operation, subject, commitment, and interlocutor stay invariant. Raw-text equality is not required.

## 26. C18–C26 regressions

Exit 0 on:

- `test_pr_br_continuation18_immutable_boundary.py`
- `test_pr_br_continuation19_hard_authority.py`
- `test_pr_br_continuation20_incidental_entity.py`
- `test_pr_br_continuation21_subject_integrity.py`
- `test_pr_br_continuation21b_referential_personhood.py`
- `test_pr_br_continuation21c_referential_head.py`
- `test_pr_br_continuation22_commitment.py`
- `test_pr_br_continuation23_precontract_routes.py`
- `test_pr_br_continuation24_contract_first_unparsed.py`
- `test_pr_br_continuation25_semantic_ownership.py`
- `test_pr_br_continuation26_semantic_closure.py`

## 27. Broader PR-BR regression

Exit 0, in the same sweep, on `test_pr_br_resolution_contract.py`, `test_pr_br_interpretation_proposal.py`, and `test_pr_br_model_interpretation.py`. An earlier sweep after the conversational-subject fix also passed C12–C16. Full suite was not run. No 10-turn smoke. No 4×10 gate.

One construction bug was found and fixed before live play: the new subject variable briefly overwrote `conversational_subject`. `test_valid_model_proposal_becomes_the_authoritative_contract` caught it. The name was split. The test then passed. That was not a live repair.

## 28. Fresh live transcript

Isolated session `artifacts/pr_br_continuation27/live/20261003T141318Z`. Four completed turns. No repair, no rerun, no evaluator.

Player-visible text is in `visible.md`. The player brief did not mention shelter, tavern, truncation, or expected topics.

## 29. Live contract / subject / resolver telemetry

| Turn | Len | Frame | Operation | Subject | Coherence | Resolver | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 179 | social_ask | ask | social | accepted | social | structured interpretation |
| 2 | 175 | inspection | inspect | perception | accepted | exploration | deterministic |
| 3 | 263 | perception | perceive | perception | accepted | exploration | deterministic |
| 4 | 216 | social_ask | ask | social | canonicalized | social | deterministic |

Turn 3 is longer than 240. The provenance excerpt cuts the tail. `raw_input` keeps the full line, including the contemplated approach. Subject stays perception. Operative loss: 0. Topic override: 0. Post-contract reinterpretation: 0. Resolver-before-contract: 0.

Turn 4 canonicalized. "Road" did not become travel. The runner answered the ask.

## 30. Live state and discourse

All four turns stayed in `frontier_gate`. No resolved transition. No uncommitted movement. Turn 1 bound the threadbare watcher. Turn 4 bound the tavern runner. Turn 2 read the notice board. Turn 3's contract also carried a tavern-runner target because the contemplated approach named him, but the emitted line was the perception inability, not runner speech. Two social generations on that turn were `hard_invalid` and were not emitted.

## 31. Manual review

| Turn | Result | Why |
| --- | --- | --- |
| 1 | PASS | Addressed question to the watcher. He refuses the news in character. Not a place lookup. |
| 2 | PASS | Reading the notice returns taxes, curfew, and the missing-patrol warning, including the northwest track. |
| 3 | PASS | The look is the committed act. The approach is only considered. Player sees an inspection inability. Rejected runner speeches were not emitted. The line is generic. The resolution matches the contract. |
| 4 | PASS | Addressed ask to the runner. He answers from what he heard. The road mention stays inside the answer. |

Manual 4/4. Prose on turn 3 is thin and does not fail the semantic bar.

## 32. Post-C27 audit

1. Yes. Addressed social questions stay social regardless of shelter, harbor, patrol, road, or combat words inside them.
2. Yes. Bare shelter, presence, climb, harbor, inscription, and hearing questions keep non-social subjects.
3. Yes. Operative clauses are available at any position. The contract semantic input is the full utterance.
4. Yes. Subject coherence is checked against operation, addressee, commitment, and the structural frame before the contract is authoritative.
5. Yes. Resolver selection still reads only the contract subject.
6. No fundamentally different contract-construction failure showed up.

## 33. Fundamentally new failure check

No. Live turn 3 showed narration routing attempt a social line for a perception contract. C19 rejected it. The player never saw it. That is the existing authority boundary, not a new owner.

## 34. Residual defects

- Mode selection and interaction-obligation text in `live_resolution.py` still slice at 240. They do not build the contract. Routing was left frozen.
- Prompt-history and peer-parser quote windows still slice at 240.
- Turn 3 bound the contemplated runner while resolving the look. Emission followed the look. Addressee binding on a supporting or contemplated nominal remains a watch item.
- Player-authored NPC dialogue remains a post-gate watch item.
- Turn 2's requested addressee string included "I nod slowly". It did not change the inspect contract or the notice answer.

## 35. Model / API cost

Model: `gpt-4.1-mini`.

| Call | Count |
| --- | --- |
| Opening generation | 1 |
| Gameplay initial generation | 4 |
| Gameplay retry generation | 1 |
| Structured interpretation | 1 |
| Player-model calls | 4 |
| Evaluator | 0 |
| Deterministic contract turns | 3 |
| Structured-interpretation contract turns | 1 |

No repair rerun. No smoke. No 4×10. No human playtest.

## 36. Readiness decision

C27 VALIDATED — structural resolution-subject derivation and lossless operative context established. Ready for a second full 4×10 synthetic gate after external review.

Do not start that gate in this cycle. Do not start a human playtest. Do not open C28.

## 37. PR-BR status

PR-BR remains OPEN. PR-BS has not started. No completion commit. No push.
