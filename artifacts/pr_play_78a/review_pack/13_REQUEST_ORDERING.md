# Request ordering

Chat-selected authored actions use the existing per-campaign request id. The holdout posted the completed follow-up twice under one `client_request_id`. The flag stayed true and the other branch stayed unset. Two campaigns in one store did not share a branch: a new campaign started without `patrol_survey`, then a report paraphrase set only `patrol_report`.

No new global lock was added. Simultaneous button-and-chat racing was covered by the existing ordering regression identities, which did not change. This cycle did not click an authored button during the browser campaigns.
