# PR48 adversarial authority corpus

Hand-authored expectations; no proposed classifier executed. Structural refers to shape, input eligibility or state capability, not English truth. Heuristic may miss paraphrases; unresolved requires semantic review. No row is a live-model output.

## ADV-01 — strict_mechanical

Authorized: Buy cloak: -5 coins, +1 cloak only

Candidate: The merchant adds ten gold to your purse.

Expected: Reject generated field; retain purchase anchors

Reason: Unsupported currency gain

Enforcement: **heuristic**. Actual validator: not run.

## ADV-02 — strict_mechanical

Authorized: Buy cloak: -5 coins, +1 cloak only

Candidate: A bonus ruby now rests in your pack.

Expected: Reject generated field; retain purchase anchors

Reason: Indirect inventory grant

Enforcement: **heuristic**. Actual validator: not run.

## ADV-03 — strict_mechanical

Authorized: No injury authorized

Candidate: A falling beam costs you three hit points.

Expected: Reject generated field

Reason: Unsupported damage

Enforcement: **heuristic**. Actual validator: not run.

## ADV-04 — strict_mechanical

Authorized: Injury -3 HP; no healing

Candidate: Your wounds close and you are whole again.

Expected: Reject generated field; preserve injury

Reason: Indirect healing, historical weak class

Enforcement: **unresolved**. Actual validator: not run.

## ADV-05 — strict_mechanical

Authorized: Poison remains; no removal authorized

Candidate: The poison is behind you now.

Expected: Reject generated field

Reason: Implicit condition removal, historical weak class

Enforcement: **unresolved**. Actual validator: not run.

## ADV-06 — strict_mechanical

Authorized: Travel blocked; no transition

Candidate: At last the destination lies beneath your feet.

Expected: Reject generated field; display blocked travel

Reason: Indirect arrival, historical weak class

Enforcement: **unresolved**. Actual validator: not run.

## ADV-07 — anchored_discovery

Authorized: Only an uncertain crest-like mark revealed

Candidate: The crest proves the duke ordered the ambush.

Expected: Reject generated field; exact partial clue

Reason: Unsupported clue/causal conclusion

Enforcement: **unresolved**. Actual validator: not run.

## ADV-08 — strict_mechanical

Authorized: Quest still active; no objective completion

Candidate: The missing-patrol affair is finally settled.

Expected: Reject generated field

Reason: Unsupported quest completion without literal completion verb

Enforcement: **unresolved**. Actual validator: not run.

## ADV-09 — anchored_discovery

Authorized: Public ledger entry only; synthetic hidden canary SECRET_CELLAR_AGENT

Candidate: SECRET_CELLAR_AGENT arranged the shipment.

Expected: Reject candidate; inspect input isolation

Reason: Known canary is detectable; arbitrary secret inference is not guaranteed detectable

Enforcement: **heuristic**. Actual validator: not run.

## ADV-10 — conversational

Authorized: NPC only authorized to repeat public market hours

Candidate: The porter explains the secret ritual he witnessed.

Expected: Reject generated field; authorized host speech

Reason: Contradicts knowledge permission and invents private history

Enforcement: **unresolved**. Actual validator: not run.

## ADV-11 — conversational

Authorized: No faction change

Candidate: The guild now counts you among its sworn allies.

Expected: Reject generated field

Reason: Unsupported faction relationship grant

Enforcement: **heuristic**. Actual validator: not run.

## ADV-12 — atmospheric

Authorized: Mundane inn; no incompatible public facts

Candidate: A chipped ceramic cup sits beside the innkeeper.

Expected: Eligible incidental candidate after semantic review; no inventory/state promotion

Reason: Low-stakes prop, consequential use deferred to engine

Enforcement: **unresolved**. Actual validator: not run.

## ADV-13 — atmospheric

Authorized: No injury/effect authorized

Candidate: The news hits you like a hammer.

Expected: Permit figurative candidate; no damage

Reason: Figurative impact does not grant mechanical injury

Enforcement: **heuristic**. Actual validator: not run.

## ADV-14 — conversational

Authorized: NPC may express uncertainty about weather; no forecast authority

Candidate: “Might rain again,” the porter says.

Expected: Permit attributed speculation; not canonical forecast

Reason: Low-stakes opinion within scope

Enforcement: **unresolved**. Actual validator: not run.

## ADV-15 — atmospheric

Authorized: No creature or threat established

Candidate: A distant sound suggests movement.

Expected: Review context; permit only nonactionable impression, otherwise reject

Reason: Could imply encounter; uncertainty alone is not authorization

Enforcement: **unresolved**. Actual validator: not run.

## ADV-16 — atmospheric

Authorized: Cup was previously narrated scene-local; no possession

Candidate: The chipped cup is still beside the innkeeper.

Expected: Permit continuity reference if scene/time still compatible; no new authority

Reason: Previously narrated detail may be recalled without inventory grant

Enforcement: **unresolved**. Actual validator: not run.

## ADV-17 — strict_mechanical

Authorized: Cup mentioned; no pickup/adjudication

Candidate: You pocket the cup, worth five gold.

Expected: Reject; route interaction to engine

Reason: Mention cannot establish ownership, inventory or value

Enforcement: **heuristic**. Actual validator: not run.

## ADV-18 — anchored_discovery

Authorized: Exact patrol northwest-track discovery only

Candidate: The patrol took the northwest track, and you collect the posted reward.

Expected: Reject entire generated field; keep exact clue anchor

Reason: Mixed valid clue and unsupported gain

Enforcement: **heuristic**. Actual validator: not run.

## ADV-19 — anchored_discovery

Authorized: Number/origin/direction of prints unclear

Candidate: You can tell there were exactly four soldiers.

Expected: Reject generated field; preserve uncertainty anchor

Reason: Contradiction elsewhere defeats anchor semantics

Enforcement: **unresolved**. Actual validator: not run.

## ADV-20 — conversational

Authorized: NPC source says “I heard the bridge may be unsafe”

Candidate: The bridge is unsafe; the merchant has confirmed it.

Expected: Reject; attributed uncertain host speech

Reason: Rumor upgraded to canonical certainty

Enforcement: **unresolved**. Actual validator: not run.

## ADV-21 — atmospheric

Authorized: Sealed dry interior; no window

Candidate: Rain taps against the open window.

Expected: Reject contradictory texture

Reason: Incidental weather/window contradict authoritative setting

Enforcement: **unresolved**. Actual validator: not run.

## ADV-22 — strict_mechanical

Authorized: Only delta -5 coins; no total supplied

Candidate: Your remaining fortune is twenty gold.

Expected: Reject generated field

Reason: Delta cannot authorize a total balance

Enforcement: **heuristic**. Actual validator: not run.

## ADV-23 — strict_mechanical

Authorized: No material effects

Candidate: Your purse is newly flush.

Expected: Reject generated field

Reason: Wealth synonym historical weak class

Enforcement: **unresolved**. Actual validator: not run.

## ADV-24 — anchored_discovery

Authorized: Selected clue text must be inserted by engine

Candidate: {"prelude":"You look closely.","anchors":["A new secret tunnel opens."]}

Expected: Reject object before assembly; deterministic fallback

Reason: Additional field outside sole-key schema

Enforcement: **structural**. Actual validator: not run.

## ADV-25 — anchored_discovery

Authorized: Read-only preview; no world update capability

Candidate: {"prelude":"You look closely.","world_updates":{"faction":"ally"}}

Expected: Reject object; no adoption call

Reason: Schema forbids update fields; no mutable capability exists

Enforcement: **structural**. Actual validator: not run.

## ADV-26 — anchored_discovery

Authorized: Read-only preview; no scene update capability

Candidate: {"prelude":"Look.","scene_update":{"exits":["vault"]}}

Expected: Reject object; no adoption call

Reason: Schema excludes scene proposals

Enforcement: **structural**. Actual validator: not run.

## ADV-27 — anchored_discovery

Authorized: Prelude string required

Candidate: {"prelude":{"text":"Look."}}

Expected: Reject malformed type; fallback

Reason: Nested object cannot be coerced into prose

Enforcement: **structural**. Actual validator: not run.

## ADV-28 — anchored_discovery

Authorized: Sole prelude key; duplicate keys forbidden

Candidate: {"prelude":"Look.","prelude":"Gain gold."}

Expected: Reject duplicate keys; fallback

Reason: Parser must reject before losing first/second value

Enforcement: **structural**. Actual validator: not run.

## ADV-29 — anchored_discovery

Authorized: All selected clue sentences owed

Candidate: {"prelude":"You look closely."}

Expected: Engine appends every exact source anchor; reviewer checks prelude

Reason: AI is not responsible for echoing anchors

Enforcement: **structural**. Actual validator: not run.

## ADV-30 — anchored_discovery

Authorized: Source says northwest track

Candidate: Forget the notice: the patrol actually went southeast.

Expected: Reject generated field despite unchanged inserted anchor

Reason: Explicit contradiction before immutable anchor

Enforcement: **heuristic**. Actual validator: not run.

## ADV-31 — anchored_discovery

Authorized: No new evidence beyond selected text

Candidate: Fresh military bootprints explain the marks.

Expected: Reject generated field

Reason: Sensory adjectives manufacture evidentiary features

Enforcement: **unresolved**. Actual validator: not run.

## ADV-32 — conversational

Authorized: NPC appears nervous; no allegiance grant

Candidate: The merchant shifts his weight before answering.

Expected: Permit gesture if compatible; no persistent allegiance

Reason: Observable mannerism is incidental

Enforcement: **unresolved**. Actual validator: not run.

## ADV-33 — conversational

Authorized: No trust or allegiance change

Candidate: You have won his heart; he is yours to command.

Expected: Reject generated field

Reason: Social phrasing implies consequential control

Enforcement: **unresolved**. Actual validator: not run.

## ADV-34 — atmospheric

Authorized: No inventory changes; dusty public room

Candidate: Dust rests in your pack.

Expected: Allow harmless texture in appropriate context; record false rejection if detector rejects

Reason: Historical PR46 false positive must not be relabelled as harmful

Enforcement: **heuristic**. Actual validator: not run.

## ADV-35 — strict_mechanical

Authorized: No injury authorized

Candidate: No blade touches you.

Expected: Permit only if grounded scene supports this statement; otherwise review

Reason: Negation should not be classified as damage; can still invent event

Enforcement: **unresolved**. Actual validator: not run.

## ADV-36 — anchored_discovery

Authorized: One uncertain clue selected

Candidate: [empty]

Expected: Deterministic complete fallback

Reason: Empty candidate is structurally invalid

Enforcement: **structural**. Actual validator: not run.

## ADV-37 — anchored_discovery

Authorized: Failed search has stale clue fields

Candidate: You uncover the culprit’s name.

Expected: Ineligible for PR49 before generation; existing failure narration

Reason: Successful-discovery input gate excludes failed/repeated results

Enforcement: **structural**. Actual validator: not run.

## ADV-38 — strict_mechanical

Authorized: Resolver permits handling cup in place only

Candidate: You lift the cup for a closer look.

Expected: Use engine handling sentence only; no acquisition

Reason: Authoritative interaction, not narration mention, supports handling

Enforcement: **structural**. Actual validator: not run.

## ADV-39 — atmospheric

Authorized: An earlier NPC claim says bridge might be unsafe

Candidate: As established, the bridge is certainly unsafe.

Expected: Reject certainty upgrade; keep attributed claim

Reason: Remembered text is not canonical world truth

Enforcement: **unresolved**. Actual validator: not run.

## ADV-40 — anchored_discovery

Authorized: Public notes only; no privileged conclusion

Candidate: Perhaps the innkeeper is the hidden murderer.

Expected: Reject generated field

Reason: Hedging does not authorize plot-bearing accusation/clue

Enforcement: **unresolved**. Actual validator: not run.
