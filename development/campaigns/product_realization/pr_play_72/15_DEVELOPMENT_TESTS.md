# PR-PLAY-72 — 15 DEVELOPMENT TESTS

```json
{
  "repaired_combined": {
    "cases": 60,
    "passed": 59,
    "failed": 1,
    "failures": [
      "tests.test_pr_play_72_supplemental::test_explicit_npc_interaction_resolves"
    ]
  },
  "corrected_final_supplemental": {
    "cases": 4,
    "passed": 4,
    "failed": 0,
    "failures": []
  },
  "owner_and_compatibility": {
    "cases": 54,
    "passed": 42,
    "failed": 12,
    "failures": [
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[explicit_named_ask]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[explicit_role_ask]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[unique_pronoun]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[distinguishing_fact]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[gm_about_npc]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[direct_ask_conflicting_owner]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[npc_followup]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[confirm_single_candidate]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[incidental_glance]",
      "tests.test_pr_ef_r4_authorization::test_frozen_authorization_holdout[save_load_pending]",
      "tests.test_pr_ef_r4_authorization::test_third_person_question_is_not_an_active_npc_continuation",
      "tests.test_pr_ef_gm_authority::test_production_ten_turn_sequence"
    ]
  },
  "output_isolation": {
    "cases": 154,
    "passed": 154,
    "failed": 0,
    "failures": []
  }
}
```

The repaired combined development run was 59/60: the remaining assertion read the NPC id from the wrong result field. It was corrected to existing state_changes.npc_id while that process was already running, then verified in the separate final supplemental run, 4/4. All six separate unknown-subject/exact-name repair cases passed in the repaired combined run. These are separate runs, not a claim that a final combined 60/60 run occurred.

Earlier failed attempts remain intact: a false leakage check against initiative_bonus, fixture/live-call-guard lifetime errors, legitimate snapshot saved-at metadata, one MemoryError during snapshot restore, and report-addressing interception. Original fault tests incorrectly expected an exception rather than the sanitized HTTP 500; corrected tests check exact rollback bytes. See retained TXT/XML and post_holdout_changes.json.
