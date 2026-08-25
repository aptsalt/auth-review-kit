# Dynatrace Correlation Report

> Findings from `<workspace>/findings/` joined against `_dynatrace/problems.json`
> Telemetry window: `<window>` · pulled `<date>` · mode `<api|capture>` · tenant `<origin>`
> Repos in scope: `<n>` · findings correlated: `<n>` · problems examined: `<n>`

---

## How to read this

| Verdict | Means |
|---|---|
| **OBSERVED** | Live production signal names this exact defect. Not a hypothesis. |
| **CONSISTENT** | Production shows the symptom this defect would produce, on the right service. Suggestive. |
| **NO SIGNAL** | Service is instrumented and in scope; nothing in 30 days. Low frequency or not yet triggered — **not** disproved. |
| **BLIND** | Service is uninstrumented, unmapped, or outside the pull. **Absence proves nothing.** |
| **UNOBSERVABLE** | This class of defect produces no telemetry even when exploited. APM cannot corroborate it by design. |

**Telemetry promotes; it does not absolve.** `OBSERVED` doubles priority. `NO SIGNAL` removes 20%.
`BLIND` and `UNOBSERVABLE` remove nothing.

---

## 1. Headline

<!-- Three sentences. How many findings have production behind them, how much of the estate was
     actually observable, and the single most important thing this join revealed. -->

| | Count | % of findings |
|---|---|---|
| OBSERVED | | |
| CONSISTENT | | |
| NO SIGNAL | | |
| BLIND | | |
| UNOBSERVABLE | | |

**Observability of the estate:** `<mapped>` of `<total>` repos are mapped to a Dynatrace entity.
`<blind>` are blind.

<!-- If the blind fraction is significant, say so here rather than burying it. It is both a caveat on
     this entire report and a finding in its own right for the platform team. -->

---

## 2. Priority queue

Ranked by `severity × corroboration × blast radius` — not by severity alone.

| # | Finding | Repo | Sev | Verdict | Score | Evidence |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

---

## 3. OBSERVED — happening in production

For each, the strongest section of the report. Quote the telemetry.

### `<F-repo-001>` — <finding title>

| | |
|---|---|
| **Dimension** | |
| **Code** | `file#Lx-Ly` |
| **Entity** | |
| **Problem** | `<Dynatrace problem title + id>` |
| **Window** | first seen … last seen · `<n>` occurrences |
| **Affected** | `<users / requests>` |

**Match:** <!-- Quote the problem text that names the finding's statement, exception, endpoint or
resource. Say precisely why this is a signature match and not just the same service. -->

**What this changes:** <!-- The argument this unlocks. Usually: this stops being a code-review opinion
and becomes an incident with a known root cause. -->

---

## 4. CONSISTENT — symptom present, cause not proven

| Finding | Repo | Problem observed | Why consistent | What would confirm it |
|---|---|---|---|---|
| | | | | |

<!-- The last column matters most: name the specific query, trace, or log field that would upgrade
     each of these to OBSERVED. That list is the next hour of work, precisely scoped. -->

---

## 5. NO SIGNAL — instrumented, quiet

These are real findings on services Dynatrace can see, which did not fire in the window.

| Finding | Repo | Sev | Why it may be quiet |
|---|---|---|---|

<!-- For each, pick one: rare trigger condition · path not exercised in this window · guarded by an
     upstream control that usually holds · low volume. That reasoning is what stops a reader
     concluding "quiet = fixed". -->

---

## 6. BLIND — cannot be seen either way

| Finding | Repo | Why blind | What would make it observable |
|---|---|---|---|

<!-- The right column is a concrete observability ask: instrument service X, add a management zone,
     emit a metric on path Y. Collected across the estate, this becomes the observability roadmap —
     often the most actionable output of the whole review. -->

---

## 7. UNOBSERVABLE — invisible to APM by design

Findings whose exploitation produces no telemetry. Listed so nobody deprioritises them for lack of
production signal.

| Finding | Repo | Sev | Why it is invisible |
|---|---|---|---|

<!-- e.g. "a forged token validates successfully — the request is a 200 and looks identical to a
     legitimate one." These are frequently the highest-severity items in the estate. -->

---

## 8. Reverse direction — problems with no finding

Where the genuinely new information is.

| Problem | Entity | Mapped repo | Interpretation |
|---|---|---|---|
| | | | missed finding / infra / unreviewed repo / unmapped entity |

**Review gaps this exposes:** <!-- Problems on reviewed repos that no finding predicted. Each is a
dimension to re-run, and worth saying out loud rather than quietly re-reviewing. -->

**Repos production says to review next:** <!-- Unreviewed repos with live problems, in order. -->

**Entities mapped to no repo:** <!-- Estate map gaps. Add to the profile. -->

---

## 9. Caveats on this report

- **Window:** `<window>`. A defect that fires quarterly cannot appear in 30 days.
- **Scope:** `<management zones / filters active during the pull>`.
- **Mode:** `capture` records only what the UI fetched while recording; it is not exhaustive.
- **Mapping:** repo→entity mapping is maintained by hand. A wrong mapping produces a wrong verdict in
  both directions.
- **`BLIND` is not `NO SIGNAL`.** Anywhere the two are conflated, this report is wrong.
