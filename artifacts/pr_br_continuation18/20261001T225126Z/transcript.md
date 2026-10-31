# PR-BR Continuation 18 focused live transcript

## T1 direct social inquiry

Intended: Ask the tavern runner whether east-lane carts are still coming through.

Player: I ask the tavern runner whether the east-lane carts are still coming through.

Contract: op=ask target=tavern_runner interlocutor=tavern_runner dimension=None

Attempt 1: "I can't say for certain if the east-lane carts are still coming through," the tavern runner replies with a shrug, his eyes scanning the mud-choked road. "From what I heard, the ash compact census has slowed things down, making that route a bit of a choke point. But as for whether the carts are still passing, that's one of those things that changes by the hour around here."

Attempt 2: none

Accepted (initial_generation): "I can't say for certain if the east-lane carts are still coming through," the tavern runner replies with a shrug, his eyes scanning the mud-choked road. "From what I heard, the ash compact census has slowed things down, making that route a bit of a choke point. But as for whether the carts are still passing, that's one of those things that changes by the hour around here."

Emitted: "I can't say for certain if the east-lane carts are still coming through," the tavern runner replies with a shrug, his eyes scanning the mud-choked road. "From what I heard, the ash compact census has slowed things down, making that route a bit of a choke point. But as for whether the carts are still passing, that's one of those things that changes by the hour around here."

exact=True regen=False attempts=1 eval=FAIL

## T2 follow-up social inquiry

Intended: Stay with the runner and ask who told him.

Player: Who told him that?

Contract: op=ask target=From what I heard, the ash compact census has slowed things down, making that route a bit of a choke point. But as for whether the carts are still passing, that interlocutor=tavern_runner dimension=source

Attempt 1: "I can't say who exactly told me that," the tavern runner answers with a shrug, eyes flicking briefly toward the rain-slicked street. "That kind of news travels in whispers and rumors, and no one I trust enough to name has been bold enough to confirm it outright. If knowing who said it could grant you any advantage, you'd do better asking around among the trade wagon drivers or the gate serjeant overseeing the rosters."

Attempt 2: none

Accepted (initial_generation): "I can't say who exactly told me that," the tavern runner answers with a shrug, eyes flicking briefly toward the rain-slicked street. "That kind of news travels in whispers and rumors, and no one I trust enough to name has been bold enough to confirm it outright. If knowing who said it could grant you any advantage, you'd do better asking around among the trade wagon drivers or the gate serjeant overseeing the rosters."

Emitted: "I can't say who exactly told me that," the tavern runner answers with a shrug, eyes flicking briefly toward the rain-slicked street. "That kind of news travels in whispers and rumors, and no one I trust enough to name has been bold enough to confirm it outright. If knowing who said it could grant you any advantage, you'd do better asking around among the trade wagon drivers or the gate serjeant overseeing the rosters."

exact=True regen=False attempts=1 eval=PASS

## T3 explicit interlocutor change

Intended: Leave the runner and ask the nearest guard about passage before the watch changes.

Player: I leave the runner and ask the nearest guard whether travelers can still pass before the watch changes.

Contract: op=act target=Gate Guard interlocutor=gate_guard dimension=content

Attempt 1: The nearest gate guard, standing watch amid the rain and shifting crowd, nods grimly at your question. "Travelers can still pass, but only until the watch changes at the third bell. After that, the gates close tight until morning," they say, voice low but firm. Despite the oppressive wet and mud, the guard’s gaze remains steady, scanning the faces lining the gate. You sense their discipline carries the weight of recent troubles; the missing patrol mentioned on the notice board adds an uneasy tension to their words.

Attempt 2: none

Accepted (initial_generation): The nearest gate guard, standing watch amid the rain and shifting crowd, nods grimly at your question. "Travelers can still pass, but only until the watch changes at the third bell. After that, the gates close tight until morning," they say, voice low but firm. Despite the oppressive wet and mud, the guard’s gaze remains steady, scanning the faces lining the gate. You sense their discipline carries the weight of recent troubles; the missing patrol mentioned on the notice board adds an uneasy tension to their words.

Emitted: The nearest gate guard, standing watch amid the rain and shifting crowd, nods grimly at your question. "Travelers can still pass, but only until the watch changes at the third bell. After that, the gates close tight until morning," they say, voice low but firm. Despite the oppressive wet and mud, the guard’s gaze remains steady, scanning the faces lining the gate. You sense their discipline carries the weight of recent troubles; the missing patrol mentioned on the notice board adds an uneasy tension to their words.

exact=True regen=False attempts=1 eval=FAIL

## T4 inspection

Intended: Read the newest posting on the notice board.

Player: I look over the notice board and read the newest posting.

Contract: op=inspect target=Notice board interlocutor=Notice board dimension=None

Attempt 1: The weather-worn notice board, nailed to the gate’s stout frame, lists recent city decrees and advisories. The latest postings include details on new taxes imposed on the outskirts, updated curfew rules requiring all to be indoors by the third bell, and a stark warning about a patrol that has gone missing. The missing patrol notice urges caution along the northwest mud track where they were last seen near some stacked crates. The board is well-thumbed and smeared with rain, yet the inked letters remain legible beneath the soggy surface.

Attempt 2: The notice board at the Cinderwatch Gate District bears the official postings: a list of recent taxes imposed by the local administration, a set of curfew rules to be observed by travelers and residents alike, and a formal warning about a patrol that has recently gone missing. The warning advises caution for those traveling near the northwest mud track beyond the crates, though further details are scarce.

Accepted (regeneration): The notice board at the Cinderwatch Gate District bears the official postings: a list of recent taxes imposed by the local administration, a set of curfew rules to be observed by travelers and residents alike, and a formal warning about a patrol that has recently gone missing. The warning advises caution for those traveling near the northwest mud track beyond the crates, though further details are scarce.

Emitted: The notice board at the Cinderwatch Gate District bears the official postings: a list of recent taxes imposed by the local administration, a set of curfew rules to be observed by travelers and residents alike, and a formal warning about a patrol that has recently gone missing. The warning advises caution for those traveling near the northwest mud track beyond the crates, though further details are scarce.

exact=True regen=True attempts=2 eval=PASS

## T5 compound action

Intended: Return to the runner with a coin and ask about the patrol.

Player: I walk back to the runner, set a coin on the counter, and ask if that buys a straight answer about the patrol.

Contract: op=act target=Tavern Runner interlocutor=tavern_runner dimension=content

Attempt 1: "I can't swear to it, but from what I heard, the patrol vanished near some muddy footprints northwest of the crates," the tavern runner admits, lowering his voice as he glances toward the rain-slicked street. "That's all the talk I caught. It doesn't sound good."

Attempt 2: none

Accepted (initial_generation): "I can't swear to it, but from what I heard, the patrol vanished near some muddy footprints northwest of the crates," the tavern runner admits, lowering his voice as he glances toward the rain-slicked street. "That's all the talk I caught. It doesn't sound good."

Emitted: "I can't swear to it, but from what I heard, the patrol vanished near some muddy footprints northwest of the crates," the tavern runner admits, lowering his voice as he glances toward the rain-slicked street. "That's all the talk I caught. It doesn't sound good."

exact=True regen=False attempts=1 eval=FAIL

## T6 ordinary control

Intended: Stay put and watch the road.

Player: I stay where I am and watch the road for a while.

Contract: op=inspect target=current scene interlocutor=None dimension=None

Attempt 1: You linger near the muddy road outside the Cinderwatch Gate District, rain pattering softly around you. The flow of wagons and travelers remains sluggish, the air thick with the scent of damp earth and fading smoke. Muddy ruts and faint, disturbed footprints mar the ground, tracing a path northwest beyond the stacked crates. Though the patrol's fate is unknown, nothing stirs along the northwest track at present, the silence only deepening the unease on your skin.

Attempt 2: You remain where you are by the gate, your eyes tracing the slick, muddy road that stretches northwest past the crates. The steady rain obscures distant shapes and sounds, while the dull roar of the crowded gate district fills the air around you. Despite the watchful gate serjeant managing the crowd and the quiet movement of weary travelers, no new signs of the missing patrol appear along the road during this time.

Accepted (regeneration): You remain where you are by the gate, your eyes tracing the slick, muddy road that stretches northwest past the crates. The steady rain obscures distant shapes and sounds, while the dull roar of the crowded gate district fills the air around you. Despite the watchful gate serjeant managing the crowd and the quiet movement of weary travelers, no new signs of the missing patrol appear along the road during this time.

Emitted: You remain where you are by the gate, your eyes tracing the slick, muddy road that stretches northwest past the crates. The steady rain obscures distant shapes and sounds, while the dull roar of the crowded gate district fills the air around you. Despite the watchful gate serjeant managing the crowd and the quiet movement of weary travelers, no new signs of the missing patrol appear along the road during this time.

exact=True regen=True attempts=2 eval=FAIL
