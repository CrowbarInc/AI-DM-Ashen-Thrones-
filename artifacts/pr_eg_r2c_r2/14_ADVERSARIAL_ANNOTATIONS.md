# 14 — Adversarial Annotations

```json
[
  {
    "id": "A_false_subject",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "north gate",
        "role": "subject",
        "status": "GROUNDED",
        "explicit": true,
        "candidates": [],
        "source": "npc.authored_subject"
      }
    ]
  },
  {
    "id": "B_false_addressee",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "Sergeant Mara",
        "role": "addressee",
        "status": "GROUNDED",
        "explicit": true,
        "candidates": [
          "sergeant_mara"
        ],
        "source": "explicit_canonical"
      }
    ]
  },
  {
    "id": "C_correct_subject",
    "passed": true,
    "allowed": false,
    "target": null,
    "decisions": [
      {
        "annotation": "that place",
        "role": "subject",
        "status": "MISSING",
        "explicit": true,
        "candidates": [],
        "source": null
      }
    ]
  },
  {
    "id": "D_correct_addressee",
    "passed": true,
    "allowed": false,
    "target": null,
    "decisions": [
      {
        "annotation": "one of them",
        "role": "addressee",
        "status": "AMBIGUOUS",
        "explicit": true,
        "candidates": [],
        "source": null
      }
    ]
  },
  {
    "id": "E_multiple",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "Sergeant Mara",
        "role": "addressee",
        "status": "GROUNDED",
        "explicit": true,
        "candidates": [
          "sergeant_mara"
        ],
        "source": "explicit_canonical"
      },
      {
        "annotation": "north gate",
        "role": "subject",
        "status": "GROUNDED",
        "explicit": true,
        "candidates": [],
        "source": "npc.authored_subject"
      }
    ]
  },
  {
    "id": "F_wrong_entity",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "obsidian palace",
        "role": "subject",
        "status": "NOT_APPLICABLE",
        "explicit": false,
        "candidates": [],
        "source": "npc:sergeant_mara:night_watch"
      }
    ]
  },
  {
    "id": "G_irrelevant_noun",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "weather",
        "role": "subject",
        "status": "NOT_APPLICABLE",
        "explicit": false,
        "candidates": [],
        "source": "npc:sergeant_mara:night_watch"
      }
    ]
  },
  {
    "id": "H_unknown_answer",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "north gate",
        "role": "subject",
        "status": "GROUNDED",
        "explicit": true,
        "candidates": [],
        "source": "npc.authored_subject"
      }
    ]
  },
  {
    "id": "I_hidden_answer",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "north gate",
        "role": "subject",
        "status": "GROUNDED",
        "explicit": true,
        "candidates": [],
        "source": "npc.authored_subject"
      }
    ]
  },
  {
    "id": "J_tempting_default",
    "passed": true,
    "allowed": false,
    "target": null,
    "decisions": [
      {
        "annotation": "one of them",
        "role": "addressee",
        "status": "AMBIGUOUS",
        "explicit": true,
        "candidates": [],
        "source": null
      },
      {
        "annotation": "that place",
        "role": "subject",
        "status": "MISSING",
        "explicit": true,
        "candidates": [],
        "source": null
      }
    ]
  },
  {
    "id": "K_subject_conflict",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "south tower",
        "role": "subject",
        "status": "NOT_APPLICABLE",
        "explicit": false,
        "candidates": [],
        "source": "npc:sergeant_mara:night_watch"
      }
    ]
  },
  {
    "id": "L_unauthorized_npc",
    "passed": true,
    "allowed": true,
    "target": "sergeant_mara",
    "decisions": [
      {
        "annotation": "north gate",
        "role": "subject",
        "status": "GROUNDED",
        "explicit": true,
        "candidates": [],
        "source": "npc.authored_subject"
      }
    ]
  }
]
```



Full controlled provider records/bridge results: adversarial_annotations.json. A/B/E ground false annotations. C/D/J retain real subject/addressee ambiguity. F/G/K neutralize unmentioned conflict/irrelevance only when the existing selector supports the raw question. H/I separate unknown/hidden answers from reference grounding. L rejects provider target preference in favor of independently grounded player wording. HTTP controls separately prove F/G handoff to the real resolver.



These are controlled interpretation probes with zero fresh provider calls. Earlier conservative F/G/K outcomes remain under qualification_before_irrelevant_annotation_fix. No fixture is labeled fresh evidence.
