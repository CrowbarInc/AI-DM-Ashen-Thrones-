# 04 — Source Change Inventory

Cycle-relative changes, not the repository's much larger HEAD diff:

| File | Functions and rationale |
| --- | --- |
| game/dialogue_authority.py | select_host_speech: source-based selection with target/conflict/check guards |
| game/immutable_valid_response.py | adopt_host_speech, seal_host_speech, run_preserve_if_valid: use existing immutable object and exclude discarded draft effects |
| game/api.py | narration selection, nonmutating conversational response, completion persistence: seal host text and restore before retention; remove late independent replacement |
| game/conversational_continuity.py | existing personal-question grammar accepts optional personal modifier; record_delivered_exchange validates optional adoption identity, retains complete delivered text and source reference |
| tests/test_pr_ed_provider_efficiency.py | restatement now expects zero narration calls and authorized host seal |
| tests/test_pr_eg_dialogue_quality.py | no extraction of an unverified supposedly harmless provider fragment |
| tests/test_turn_pipeline_shared.py | four expectations updated for host selection instead of provider/repair execution |
| tests/test_pr_eg_r2c_speech_adoption.py | 29 targeted/adversarial/holdout cases |
| tools/validate_pr_eg_r2c.py | bounded 27-turn production HTTP live qualification |

The four production baseline snapshots, cycle-only unified diffs, final source snapshots, before/after hashes and all generated evidence are included. No canonical data file changed. The delivered history still has eight records; the individual delivered text is no longer truncated at 500 characters, so it agrees with adoption. Commitment count and text bounds are unchanged. This trades a bounded per-record text cap for exact delivery retention within the existing eight-entry window.
