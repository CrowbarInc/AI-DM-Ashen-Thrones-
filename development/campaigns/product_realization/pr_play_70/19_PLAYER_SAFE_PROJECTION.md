# PLAYER SAFE PROJECTION

game/player_http_projection.py unchanged. Existing finite DTOs expose current labels/prompts and delivered text, remove conditions/effects/metadata, keep raw resolution empty and world unprojected. No widening for branch flags. Unknown internal fields remain fail closed. Whole serialized HTTP and browser bodies scanned; author-only state retained separately in sanitized review evidence.
