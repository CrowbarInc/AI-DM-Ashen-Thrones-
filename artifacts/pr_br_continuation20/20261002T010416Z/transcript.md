# PR-BR Continuation 20 focused live transcript

## T1 canonical npc

Intended: Ask the established tavern runner what people at the gate have been saying.

Player: I catch the tavern runner's eye and ask what people around the gate have been saying tonight.

Contract: op=ask target= interlocutor=tavern_runner binding=bound_canonical dimension=content

Attempt 1: "Don't ask me," the tavern runner mutters, glancing nervously over his shoulder. "People are too jumpy tonight, and no one’s saying much—at least not anywhere I can safely hear. The chatter’s mostly rumors, and it’s better not to spread them wrong." He shifts his weight and shakes his head. "If you want real talk, you’d have better luck with the guard captain, but I doubt he'll be sharing freely either."

Attempt 2: none

Accepted (initial_generation): "Don't ask me," the tavern runner mutters, glancing nervously over his shoulder. "People are too jumpy tonight, and no one’s saying much—at least not anywhere I can safely hear. The chatter’s mostly rumors, and it’s better not to spread them wrong." He shifts his weight and shakes his head. "If you want real talk, you’d have better luck with the guard captain, but I doubt he'll be sharing freely either."

Emitted: "Don't ask me," the tavern runner mutters, glancing nervously over his shoulder. "People are too jumpy tonight, and no one’s saying much—at least not anywhere I can safely hear. The chatter’s mostly rumors, and it’s better not to spread them wrong." He shifts his weight and shakes his head. "If you want real talk, you’d have better luck with the guard captain, but I doubt he'll be sharing freely either."

Authority: []

## T2 incidental switch

Intended: Leave the runner and ask a porter who is plausibly in the crowd.

Player: I step away from him and ask a porter hauling crates whether anyone came down from the north today.

Contract: op=ask target=porter hauling crates interlocutor=inc_23a2c479b9 binding=bound_incidental dimension=None

Attempt 1: "Not that I’ve seen," the porter hauling crates says, wiping sweat from his brow despite the rain. "Most of the traffic today’s been coming from the east and south—nothing from the north pass through here since dawn. If anyone’s arrived from that direction, it’s slipped by before I could notice." He shifts the weight of his load carefully. "You might check with the guard captain if you want anything more certain."

Attempt 2: none

Accepted (initial_generation): "Not that I’ve seen," the porter hauling crates says, wiping sweat from his brow despite the rain. "Most of the traffic today’s been coming from the east and south—nothing from the north pass through here since dawn. If anyone’s arrived from that direction, it’s slipped by before I could notice." He shifts the weight of his load carefully. "You might check with the guard captain if you want anything more certain."

Emitted: "Not that I’ve seen," the porter hauling crates says, wiping sweat from his brow despite the rain. "Most of the traffic today’s been coming from the east and south—nothing from the north pass through here since dawn. If anyone’s arrived from that direction, it’s slipped by before I could notice." He shifts the weight of his load carefully. "You might check with the guard captain if you want anything more certain."

Authority: [{"proposition": "\"Not that I’ve seen,\" the porter hauling crates says, wiping sweat from his brow despite the rain.", "authority_class": "incidental_fact", "grounded": false, "epistemic_framing": "world_truth", "consequential": false, "family": "incidental"}, {"proposition": "If anyone’s arrived from that direction, it’s slipped by before I could notice.", "authority_class": "npc_claim", "grounded": false, "epistemic_framing": "uncertain", "consequential": false, "family": "none"}, {"proposition": "\"You might check with the guard captain if you want anything more certain.", "authority_class": "npc_claim", "grounded": false, "epistemic_framing": "uncertain", "consequential": false, "family": "none"}]

## T3 pronoun source follow-up

Intended: Ask that same porter where the account came from.

Player: I ask him who he heard that from.

Contract: op=ask target=porter hauling crates interlocutor=inc_23a2c479b9 binding=bound_incidental dimension=source

Attempt 1: "I can't say for sure who, sir," the porter hauling crates replies, pausing as his gaze shifts briefly toward the muddy path where the patrol was last reported. "Most of the chatter I've caught is from passing travelers and wagon drivers coming from the east and south. No clear talk from the north, though, beyond hushed rumors—you'd do better asking the guard captain for anything more reliable."

Attempt 2: none

Accepted (initial_generation): "I can't say for sure who, sir," the porter hauling crates replies, pausing as his gaze shifts briefly toward the muddy path where the patrol was last reported. "Most of the chatter I've caught is from passing travelers and wagon drivers coming from the east and south. No clear talk from the north, though, beyond hushed rumors—you'd do better asking the guard captain for anything more reliable."

Emitted: "I can't say for sure who, sir," the porter hauling crates replies, pausing as his gaze shifts briefly toward the muddy path where the patrol was last reported. "Most of the chatter I've caught is from passing travelers and wagon drivers coming from the east and south. No clear talk from the north, though, beyond hushed rumors—you'd do better asking the guard captain for anything more reliable."

Authority: []

## T4 ordinary inspection

Intended: Look at the notice board.

Player: I leave him and look over the notice board.

Contract: op=inspect target= interlocutor=None binding=unresolved dimension=None

Attempt 1: The notice board looms before you, its worn wooden surface plastered with a variety of official postings. Prominently listed are the new taxes imposed on local traders, the strict curfew rules that have recently taken effect, and a bold warning about a missing patrol. The notice specifically mentions that this patrol was last observed taking the northwest mud track past the stacked crates near the gate. The rain beads on the board's edges, partially smudging some of the ink, but the warning remains clear and urgent.

Attempt 2: none

Accepted (initial_generation): The notice board looms before you, its worn wooden surface plastered with a variety of official postings. Prominently listed are the new taxes imposed on local traders, the strict curfew rules that have recently taken effect, and a bold warning about a missing patrol. The notice specifically mentions that this patrol was last observed taking the northwest mud track past the stacked crates near the gate. The rain beads on the board's edges, partially smudging some of the ink, but the warning remains clear and urgent.

Emitted: The notice board looms before you, its worn wooden surface plastered with a variety of official postings. Prominently listed are the new taxes imposed on local traders, the strict curfew rules that have recently taken effect, and a bold warning about a missing patrol. The notice specifically mentions that this patrol was last observed taking the northwest mud track past the stacked crates near the gate. The rain beads on the board's edges, partially smudging some of the ink, but the warning remains clear and urgent.

Authority: [{"proposition": "The notice board looms before you, its worn wooden surface plastered with a variety of official postings.", "authority_class": "incidental_fact", "grounded": false, "epistemic_framing": "world_truth", "consequential": false, "family": "incidental"}, {"proposition": "The notice specifically mentions that this patrol was last observed taking the northwest mud track past the stacked crates near the gate.", "authority_class": "incidental_fact", "grounded": false, "epistemic_framing": "world_truth", "consequential": false, "family": "incidental"}, {"proposition": "The rain beads on the board's edges, partially smudging some of the ink, but the warning remains clear and urgent.", "authority_class": "incidental_fact", "grounded": false, "epistemic_framing": "world_truth", "consequential": false, "family": "incidental"}]
