# PR-BR Continuation 26 — Contract Sufficiency & Post-Contract Semantic Closure

### 1. Purpose

Close three residual holes left by C25 without reopening the contract-first ownership path: stop a downstream family selector from treating place words as a second reading of the turn, reject a structured proposal that contradicts strong speech structure, and stop a raw model envelope from becoming narration.

### 2. Authorization basis

C25 kept one semantic owner and passed its historical suites. Fresh live quality was 4 / 6. Turn 4 answered a contemplated harbor plan as a tavern-existence question. Turn 1 sealed a spoken approach as an act and included a JSON object in the player-visible retry. This cycle was authorized to close those mechanisms only.

### 3. Frozen C25 invariant

Ordinary gameplay remains:

```
raw language
    -> structural preprocessing
    -> authoritative Resolution Contract
    -> resolver selection
    -> specialized resolver
    -> C19 / C18
    -> commit
    -> emit
```

Peer parsers were not restored. `establish_ordinary_gameplay_contract` still runs before specialized resolution. No new resolver architecture was added.

### 4. C25 Turn 4 forensic trace

Exact player line, replayed with `construct_resolution_contract` before the edit:

- Proposed operation: `act`
- Commitment: `contemplated`
- Authoritative operation after the existing uncommitted rewrite: `ask`
- `select_resolver_family` then matched `tavern` and `shelter` in `game/contract_adjudication_bridge.py` and returned `place_location`
- Ordinary selection: `adjudication` / `place_location`

The function that contradicted the contemplated plan was `select_resolver_family`. It re-read `raw_input` after the contract existed. The place answer "No nearby tavern is currently established in this scene." came from `resolve_adjudication_query` once that family had been chosen.

After the edit, the same line stores `resolution_subject=social` (the uncommitted plan is not a place question) and selects social, not `place_location`.

### 5. Resolver-family contract-sufficiency audit

`operation=ask` is shared by a social ask, a place question, a presence question, a feasibility question, a state question, and a roll question. Commitment and addressee do not separate them. That is why the C24 selector kept a second lexical reading. The smallest added fact is `construction.resolution_subject`, set while the contract is built.

| Family | Needs | Already on the contract before C26 | After C26 |
| --- | --- | --- | --- |
| social | addressed speech, not a world query | operation `ask` was too coarse | subject `social` |
| exploration / perception | inspect or perceive | operation | subject `perception` |
| travel | committed movement | operation `act` plus a later raw travel scan | subject `travel` |
| world action | committed non-travel act | operation `act` | subject `world_action` |
| combat | committed attack, then combat state | raw attack scan at selection | subject `combat`, combat state at selection |
| earshot / presence | direct presence question | raw scan | subject `earshot` or `nearby_presence` |
| place / location | direct place question | raw scan | subject `place_location` |
| feasibility | direct modal question | raw scan | subject `feasibility` |
| state query | direct state question | raw scan | subject `state_query` |
| roll | direct roll question | raw scan | subject `roll_mechanical` |
| generation | no specialized family | missing contract or unresolved operation | subject not an adjudication family |

### 6. Smallest missing semantic dimension

Yes. `construction.resolution_subject`. It is one closed label, not a parse tree. Values used for selection: `social`, `place_location`, `nearby_presence`, `earshot`, `feasibility`, `state_query`, `roll_mechanical`, `perception`, `travel`, `world_action`, `combat`, `action`, `unspecified`.

### 7. Contract-schema changes

No new dataclass field. The existing `construction` map gains `resolution_subject`. `ResolutionContract` itself was not expanded into an intent schema.

### 8. Resolver-selection changes

`select_resolver_family` returns the stored subject when it names an adjudication family. It does not read `raw_input`. `select_ordinary_resolver` maps that subject, plus operation, commitment, and whether combat is active. `derive_resolution_subject` performs the reading once, during contract construction.

A direct feasibility question such as "Can I climb the wall?" is no longer swallowed by the physical-act rule. An ask that governs an embedded "whether I can climb" stays an ask.

### 9. Allowed and forbidden post-contract raw-text uses

Allowed:

- Quoted dialogue and descriptive flavor passed into an already selected resolver
- Object or place names used as content once the family is already `place_location` (`extract_place_existence_subject`, `_availability_subject`)
- Surface wording for generation

Forbidden:

- Choosing or replacing operation, addressee, commitment, or resolver family from raw tokens after the contract exists

`resolve_selected_family` still passes the utterance into the selected resolver as content. It refuses a caller-supplied place, presence, or earshot family when the subject is social or otherwise not that family. The unforced `resolve_adjudication_query` call in `game/api.py` runs only when no contract id exists.

### 10. D1–D8 semantic distinctions

8 / 8 in `test_d1_through_d8_distinctions`. An ask that mentions shelter, harbor, nearby people, or climbing stays social. The direct questions select place, presence, or feasibility.

### 11. C25 Turn 1 forensic trace

Isolated deterministic construction of the traveler line was already `ask` / social. The live failure was the model proposal. Before the edit, `validate_interpretation_proposal` accepted `primary_operation=act` for that quoted question. The validator did not compare the proposal with the speech span.

### 12. Interpretation-coherence validation

`structural_coherence_operation` runs inside `validate_interpretation_proposal` before a proposal can be authoritative.

- Quoted or explicit ask addressed to someone canonicalizes `act` / `inspect` / `perceive` to `ask` when that reading is unambiguous
- "I open the door and ask..." abstains, because the act is outside the ask
- A bare approach proposed as `ask` becomes `act`
- A bare "look at" becomes `inspect`
- A bare attack proposed as `ask` becomes `act`
- A question mark alone does not force `ask`

The corrected operation is copied back onto the contract when validation is authoritative.

### 13. J1–J6 controls

6 / 6 in `test_j1_through_j6_controls`. Quoted ask and tell are social. Bare approach is an act. "I look at the traveler" is inspection. "I ask whether the traveler looks injured" stays an ask. "Traveler?" is not invented into a full ask.

### 14. Structured-output forensic trace

C25 turn 1's sealed text was narration followed by a JSON object whose keys included `player_facing_text`, `tags`, `improvisation_proposals`, and `debug_notes`. `game/gm.py` `_safe_json` called `json.loads` on the whole string. The leading prose made the parse fail, and the `except` branch stored the entire raw string as `player_facing_text`. C18 then sealed that string because accepted and emitted text matched.

### 15. Structured-response parsing boundary

`game/structured_player_output.py` classifies model output as plain, structured, or malformed.

- A JSON object with `player_facing_text` contributes that string only
- Extra schema fields stay off the narration
- An object missing player-facing prose is rejected
- Prose with an embedded schema object is rejected
- Unparseable text that still contains a schema key is rejected
- Braces, colons, and quotes in ordinary sentences stay plain text

### 16. Hard-validation changes

`validate_generated_response` appends `structured_envelope` when the candidate text itself contains a response envelope. Empty rejected output still fails the existing malformed check. Narration is not rejected for braces or quotes alone.

### 17. Retry behavior

`run_preserve_if_valid` still retries once, then uses the existing safe nonresolution. The retry receives the same resolution object and therefore the same contract. A formatting failure does not select a new family. T9 extracts a valid structured retry. T10 rejects a second malformed envelope and seals nonresolution text with the original contract id.

### 18. Post-contract semantic closure audit

| Site | Class |
| --- | --- |
| `select_resolver_family` | reads `resolution_subject` only |
| `select_ordinary_resolver` | reads subject, operation, commitment, and combat state |
| `resolve_selected_family` | content handoff; refuses a contradictory place/presence/earshot family |
| `resolve_adjudication_query` with a family | content extraction for the already chosen family |
| `resolve_adjudication_query` without a family | not used once a contract id exists |
| `derive_resolution_subject` | contract construction, not a downstream reader |

The downstream selector no longer reclassifies. Construction still classifies with the old place, presence, feasibility, roll, and state patterns. Live turns 3 and 4 show that classification can still name `place_location` for addressed speech.

### 19. Contract-sufficiency matrix

Unit fixtures: every exercised family is selected from the stored subject. Live counterexample: turns 3 and 4 stored `place_location` for speech that was not a direct place question, and the selector obeyed that subject. Selection is contract-sufficient. The subject is not yet a sufficient reading of addressed speech.

### 20. R1–R20 matrix

20 / 20 in `test_r1_through_r20_matrix`. Social asks that contain shelter, harbor, nearby, climb, road, or attack words stay social. Direct queries select the matching adjudication family. The contemplated C25 turn 4 line stays social. The conditional shelter line stays social.

### 21. S1–S10 matrix

10 / 10 in `test_s1_through_s10_malformed_proposals_do_not_stick`. An `act` proposal on a quoted question becomes `ask`. An independent open-and-ask proposal abstains.

### 22. T1–T10 matrix

10 / 10 in `test_t1_through_t8_output_boundary` and `test_t9_t10_retry_keeps_the_contract_and_hides_the_envelope`. The C25-shaped prose-plus-JSON leak is rejected. The envelope is not sealed.

### 23. Historical replay results

Deterministic modules, no historical API reruns: C12, C13, C14, C15, C16, C18, C19, C20, C21, C21b, C21c, C22, C23, C24, C25, C26. All passed in one pytest run.

### 24. C25 frozen-architecture regression

Pass. `test_pr_br_continuation25_semantic_ownership.py` passed, including Y1–Y20, contract-before-resolver, and `semantic_owner=resolution_contract`.

### 25. C18 regression

Pass. `test_pr_br_continuation18_immutable_boundary.py`.

### 26. C19 regression

Pass. `test_pr_br_continuation19_hard_authority.py`.

### 27. C20 regression

Pass. `test_pr_br_continuation20_incidental_entity.py`.

### 28. C21 regression

Pass. C21, C21b, and C21c modules.

### 29. C22 regression

Pass. `test_pr_br_continuation22_commitment.py`.

### 30. C24 regression

Pass. `test_pr_br_continuation24_contract_first_unparsed.py`, including the nearby and shelter contrasts.

### 31. C25 regression

Pass. Same module as section 24.

### 32. Broader PR-BR regression

C12–C16 passed with the modules above. Nearby-place, local-presence, and the earshot chat test passed except `test_question_rule_does_not_rewrite_resolved_place_existence`, which C25 already recorded as red before this cycle.

### 33. Fresh live transcript

`artifacts/pr_br_continuation26/live/20261003T134953Z/visible.md`. Four turns. One isolated session. No repair, no rerun, no evaluator. Opening plus Galinor at the frontier gate.

### 34. Live contract / resolver telemetry

| Turn | Source | Operation | Subject | Resolver | Commitment |
| --- | --- | --- | --- | --- | --- |
| 1 | deterministic | ask | social | social | executed_now |
| 2 | deterministic | ask | social | social | executed_now |
| 3 | deterministic | ask | place_location | adjudication / place_location | executed_now |
| 4 | structured | ask | place_location | adjudication / place_location | executed_now |

Every turn has a contract, `semantic_owner=resolution_contract`, and `contract_before_resolver=true`. Family matched subject on all four turns, so the selector did not contradict the contract. The subject on turns 3 and 4 was the wrong reading.

### 35. Live structured-output telemetry

Turns 1 and 2: output form `structured`. Extracted prose was sealed. No envelope in the player-visible text. Turns 3 and 4: engine adjudication lines, no model envelope. Structured-envelope leaks: 0.

### 36. State / discourse review

Scene stayed `frontier_gate` on all four turns. No uncommitted transition. Turns 1 and 2 bound `tavern_runner`. Turn 3 bound no interlocutor while answering a place question the spoken approach did not ask. Turn 4 bound `threadbare_watcher` and still emitted a place-existence line. Accepted text equals emitted text on all four turns.

### 37. Manual review

2 / 4 PASS. See `MANUAL_REVIEW.md`. Turns 3 and 4 fail.

### 38. Post-C26 audit

1. The selector can choose a family from the stored subject without reading the utterance again. The subject itself is still assigned by lexical patterns during construction, and those patterns misread addressed speech.
2. No. Construction still uses place, presence, feasibility, roll, and state patterns to decide the semantic subject. That is semantic ownership, not content extraction. Content extraction remains only after the family is chosen.
3. Yes. Turn 3's quoted question to the figure, and turn 4's trailing ask that fell outside the 240-character contract window, became an authoritative `place_location` subject.
4. No envelope reached the player in this session. The unit matrix rejects the C25 leak shape.
5. Yes. The contract is still built before resolver selection. Peer parsers were not restored. No state mutation was added before the contract.

### 39. Residual defects

- Addressed quoted speech that does not contain the word "ask" can still be labeled `place_location` when it mentions shelter or a tavern. Live turn 3.
- `construct_resolution_contract` keeps 240 characters. Live turn 4's terminal "I ask..." was outside that window, so the kept "Shelter?" / tavern sentence owned the subject.
- Those two defects are the same player-visible failure: a place-existence line instead of an answer from the person being spoken to.

### 40. Model / API cost accounting

Opening generation 1. Gameplay initial generation 2. Gameplay retry 0. Interpretation invocations 1. Deterministic contracts 3. Structured contracts 1. Player-model calls 4 (`gpt-4.1-mini`). Evaluator 0. Repair/rerun: no.

### 41. Readiness decision

C26 INCOMPLETE — INTERPRETATION COHERENCE REMAINS UNSAFE.

The downstream selector now follows the contract subject, and the JSON boundary held. The subject is still wrong for addressed speech that mentions a place. Manual review is 2 / 4, below the 3 / 4 bar. No C27 was opened. The second 4×10 gate was not run. Human playtest was not run.

### 42. PR-BR status

PR-BR remains OPEN. No completion commit. No push. No PR-BS. The second 4×10 gate is not authorized. Human playtest is not authorized.
