# PR-CK selection contract

Live provider calls: 0.

The ordinary semantic owner remains the resolution contract. `select_ordinary_resolver` chooses one existing resolver. It does not resolve the turn. No new authority owner and no second semantic classifier were added.

## Categories

| Category | Owner | Resolver |
| --- | --- | --- |
| A. Explicitly addressed social interaction, including talk, tell, persuade, quoted speech, and an informational question to an interlocutor | Existing social subject | social |
| B. Unaddressed question about the world, such as place, presence, or feasibility | Existing adjudication subject | adjudication |
| C. Exploration or investigation, including search and investigate | Existing inspect/perceive operation and perception subject | exploration |
| D. Passive waiting or silent observation | Existing generation resolver, which may run the existing passive-wait stage | generation |
| E. Ordinary narration or a descriptive request, including "describe" and deictic "where are we" | Existing generation resolver | generation |
| F. Explicit world action | Existing act operation and world-action subject | world_action |
| G. Ambiguous or unmatched input | Unresolved operation, unspecified subject, no invented addressee | generation |

A grammatical question is not automatically social. "Where is the harbor?" stays place adjudication. "Where are we?" is scene orientation, not an addressed NPC question. "Where are you?" stays social.

An active scene focus or an active interlocutor does not convert a wait, a description, or an unmatched statement into dialogue. A follow-up that continues an addressed conversation, such as "Who attacked them?" while an interlocutor is established, stays social and keeps that addressee.

Consequential world actions stay on world-action handling. Compound search-plus-ask stays unresolved. A quoted social line that only mentions investigating later stays social.

`gm_resolution_decision` still decides which facts narration may carry. This change does not authorize a new fact, an unauthored clue, or a consequential wait event.
