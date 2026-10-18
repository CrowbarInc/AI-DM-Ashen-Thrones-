# PR-CR Before/After Replay

PR-CQ patrol replay input:

Player: `Captain, what do you know about the missing patrol?`

Selected topic: `patrol`

Canonical authored answer: `A patrol went missing near the old milestone.`

Recorded first provider draft:

`The guard captain's eyes harden beneath the sodden hood as they reply, "We've had no word from a patrol assigned near the old milestone. They were tasked with scouting the old trading crossroads, a crucial route. They simply didn't return, and a warning was posted on the notice board here. It's troubling-no sign of them, no messages. The town's on edge, and rumors spread fast, though few facts yet." Their gaze flicks over the muddied crowd, expression a mix of concern and the weary resolve of duty.`

Before:

- first draft hard-invalid;
- rejection reason: `unauthorized_resolution_decision_fact`;
- regeneration callback invoked;
- retry count: 1;
- second provider draft also hard-invalid;
- final seal used canonical projection after retry;
- accepted provenance label: `safe_nonresolution`;
- acceptance reason: `authored_answer_projection`.

After:

- first draft hard-invalid;
- rejection reason preserved;
- early authored projection eligible;
- projected line: `Guard Captain mutters, "Word is, a patrol went missing near the old milestone."`
- projected line hard-valid;
- regeneration callback not invoked;
- retry count: 0;
- accepted provenance: `authored_answer_projection`;
- acceptance reason: `authored_answer_projection`.

