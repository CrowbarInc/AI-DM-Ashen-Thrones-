# BROWSER GAMEPLAY

{
  "status": "verified_with_limits",
  "gameplay_actions": 13,
  "branches": {
    "survey": {
      "gameplay_actions": 6,
      "persisted_after_reload": true,
      "continuation": true,
      "final_flags": {
        "patrol_survey": true,
        "patrol_survey_recorded": true
      },
      "statuses": [
        200,
        200,
        200,
        200,
        200,
        200
      ]
    },
    "report": {
      "gameplay_actions": 7,
      "persisted_after_reload": true,
      "continuation": true,
      "final_flags": {
        "patrol_report": true,
        "patrol_guards_warned": true
      },
      "statuses": [
        200,
        200,
        200,
        200,
        200,
        200,
        200
      ]
    }
  },
  "initial_attachment": "First about:blank attachment timed out; second recovered.",
  "interaction_recovery": "Report selection click dispatch timeout; AX confirmed no selection before single retry. Network confirms one committed report request.",
  "mode": "Actual existing UI; clean seeded prestarted campaigns",
  "screenshots": [
    "browser_report_choices.png",
    "browser_report_full.png",
    "browser_report_reload.png",
    "browser_survey_reload.png"
  ],
  "browser_visible_latency": null,
  "limitations": [
    "Normal New Campaign/Start Campaign and browser snapshot loading not tested.",
    "Host screenshot viewport clips normal captures. Full-page report screenshot also retained."
  ]
}

Actual existing frontend controls used. First webview attachment timed out; second recovered. Both sessions were clean prestarted isolated campaigns, resumed through the actual UI. Normal New Campaign/Start Campaign and save-slot loading were not exercised in browser. Reload and subsequent travel/investigation were exercised. Screenshots are clipped by the host viewport; AX snapshots and full network responses retain complete labels/text. Browser-visible latency not instrumented.
