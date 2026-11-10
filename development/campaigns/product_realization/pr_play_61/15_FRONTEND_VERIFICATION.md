# 15 Frontend verification

The replay session was served at `http://127.0.0.1:8761/` with provider calls disabled and the experimental flag unset.

Verified in the browser:

- Player mode opened on Cinderwatch Gate District.
- The log showed the four actions in order.
- The two passing narrations appeared as GM text.
- The two engine fallbacks appeared. The rejected provider sentences did not.
- The journal listed the route clue once.
- HP remained 8/8 and conditions remained none.
- The chat input accepted "I examine the notice board again."
- Send cleared the input, appended the player line and a GM line, and left the input enabled.
- No duplicate of the earlier four lines was added.

The fifth UI response was the ordinary disabled-provider sentence because that server was not running the experiment flag. Rendering latency was not measured. Screenshot: `artifacts/pr_play_61/frontend/player_log.png`.
