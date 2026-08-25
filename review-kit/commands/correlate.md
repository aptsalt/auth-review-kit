---
description: Pull Dynatrace telemetry if stale, then correlate all findings against it
argument-hint: [window, e.g. 30d]
---

Correlate the review findings against Dynatrace production telemetry. Window: **$ARGUMENTS** (default 30d).

1. Check `_dynatrace/pull-manifest.json`. If there is no pull, or it is stale, or the window does not
   match, use the `dynatrace-pull` skill — and walk me through the browser steps rather than assuming
   the session is ready.
2. Use the `dynatrace-correlate` skill to produce `<workspace>/dynatrace-correlation.md`.
3. Update the finding files with their verdicts, and `config/repos.json` with the verdict counts.

Then tell me:

- the verdict split, and the top 5 findings by priority score
- for each `OBSERVED` one, quote the telemetry that names it
- what the **reverse** direction found: problems matching no finding, and whether each means a missed
  finding, an unreviewed repo, or an unmapped entity
- what fraction of the estate was actually observable

Do not let a quiet dashboard downgrade a finding. `BLIND` and `UNOBSERVABLE` are not `NO SIGNAL`, and
`secret-leak` / `token-integrity` findings produce no telemetry even when they are being exploited.
