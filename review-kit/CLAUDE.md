# Reliability Review — working agreement

> Copy this block into the CLAUDE.md of the repo where reviews are run (e.g. `review-workspace/`),
> or keep this file at the root of that workspace.

## What this workspace is

A repeatable performance and security review across an estate of repos, corroborated against Dynatrace
production telemetry. The mechanism lives in the `reliability-review` plugin; the client-specific
knowledge lives in `profiles/<name>.md`; the state lives in `config/repos.json`.

## Read before reviewing anything

1. `profiles/<active>.md` — architecture, vocabulary, tiers, sensitive paths, severity policy, out of scope
2. `config/repos.json` — what has been reviewed, what is mapped to which Dynatrace entity
3. `<workspace>/source-index/<repo>.md` — if reviewing a repo that has one

## Evidence discipline — the rule that makes this work

| Marker | Means | You may |
|---|---|---|
| ✅ verified | Read the code path end to end in this workspace | Raise a finding |
| 🟡 partial | One side present, counterpart elsewhere | Raise a finding, stated as conditional |
| ❌ needs-evidence | Deciding code or config is not in the workspace | Record an evidence gap naming the artifact |

**❌ is not "probably fine" and it is not "a vulnerability."** It is a request with an address on it.

Never mark a dimension clean that you could not actually evaluate. Marking something clean that you
could not see is the one failure mode that discredits the entire review.

## Findings must survive contact

Every finding: file:line, a concrete failure scenario, what guards it today, and the strongest
objection the owning team will raise plus your answer. If you cannot write the failure scenario, it is
a code smell, not a finding.

Prefer a short list that holds up to a long list that gets picked apart.

## Telemetry promotes, it does not absolve

A quiet Dynatrace has four possible causes: not happening, not instrumented, filtered out, or
invisible-by-design. Only the first is evidence. `secret-leak`, `token-integrity` and `client-crypto`
findings produce no telemetry even when actively exploited — a green dashboard says nothing about them.

## Scope honesty

Say what was not covered, every time: dimensions skipped, repos not reviewed, areas in the profile's
out-of-scope list. Absence of findings is never a pass unless someone actually looked.

## Never commit

- `config/dynatrace.local.json` (tenant URL, discovered endpoints)
- `_dynatrace/` (raw telemetry pulls — may contain customer-identifying detail)
- Anything containing a token, credential, PAN, or customer data pulled from a problem payload
