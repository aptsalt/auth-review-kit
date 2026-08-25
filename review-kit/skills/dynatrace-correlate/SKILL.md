---
name: dynatrace-correlate
description: Correlate static code-review findings against Dynatrace production telemetry and produce a corroboration report — which findings have observed live signal behind them, which are consistent with observed symptoms, which are quiet, and which are unobservable in principle. Use when the user says "correlate findings with dynatrace", "which findings are real in prod", "cross-reference telemetry", "corroborate the findings", or after a dynatrace-pull. Guards against the trap of reading a quiet dashboard as a clean system.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Dynatrace Correlate

Join two evidence sources that are usually kept apart: what the code says could happen, and what
production says did happen. Neither is authoritative alone. A finding with live signal behind it is a
priority argument that needs no further persuasion; a finding with none is still a finding.

**The trap this skill exists to avoid:** treating absence of a Dynatrace problem as evidence that a
finding is not real. Most security findings are structurally invisible to APM — a forged token
*succeeds*, a leaked secret produces no error, a missing authorization check returns 200. Downgrading
those because the dashboard is green is the single most damaging mistake available here.

## Inputs

| | |
|---|---|
| Findings | `<workspace>/findings/*.md` — each carries a `dimension` |
| Telemetry | `_dynatrace/problems.json` + `_dynatrace/pull-manifest.json` |
| Mapping | profile §7 repo→entity map, and `config/repos.json` |
| Symptom classes | `skills/issue-hunt/references/dimensions.md` — each dimension declares what live signal *would* look like |

If there is no recent pull, run `dynatrace-pull` first.

## Verdicts

Assign exactly one per finding.

| Verdict | Criteria | What it licenses you to say |
|---|---|---|
| **OBSERVED** | Same entity **and** a signature match — the problem names the exact statement, exception, endpoint or resource the finding is about | "This is happening in production." Strongest possible argument. |
| **CONSISTENT** | Same entity, and a problem in the dimension's symptom class, but no signature-level match | "Production shows the symptom this defect would produce." Suggestive, not proof — a different cause could produce the same symptom. |
| **NO SIGNAL** | Entity is `mapped`, appears in the pull's scope, and nothing in its symptom class occurred in the window | "Not observed in 30 days." Means low frequency or not-yet-triggered. **Never means "not real".** |
| **BLIND** | Entity is `blind`, `unmapped`, or excluded by the pull's filters | "We cannot see this either way." Absence proves nothing. |
| **UNOBSERVABLE** | The dimension's symptom class is `none` — the defect produces no telemetry even when exploited | "APM cannot corroborate this by design." Applies to `secret-leak`, `token-integrity`, `client-crypto`. |

`UNOBSERVABLE` is not a weaker `NO SIGNAL`. It is a statement about the *method*, and it protects the
most severe findings in the estate from being quietly deprioritised.

## Matching

Work through these in order; stop at the first that fits.

1. **Signature** — the problem text names the file, class, exception, SQL statement, endpoint path or
   resource the finding cites. This is an `OBSERVED` match. Quote the matching text in the report.
2. **Entity + symptom class** — the problem is on the mapped entity and its type falls in the
   dimension's symptom class (e.g. an `outbound-resilience` finding and a `service-slowdown` /
   `timeout` problem). This is `CONSISTENT`.
3. **Downstream entity** — the finding is in a library or config repo (`blind`) but a *consumer* shows
   the symptom. Record it as `CONSISTENT`, and name the consumer — this is how library findings get
   evidence at all.
4. **Temporal** — problem onset lines up with a deploy or config change touching the finding's code.
   Strong for `config-drift`. Say explicitly that this is a timing coincidence, not a proven cause.

**Do not force a match.** A weak correlation reported confidently is worse than an honest `NO SIGNAL`,
because it is the claim the owning team will attack first — and when it falls, it takes the credible
findings with it.

## Priority score

Rank the report by this, not by severity alone:

```
priority = severity_weight  ×  corroboration_weight  ×  blast_radius
```

| severity | weight | | corroboration | weight |
|---|---|---|---|---|
| Critical | 8 | | OBSERVED | 2.0 |
| High | 5 | | CONSISTENT | 1.4 |
| Medium | 3 | | UNOBSERVABLE | 1.0 |
| Low | 1 | | BLIND | 1.0 |
| | | | NO SIGNAL | 0.8 |

`blast_radius`: 1.0 by default; use the problem's affected-user or affected-request count from
Dynatrace where present, normalised into 1.0–2.0.

Note the deliberate asymmetry: `OBSERVED` doubles priority, but `NO SIGNAL` only takes off 20%, and
`UNOBSERVABLE` / `BLIND` take off nothing. Telemetry can *promote* a finding strongly; it can barely
demote one. That asymmetry is the whole ethic of the method — the dashboard is allowed to raise alarm,
never to grant absolution.

## Also look the other way

Correlation is bidirectional, and the reverse direction is where the genuinely new information is.

Go through the Dynatrace problems that matched **no** finding:

- **On a reviewed repo?** Either the review missed something, or it is an infra/dependency issue outside
  the code. Say which — and if it is the former, that is a gap in the review to go close.
- **On an unreviewed repo?** That is a prioritisation signal: production is telling you which repo to
  onboard next. Name it.
- **On an entity mapped to no repo at all?** Coverage gap in the estate map. Add it to the profile.

A correlation report that only walks findings→telemetry has done half the job.

## Output

Write `<workspace>/dynatrace-correlation.md` using `assets/report-template.md`.

Then update each finding file: fill the `Correlation` row with the verdict, and apply the severity
uplift for `OBSERVED` if the profile's policy calls for it.

Finally update `config/repos.json`: set `correlation.last_run`, and per repo store the verdict counts,
so `review-status` can show corroboration coverage across the estate.

## Report to the user

- how many findings in each verdict
- the top 5 by priority score, one line each, quoting the evidence for the `OBSERVED` ones
- unmatched problems, and what each implies (missed finding / unreviewed repo / unmapped entity)
- how much of the estate was actually observable — `BLIND` count over total. **If that fraction is
  high, say so plainly: it is the honest headline of the whole exercise**, and it is itself an
  observability finding worth raising with the platform team.
