# Manual review — PR-BR Continuation 26 live session

Session `artifacts/pr_br_continuation26/live/20261003T134953Z`. Four completed turns. No repair and no rerun.

| Turn | Judgment | Why |
| --- | --- | --- |
| 1 | PASS | The player reads the notice, then asks the tavern runner. The contract subject is `social` and the resolver is social. The runner answers about the patrol. The notice clause does not become the operation. |
| 2 | PASS | The player asks the runner about stew and shelter. Subject stays `social`. The runner answers in character and does not emit a place-existence line. The later glance does not steal the turn. |
| 3 | FAIL | The player approaches the lone figure and speaks a quoted question that also mentions shelter. The contract operation is `ask`, but `resolution_subject` is `place_location`. The player sees "No nearby shelter is currently established in this scene." Addressed speech was read as a place query. |
| 4 | FAIL | The player line ends with "I ask if they have any more details..." The contract text window keeps the earlier "Shelter?" / tavern sentence and drops that ask. Subject is again `place_location`. The player sees another place-existence line. |

Manual result: 2 / 4 PASS. The required live bar was at least 3 / 4.
