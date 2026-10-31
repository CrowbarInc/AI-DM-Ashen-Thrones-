# Browser and Gameplay Extension

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

Assessment: requirements.txt has FastAPI/Uvicorn/OpenAI/Pydantic/Pytest/HTTPX,
with no Playwright/Selenium. Existing frontend tests exercise Node handlers but
do not run a rendered browser. No large browser dependency was introduced.
`tools/playtest/browser.py` defines the adapter boundary: own New/Start-once clicks,
bounded wait, visible narration/error, screenshots, API/UI agreement and close.
A future browser adapter must replace API mutation steps, not repeat them.
Current reports always show UI NOT_TESTED. Screenshots directory is reserved.

ScriptedObservation implements deterministic opening, scene observation and explicit
started-state verification, with per-step collection and stop-on-first-failure.
Dispatcher contracts also map NPC interaction/examination to existing /api/chat
and rules/movement to /api/action request bodies. No gameplay behavior is authored
by the dispatcher. Future scenarios need reviewed deterministic response/request
fixtures and extended outcome invariants. Current opening comparator is deliberately
conservative; arbitrary five-/ten-turn progression is not claimed implemented.

No live multi-turn testing, autonomous play, large scenario library, ATGB scoring,
or PR-EG integration occurred. API success does not establish UI success or
AI-DM communication quality. These limitations are explicit in result/summary/guide.
