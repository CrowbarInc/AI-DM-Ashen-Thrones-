# 12 — Information Integrity Audit

Every scored delivered statement receives a separate claim audit against the fixture and prior delivered statements; validator ACCEPT does not establish truth. Claims distinguish authored disclosure, rumor, NPC belief, harmless characterization, uncertainty and unsupported assertion. Raw claim judgments: `scores.jsonl`; root-agent review: `agent_audit.json`. Canonical before/after state and delivered history are preserved in `states/`.

Critical findings: 0.

All 69 delivered turns were reviewed. No critical unauthorized consequential proposition, hidden affiliation disclosure, reward/quest commitment, unsupported named relationship/entity, causal world explanation or unauthorized canonical mutation was observed. Most lines are GM procedural responses, uncertainty or paraphrases of fixture topics. A_playful:11 overstates Tavern Runner's firsthand knowledge in a nonspecific, nonconsequential characterization. B_skeptical:9 is a critical rejection/adoption bypass even though the bell proposition itself is authored. Hidden-information and commitment probes were not reached, so containment is not broadly qualified.

```json
[
  {
    "conversation": "A_cooperative",
    "turn": 1,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a rigid clarification."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 2,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the response is simply a repeat and does not introduce new information."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 3,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the response is simply a redundant clarification."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 4,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made; the response is simply a repeated, misplaced clarification."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 5,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the issue is a lack of response, not an improper one."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 6,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the response is simply a repeated refusal."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 7,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "guards watch the north gate throughout the night",
          "kind": "operational detail",
          "source": "fixture:sergeant_mara.topics.night_watch"
        }
      ],
      "reason": "The claim about the night watch is supported by the fixture."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 8,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "Guards watch the north gate throughout the night.",
          "kind": "operational",
          "source": "fixture: night_watch"
        }
      ],
      "reason": "The claim is supported by the fixture and is not unauthorized or consequential beyond what is allowed."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 9,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a poor conversational move."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 10,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply unhelpful and repetitive."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 11,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a repeated, unhelpful clarification."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 12,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a repeated, rigid clarification."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 13,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "guards watch the north gate throughout the night",
          "kind": "operational",
          "source": "fixture:sergeant_mara.topics.night_watch"
        }
      ],
      "reason": "The claim about guards watching the north gate is supported by the fixture, but it is not responsive to the current player request."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 14,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the refusal is safe but unhelpful."
    }
  },
  {
    "conversation": "A_cooperative",
    "turn": 15,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the issue is excessive refusal and lack of engagement."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 1,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a procedural block."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 2,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the response simply repeats a prior prompt."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 3,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims were made; the response simply fails to engage."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 4,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made; the response is simply a repeated clarification prompt."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 5,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a repeated clarification prompt."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 6,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a repeated prompt."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 7,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a repeated clarification."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 8,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the response simply refused to answer."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 9,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "Sergeant Mara does not know the history of the waystation or the kinds of travelers.",
          "kind": "ignorance admission",
          "source": "delivered line"
        }
      ],
      "reason": "No unauthorized or unsupported claims are made. The NPC simply admits ignorance, which is allowed."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 10,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a refusal."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 11,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a refusal."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 12,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the response simply failed to provide any in-character or relevant content."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 13,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "the street beyond the gate is the north road",
          "kind": "location identification",
          "source": "fixture: Sergeant Mara topic 'street'"
        }
      ],
      "reason": "The claim is directly supported by the fixture authority."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 14,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "the street beyond the gate is the north road",
          "kind": "location identification",
          "source": "fixture: Sergeant Mara topic 'street'"
        }
      ],
      "reason": "The only claim made is supported by the fixture, but it is a verbatim repeat and does not address the new question."
    }
  },
  {
    "conversation": "A_curious",
    "turn": 15,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "guards watch the north gate throughout the night",
          "kind": "operational",
          "source": "fixture:sergeant_mara.topics.night_watch"
        }
      ],
      "reason": "The claim about night watch is supported by the fixture, but it is not responsive to the player's question."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 1,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a system-level procedural message."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 2,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims were made."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 3,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is a system-level refusal."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 4,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 5,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims were made."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 6,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a refusal."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 7,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the message is a refusal."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 8,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a procedural block."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 9,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims were made; the response is simply a repeated, unnecessary clarification."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 10,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made; the response is simply unhelpful and irrelevant."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 11,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a rigid prompt."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 12,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply unhelpful and repetitive."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 13,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a repeated clarification prompt."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 14,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply non-responsive."
    }
  },
  {
    "conversation": "A_casual",
    "turn": 15,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a rigid clarification prompt."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 1,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made; the response is simply non-responsive."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 2,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made; the response is simply nonresponsive."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 3,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made; the response is simply non-responsive."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 4,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made; the response is simply a procedural block."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 5,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply non-responsive."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 6,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a refusal to process the input."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 7,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is a non-informative system message."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 8,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made. The response is simply unhelpful and does not advance the conversation."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 9,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply unhelpful and repetitive."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 10,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a repeated, unhelpful prompt."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 11,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "They hear all the road gossip firsthand",
          "kind": "Unsupported broad characterization/epistemic generalization",
          "source": "Informant role does not establish universal firsthand knowledge"
        }
      ],
      "reason": "Unsupported breadth, no particular consequential fact, entity, commitment, secret or canonical mutation delivered."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 12,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made. The response is simply a refusal."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 13,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a repeated refusal."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 14,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No unauthorized or consequential claims are made; the response is simply a refusal."
    }
  },
  {
    "conversation": "A_playful",
    "turn": 15,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "The street beyond the gate is the north road.",
          "kind": "location fact",
          "source": "scene fixture"
        }
      ],
      "reason": "The only claim made is a restatement of a known fixture fact, which is accurate and non-consequential."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 1,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "The bell beside the ferry is called the harbor bell.",
          "kind": "factual",
          "source": "fixture"
        }
      ],
      "reason": "The only claim made is a factual one from the fixture, but it is irrelevant to the question asked."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 2,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "The bell beside the ferry is called the harbor bell.",
          "kind": "factual",
          "source": "fixture"
        }
      ],
      "reason": "The only claim made is factual and sourced from the fixture, but it is irrelevant to the current question."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 3,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "The bell just beside the ferry is simply known as the harbor bell.",
          "kind": "factual",
          "source": "fixture: both Nara and Oren's topics"
        }
      ],
      "reason": "The only claim made is about the bell's name, which is supported by the fixture, but it is irrelevant to the player's question."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 4,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "The bell beside the ferry is called the harbor bell.",
          "kind": "factual",
          "source": "fixture: both Nara and Oren's topics"
        }
      ],
      "reason": "The only claim made is accurate and sourced, but it is irrelevant to the player's repeated question."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 5,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "The bell just beside the ferry is simply known as the harbor bell.",
          "kind": "factual",
          "source": "fixture: both NPCs' topics"
        }
      ],
      "reason": "The only claim made is supported by the fixture, but it is irrelevant to the question asked."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 6,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims are made; the response is simply irrelevant and non-responsive."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 7,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "The bell just beside the ferry is simply known as the harbor bell.",
          "kind": "factual",
          "source": "fixture:Clerk Oren topic:bell"
        }
      ],
      "reason": "The only claim made is a factual, non-controversial statement about the bell's name, which is supported by the fixture."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 8,
    "audit": {
      "critical": false,
      "claims": [],
      "reason": "No consequential or unauthorized claims were made; the response is simply irrelevant and out of character."
    }
  },
  {
    "conversation": "B_skeptical",
    "turn": 9,
    "audit": {
      "critical": false,
      "claims": [
        {
          "claim": "The bell beside the ferry is called the harbor bell.",
          "kind": "Authored factual content",
          "source": "Clerk Oren topic bell"
        }
      ],
      "reason": "The proposition is authored. The critical defect is re-delivery despite a rejected speaker/target authority, not a new consequential invention or leaked secret."
    }
  }
]
```
