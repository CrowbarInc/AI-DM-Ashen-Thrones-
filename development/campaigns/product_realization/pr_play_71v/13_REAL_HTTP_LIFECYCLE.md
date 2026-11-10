# 13 — Real HTTP lifecycle

Both campaigns were driven through the application HTTP routes on a dedicated host. Internal resolver methods were not called and no session was seeded. The provider was the offline fixture. This is not live-provider evidence.

`artifacts/pr_play_71v/http_summary.json`:

- 31 requests.
- 17 gameplay actions.
- Mean server time 159.1 milliseconds.
- Maximum server time 545.1 milliseconds.
- Hidden exposures 0.

Campaign A, survey, id `c63a2da4460ed7eb93cf07fd`, snapshot `2026-11-06T03-53-12_3626ea0a`. Opening, notice clue, travel to Old Milestone, milestone clue, survey choice, survey follow-up, snapshot, load, and a continuation. The report flag stayed unset.

Campaign B, report, id `aada41903dcfd1fa2ccfc916`, snapshot `2026-11-06T03-53-16_dc0bd10b`. The same approach, then the report choice, return to the gate, and the watch warning. The survey flag stayed unset.

Each load restored that campaign's transcript. A duplicate action did not flip the other branch. HTTP 200 here was checked against the stored flags and the transcript, not treated as proof by itself.
