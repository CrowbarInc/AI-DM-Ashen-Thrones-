# CI_2 — Hotspot Compression Measurement Standard Closeout

**Closeout date:** 2026-06-26  
**Scope:** Measurement governance and documentation only. No production code changes.  
**Primary metric:** Hotspot Measurement Consistency

---

## Closeout Record

| Field | Value |
|---|---|
| Discovery artifact reviewed | [`CI_2_hotspot_compression_measurement_standard_discovery.md`](../../CI_2_hotspot_compression_measurement_standard_discovery.md) |
| Measurement standard adopted | [`docs/processes/hotspot_compression_measurement_standard.md`](../processes/hotspot_compression_measurement_standard.md) (version 1) |
| Closeout date | 2026-06-26 |
| Branch | `feature/stabilized-foundation` |
| Commit | `85855df` (`85855df00ebdee20a33c0ada447c178bf1f49820`) |
| Active watch | [`CK_hotspot_compression_watch.md`](CK_hotspot_compression_watch.md) — **remains Active** |

---

## Adopted Decisions

| Decision | Value |
|---|---|
| Primary HCI lane | **CK-GIT** (git path touch, cumulative window `85855df..M`) |
| HCI formula | **HCI = Top 5 Share %** (`top5_share_pct`) |
| Supplementary lane | **CK-FI** (AST module fan-in from `BU_import_fan_in_fan_out.csv`) |
| Supplementary role | Informational only — CK **Notes** column and event evidence; **never replaces HCI** |
| Touch threshold (primary) | **T_touch = 3** |
| FI threshold (supplementary) | **T_fi = 10** |
| Repeatability verdict | **STABLE_WITH_EXEMPT_FIELDS** |
| Stability-exempt fields | `generated_at`, `summary.generated_utc`, and other generator timestamps |

---

## Governance Outcome

| Field | Value |
|---|---|
| CI_2 status | **Closed** |
| Outcome | **Measurement Standard Adopted** |
| CK status | **Active** (rolling watch unchanged) |
| First CK measurement | **Pending** — awaits next qualifying maintenance cycle after `85855df` |
| Historical backfill | **None** — watch activation row remains `pending` |

The measurement standard is now the authoritative procedure for all future CK rows. BV/BU hotspot snapshots remain historical reference lanes only.

---

## CK Integration

[`CK_hotspot_compression_watch.md`](CK_hotspot_compression_watch.md) measurement procedure now references the adopted standard. Watch log rows, compression events, expansion events, and baseline placeholders were **not** modified by this closeout.

---

## Future Measurement Rules

1. **Mandatory standard** — All future CK measurements must use [`docs/processes/hotspot_compression_measurement_standard.md`](../processes/hotspot_compression_measurement_standard.md) (version 1 unless superseded).
2. **Direct comparability** — HCI values remain directly comparable across cycles while standard version 1 and cumulative window `85855df..M` are in force.
3. **Version discipline** — Methodology changes require a **version increment** in the standard document and an **explicit baseline reset** note in CK (new measurement row labeled with new `baseline_version`; prior rows retain their recorded standard version in Notes).
4. **Supplementary FI** — CK-FI metrics may provide structural context in **Notes** but **may not replace** CK-GIT HCI in the measurement log or compression/expansion judgments.
5. **No retroactive edits** — Do not recompute or alter prior CK rows when the standard is versioned; append forward-only measurements.
6. **Cadence** — Record one measurement row per significant maintenance cycle closeout commit, not per incidental commit.

---

## Verification Checklist

| Check | Result |
|---|---|
| CK remains an active rolling watch | ✓ |
| No historical measurements backfilled | ✓ |
| First measurement pending until next qualifying cycle | ✓ |
| No production code modified | ✓ |
| No new hotspot measurements computed | ✓ |
| CK-specific validation tests | None present — closeout verified by document cross-reference only |

---

## Related Artifacts

| Artifact | Role |
|---|---|
| [CI_2_hotspot_compression_measurement_standard_discovery.md](../../CI_2_hotspot_compression_measurement_standard_discovery.md) | Discovery and repeatability evidence |
| [hotspot_compression_measurement_standard.md](../processes/hotspot_compression_measurement_standard.md) | Adopted measurement authority (v1) |
| [CK_hotspot_compression_watch.md](CK_hotspot_compression_watch.md) | Active HCI rolling ledger |
| [CJ_corrective_cohort_watch.md](CJ_corrective_cohort_watch.md) | Complementary corrective locality watch |
