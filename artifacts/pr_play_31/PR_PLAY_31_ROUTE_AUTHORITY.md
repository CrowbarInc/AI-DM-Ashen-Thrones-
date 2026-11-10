# PR-PLAY-31 route authority
Source: frontier_gate, destination: old_milestone, label: “Follow the missing patrol rumor”. The authored row has no explicit ID; the existing affordance convention derives `leave_for_follow_the_missing_patrol_rumor`. The adapter copies the current authored row; it adds no graph edge or canon mutation. Both authored rows and adapted views are in authored_route_evidence.json.

Visibility: public legacy exit (no hidden/visible restriction). Availability: no locked/accessibility restriction. Prerequisites/required discoveries/conditions: absent. Travel cost: none authored; existing ordinary turn clock advances once. The destination must still exist and be reachable through the existing bridge and scene graph.

Knowledge: the actual conversation discloses patrol_rumor and persists muddy_footprints_northwest. The existing minimum-lead mechanism separately persists minlead_exit_frontier_gate_old_milestone with the public route label. This makes the route a legitimate choice, but does not establish that it reaches the precise footprints in the rumor. No foreign-key association links the rumor clue to the exit or to milestone_mud_prints. No prose similarity or clue-ID alias authorizes automatic selection.

Original decision: NO_AUTHORIZED_ROUTE for the exact referenced destination; actionable clarification presents currently available public exits. Multiple public choices are not treated as multiple proven routes to the exact evidence. The player explicitly selecting the patrol route authorizes the control travel. Direct unambiguous authored destination + purpose selects UNIQUE_AUTHORIZED_ROUTE; ambiguous explicit destinations clarify; blocked routes refuse; unsupported references never move.

Visibility and source-scene filters exclude hidden/wrong-scene routes. Eligibility uses existing flag/clue conditions and checks locked, available, accessible, reachable and availability fields. Unknown prerequisites/required_discoveries fail closed. The bridge rechecks at execution, including after clarification. No hidden route is offered. Data files were not changed.

Clue identity: travel discovers no milestone_mud_prints. Only the separate prints examination discovers it; the original rumor entry remains intact. Neither discovery nor narration asserts that the two clues are identical or causally proven related.
