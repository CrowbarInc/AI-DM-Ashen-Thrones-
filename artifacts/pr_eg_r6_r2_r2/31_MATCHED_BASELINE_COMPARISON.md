# 31 — Matched Baseline Comparison

{
  "turns": 45,
  "baseline": {
    "operation_correct": {
      "count": 41,
      "denominator": 45,
      "rate": 0.9111111111111111
    },
    "referent_correct": {
      "count": 24,
      "denominator": 24,
      "rate": 1.0
    },
    "roles_preserved": {
      "count": 45,
      "denominator": 45,
      "rate": 1.0
    },
    "correction_success": {
      "count": 4,
      "denominator": 5,
      "rate": 0.8
    },
    "follow_up_success": {
      "count": 12,
      "denominator": 15,
      "rate": 0.8
    },
    "focus_preserved": {
      "count": 41,
      "denominator": 45,
      "rate": 0.9111111111111111
    },
    "false_clarification": {
      "count": 4,
      "denominator": 45,
      "rate": 0.08888888888888889
    },
    "genuine_clarification_correct": {
      "count": 1,
      "denominator": 1,
      "rate": 1.0
    },
    "relevant": {
      "count": 42,
      "denominator": 45,
      "rate": 0.9333333333333333
    },
    "sufficient": {
      "count": 41,
      "denominator": 45,
      "rate": 0.9111111111111111
    },
    "quality": 2.8222222222222224,
    "playability": 2.8222222222222224
  },
  "final_matched": {
    "operation_correct": {
      "count": 45,
      "denominator": 45,
      "rate": 1.0
    },
    "referent_correct": {
      "count": 39,
      "denominator": 39,
      "rate": 1.0
    },
    "roles_preserved": {
      "count": 45,
      "denominator": 45,
      "rate": 1.0
    },
    "correction_success": {
      "count": 6,
      "denominator": 6,
      "rate": 1.0
    },
    "follow_up_success": {
      "count": 16,
      "denominator": 16,
      "rate": 1.0
    },
    "focus_preserved": {
      "count": 45,
      "denominator": 45,
      "rate": 1.0
    },
    "false_clarification": {
      "count": 3,
      "denominator": 31,
      "rate": 0.0967741935483871
    },
    "genuine_clarification_correct": {
      "count": 2,
      "denominator": 2,
      "rate": 1.0
    },
    "relevant": {
      "count": 45,
      "denominator": 45,
      "rate": 1.0
    },
    "sufficient": {
      "count": 43,
      "denominator": 45,
      "rate": 0.9555555555555556
    },
    "quality": 3,
    "playability": 3
  },
  "method": "Same three initial scripted worlds/NPC knowledge/disclosure and empty conversational contexts, same 45 utterances. Histories diverge naturally after differing responses. Fresh provider samples are not deterministic causal isolation. Every pair retained.",
  "explicit_local_baseline": {
    "operation_correct": {
      "count": 43,
      "denominator": 45,
      "rate": 0.9555555555555556
    },
    "referent_correct": {
      "count": 15,
      "denominator": 22,
      "rate": 0.6818181818181818
    },
    "correction_success": {
      "count": 3,
      "denominator": 6,
      "rate": 0.5
    },
    "follow_up_success": {
      "count": 12,
      "denominator": 16,
      "rate": 0.75
    },
    "false_clarification": {
      "count": 7,
      "denominator": 45,
      "rate": 0.15555555555555556
    },
    "communication_roles": {
      "count": 0,
      "denominator": 0,
      "rate": null
    }
  },
  "explicit_local_final_matched": {
    "operation_correct": {
      "count": 43,
      "denominator": 45,
      "rate": 0.9555555555555556
    },
    "referent_correct": {
      "count": 9,
      "denominator": 22,
      "rate": 0.4090909090909091
    },
    "correction_success": {
      "count": 2,
      "denominator": 6,
      "rate": 0.3333333333333333
    },
    "follow_up_success": {
      "count": 7,
      "denominator": 16,
      "rate": 0.4375
    },
    "false_clarification": {
      "count": 5,
      "denominator": 45,
      "rate": 0.1111111111111111
    },
    "communication_roles": {
      "count": 0,
      "denominator": 0,
      "rate": null
    }
  },
  "grading_limitation": "UNRELIABLE FOR ACCEPTANCE. Automated grading overcredits absent/wrong bindings and communication-role handling, and omits intended correction/followup denominators. Raw outputs are preserved rather than silently repaired. Relevance, sufficiency and focus claims require external adjudication; no matched improvement is established by these grades."
}

All 45 pairs and every divergence: [artifacts/pr_eg_r6_r2_r2/matched_comparison.json:1](<C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm/artifacts/pr_eg_r6_r2_r2/matched_comparison.json:1>)
