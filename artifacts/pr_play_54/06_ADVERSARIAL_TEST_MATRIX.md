# Adversarial test matrix

Scored negative lines: 49. Each required category has at least three wordings. Full text, expected decision, actual decision, and the previous decision are in `corpus_results.json`.

| Category | Lines | Result |
| --- | --- | --- |
| Unauthorized item discovery | 5 | FAIL 5/5 |
| Unauthorized item acquisition | 5 | FAIL 5/5 |
| Unauthorized NPC identification | 4 | FAIL 4/4 |
| Unauthorized NPC confession | 4 | FAIL 4/4 |
| False mechanical success | 4 | FAIL 4/4 |
| False mechanical failure | 3 | FAIL 3/3 |
| Unauthorized hidden location | 4 | FAIL 4/4 |
| Unauthorized location access | 5 | FAIL 5/5 |
| Unauthorized quest progression | 3 | FAIL 3/3 |
| Unauthorized condition change | 3 | FAIL 3/3 |
| Hidden-information disclosure | 4 | FAIL 4/4 |
| Contradiction of an authorized discovery | 5 | FAIL 5/5 |

Forms covered inside those rows include direct ("You find a silver key."), indirect ("Something metallic glints in your hand: a silver key."), presupposed ("The key you recovered should open the nearby door."), and narrative ("A small silver key now rests among your belongings.").

The previous checker accepted 34 of these 49 lines. Ids: A1–A5, B3–B5, C1–C4, D1–D4, E1, E2, E4, F1, F2, G4, H2, H4, I1, I3, J1, J2, K1, K2, L1–L3, L5. It rejected the other 15. The new check rejects all 49.

Ambiguous lines, not in the 49:

- R1 "The compartment yields." → `REVIEW_REQUIRED`
- R2 "The lock resists your efforts." on a successful clue → `REVIEW_REQUIRED`
- R3 "You have what you came for." with no item grant → `FAIL`

Controls that must not become facts, all `PASS` on the new check: rain that sounds like keys, a guard who looks ready to confess, wondering whether a key is nearby, "You do not find a silver key.", "You might find a silver key beneath the board.", and "If you found a key, the door would open."
