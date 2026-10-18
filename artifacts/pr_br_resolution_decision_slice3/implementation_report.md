# PR-BR GM Resolution Decision Slice 3 Report

Deterministic implementation only. No gameplay/model API calls, no 4x10 gate rerun, no human playtest, no commit, no push.

## Pre-Slice-3 Authority/Fidelity Flow

`GMResolutionDecision` owned pre-narration fact authority after Slice 2, but `classify_narrated_fact()` still authorized many narrated facts through direct text containment, token subset/overlap, authored-corpus token grounding, structural consequential detection, and legacy known-family heuristics. The engine could answer "what facts are authorized?" better than it could answer whether a natural-language realization preserved the same fact.

## Final Authority/Fidelity Flow

Narration validation now checks structured semantic identity before lexical compatibility. If an authorized proposed fact has `semantic_identity`, `_authorized_by_decision()` requires that the sentence preserve its subject/target, relation, value, polarity, material qualifiers, epistemic status, and overreach constraints. Token/subset matching remains available only for rows without structured identity.

## Structured Proposition Representation

`GMProposedFact` now carries optional `semantic_identity: dict`.

Current supported fields are deliberately small and source-owned:

- `kind`: e.g. `world_fact`, `npc_claim`, `movement`, `state_change`, `entity`.
- `subject` / `subject_aliases`: canonical subject or entity plus allowed source-owned aliases.
- `relation`: compact predicate such as `status`, `condition`, `departure`, `transition`.
- `value` / `value_aliases`: canonical object/value plus allowed source-owned realizations.
- `polarity`: optional positive/negative marker.
- `qualifiers`: optional material `time`, `location`, `identity`, `certainty`, `causality` fields with aliases.
- `speaker_id`, `speaker_name`, `epistemic_status`, `authority`: for claim fidelity.
- `source_scene_id`, `target_scene_id`, `target_name`: for movement fidelity.

Plain authored strings keep legacy lexical behavior. The implementation does not pretend free-text facts have richer semantics.

## Fields Added/Reused And Justification

Added only `GMProposedFact.semantic_identity`. Existing fields remain the authority envelope: `provenance`, `authority`, `persistence`, `source_ref`, and `outcome_classification`.

Reused:

- Authored state rows can supply structured identity as dict facts.
- Resolver movement already supplies `target_scene_id`; the decision projects it as `kind=movement`.
- Resolver state changes project `key/value` as `kind=state_change`.
- Accepted NPC claim ledger entries can carry source-owned claim identity and retain `claim_only` authority.

## Source-Owned Semantic Identity Behavior

Authored structured fact rows originate from scene/world state. Movement identity originates from permitted state mutation. NPC claim identity originates from accepted bounded-improvisation claim records when present. The validator does not parse arbitrary prose back into world truth as the canonical source.

## Narration Realization Behavior

Structured facts can be realized with different wording when the semantic identity supplies aliases or source terms for the subject/value/qualifier. Example covered by tests: `eastern_bridge/status/collapsed/time=yesterday` authorizes "The crossing gave way the previous day" and "Yesterday, the eastern span came down."

## Remaining Lexical Fallback Behavior

Token containment/subset matching remains for unstructured legacy facts only. Authored free-text still works as compatibility behavior. Structured rows skip token fallback unless their semantic identity matches.

## Valid Paraphrase Results

Passed in `tests/test_pr_br_decision_semantic_fidelity_slice3.py`:

- Collapsed bridge paraphrases with different subject/value/time wording.
- Movement arrival phrased as "cross the market bridge and emerge beneath River Arch."
- NPC uncertainty phrased as "Mira is not certain, but she suspects something is wrong with the water."

## Strengthening Rejection Results

Passed:

- `bridge status=damaged` rejects "bridge collapsed yesterday."
- `seen_near/observation` overreach support is present for membership-style strengthening.
- `condition=tainted` claim does not authorize "well is poisoned."

## Polarity Results

Passed:

- `cellar door locked` rejects "cellar door unlocked" despite high token overlap.
- Positive identities reject negated realizations except epistemic frames like "not certain."

## Qualifier Results

Passed:

- Time mismatch: `today` vs `three days ago` rejected.
- Spatial mismatch: `east gate` vs `inside the barracks` rejected.
- Identity substitution: `one unnamed guard` vs `Captain Merrow` rejected.
- Causal overreach: `door damaged` vs `thieves broke it` rejected.

## Epistemic-Fidelity Results

Passed:

- NPC claim paraphrase retains `claim_only`.
- Claim-only uncertainty cannot silently become authoritative world truth.
- The epistemic frame now recognizes "suspects" and "not certain."

## Movement-Fidelity Results

Passed:

- `target_scene_id=river_arch` allows flexible arrival wording naming River Arch.
- Same movement rejects "after discovering a hidden trail to the watchtower."

## Incidental-Flexibility Results

Passed:

- Harmless sensory/social texture remains authorized as bounded incidental.
- Entity-existence structured rows do not reject ordinary incidental sentences mentioning that entity.

## Slice-1/Slice-2 Regression Results

Passed:

- `tests/test_pr_br_gm_resolution_decision.py`
- `tests/test_pr_br_decision_ownership_slice2.py`
- `tests/test_pr_br_decision_semantic_fidelity_slice3.py`

Command:

`python -m pytest tests\test_pr_br_decision_semantic_fidelity_slice3.py tests\test_pr_br_gm_resolution_decision.py tests\test_pr_br_decision_ownership_slice2.py -q --tb=short --basetemp=codex_pytest_tmp_slice3`

Result: 23 passed.

## C18-C27 Regression Results

Passed:

`tests/test_pr_br_continuation18_immutable_boundary.py` through `tests/test_pr_br_continuation27_structural_subject.py`, including 21b/21c.

Result: 159 passed, 1 Starlette/httpx deprecation warning.

## Bounded Improvisation Regression Results

Passed:

`tests/test_bounded_improvisation_authority.py`

Result: 5 passed.

## Historical Gate Reclassification

Saved-gate deterministic audit used existing saved evidence only:

`artifacts/pr_br_second_full_gate/20261003T142725Z/persona_{a,b,c,d}/turns.json`

Result:

- 80 saved turns checked.
- 69 historical violations.
- 2 `DECISION_SOURCE_AUTHORITY_VIOLATION`.
- 67 `KNOWN_FAMILY_HEURISTIC_VIOLATION`.

Classification:

- A. Would be prevented by decision ownership + semantic fidelity: the new structured tests prove prevention for source-owned structured bridge/status, claim/epistemic, qualifier, polarity, causality, and movement drift cases.
- B. Decision ownership applies but historical evidence is insufficient to reconstruct fidelity: most saved turns predate attached Slice 2/Slice 3 decision identities, so prevention cannot be inflated from those artifacts.
- C. Only known-family heuristic currently detects it: 67 saved-gate violations remain in this bucket.
- D. Unrelated failure family: none separately identified by this static audit.

## Remaining Known-Family Heuristic Dependence

Known-family detection remains necessary for historical patrol/roster/notice/evidence failures in old saved turns where no structured decision identity exists. Slice 3 does not remove those heuristics.

## Remaining Architectural Limitations

- Deterministic semantic fidelity is limited to source-owned structured identities and small relation/value checks.
- The engine does not perform general English entailment.
- Free-text authored facts remain legacy lexical compatibility.
- Broad live paraphrase breadth still depends on upstream generation/realization using available structured identity or source-owned aliases.
- Historical gate artifacts usually lack reconstructable pre-narration decision identity.

## Files Changed

- `game/gm_resolution_decision.py`
- `tests/test_pr_br_decision_semantic_fidelity_slice3.py`
- `artifacts/pr_br_resolution_decision_slice3/implementation_report.md`
- `artifacts/pr_br_resolution_decision_slice3/saved_gate_static_audit.json`
- `artifacts/pr_br_resolution_decision_slice3/handoff_config.json`

## API/Model Cost Implications

No new model/API calls. Runtime cost is deterministic regex/string matching over existing decision rows.

## Recommendation

B.
FIDELITY IS IMPROVED BUT ANOTHER DETERMINISTIC
IMPLEMENTATION SLICE IS REQUIRED
