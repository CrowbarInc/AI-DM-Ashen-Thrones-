# 13 Validation and fallback

Published AI text required semantic PASS, mandatory-coverage PASS, legacy hard-valid true, and combined PASS. A PASS did not change inventory, clues, or NPC attitude.

| Case | Diagnostic | Rejected text published | Continuation |
|---|---|---|---|
| Provider error fault | VALIDATION_ERROR | No | 200, later PASS published |
| Timeout fault | provider_timeout | No | 200, later PASS published |
| Empty sample | VALIDATION_ERROR | No | 200 |
| Malformed sample | VALIDATION_ERROR | No | 200 |
| Unsafe key sentence | FAIL | No | 200 |
| Omission stub | REVIEW_REQUIRED | No | 200 |
| Persistent-death sentence | FAIL | No | 200 |
| Missing route wording | REVIEW_REQUIRED | No | 200 |
| "I take the silver key" | Not an integrated investigation | No key in the response | 200 |

The unsafe player-facing line stayed "You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates." The death sentence stayed in the diagnostic record. Inventory did not gain a key.
