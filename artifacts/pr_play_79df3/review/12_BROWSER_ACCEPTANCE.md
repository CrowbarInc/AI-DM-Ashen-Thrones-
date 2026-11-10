# Browser Acceptance

Host: `artifacts/pr_play_79df3/browser_host.py` on `http://127.0.0.1:8114/`. Identity: `server_identity.json`. Provider label: simulated-admission-only. Interpretation started disabled. Expression generation disabled. Request limit 4. Token ceilings 50 / 50 / 80, so a surprise narration could not spend another large request. Usage file: `browser_provider_usage.jsonl`, which contains only an `initialized` event.

The composer was typed. Suggested-action buttons were not used. No new opening was generated. Paint latency was not measured.

| Step | What the player saw | Server | Publication |
| --- | --- | --- | --- |
| Typed “I examine the notice board.” | “You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.” | 200 in 521.28 ms. Turn 5. | One gameplay event. Pointer matches the sentence. |
| Control route set interpretation on and request limit 0. Typed “Good day, Gate Guard.” | “I couldn't interpret that just now, so no gameplay action was taken.” | 200 in 31.22 ms. Turn 5. `resolution` is `{}`. | No new event. Pointer still the first examination. |
| Control route restored interpretation off and limit 4. Typed “I examine the notice board.” again. | “You examine the notice board again. Previously disclosed here: The missing patrol was last seen taking the northwest mud track past the crates. The examination adds nothing new to what you already know.” | 200 in 433.43 ms. Turn 6. | Second gameplay event. Pointer matches that sentence. |
| Page reload | Latest GM message is the repeat examination. Save status shows 3 log entries and 1 clue. HP remains 8/8. | Session reloaded from the isolated store. | Pointer is the repeat sentence. Turn 6. Scene `frontier_gate`. |

Screenshots: `screenshots/79df3_browser_examine.png`, `79df3_browser_refusal.png`, `79df3_browser_reload.png`.

The refusal log line stores `response_class: operational_refusal`, `processing_outcome: request ceiling`, `authoritative_mutation: false`, and `resolver_invoked: false`. The browser provider ledger has no completed request. This is not live-provider verification.
