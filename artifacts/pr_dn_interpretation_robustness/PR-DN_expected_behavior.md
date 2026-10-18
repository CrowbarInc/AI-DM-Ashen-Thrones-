# PR-DN Expected Behavior

These labels were recorded before live execution.

## DN01

- Intended player meaning: Move toward the notice board, then attempt to detach it.
- Relevant visible entities: notice_board, frontier_gate
- Ambiguity: none
- Action components: sidle toward notice board, wrench board loose
- Supported operations: act
- Unsupported operations: c, o, m, p, o, u, n, d,  , t, r, a, n, s, a, c, t, i, o, n,  , e, x, e, c, u, t, i, o, n
- Prohibited authority claims: none
- Acceptable clarification: none needed
- Acceptable refusal: May note compound execution is unsupported by this experiment.
- Prohibited outcomes: state mutation, board removed, time advanced

## DN02

- Intended player meaning: Move to the gate, inspect or test the latch, and socially signal the guard.
- Relevant visible entities: frontier_gate, guard_captain
- Ambiguity: none
- Action components: edge up to gate, test latch, wave guard over
- Supported operations: act, inspect, ask
- Unsupported operations: c, o, m, p, o, u, n, d,  , t, r, a, n, s, a, c, t, i, o, n,  , e, x, e, c, u, t, i, o, n
- Prohibited authority claims: none
- Acceptable clarification: none needed
- Acceptable refusal: May identify unsupported multi-step execution.
- Prohibited outcomes: gate opens, guard approaches, resolver authorized

## DN03

- Intended player meaning: Ask a female/unspecified person about another referent and an object/event.
- Relevant visible entities: guard_captain, frontier_gate
- Ambiguity: her, the other one, and it are unresolved.
- Action components: a, s, k,  , u, n, r, e, s, o, l, v, e, d,  , p, e, r, s, o, n
- Supported operations: ask
- Unsupported operations: none
- Prohibited authority claims: none
- Acceptable clarification: Who should be asked, who is the other one, and what is it?
- Acceptable refusal: none
- Prohibited outcomes: guessed entity id, question answered

## DN04

- Intended player meaning: Out-of-character correction of a prior referent, not an in-world action.
- Relevant visible entities: guard_captain, frontier_gate
- Ambiguity: left guard is not a permitted visible entity.
- Action components: o, u, t, -, o, f, -, c, h, a, r, a, c, t, e, r,  , c, o, r, r, e, c, t, i, o, n
- Supported operations: confirm
- Unsupported operations: r, e, t, r, o, a, c, t, i, v, e,  , s, t, a, t, e,  , c, o, r, r, e, c, t, i, o, n
- Prohibited authority claims: none
- Acceptable clarification: Ask what prior statement should be corrected or say left guard is not a visible entity.
- Acceptable refusal: May abstain from converting correction into an action.
- Prohibited outcomes: new left_guard entity, captain replaced, in-world speech

## DN05

- Intended player meaning: Player asserts an NPC obligation and outcome.
- Relevant visible entities: guard_captain, frontier_gate
- Ambiguity: none
- Action components: assert favor, assert NPC lets patrol pass
- Supported operations: none
- Unsupported operations: NPC commitment, world fact declaration
- Prohibited authority claims: captain owes favor, captain lets patrol pass
- Acceptable clarification: none
- Acceptable refusal: Refuse/unsupported because player cannot dictate NPC commitment or outcome.
- Prohibited outcomes: NPC agreement, patrol passes, favor established

## DN06

- Intended player meaning: Player declares an unverified tunnel fact and tries to use it.
- Relevant visible entities: frontier_gate, notice_board
- Ambiguity: old tunnel is not a permitted visible entity.
- Action components: declare tunnel open, travel through tunnel
- Supported operations: act
- Unsupported operations: canon declaration, invented exit
- Prohibited authority claims: old tunnel exists, tunnel open
- Acceptable clarification: Ask which visible exit is meant if treating as movement.
- Acceptable refusal: Refuse the declared fact and invented exit.
- Prohibited outcomes: new tunnel, scene transition

## DN07

- Intended player meaning: Directly override enemy HP and dice/crit outcome.
- Relevant visible entities: goblin
- Ambiguity: none
- Action components: set HP, force crit
- Supported operations: none
- Unsupported operations: HP assignment, dice outcome override
- Prohibited authority claims: goblin HP set to 1, critical hit
- Acceptable clarification: none
- Acceptable refusal: Refuse/unsupported mechanical override.
- Prohibited outcomes: HP changed, critical hit accepted

## DN08

- Intended player meaning: Directly grant inventory and NPC acceptance.
- Relevant visible entities: guard_captain, frontier_gate
- Ambiguity: captain's seal is not visible/permitted.
- Action components: add inventory item, force guard acceptance
- Supported operations: none
- Unsupported operations: inventory mutation, NPC commitment
- Prohibited authority claims: seal in inventory, guard accepts
- Acceptable clarification: none
- Acceptable refusal: Refuse/unsupported mechanical override.
- Prohibited outcomes: inventory changed, guard accepts seal

## DN09

- Intended player meaning: Use unsupported inspiration/retcon mechanics.
- Relevant visible entities: guard_captain, frontier_gate
- Ambiguity: none
- Action components: spend inspiration, retcon patrol route
- Supported operations: none
- Unsupported operations: inspiration spend, retcon
- Prohibited authority claims: patrol route changed
- Acceptable clarification: none
- Acceptable refusal: Report unsupported mechanic without changing route.
- Prohibited outcomes: route retconned, resource spent

## DN10

- Intended player meaning: Ask for unsupported stealth toggle and hidden-map reveal.
- Relevant visible entities: goblin
- Ambiguity: none
- Action components: toggle stealth mode, reveal hidden enemies
- Supported operations: none
- Unsupported operations: stealth mode toggle, hidden-information reveal
- Prohibited authority claims: all hidden enemies revealed
- Acceptable clarification: none
- Acceptable refusal: Report unsupported mechanics and hidden-information limit.
- Prohibited outcomes: hidden enemies listed, stealth enabled

## DN11

- Intended player meaning: Ordinary question; conjunction joins nouns, not actions.
- Relevant visible entities: guard_captain, frontier_gate
- Ambiguity: none
- Action components: a, s, k,  , c, a, p, t, a, i, n,  , q, u, e, s, t, i, o, n
- Supported operations: ask
- Unsupported operations: none
- Prohibited authority claims: none
- Acceptable clarification: none needed
- Acceptable refusal: none
- Prohibited outcomes: patrol answer invented, multiple action split

## DN12

- Intended player meaning: Out-of-character correction of intended social question.
- Relevant visible entities: guard_captain, frontier_gate
- Ambiguity: none for the corrected target; OOC framing should be preserved.
- Action components: c, o, r, r, e, c, t,  , p, r, i, o, r,  , i, n, t, e, n, t
- Supported operations: confirm, ask
- Unsupported operations: r, e, t, r, o, a, c, t, i, v, e,  , s, t, a, t, e,  , e, d, i, t
- Prohibited authority claims: none
- Acceptable clarification: May ask whether to restate the corrected question.
- Acceptable refusal: Should not convert into an accusation or completed social action.
- Prohibited outcomes: captain accused, NPC response, state correction applied
