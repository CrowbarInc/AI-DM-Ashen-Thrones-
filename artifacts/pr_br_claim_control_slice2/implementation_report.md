# PR-BR Claim Control Slice 2 Implementation Report

Date: 2026-10-03

## 1. Executive conclusion

Claim control improved materially under deterministic adversarial paraphrase testing. The slice now catches ordinary actor, cause, time, history/state-transition, relationship, and cue-less residual paraphrases without adding the requested test-domain nouns to production detectors.

Decision: B. Claim control improved but remains locally incomplete; another deterministic slice is required.

## 2. Adversarial paraphrase matrix

- Actor attribution: 5 negative paraphrases, including "Guild hands did this" and "This was the guild's work", rejected.
- Cause attribution: 5 negative paraphrases, including "Bad water is what finished the orchard", rejected.
- Time attribution: 5 negative paraphrases, including "The break-in happened overnight", rejected.
- History/state transition: 4 negative paraphrases, including "Someone took it after the priests left", rejected.
- Relationship composition: 5 negative paraphrases, including "Those two details tell the same story: someone climbed inside", rejected.
- Cue-less residuals: 5 negative paraphrases, including "A smuggler's knife did that" and "The driver fled toward the southern farms", rejected.
- False-positive controls: 10 incidental/unresolved controls accepted.
- Positive authority controls: explicit actor relation with deictic subject alias permits "Guild hands did this."

## 3. Escaped-claim analysis before repair

Before repair, current architecture escaped:

- Actor forms: "Someone from the guild broke the hinge", "Guild hands did this", "This was the guild's work", and "You can tell guild workers were responsible."
- Cause forms: "The trees died from tainted runoff", "Bad water is what finished the orchard", and "The drainage explains the dead trees."
- Time/history forms: "The break-in happened overnight", "The damage is only a few hours old", "Whoever did it came through before sunrise", "Someone took it after the priests left", and "This is where it stood before thieves carried it off."
- Relationship/cue-less forms: "Whoever came through the window searched the desk" and "Those two details tell the same story: someone climbed inside."

These escapes clustered around missing structural responsibility for ordinary actor-action, event-cause, event-time, and event-history assertions when classic causal/evidential cue words were absent.

## 4. Detector/responsibility map

- Structured semantic identity: authorizes explicitly established observation/relation facts; fixed subject miss behavior so nearby subjects do not cross-authorize.
- relation_kind: still authorizes explicit causal/evidential/actor relation facts when represented in the decision.
- Epistemic act/status: now guards certainty upgrades around possible/inferred claims.
- Stateful assertion detector: expanded to catch ordinary state claims like "is damaged", "is missing", "is empty", and action verbs like "cut" when not otherwise authorized.
- classify_propositions: unchanged; still handles older operational-rule families.
- Known-family consequential detector: unchanged; no new domain-family nouns were added.
- Lexical/token compatibility: subject matching was tightened so missing authorized subjects fail instead of falling through.
- Other: new ordinary residual family detects actor attribution, cause attribution, time attribution, and event/history assertions near unresolved slots, governed subjects, or deictic anchors.

## 5. Generalized repairs implemented

- Added structural actor-attribution residual detection.
- Added structural event-cause attribution detection.
- Broadened event-time attribution detection.
- Added event-history/state-transition residual detection.
- Added deictic residual anchoring for "this/that/it/the damage/those details."
- Tightened semantic identity subject matching.
- Added subject-head fallback only when the authorized value also appears.
- Added explicit unknown-slot and possibility-frame protections to reduce false positives.
- Corrected quote/source handling so narrator certainty outside a quote is not masked as NPC hearsay.

## 6. Actor-attribution results

All adversarial actor paraphrases in the new deterministic matrix reject. Explicit positive authority can permit a deictic actor paraphrase when the decision represents that relation.

## 7. Cause-attribution results

All adversarial cause paraphrases reject, including cue-light "finished" and "explains" forms.

## 8. Time-attribution results

All adversarial time paraphrases reject, including overnight, before sunrise, and "few hours old" forms.

## 9. History/state-transition results

All tested removal, prior-standing, carried-off, fleeing, and entry-history claims reject unless explicitly represented.

## 10. Cue-less residual results

The cue-less residual matrix rejects all tested actor-action and movement/history claims without relying on sample-domain nouns.

## 11. Epistemic certainty results

Possibility wording remains valid. Certainty upgrades including "clearly", "no doubt", "confirms", "now we know", and "that's what happened" reject.

## 12. Player-presupposition results

Player hypotheses recorded through temporal provenance remain non-world-truth. Player wording alone does not promote sabotage.

## 13. NPC-repetition results

Quoted/hearsay NPC repetition remains claim-only. Narrator certainty appended outside a quote is no longer masked as claim-only.

## 14. False-positive controls

Incidental controls and explicit unresolved-status controls pass, including cut rope hanging, wet sacks smelling musty, burned cloth leaving soot, and "who did it remains unknown."

## 15. Mixed-sentence results

Authorized + authorized, authorized + incidental, authorized + permitted inference, and authorized + explicit unresolved status pass. Authorized/incidental + unauthorized residual and claim + narrator certainty fail.

## 16. Multi-sentence/preservation results

The preservation test drops the unsafe cue-less residual sentence and keeps the authorized observation plus uncertainty sentence.

## 17. Temporal provenance lifecycle

The new test directly exercises gm_inferences, player_hypotheses, rejected_consequential capping, and precise explicit promotion. Cap behavior retained the latest 24 rejected records.

## 18. Claim-identity collision results

Nearby claims such as bridge cable versus bridge railing, sheep versus shepherd, warehouse shelf versus warehouse locked, and ledger burned versus ledger missing do not cross-authorize.

## 19. Positive-authority controls

Explicitly established actor relation permits its represented paraphrase. Existing Slice 1 positive evidential relation still passes.

## 20. Broad regression results

Completed:

- Slice 1 + Slice 2 claim control: 16 passed.
- GMResolutionDecision focused suites: 9 + 7 + 7 + 9 passed.
- C18/C19 excluding raw-chat stubs: 29 passed.
- C20 prefix before raw-chat stub: 13 passed before blocked raw-chat stub.
- C21 prefix before raw-chat stub: 9 passed before blocked raw-chat stub.
- C21b/C21c prefix before raw-chat stub: 17 passed before blocked raw-chat stub.
- C22 prefix: 26 passed before blocked later client-path test.
- C24 prefix: 5 passed before blocked later client-path test.

Interrupted blocked runs emitted no traceback or assertion failure.

## 21. Raw-chat stall diagnosis

The stall reproduces in deterministic pytest, not gameplay. It occurs after fast prefixes in raw-chat/client-path tests, notably:

- `test_raw_chat_stub_preserves_valid_and_contains_invalid`
- `test_raw_chat_stub_authority_and_contracts`
- `test_raw_chat_stub_covers_incidental_binding_and_authority`
- `test_raw_chat_stub_covers_the_ten_boundaries`
- `test_raw_chat_stub_rejects_nonpersons_and_keeps_people`
- `test_raw_chat_stub_covers_referential_heads`

Additional later C22/C24 client-path tests also block silently. Collection succeeds. Fast unit-style deterministic tests pass. This points to test harness/client-path blocking rather than a production assertion failure or live model path. No evidence of model/API calls was observed.

## 22. Files changed

- `game/gm_resolution_decision.py`
- `tests/test_pr_br_claim_control_slice2.py`
- `artifacts/pr_br_claim_control_slice2/implementation_report.md`
- `artifacts/pr_br_claim_control_slice2/test_results.md`

## 23. Known limitations

- This is still bounded structural detection, not general NLI.
- Positive paraphrase expressiveness depends on structured semantic identities containing the right subject/value aliases.
- Some client/raw-chat deterministic harnesses block silently and need separate harness repair before they can serve as broad regression evidence.

## 24. Exact gameplay/model API call count

0 gameplay/model API calls.

## 25. Recommendation

Do not proceed to live validation yet. Run another deterministic slice or harness-repair pass focused on raw-chat/client-path blocking and remaining expressiveness limits for positive relation paraphrases.

B.
CLAIM CONTROL IMPROVED BUT REMAINS LOCALLY INCOMPLETE;
ANOTHER DETERMINISTIC SLICE IS REQUIRED
