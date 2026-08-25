---
name: issue-hunt
description: Run a dimensioned performance and security review pass over a repo that is already onboarded, producing findings with evidence markers, file:line citations and severity. Use when the user says "review this repo", "hunt for issues", "find security issues in <repo>", "performance review", "run the review pass", "what's wrong with <repo>", or asks to re-review after changes. Enforces evidence discipline so unverifiable claims become evidence gaps rather than findings.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Issue Hunt

The review pass. One repo, a chosen set of dimensions, findings that a sceptical engineer would accept.

**The standard to hold:** every finding names a file and line, states the failure scenario concretely,
and carries an evidence marker. A finding that cannot survive "show me where" is not a finding — it is
a question, and it belongs in the evidence-gap list instead.

## Before you start

1. Read the active profile (`profiles/<name>.md`) — architecture, vocabulary, sensitive paths, severity policy.
2. Read `<workspace>/source-index/<repo>.md`. If it does not exist, run `repo-onboard` first; hunting
   without an index means re-reading the repo for every dimension.
3. Read the repo's entry in `config/repos.json` for its tier, kind and pending dimensions.

## Evidence discipline

This is the part that makes the review credible. Every claim gets one of three markers:

| Marker | Means | You may |
|---|---|---|
| ✅ **verified** | You read the code path end to end in this workspace | Raise a finding |
| 🟡 **partial** | One side is present; the counterpart is elsewhere | Raise a finding, stated as conditional on the missing side |
| ❌ **needs-evidence** | The deciding code or config is not in the workspace | **Not** a finding. Record an evidence gap naming the artifact required. |

❌ is not "probably fine" and it is not "a vulnerability". It is a request with an address on it.
Turning ❌ into a finding is how a review loses the room; turning ❌ into a silent pass is how it
misses the real thing. Do neither.

## Steps

### 1. Pick dimensions

From `references/dimensions.md`, filtered by the repo's tier and kind
(`skills/repo-onboard/references/tier-dimensions.md` has the mapping).

Run `secret-leak` first — it is mechanical and needs no understanding of the codebase.

Announce which dimensions you are running and which you are skipping, with the reason. Silent scope
reduction is what makes a later reader think the repo was cleared when it was only sampled.

### 2. Hunt, one dimension at a time

For each dimension, work its checklist against the source index. Search for the pattern, then **read
the surrounding code before concluding** — a grep hit is a lead, not a finding. Most false positives
in this kind of review come from a matched pattern that is guarded three lines above.

Keep a running list. Do not write the report until the dimension is finished; interleaving makes you
stop early.

### 3. Verify each candidate before it becomes a finding

For every candidate, answer all four:

1. **Where exactly?** file:line, and the specific expression.
2. **What is the concrete failure?** Real inputs or state → the wrong outcome. If you cannot write the
   scenario, you have a code smell, not a finding.
3. **What guards it?** Look up the call chain. Is there a validation, a gateway policy, a framework
   default that already prevents this? If enforcement lives outside the workspace, this drops to 🟡 or ❌.
4. **Would a reasonable engineer disagree?** If yes, capture their objection in the finding and answer
   it. Findings that survive contact with the owning team are the only ones worth filing.

Discard anything that fails step 2 or 3. A shorter list of surviving findings is worth more than a
long list that gets picked apart in review.

### 4. Severity

Use the profile's severity policy, then apply its uplift rules. Do **not** apply the correlation uplift
here — that happens in `dynatrace-correlate`, after there is telemetry to justify it.

### 5. Write findings

One file per repo: `<workspace>/findings/<repo>.md`. Use `assets/finding-template.md`.

Order by severity, then by confidence. Include the evidence-gap list at the end — it is part of the
deliverable, not an appendix nobody reads. It is what the next reviewer picks up.

### 6. Update the registry

In `config/repos.json`, set `reviewed`, move the dimensions from pending into `dimensions_run`, and
update the `findings` counts and `evidence_gaps`. `review-status` reads only this file, so a review
that does not update it did not happen as far as the estate is concerned.

### 7. Report

- dimensions run, and skipped with reasons
- findings by severity, one line each
- the evidence gaps, with the artifact each needs
- what you would look at next, and why

## Re-reviewing a repo

State what changed since `reviewed` (use `git log --since=<date> --stat` when the repo is a git
checkout). Re-run only the dimensions the changes could plausibly affect, and say which you are
re-running and which you are trusting from last time. Re-running everything on every change is how a
review process stops being run at all.

## Cross-repo patterns

When the same defect shows up in a second repo, do not file it twice in isolation. Note the pattern in
`<workspace>/findings/_patterns.md` with every instance. An estate-wide pattern with six instances is a
different conversation with leadership than six unrelated tickets — it argues for a shared fix, a lint
rule, or a platform change rather than six patches.
