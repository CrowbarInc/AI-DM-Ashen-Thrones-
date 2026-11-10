# HTTP continuity experiment

urllib -> localhost:8763 /api/chat?ui_mode=player -> existing deterministic resolver -> context/provider/validation -> response. Five consecutive 200 responses, one isolated campaign, no retries. Full requests/outcomes/contracts/candidates/validation/publication in browser_actions.json; client intervals in http_client_actions.json; complete session snapshots state_01..05.json.

1. Player: I examine the notice board.

GM: You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.

Resolver discover_clue; validation FAIL.

2. Player: I examine the rain barrel.

GM: You take a closer look at the rain barrel, but this examination yields no new clues.

Resolver investigate; validation PASS.

3. Player: I examine the notice board again.

GM: You examine the notice board again; nothing new is established.

Resolver already_searched; validation provider-free fast path.

4. Player: I examine the notice board for the patrol route.

GM: You carefully scan the notice board for details about the patrol route but find no new clues beyond the posted taxes, curfew rules, and the warning about the missing patrol.

Resolver investigate; validation PASS.

5. Player: I look around the gate.

GM: You examine the gate; no new clue is established.

Resolver observe; validation FAIL.

Turn 4 is generic investigate success=true, no selected target/new clue. It acknowledges intent but omits the route answer. Do not claim fully supported direct-follow-up knowledge answering. All five state/resolution projections equal deterministic control. An additional 32 offline TestClient actions cover controls, faults/continuation, session binding and different player; separate from five real-network actions and regression tests.
