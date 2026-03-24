from game.campaign_state import create_fresh_combat_state, create_fresh_session_document


def default_campaign():
    return {
        "title": "Ashen Thrones",
        "premise": "A grimdark political sandbox where fractured powers, ancient mysteries, and ruthless factions compete for dominance in a dangerous world. Survival, intrigue, and warfare shape the rise or destruction of new rulers.",
        "tone": "grimdark political intrigue with survival and horror elements",
        "player_character": "Galinor",
        "character_role": "A wandering wizard seeking to establish a stronghold of power in a fractured and hostile world.",
        "starting_context": "Galinor arrives in a struggling frontier city at the edge of rival territories, where noble houses scheme, criminal syndicates rule the shadows, and whispers spread of an abandoned fortress nearby—one said to rest atop ancient and dangerous magical foundations.",
        "character_secret": {
            "title": "The Betrayed Loyalist",
            "description": "Galinor once served faithfully as a trusted court mage. When he uncovered evidence of a conspiracy and brought it to his ruler, he discovered the conspiracy was orchestrated by the throne itself.",
            "implications": [
                "The ruler cannot allow Galinor to live if his identity becomes known.",
                "Agents of the throne may hunt surviving witnesses of the purge.",
                "Galinor holds knowledge capable of destabilizing an entire realm."
            ],
            "hidden_truth": "The conspiracy may have involved forbidden magic or darker powers influencing the throne."
        },
        "world_pressures": [
            "Rival noble houses competing for territory and influence.",
            "Religious orders attempting to control or suppress dangerous magic.",
            "Criminal syndicates dominating trade, smuggling, and urban power.",
            "Invading armies exploiting political instability.",
            "Eldritch cults pursuing forgotten rituals and ancient powers."
        ],
        "environmental_threats": [
            "harsh seasons and famine",
            "disease and plague",
            "dangerous wilderness and monsters",
            "war-torn lands and refugee movements",
            "cursed ruins and unstable magical sites"
        ],
        "magic_style": "rare, mysterious, feared, and poorly understood. Magical knowledge is fragmented and often tied to ancient relics, ruins, or forbidden traditions.",
        "campaign_structure": "A sandbox political world where the player gradually establishes a locus of power through alliances, conquest, intrigue, and exploration.",
        "long_term_goals": [
            "Establish a fortified stronghold",
            "Build a network of agents and allies",
            "Acquire rare magical knowledge",
            "Manipulate regional politics"
        ],
        "gm_guidance": [
            "Emphasize faction intrigue, shifting alliances, and fragile political balance.",
            "Make survival and logistics meaningful pressures.",
            "Allow the player to acquire land, followers, and influence gradually.",
            "Let the world react dynamically as the player's influence grows."
        ]
    }


def default_character():
    return {
        "id": "galinor",
        "name": "Galinor",
        "class": "Wizard",
        "level": 1,
        "ancestry": "Human",
        "hp": {"current": 8, "max": 8, "nonlethal": 0},
        "ac": {"normal": 12, "touch": 12, "flat_footed": 10},
        "initiative_bonus": 2,
        "speed": 30,
        "ability_scores": {"str": 10, "dex": 14, "con": 12, "int": 18, "wis": 12, "cha": 10},
        "saves": {"fort": 1, "ref": 2, "will": 3},
        "bab": 0,
        "cmb": 0,
        "cmd": 12,
        "skills": {"knowledge_arcana": 8, "spellcraft": 8, "perception": 4, "sense_motive": 4, "stealth": 4, "diplomacy": 4, "intimidate": 2, "bluff": 2},
        "attacks": [
            {
                "id": "quarterstaff",
                "name": "Quarterstaff",
                "attack_bonus": 0,
                "damage": {"dice_count": 1, "dice_sides": 6, "bonus": 0, "type": "bludgeoning"},
                "type": "melee"
            },
            {
                "id": "crossbow",
                "name": "Light Crossbow",
                "attack_bonus": 2,
                "damage": {"dice_count": 1, "dice_sides": 8, "bonus": 0, "type": "piercing"},
                "type": "ranged"
            }
        ],
        "conditions": [],
        "inventory": [{"id": "spellbook", "name": "Spellbook", "quantity": 1, "usable": False}],
        "spells": {
            "prepared": [
                {"id": "daze", "name": "Daze", "cast": False, "level": 0},
                {"id": "detect_magic", "name": "Detect Magic", "cast": False, "level": 0},
                {"id": "magic_missile", "name": "Magic Missile", "cast": False, "level": 1},
                {"id": "shield", "name": "Shield", "cast": False, "level": 1}
            ],
            "slots": {"0": 3, "1": 1}
        },
        "notes": "Default template character. Import a custom sheet for campaign play."
    }


def default_session():
    """Bootstrap file default for missing ``session.json`` — delegates to runtime factory."""
    return create_fresh_session_document()


def default_world():
    return {
        "settlements": [
            {
                "id": "cinderwatch",
                "name": "Cinderwatch",
                "type": "frontier_city",
                "tags": ["frontier", "trade", "unstable"],
                "status": "strained",
                "notes": "A frontier city balanced between noble influence, criminal pressure, and military necessity."
            }
        ],
        "factions": [
            {"id": "house_verevin", "name": "House Verevin", "type": "noble_house", "attitude": "wary", "influence": 3, "pressure": 2, "goal": "Expand territory", "current_plan": "Gathering influence", "agenda_progress": 0, "assets": []},
            {"id": "ash_cowl", "name": "The Ash Cowl", "type": "criminal_syndicate", "attitude": "opportunistic", "influence": 3, "pressure": 2, "goal": "Control black market", "current_plan": "Establishing smuggling routes", "agenda_progress": 0, "assets": []},
            {"id": "ordo_pyric", "name": "Ordo Pyric", "type": "religious_order", "attitude": "suspicious", "influence": 2, "pressure": 1, "goal": "Suppress dangerous magic", "current_plan": "Watching newcomers", "agenda_progress": 0, "assets": []}
        ],
        "assets": [],
        "projects": [],
        "world_flags": [],
        "event_log": [],
        "inference_rules": [],
        "clues": {},
        "npcs": [
            {"id": "guard_captain", "name": "Guard Captain", "location": "frontier_gate", "role": "guard", "affiliation": "cinderwatch", "disposition": "neutral", "current_agenda": "patrol_gate", "availability": "available", "topics": [{"id": "patrol", "text": "A patrol went missing near the old milestone."}]},
            {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate", "role": "informant", "affiliation": "ash_cowl", "disposition": "friendly", "current_agenda": "sell_rumors", "availability": "available", "topics": [{"id": "stew", "text": "Hot stew and rumors for coin."}]},
        ],
        "world_state": {
            "flags": {},
            "counters": {},
            "clocks": {}
        }
    }


def default_combat():
    """Bootstrap file default for missing ``combat.json`` — delegates to runtime factory."""
    return create_fresh_combat_state()


def default_scene(scene_id: str = 'frontier_gate'):
    if scene_id == 'frontier_gate':
        return {
            "scene": {
                "id": "frontier_gate",
                "location": "Cinderwatch Gate District",
                "summary": "Rain spatters soot-dark stone as caravans and refugees choke the eastern gate. Guards watch the crowd with the brittle discipline of men who expect trouble, while old banners rot above the walls.",
                "mode": "social",
                "visible_facts": [
                    "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate.",
                    "Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in.",
                    "A notice board lists new taxes, curfews, and a posted warning about a missing patrol.",
                    "A tavern runner shouts offers of hot stew and paid rumor.",
                    "A well-appointed townhouse overlooking the square flies noble colors—a quiet contrast to the mud and clamor.",
                    "One figure in threadbare clothes stands uncannily still, gaze flicking to packs and faces more than the gate queue.",
                ],
                "journal_seed_facts": [
                    "You arrive at Cinderwatch's eastern gate in cold rain, under frayed banners.",
                    "The approach is jammed with refugees, wagons, and travelers; guards watch with hard, tired discipline.",
                    "A notice board announces new taxes and curfews, and names a missing patrol.",
                    "A tavern runner is hawking hot stew and rumor for coin.",
                    "A ragged stranger hangs back, watching the crowd more than the queue.",
                ],
                "discoverable_clues": [
                    "Closer reading or asking around may reveal who posted the missing-patrol notice—some name the town crier Lirael.",
                    "Paying the runner (or sharing a drink) might buy a clearer line on where the patrol was last seen; talk drifts toward the old trading crossroads.",
                    "A well-dressed watcher near the gate studies newcomers more than stamped papers; tailing or testing him could show whether he's House, guild, or hired eyes.",
                    "A rough customer in the press keeps sizing up travelers with unusual packs or sigils—enough attention might expose black-market or arcane interest.",
                    "The threadbare watcher starts at certain whistles and hand-signs; shadowing him could reveal who he's meeting.",
                    "When guards look away, voices near the tavern door drop to hurried talk about the patrol and whether the inn is safe after dark.",
                    "Stall-holders and porters mutter about needing extra hands—busy season, nerves, or both.",
                    "Job chalkboards and runner gossip hint at merchants hiring short-term muscle for the next caravan push.",
                ],
                "hidden_facts": [
                    "An agent of a noble house is watching new arrivals from the square's edge.",
                    "A contact tied to the Ash Cowl smuggling web is scouting the crowd for arcane talent.",
                    "The threadbare watcher is waiting on a coordinated signal from someone already past the checkpoint.",
                    "A spotter above the lane is matching faces to a written list paid for in silver.",
                ],
                "exits": [
                    {"label": "Enter Cinderwatch", "target_scene_id": "market_quarter"},
                    {"label": "Follow the missing patrol rumor", "target_scene_id": "old_milestone"}
                ],
                "enemies": [],
                "actions": []
            }
        }
    if scene_id == 'market_quarter':
        return {
            "scene": {
                "id": "market_quarter",
                "location": "Cinderwatch Market Quarter",
                "summary": "Canvases snap in the wind over a market built from salvage timber and old stone. Mercenaries, pilgrims, smugglers, and hungry townsfolk bargain under armed watch.",
                "mode": "exploration",
                "visible_facts": ["A moneylender's house flies noble colors.", "Rumors of an abandoned fortress circulate among caravan guards."],
                "discoverable_clues": [],
                "hidden_facts": ["The Ash Cowl taxes black-market arcane goods here."],
                "exits": [
                    {"label": "Return to the Gate", "target_scene_id": "frontier_gate"},
                    {"label": "Seek the fortress trail", "target_scene_id": "old_milestone"}
                ],
                "enemies": [],
                "actions": []
            }
        }
    return {
        "scene": {
            "id": scene_id,
            "location": "Unnamed Scene",
            "summary": "A blank scene awaiting definition.",
            "mode": "exploration",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
            "actions": []
        }
    }


def default_conditions():
    return {
        "dazed": {"name": "Dazed", "kind": "condition", "default_effects": {"no_actions": True}},
        "shaken": {"name": "Shaken", "kind": "condition", "default_effects": {"attack_penalty": 2, "save_penalty": 2, "skill_penalty": 2}},
        "sickened": {"name": "Sickened", "kind": "condition", "default_effects": {"attack_penalty": 2, "damage_penalty": 2, "save_penalty": 2, "skill_penalty": 2}},
        "blinded": {"name": "Blinded", "kind": "condition", "default_effects": {"ac_penalty": 2, "lose_dex_to_ac": True}},
        "stunned": {"name": "Stunned", "kind": "condition", "default_effects": {"no_actions": True, "ac_penalty": 2, "lose_dex_to_ac": True}},
        "risky_strike": {"name": "Risky Strike", "kind": "combat_toggle", "default_effects": {}},
        "defensive_stance": {"name": "Defensive Stance", "kind": "combat_toggle", "default_effects": {}},
        "shield": {"name": "Shield", "kind": "spell_effect", "default_effects": {"ac_bonus": 4}}
    }
