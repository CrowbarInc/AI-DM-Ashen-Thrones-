# 06 — Failed new-campaign rollback

Injected failures during identifier creation, metadata persistence, session creation, session persistence, opening initialization, registration, response generation, a transient Windows replace, and a permanent replace all rolled the runtime files back to their pre-call bytes.

After each injected failure:

- The previous campaign did not remain marked as a second active campaign.
- No new campaign id was left active.
- No unrelated campaign directory was deleted.
- A following ordinary new campaign and start succeeded.

Retained temporary names that the storage helper removes are not treated as orphaned campaigns. A failure that happens before durable commit is returned as a failed request, not as a started campaign.

`test_new_campaign_failure_restores_prior_runtime` and `test_opening_persistence_failure_does_not_publish_start` passed in the isolated rerun.
