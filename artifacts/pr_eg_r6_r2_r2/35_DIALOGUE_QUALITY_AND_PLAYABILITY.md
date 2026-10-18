# 35 — Dialogue Quality and Playability

{
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
  "final": {
    "operation_correct": {
      "count": 149,
      "denominator": 150,
      "rate": 0.9933333333333333
    },
    "referent_correct": {
      "count": 123,
      "denominator": 124,
      "rate": 0.9919354838709677
    },
    "roles_preserved": {
      "count": 150,
      "denominator": 150,
      "rate": 1.0
    },
    "correction_success": {
      "count": 15,
      "denominator": 16,
      "rate": 0.9375
    },
    "follow_up_success": {
      "count": 38,
      "denominator": 38,
      "rate": 1.0
    },
    "focus_preserved": {
      "count": 149,
      "denominator": 150,
      "rate": 0.9933333333333333
    },
    "false_clarification": {
      "count": 4,
      "denominator": 136,
      "rate": 0.029411764705882353
    },
    "genuine_clarification_correct": {
      "count": 11,
      "denominator": 11,
      "rate": 1.0
    },
    "relevant": {
      "count": 150,
      "denominator": 150,
      "rate": 1.0
    },
    "sufficient": {
      "count": 136,
      "denominator": 150,
      "rate": 0.9066666666666666
    },
    "quality": 2.9466666666666668,
    "playability": 2.9466666666666668
  },
  "predecessors": {
    "operation_correct": {
      "count": 88,
      "denominator": 89,
      "rate": 0.9887640449438202
    },
    "referent_correct": {
      "count": 73,
      "denominator": 73,
      "rate": 1.0
    },
    "roles_preserved": {
      "count": 89,
      "denominator": 89,
      "rate": 1.0
    },
    "correction_success": {
      "count": 9,
      "denominator": 10,
      "rate": 0.9
    },
    "follow_up_success": {
      "count": 13,
      "denominator": 17,
      "rate": 0.7647058823529411
    },
    "focus_preserved": {
      "count": 86,
      "denominator": 89,
      "rate": 0.9662921348314607
    },
    "false_clarification": {
      "count": 4,
      "denominator": 75,
      "rate": 0.05333333333333334
    },
    "genuine_clarification_correct": {
      "count": 4,
      "denominator": 4,
      "rate": 1.0
    },
    "relevant": {
      "count": 89,
      "denominator": 89,
      "rate": 1.0
    },
    "sufficient": {
      "count": 86,
      "denominator": 89,
      "rate": 0.9662921348314607
    },
    "quality": 2.932584269662921,
    "playability": 2.932584269662921
  },
  "method": "Separately prompted automated provider grading; packet versions hidden, shuffled order. Same configured model, not independent human review. Criteria, every input, usage and raw outputs preserved. Grading was not used to tune production.",
  "grading_validity": "UNRELIABLE FOR ACCEPTANCE. Automated grading overcredits absent/wrong bindings and communication-role handling, and omits intended correction/followup denominators. Raw outputs are preserved rather than silently repaired. Relevance, sufficiency and focus claims require external adjudication; no matched improvement is established by these grades.",
  "graded_turns": 284,
  "implementing_agent_assessment": "Named role correctness is established in controlled cases, but final live malformed-operation/source proposals and wrong classifications remain. Controlled validity does not establish conversational qualification."
}

Explicit local intent denominators and scores: [artifacts/pr_eg_r6_r2_r2/local_assessment.json:1](<C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm/artifacts/pr_eg_r6_r2_r2/local_assessment.json:1>)

Automated grades substantially overcredit structure and miss intended dependent acts. Their quality/playability means and relevance/sufficiency claims are not accepted as validated metrics. Local correction/followup success figures are optimistic upper bounds; even these miss the thresholds. External adjudication remains necessary.
