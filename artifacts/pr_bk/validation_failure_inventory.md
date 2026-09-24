# PR-BK validation failure inventory

Initial full-suite rerun, before any validation edit:

```text
python -m pytest -q --tb=no
```

Progress marks in `development/tmp/pr_bk_validation_full_suite_initial.txt`:

```text
7053 collected
6927 passed
27 failed
99 skipped
```

The pytest footer line was not flushed by the capture. Counts are the progress marks (`.` / `F` / `s`) on the percentage lines.

Every one of these 27 nodes also fails on committed `90fdcc3` (pre-PR-BK). That comparison used a detached worktree, removed after the run. No validation edit was applied before this inventory.

Classification key: A fixture migration, B PR-BK regression, C previously unsafe expectation, D unrelated pre-existing, E brittle wording, F infrastructure.

---

## 1

```text
TEST: test_general_http_informational_social_prose_mints_no_lead
FILE: tests/test_authoritative_lead_provenance_social_prose_non_ingestion.py
ASSERTION / ERROR: trestle / coal loft absent. Current facing text is Harbor Clerk says, "I do not know enough to answer that." On 90fdcc3 the same assert fails against Harbor Clerk shakes their head. "I won't answer that about tide—not here."
OWNER: informational-prose non-ingestion / grounded refusal realization
BEHAVIOR UNDER TEST: suggestive model prose stays visible and mints no lead
PR-BK PATH INVOLVED?: the refusal sentence differs; the prose was already replaced before PR-BK
PRE-PR-BK EXPECTATION: already red
POST-PR-BK ACTUAL: still red; refusal wording changed
AUTHORITATIVE PROVENANCE PRESENT?: no
CLASSIFICATION: D
REQUIRED ACTION: document. Do not absorb refusal-catalog wording into PR-BK.
```

## 2

```text
TEST: test_by3_generate_repo_artifacts
FILE: tests/test_by3_strict_social_semantic_mutation.py
ASSERTION / ERROR: assert unknown_first_source_count == 0 (assert 1 == 0) at line 142
OWNER: BY3 semantic-mutation artifact generator
BEHAVIOR UNDER TEST: protected-replay first-source coverage
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same assert
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: leave to the mutation-attribution owner. Do not refresh baselines to go green.
```

## 3

```text
TEST: test_by4_closeout_generator_regression_guard
FILE: tests/test_by4_semantic_mutation_attribution_closeout.py
ASSERTION / ERROR: assert attribution_gap_count / unknown_first_source_count == 0 (assert 1 == 0) at line 46
OWNER: BY4 closeout generator
BEHAVIOR UNDER TEST: zero attribution gaps
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same assert
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same family as test 2 and test 4.
```

## 4

```text
TEST: test_by4_generate_repo_artifacts
FILE: tests/test_by4_semantic_mutation_attribution_closeout.py
ASSERTION / ERROR: persisted closeout unknown_first_source_count == 0 (assert 1 == 0) at line 82
OWNER: BY4 closeout generator
BEHAVIOR UNDER TEST: written artifact matches the zero-gap contract
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same assert
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Duplicate of the BY3/BY4 generator gap.
```

## 5

```text
TEST: test_bv14c_social_exchange_compat_import_guard_non_owners_route_through_authorities
FILE: tests/test_compat_import_governance.py
ASSERTION / ERROR: BV14C social-exchange compat-barrel import-guard violations
OWNER: BV14C import governance
BEHAVIOR UNDER TEST: non-owners do not import the compat barrel directly
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same guard
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Not a last_answer change.
```

## 6

```text
TEST: test_bv14c_social_exchange_compat_fi_cap_locked
FILE: tests/test_compat_import_governance.py
ASSERTION / ERROR: new social_exchange_emission importers require BV14C registry update: tests/test_grounded_refusal_topic_hook_integrity.py
OWNER: BV14C import registry
BEHAVIOR UNDER TEST: importer set matches the locked registry
PR-BK PATH INVOLVED?: no. That test file is not part of the PR-BK diff.
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same missing registry row
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same governance family as test 5.
```

## 7

```text
TEST: test_generic_to_the_guard_redirects_from_prior_stranger_target
FILE: tests/test_dialogue_interaction_establishment.py
ASSERTION / ERROR: assert False is True at line 188 (est["established"] is True)
OWNER: dialogue-target establishment
BEHAVIOR UNDER TEST: "to the guard" leaves the prior stranger and binds gate_guard
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same assert
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Not structured-fact selection.
```

## 8

```text
TEST: test_force_terminal_fallback_plus_enforcement_then_gate_retains_shipped_cs_contract
FILE: tests/test_fallback_shipped_contract_propagation.py
ASSERTION / ERROR: TypeError: 'NoneType' object is not iterable at game/gm_retry.py:1858
OWNER: shipped campaign-structure contract / retry fallback
BEHAVIOR UNDER TEST: terminal fallback keeps the shipped contract through the gate
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same TypeError
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document.
```

## 9

```text
TEST: test_response_type_failure_skips_social_response_structure_layer
FILE: tests/test_final_emission_gate_orchestration_order.py
ASSERTION / ERROR: assert None == 'response_type_contract_failed' at line 757
OWNER: final-emission gate order
BEHAVIOR UNDER TEST: a response-type failure skips the social-structure layer
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same missing skip reason
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document.
```

## 10

```text
TEST: test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability
FILE: tests/test_golden_replay_long_session.py
ASSERTION / ERROR: AssertionError: scenario_id: 'frontier_gate_social_inquiry_25_turn' (same on 90fdcc3)
OWNER: frontier-gate golden replay
BEHAVIOR UNDER TEST: 25-turn structural stability
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red; recorded in NEXT_SESSION as intended realization drift
POST-PR-BK ACTUAL: still red
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Do not refresh the protected replay baseline.
```

## 11

```text
TEST: test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting
FILE: tests/test_golden_replay_long_session.py
ASSERTION / ERROR: AssertionError: split_at: 12 at line 306 (same on 90fdcc3)
OWNER: frontier-gate golden replay resume
BEHAVIOR UNDER TEST: checkpoint counter continuity at the resume split
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: still red
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same replay family as tests 10 and 12.
```

## 12

```text
TEST: test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability
FILE: tests/test_golden_replay_long_session.py
ASSERTION / ERROR: AssertionError: scenario_id: 'frontier_gate_direct_intrusion_25_turn_diagnostic' (same on 90fdcc3)
OWNER: frontier-gate golden replay
BEHAVIOR UNDER TEST: direct-intrusion diagnostic stability
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: still red
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same replay family.
```

## 13

```text
TEST: test_cross_file_duplicate_allowlist_from_derived_full_audit
FILE: tests/test_inventory_governance.py
ASSERTION / ERROR: cross-file duplicate test name test_anti_overfitting_generic_helpers_have_no_calibration_special_case is not allowlisted (scene-exit resolution vs stay/leave social lock)
OWNER: test-inventory governance
BEHAVIOR UNDER TEST: duplicate test names are allowlisted or renamed
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same duplicate name
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same governance failure as test 14.
```

## 14

```text
TEST: test_ownership_registry_governance
FILE: tests/test_ownership_registry.py
ASSERTION / ERROR: same duplicate test name as test 13
OWNER: ownership registry
BEHAVIOR UNDER TEST: registry governance includes the duplicate-name allowlist
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same message
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Duplicate of test 13.
```

## 15

```text
TEST: test_response_policy_enforcement_question_resolution_mutation_records_reason
FILE: tests/test_response_policy_enforcement_mutation.py
ASSERTION / ERROR: assert 'Rain ticks against the gatehouse stones.' != 'Rain ticks against the gatehouse stones.' at line 262
OWNER: question-resolution enforcement
BEHAVIOR UNDER TEST: the rain sentence must be rewritten
PR-BK PATH INVOLVED?: no. Adjudication is exempt from question_resolution_rule_check. game/gm.py was not edited.
PRE-PR-BK EXPECTATION: already red on 90fdcc3; recorded since the PR-BK implementation note
POST-PR-BK ACTUAL: sentence unchanged
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Do not edit gm.py to force a rewrite.
```

## 16

```text
TEST: test_contract_topic_progress_commit_receives_post_enforcement_reply_text
FILE: tests/test_response_policy_enforcement_mutation.py
ASSERTION / ERROR: same rain-sentence inequality at line 648
OWNER: topic-progress commit contract
BEHAVIOR UNDER TEST: post-enforcement reply text differs from the rain sentence
PR-BK PATH INVOLVED?: the commit wrapper now forwards resolution and world. The failing assert is still the unchanged rain sentence.
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same sentence
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same exemption as test 15.
```

## 17

```text
TEST: test_emission_quality_anyone_else_talk_to_manifests_preserves_redirect_not_fragment
FILE: tests/test_social_emission_quality.py
ASSERTION / ERROR: assert 'topic_pressure:last_answer' == 'topic_pressure:last_answer:redirect' at line 166
OWNER: strict-social emission source label
BEHAVIOR UNDER TEST: a harbor-clerk redirect is labeled :redirect
PR-BK PATH INVOLVED?: the fixture now carries authored_topic provenance. Path A selects the line as a full fact, so the source is topic_pressure:last_answer. The label mismatch was already red on 90fdcc3, before that provenance line existed, and has been recorded since PR-AO.
PRE-PR-BK EXPECTATION: source label :redirect, already receiving topic_pressure:last_answer
POST-PR-BK ACTUAL: same source mismatch
AUTHORITATIVE PROVENANCE PRESENT?: yes, authored_topic, added during implementation. It did not create this failure.
CLASSIFICATION: D
REQUIRED ACTION: document. Do not retitle the source or strip provenance to chase :redirect.
```

## 18

```text
TEST: test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere
FILE: tests/test_social_exchange_emission.py
ASSERTION / ERROR: assert 'the tattered man' in 'the square stays hushed except for the scrape of boots on wet stone.' at line 1525
OWNER: passive scene pressure / figure leads
BEHAVIOR UNDER TEST: a recent suspicious figure replaces weak atmosphere
PR-BK PATH INVOLVED?: no. This is recent_contextual_leads figure copy, not last_answer selection.
PRE-PR-BK EXPECTATION: already red on 90fdcc3; recorded since PR-AU / PR-AV
POST-PR-BK ACTUAL: atmosphere line, no figure
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same figure-atmosphere family as tests 25–27.
```

## 19

```text
TEST: test_transcript_runner_asks_about_aldric_followup_stays_runner
FILE: tests/test_social_speaker_grounding.py
ASSERTION / ERROR: assert None is True at line 454 (resolution.success)
OWNER: speaker grounding
BEHAVIOR UNDER TEST: Aldric follow-up stays on Tavern Runner and success is true
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3; recorded in PR-BJ
POST-PR-BK ACTUAL: success is None
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Not a speaker-label repair.
```

## 20

```text
TEST: test_transcript_where_is_aldric_repeated_followups_stay_runner
FILE: tests/test_social_speaker_grounding.py
ASSERTION / ERROR: assert None is True at line 519 (resolution.success)
OWNER: speaker grounding
BEHAVIOR UNDER TEST: repeated Aldric follow-ups stay on the runner
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3; recorded in PR-BJ
POST-PR-BK ACTUAL: success is None
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same pair as test 19.
```

## 21

```text
TEST: test_transcript_anyone_chat_open_solicitation_not_dead_air
FILE: tests/test_transcript_gauntlet_actor_addressing.py
ASSERTION / ERROR: guard captain / tavern runner absent. Facing text is The guard says, "I do not know enough to answer that." The same string fails this assert on 90fdcc3.
OWNER: open-social solicitation recovery
BEHAVIOR UNDER TEST: "Anyone up for a chat?" recovers a named responder
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same guard-fallback sentence
AUTHORITATIVE PROVENANCE PRESENT?: no
CLASSIFICATION: D
REQUIRED ACTION: document. The empty "The guard" label stays deferred residue.
```

## 22

```text
TEST: test_action_and_chat_investigate_both_mark_runtime_discovery_memory
FILE: tests/test_turn_pipeline_shared.py
ASSERTION / ERROR: assert 'inv-desk' in (['desk']) at line 201
OWNER: investigate discovery memory
BEHAVIOR UNDER TEST: action and chat both record the desk discovery id
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: stored id is desk
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document.
```

## 23

```text
TEST: test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback
FILE: tests/test_turn_pipeline_shared.py
ASSERTION / ERROR: assert False is True at line 428
OWNER: dialogue response-type contract
BEHAVIOR UNDER TEST: a direct NPC question keeps the dialogue contract and an unknown fallback
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: same assert
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document.
```

## 24

```text
TEST: test_chat_single_wait_in_tense_scene_forces_interaction_pressure
FILE: tests/test_turn_pipeline_shared.py
ASSERTION / ERROR: assert False via _assert_concrete_pressure at line 74
OWNER: passive interaction pressure
BEHAVIOR UNDER TEST: one wait in a tense scene forces a concrete pressure line
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: pressure phrase absent
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same pressure family as test 25.
```

## 25

```text
TEST: test_chat_repeated_passive_actions_do_not_stall_into_atmosphere
FILE: tests/test_turn_pipeline_shared.py
ASSERTION / ERROR: assert False via _assert_concrete_pressure at line 74
OWNER: passive interaction pressure
BEHAVIOR UNDER TEST: repeated passive actions do not stall into atmosphere
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: pressure phrase absent
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same helper failure as test 24.
```

## 26

```text
TEST: test_chat_passive_scene_prefers_already_introduced_suspicious_figure
FILE: tests/test_turn_pipeline_shared.py
ASSERTION / ERROR: 'the tattered man' absent from the hushed-square atmosphere line at line 782
OWNER: passive scene pressure
BEHAVIOR UNDER TEST: an introduced suspicious figure is preferred over atmosphere
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: atmosphere line
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same figure residue as tests 18 and 27.
```

## 27

```text
TEST: test_chat_passive_wait_with_recent_suspicious_figure_replaces_weak_atmosphere
FILE: tests/test_turn_pipeline_shared.py
ASSERTION / ERROR: 'the tattered man' absent from the hushed-square atmosphere line at line 817
OWNER: passive scene pressure
BEHAVIOR UNDER TEST: a wait with a recent suspicious figure replaces weak atmosphere
PR-BK PATH INVOLVED?: no
PRE-PR-BK EXPECTATION: already red on 90fdcc3
POST-PR-BK ACTUAL: atmosphere line
AUTHORITATIVE PROVENANCE PRESENT?: n/a
CLASSIFICATION: D
REQUIRED ACTION: document. Same figure residue as tests 18 and 26.
```

---

## Counts

| Class | Count |
| --- | --- |
| A | 0 |
| B | 0 |
| C | 0 |
| D | 27 |
| E | 0 |
| F | 0 |

Semantic duplicates inside D: BY3/BY4 generator gap (2–4), BV14C import registry (5–6), frontier-gate golden replay (10–12), duplicate test-name governance (13–14), rain-sentence adjudication exemption (15–16), Aldric `success is None` (19–20), concrete-pressure helper (24–25), tattered-man atmosphere (18, 26, 27).
