# Performance

Milestone: `pr_play_object_instance_identity`. Date: 2026-11-09.

Validation scans the single inventory O(N); detached staging/copy and existing JSON write O(character bytes). No full-world scans, history logs, prompts, model calls or retries. UUID4 allocation is random; validation/eligibility are deterministic. Existing IDs never regenerate. Normal gameplay incurs no new identity calls.

Local 30-sample, 100-row microbenchmark (not gameplay throughput): new assignment median 2.279 ms; repeat 1.187 ms. Existing save median 2.171 ms vs identity-bearing save 1.855 ms; noisy sequential measurements do not establish speedup/slowdown. Serialized bytes 18323 → 18637 (+314 bytes for one promoted row). Raw samples summary in performance.json. Provider calls/token increase 0.
