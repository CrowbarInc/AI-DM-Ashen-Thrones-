PR-DU Failure Baseline

Observed baseline concerns before repair:
- Stored interpretation was only available through experimental replay; production chat could fall back to local generic parsing for the lantern sentence.
- Explicit OOC appearance correction could continue into normal chat processing and attempt provider narration.
- Scene transition reloaded session from disk through activate_scene and could lose same-turn in-memory fields such as turn_counter/clocks.
- Starlette TestClient hung in this Windows sandbox before route execution while creating its async portal; focused tests therefore call the production chat() entry function directly.

Baseline grouping:
- interpretation: stored PR-DR interpretation not connected to production route.
- OOC classification: explicit correction needed a non-mutating short path.
- persistence: transition reload could discard current turn session changes.
- UI/transport: TestClient environment stall unrelated to game pipeline.
