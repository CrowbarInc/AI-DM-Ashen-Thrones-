# 12 PLAYER FACING PUBLICATION

Three consecutive supported actions through FastAPI TestClient HTTP `/api/chat?ui_mode=player`: notice discovery, barrel investigation, notice repeat. HTTP statuses 200 throughout. Two initial actions use the live experimental provider. The third injects provider timeout and publishes deterministic repeat fallback in the same session.

One AI response published; two fallbacks. Initial discovery fallback contains the mandatory route; the unrelated barrel publication does not unnecessarily repeat it. Third action confirms session continuity and fallback availability. This exercises the application HTTP route in process; no external TCP listener or browser was used. Evidence: `gameplay_actions.json`, `state_snapshots.json`.
