# 30 Performance

{
  "turns": 122,
  "conversations": 9,
  "calls": 182,
  "calls_per_turn": 1.4918032786885247,
  "input_tokens_per_turn": {
    "mean": 1538.9098360655737,
    "median": 1586.5,
    "p95": 1759,
    "maximum": 1816
  },
  "output_tokens_per_turn": {
    "mean": 257.3524590163934,
    "median": 232.5,
    "p95": 411,
    "maximum": 527
  },
  "latency_ms": {
    "mean": 2913.7559926240383,
    "median": 2952.0244000013918,
    "p95": 4128.386500000488,
    "maximum": 9563.662700005807
  },
  "retry_calls": 0,
  "planning": {
    "calls": 116,
    "input_tokens_per_call": {
      "mean": 1470.0862068965516,
      "median": 1495.0,
      "p95": 1627,
      "maximum": 1646
    },
    "latency_ms_per_call": {
      "mean": 2375.537405172414,
      "median": 2153.2205,
      "p95": 3529.207,
      "maximum": 9519.731
    }
  },
  "nonplanning_input_tokens_per_call": {
    "mean": 260.8636363636364,
    "median": 161.0,
    "p95": 1756,
    "maximum": 1816
  },
  "total_input_tokens": 187747,
  "total_output_tokens": 31397,
  "note": "Engine calls only; development pilots, matched runs and scoring excluded. Currency cost not estimated; actual token consumption is reported. Null usage is not asserted to be measured zero."
}
