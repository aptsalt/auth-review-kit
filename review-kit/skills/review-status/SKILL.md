---
name: review-status
description: Render the per-repo coverage index across the whole estate — what has been reviewed, what is queued, findings by severity, open evidence gaps, and how much of it is observable in Dynatrace. Use when the user asks "where are we", "review status", "coverage", "which repos are done", "what's left to review", "show me the dashboard", or wants a progress update to share with a lead or a team. Produces review-status.md and review-status.html.
allowed-tools: Read, Write, Bash, Glob
---

# Review Status

The honest picture of the estate. Its job is to make *uncovered* and *invisible* as legible as *found*.

A coverage board that shows only findings implies everything else is fine. This one shows four things
that findings-only boards hide: repos not yet reviewed, dimensions skipped, evidence gaps outstanding,
and repos where telemetry can see nothing at all.

## Steps

### 1. Reconcile before rendering

`config/repos.json` is the source of truth, and it drifts. Before rendering, check it against reality:

- Every file in `<workspace>/findings/` has a registry entry, and its severity counts match
- Every repo with `reviewed` set has non-empty `dimensions_run`
- No repo is still `unmapped` if a correlation has been run — that combination silently produces
  meaningless verdicts
- `correlation.last_run` matches the latest `_dynatrace/pull-manifest.json`

Fix drift in the registry, and tell the user what you corrected. Silent repair is how a registry stops
being trusted.

### 2. Render

```bash
python scripts/render_status.py --out <workspace>
```

Writes `review-status.md` (greppable, diffable in a PR) and `review-status.html` (shareable).

### 3. Read it back and interpret

Numbers do not speak. Give the user the three or four sentences that matter:

- **Coverage** — reviewed / partial / queued, and which tier is least covered. Uneven coverage by tier
  matters more than the raw count; an estate with every client reviewed and no gateway repos reviewed
  is not 50% done in any meaningful sense.
- **Concentration** — are findings clustered in a few repos, or spread? Clustering usually means either
  a genuinely weak component or a reviewer who went deepest there first. Say which you think it is.
- **Evidence gaps** — the total, and whether any are answerable from the current workspace. Those are
  the cheapest wins available and should be named explicitly.
- **Observability** — mapped vs blind vs unmapped. **If a large share of the estate is blind, that is
  the headline**, because it caps what any correlation can ever prove.

### 4. Offer the next step

Recommend one thing, with a reason. Usually one of:

- an evidence gap that can be closed today from the repos already in hand
- the unreviewed repo that production problems are pointing at
- the tier with the thinnest coverage
- resolving `unmapped` entries, if a correlation run is coming

## Sharing this with a lead

When the user wants this for a status update or a meeting, lead with the shape rather than the totals:

> *N of M repos reviewed, concentrated in the identity tier. X findings, of which Y are corroborated by
> production telemetry. Z evidence gaps are blocked on artifacts we do not have access to — here they
> are, and here is who owns them.*

The evidence-gap list is the most useful thing on the page for a lead, because every item is something
only they can unblock. Put it in front of them rather than burying it under the findings count.
