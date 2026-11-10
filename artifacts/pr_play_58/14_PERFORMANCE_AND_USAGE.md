# Performance and usage

{
  "previous_coverage": {
    "count": 800,
    "average_ms": 0.10742787519120611,
    "maximum_ms": 0.7321999873965979,
    "median_ms": 0.09955000132322311
  },
  "updated_coverage": {
    "count": 800,
    "average_ms": 0.21440549957333133,
    "maximum_ms": 0.7127000135369599,
    "median_ms": 0.2067500026896596
  },
  "combined": {
    "count": 800,
    "average_ms": 4.399226250388892,
    "maximum_ms": 128.67259996710345,
    "median_ms": 2.6539500104263425
  },
  "provider_requests": 0,
  "provider_tokens": 0,
  "method": "800 warmed invocations per timing series, fixed samples only; wall clock, no tracemalloc during latency.",
  "memory": {
    "previous": {
      "current_bytes": 240,
      "peak_bytes": 6840
    },
    "updated": {
      "current_bytes": 600,
      "peak_bytes": 11487
    },
    "scope": "Sequential eight-sample coverage allocation peaks; not process RSS or persistent-state overhead."
  }
}

Timing is measured wall clock, including scheduling noise while regression tests run. Memory reports transient traced allocation peaks across eight fixed samples (updated minus previous peak 4,647 bytes), not persistent memory or RSS. Cold per-case timings remain in both corpus results. No holdout evaluation is repeated for performance. Provider requests: 0; tokens: 0; additional provider dependencies: none.
