# HTTP Acceptance

Script: `artifacts/pr_play_79df3/http_acceptance.py`. Result: `http_acceptance.json`. Isolated campaign data under `http_data/`. No new opening.

| Step | HTTP | Visible response | Events | Pointer | Requests |
| --- | --- | --- | --- | --- | --- |
| Examine, interpretation off | 200 | “You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.” | 1 | That sentence | 0 |
| “Good day, Gate Guard.”, interpretation on, request limit 0 | 200 | “I couldn't interpret that just now, so no gameplay action was taken.” | 1 | Unchanged | 0 |
| Reload | 200 | Pointer still the examine sentence. Turn 5. | 1 | Unchanged | 0 |
| “I step back from the notice board.”, interpretation off | 200 | Notice-board restyle sentence | 2 | Advances to that sentence | 1 |

The refusal is not among the event texts. `log_class` is `operational_refusal`. World unchanged on the refusal. Turn held at 5 until the continuation.

The continuation’s one request is the unintended live primary narration. Classification still held: the refusal added no event, and the later gameplay response added one event and moved the pointer.

Server errors, clarification, unsupported action, accepted dialogue, and grounded fallback were exercised on the same HTTP publication boundary by the development tests, not only by this four-step script.
