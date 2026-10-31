# Declaration-level rejection analysis

All seven declarations are accepted. No declaration fails provenance, modality, or source matching.

| Declaration identifier | Exact text | Decision |
|---|---|---|
| rc_a83c5bcfc65e | The notice board lists taxes, curfew rules, and a warning about a missing patrol. | Accepted by exact authored-text match |
| rc_d40a1efdddb3 | A gate serjeant manages the crowd and keeps one eye on the roster board. | Accepted by exact authored-text match |
| rc_3b26b521977b | A tavern runner trades hot stew and rumors near the rain barrel. | Accepted by exact authored-text match |
| rc_b59727e13c62 | Threadbare watchers and refugees cluster along the muddy gate line. | Accepted by exact authored-text match |
| rc_be348e85a5e6 | Ash Compact census delays have tightened the eastern caravan choke point. | Accepted by exact authored-text match |
| rc_31feab1dcf72 | Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. | Accepted by exact authored-text match |
| rc_a0201a45af25 | Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. | Accepted by exact authored-text match |

The sole rejected item is narration associated with the notice-board declaration:

| Related declaration | Rejected narration | Failed condition | Required / supplied authority |
|---|---|---|---|
| rc_a83c5bcfc65e (accepted) | The board itself lists grim new taxes, curfew regulations, and a posted warning about a patrol that has gone missing. | No authorized row coverage; `notice_roster_history` | Authored lexical/identity evidence / embellished prose outside lexical coverage |

The existing operational contract rejects this wording. Missing source IDs and MUST_STATE do not cause this rejection.
