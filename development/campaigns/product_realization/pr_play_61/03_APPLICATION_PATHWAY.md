# 03 Application pathway

The live sequence used the FastAPI application object and `POST /api/chat?ui_mode=player`. Each request went through deterministic resolution, ordinary narration construction with provider calls disabled, the existing integrated hook, validation, and response assembly. Publication happens after session, world, and combat saves, and after the response payload is built, so narration does not write authority.

The player UI at `http://127.0.0.1:8761/` loaded the replayed session and rendered the four responses. A fifth action was typed into the chat box and sent. The input cleared, the new line appeared after the earlier lines, and the input stayed enabled.

The four live provider calls were submitted through the application route, not by typing in the browser. The browser verified rendering and a later input. Frontend rendering latency was not measured.
