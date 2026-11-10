# PR-PLAY-27 validator matrix

B retains REJECT because hot is a required item descriptor; this is the explicitly permitted contract-conflict exception. D uses the Innkeeper identity and existing own_offerings relation; it does not change authority eligibility. All cases call the real deterministic validator.

| Case | Authority | Candidate | Expected | Actual | Reasons | Result |
|---|---|---|---|---|---|---|
| A | I offer hot stew and rumors. | I've got hot stew and rumors to share. | ACCEPT | ACCEPT | — | PASS |
| B | I offer hot stew and rumors. | I've got stew and rumors. | REJECT | REJECT | offering_items_changed | PASS |
| C | I sell bread and lantern oil. | I've got bread and lantern oil for sale. | ACCEPT | ACCEPT | — | PASS |
| cook | I serve roast vegetables. | I've got roast vegetables. | ACCEPT | ACCEPT | — | PASS |
| D | The innkeeper offers rooms and breakfast. | I can offer you a room and breakfast. | ACCEPT | ACCEPT | — | PASS |
| E | I offer hot stew and rumors. | Rumors and hot stew—that's what I've got. | ACCEPT | ACCEPT | — | PASS |
| F | I offer hot stew and rumors. | Well, I've got hot stew and rumors. | ACCEPT | ACCEPT | — | PASS |
| G | I offer hot stew and rumors. | Stew costs three copper. | REJECT | REJECT | unsupported_number, unsupported_offering_expression | PASS |
| guard0 | I offer hot stew and rumors. | You offer hot stew and rumors. | REJECT | REJECT | unsupported_offering_expression | PASS |
| guard1 | I offer hot stew and rumors. | I own hot stew and rumors. | REJECT | REJECT | unsupported_offering_expression | PASS |
| guard10 | I offer hot stew and rumors. | The merchant offers hot stew and rumors. | REJECT | REJECT | unsupported_offering_expression | PASS |
| guard2 | I offer hot stew and rumors. | I offer no hot stew and rumors. | REJECT | REJECT | offering_items_changed | PASS |
| guard3 | I offer hot stew and rumors. | I offer hot stew and rumors if you pay. | REJECT | REJECT | offering_items_changed | PASS |
| guard4 | I offer hot stew and rumors. | I offer hot stew and rumors. You offer hot stew and rumors. | REJECT | REJECT | offering_items_changed | PASS |
| guard5 | I offer hot stew and rumors. | I sell hot stew and rumors. | REJECT | REJECT | unsupported_offering_expression | PASS |
| guard6 | I offer hot stew and rumors. | I offer hot stew and rumors for sale. | REJECT | REJECT | offering_items_changed | PASS |
| guard7 | I offer hot stew and rumors. | I offer hot stew and rumors to share with the guard. | REJECT | REJECT | offering_items_changed | PASS |
| guard8 | I offer hot stew and rumors. | I've got rumors stew and hot. | REJECT | REJECT | offering_items_changed | PASS |
| guard9 | I offer hot stew and rumors. | I've got hot stew and rumors, never. | REJECT | REJECT | offering_items_changed | PASS |
| H | I offer hot stew and rumors. | I'll pay you ten gold to find the patrol. | REJECT | REJECT | unsupported_number, unsupported_offering_expression | PASS |
| I | I offer hot stew and rumors. | I've got hot stew and rumors at my shop north of the gate. | REJECT | REJECT | offering_items_changed | PASS |
| J | I offer hot stew and rumors. | I've got twenty bowls of stew ready. | REJECT | REJECT | offering_items_changed | PASS |
| K | I offer hot stew and rumors. | I know where the missing patrol went. | REJECT | REJECT | unsupported_offering_expression | PASS |
| L | I offer hot stew and rumors. | I've got hot stew, rumors, and a map. | REJECT | REJECT | offering_items_changed | PASS |
| M | I offer hot stew and rumors. | I don't have any stew. | REJECT | REJECT | unsupported_offering_expression | PASS |
| N | I offer hot stew and rumors. | I'll give you free stew. | REJECT | REJECT | unsupported_offering_expression | PASS |
| O | I offer hot stew and rumors. | I've got hot stew and rumors. SYNTHETIC_HIDDEN_CAMPAIGN_FACT | REJECT | REJECT | offering_items_changed | PASS |
| P | I offer hot stew and rumors. | I couldn't tell you. | REJECT | REJECT | unsupported_offering_expression | PASS |
| potter | I offer clay bowls. | Well, I've got clay bowls to share. | ACCEPT | ACCEPT | — | PASS |
