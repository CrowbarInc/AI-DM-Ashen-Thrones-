# PR-PLAY-72V — REAL HTTP GAMEPLAY

Both normal real TCP campaigns, with no developer-only state seeding:

```json
{
  "campaigns": [
    {
      "branch": "survey",
      "identity": "7df40c1d94c9da3c3c367e65",
      "snapshot_id": "2026-11-07T02-26-41_808668e0",
      "followup_flag": "patrol_survey_recorded",
      "information": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear. The missing patrol was last seen taking the northwest mud track past the crates. The northwest mud track reaches an old milestone beyond the gate. The mud around the marker is churned; any trail beyond it is unclear. You commit to surveying the ground beyond the milestone yourself. Reporting to the watch is no longer your response to this discovery. You can now record the limits of your survey here. You record your survey: the overlapping prints remain inconclusive. Your survey is now recorded; you have not warned the watch. You can return to the gate or continue investigating here.",
      "resumed": true,
      "natural_followup": true,
      "transcript_restored": true
    },
    {
      "branch": "report",
      "identity": "651a521bc32ccae4ee6b0093",
      "snapshot_id": "2026-11-07T02-29-01_f8b85441",
      "followup_flag": "patrol_guards_warned",
      "information": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear. Follow the missing patrol rumor The patrol route changed after the Ash Compact census choke worsened. The missing patrol was last seen taking the northwest mud track past the crates. Cold rain needles Cinderwatch's eastern gate under frayed banners. The approach is jammed with refugees, wagons, and travelers; guards watch with hard, tired discipline. A notice board announces new taxes and curfews, and names a missing patrol. A tavern runner is hawking hot stew and rumor for coin. A ragged stranger hangs back, watching the crowd more than the queue. You commit to bringing the uncertain trail to the watch instead of conducting a private survey. Return to Cinderwatch Gate to give your report. The watch receives your report that the patrol trail becomes unclear at the milestone. The watch has now been warned; no private survey was conducted. You can continue your inquiry at the gate or return to the milestone. You have no established report of further guard activity.",
      "resumed": true,
      "natural_followup": true,
      "transcript_restored": true
    }
  ],
  "requests": 48,
  "mean_http_ms": 1769.549712499914,
  "median_http_ms": 1805.628450063523,
  "max_http_ms": 5754.814599989913,
  "provider_requests": 0,
  "provider_tokens": 0,
  "hidden_exposures": 0,
  "stage_timings": "Server function durations captured through ContextVar middleware; HTTP total measured separately. Replay interpretation is labeled separately."
}
```

Original text, captured interpretation (not only replay), mapping, resolver, authority snapshots, publication, persistence and per-request timing are in http_traces.json/http_network.jsonl. Final runs add the repaired retrospective questions and hidden-camp refusal in both branches. Earlier HTTP attempts remain: one probe had not actually examined the same target; another wrongly expected a single-object contextual reference to clarify. Neither is silently counted as a product pass.
