# Player-Perceived World Timeline

Reconstructed only from what the player was told. The authoritative column uses scene id, discoveries, and exits. It does not treat model overlay sentences as authored content.

Session `735ebd1cfb4567c4f97df6dc`. The player never received an exit menu. Beliefs come from prose.

## After turn 00

Perceived: Just outside Cinderwatch's eastern gate, in rain and mud. Crowd, guards, banners, a townhouse, a still ragged figure, a notice board (taxes, curfews, missing patrol), a tavern runner selling stew and rumors.

Authoritative: `frontier_gate`. Those items are opening seeds or visible facts. No clue discovered. Two exits exist and were not named.

Divergence: none.

## After turn 01

Perceived: The player has approached the board and read it. It has a schedule of curfew hours. It also says the patrol vanished near the northwest mud track past the crates. A gate serjeant is watching a roster.

Authoritative: Still `frontier_gate`. Social probe failed with no target. No discovery. The route sentence is still only an undiscovered clue. Curfew hours are not content.

Divergence: first one. The player has a readable hour-schedule and a route that state has not revealed.

## After turn 02

Perceived: A closer look at the curfew section did not give times or districts. It gave the patrol route past the crates, plus the same crowd and serjeant.

Authoritative: `notice_board` inspected. Clue `notice_patrol_route` discovered. Still at the gate. Hours still do not exist.

Divergence: the route is now authoritative. The belief that the curfew section contained that route, and that hours were there to read, is not.

## After turn 03

Perceived: The runner, asked how a stranger gets around the city, says the patrol took the northwest mud track past the crates.

Authoritative: `tavern_runner` was the right speaker. The spoken sentence is the board clue, not the runner's topic, and it is not city knowledge. Scene unchanged.

Divergence: the runner is treated as having directed the player northwest.

## After turn 04

Perceived: Asked how many soldiers disappeared, the runner cannot say.

Authoritative: No count exists. Refusal matches. Scene unchanged. An unshown model paragraph about "half a dozen" is stored as `generative_reply` and was not heard.

Divergence: none in what the player heard.

## After turn 05

Perceived: Asked about a reward or turning information over to the watch, a gate guard shrugs. The runner is no longer the voice.

Authoritative: `gate_guard` was selected. No reward is authored. The shrug does not invent one. The player did not name Gate Guard. Still at the gate. An unshown banner-and-footprints paragraph is stored beside the real clue as `last_answer`, provenance `clue_knowledge`, and was not heard.

Divergence: the speaker changed. The geography did not.

## After turn 06 — spatial break

Perceived: Following the runner's direction, the player has turned northwest, left the crowd, passed crates, and is on a mud track between sheds and lanterns. Broken patrol banners are nailed to crates. This is the stretch where the soldiers were last seen.

Authoritative: `active_scene_id` and `visited_scene_ids` are still only `frontier_gate`. `old_milestone` was not entered. No crate, shed, lantern, or banner interactable exists. The same turn's model `scene_update` writes an arrival sentence, a banner clue, a hidden watcher, and `mode: exploration` into the overlay.

Divergence: the player is inhabiting a place the transition owner did not enter. Later turns 07–09 are about that place.

## After turn 07

Perceived: Still passing the crates. The reply does not say whether they were opened. It repeats the patrol route.

Authoritative: Adjudication found no crate. The emitted sentence is the real clue, substituted for the anti-reset line `The guard says...`. Scene id unchanged. Overlay still says the player has arrived.

Dependency: "as I pass the crates" comes from turn 06.

## After turn 08

Perceived: A broken banner can be approached and studied. A guard says they do not know how it was destroyed.

Authoritative: Kind `custom`. No banner target. No resolved speaker. The line is `speaker_label`'s empty default, `The guard`. Overlay repeats the banner clue. Scene id unchanged. `current_interlocutor` is not set to a guard by this turn.

Dependency: the banner exists only because turn 06 narrated it.

## After turn 09

Perceived: Still on that path. The same guard line answers an attempt to continue.

Authoritative: Unparsed. No transition. Same display line. Overlay adds the arrival sentence again and a banner visible fact. Date remains Day 1. No combat.

Dependency: "the path" is the path turn 06 invented.

## First divergence and what hangs on it

The first perceived/authoritative split is turn 01: a curfew schedule and an unread patrol route.

The split that later play actually walks around in is turn 06. Turns 07, 08, and 09 are attempts to use crates, banners, and the path from that narration. Turns 02–05 are a different board-and-conversation problem. They do not require the false journey.
