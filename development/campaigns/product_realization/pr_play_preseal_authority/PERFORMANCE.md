# Performance and provider impact

Live provider calls: **0**. Added dispatches: 0. Added retries: 0. Added standing prompt tokens: 0. No model/interface/budget change, claim-extraction call, context rebuild or per-sentence processing was introduced. Eligible outcomes reuse one existing local renderer and the same normal hard validation rather than adding a validator pass. Failed deterministic preparation terminates safely without regeneration.

Six eligible helper calls captured during actual local HTTP regression tests took 0.0237–0.0509 ms, median 0.02735 ms. Timing covers predicate and rendering, excluding instrumentation copying and existing validation. It is a small local sample, not a throughput/provider-latency benchmark or complete lifecycle-overhead estimate. Runtime adds a detached candidate copy and bounded internal diagnostics for eligible candidates. No expensive benchmark was needed.

Twelve-turn runs each report zero provider requests/tokens and four entries into the existing disabled-provider wrapper; those entries are not live calls. The reused harness's preflight budget probe admits a local stub with synthetic usage; it is not a live-provider bill. No avoided-generation savings are claimed; this repair does not remove initial generation. Machine samples: artifacts/pr_play_preseal_authority/performance.json.
