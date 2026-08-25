---
name: dynatrace-pull
description: Pull Dynatrace problems and telemetry for the last 30 days through an already-authenticated browser session using Playwright over CDP — no API token, no credentials stored. Use when the user says "pull dynatrace", "get the dynatrace data", "grab last 30 days of problems", "refresh telemetry", or asks to correlate findings and no recent pull exists. Produces the problems.json that dynatrace-correlate consumes.
allowed-tools: Read, Write, Bash, Glob
---

# Dynatrace Pull

Get production signal onto disk so findings can be corroborated against it.

**Why through the browser:** Dynatrace in a bank sits behind SSO and MFA. Attaching to a session the
user already established means no API token to mint, no credential to store, and no secret in the repo.
The cost is that it needs a browser open and a human logged in — which is the right trade for a review
tool that runs occasionally, not in CI.

## Steps

### 1. Check whether a fresh pull already exists

Read `_dynatrace/pull-manifest.json`. If `finished` is within the last day or so and the window matches
what the user needs, say so and offer to reuse it rather than pulling again. Re-pulling is not free —
it needs their browser and their attention.

### 2. Make sure a debuggable browser is running

```bash
python scripts/dt_pull.py --launch
```

This starts Chrome or Edge on port 9222 with an isolated profile. Tell the user to **log into Dynatrace
in that window** and confirm when they are in. The isolated profile means this never touches their
normal browser profile or its cookies.

If they already have a debuggable browser open with Dynatrace loaded, skip this.

### 3. Pull

Start with `capture` — it works on any tenant version because it records what the UI itself fetches:

```bash
python scripts/dt_pull.py --mode capture --minutes 3
```

Then tell the user exactly what to do while it records:

1. Open **Problems**
2. Set the time window to the **last 30 days**
3. Scroll the list so the UI actually loads the pages — the script only sees what the browser fetches

Once a working endpoint has been discovered and stored in `config/dynatrace.local.json`, later pulls
can use the faster path:

```bash
python scripts/dt_pull.py --mode api --window 30d
```

If `api` returns nothing, fall back to `capture`. Endpoint shapes differ across tenant versions and a
404 there means nothing about the data.

### 4. Sanity-check the pull before trusting it

Read `_dynatrace/pull-manifest.json` and `_dynatrace/problems.json`, then ask:

- **How many problems, over what window?** Zero problems in 30 days across a whole estate usually means
  a filter was applied, not that everything is healthy.
- **Which entities appear?** Compare against the repo→entity map in the profile. Entities in Dynatrace
  that map to no reviewed repo are review coverage gaps. Repos mapped to entities that never appear are
  either healthy or not instrumented — and those two are very different.
- **Was a management zone filter active?** If the UI was scoped to one zone, the pull is scoped to it too.

Record the answers. `dynatrace-correlate` needs to know the shape of what was collected in order to
read silence correctly.

### 5. Report

- window, mode, number of problems, number of distinct entities
- entities seen that are not in the profile's repo map (coverage gaps in the review)
- mapped repos with no signal (candidates for `NO SIGNAL`, unless they are `blind`)
- any filter that narrowed the pull

## The rule that matters

**A quiet Dynatrace is not a clean system.** Silence has at least four causes:

1. The problem is genuinely not occurring
2. The service is not instrumented (`blind`)
3. The window or management-zone filter excluded it
4. The failure mode is invisible to APM — a leaked secret, a forgeable token, a missing authorization
   check that *succeeds* every time it is exploited

Only the first is evidence. Findings in the `secret-leak` and `token-integrity` dimensions are
structurally invisible to Dynatrace, so absence of signal there says nothing whatsoever — never let a
clean pull downgrade one of those.
