---
name: repo-onboard
description: Add a new repository to the reliability review process — register it, map it to a Dynatrace entity, build its source index and interaction map, and queue it for review. Use whenever the user says "add this repo to the review", "onboard <repo>", "new repo to review", "index this repo", "we got another repo", or points at a codebase that is not yet in the coverage index. Produces the registry entry and index that every later skill (issue-hunt, dynatrace-correlate, review-status) depends on.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Repo Onboard

Bring a new repository into the same review process every other repo went through, so findings are
comparable across the estate and nothing is reviewed from a blank slate.

**Onboarding is not reviewing.** This skill produces the *map*. `issue-hunt` does the review. Keep them
separate — an index built while hunting is an index shaped by what you happened to find.

## Before you start

Read the active profile (`profiles/<name>.md`, named in `config/repos.json` → `profile`). It carries the
architecture, vocabulary and sensitive paths. A reviewer who onboards a repo without the profile will
mis-tier it and mis-map its telemetry.

## Steps

### 1. Register

Append an entry to `config/repos.json`. If the file does not exist, copy `config/repos.example.json`.

```json
{
  "name": "<repo-dir-name>",
  "path": "<relative path from repo root>",
  "language": "<primary language/framework>",
  "kind": "spa | service | library | config | adapter | infra",
  "tier": "client | gateway-identity | service | data-events",
  "dynatrace": { "entity": null, "type": null, "status": "unmapped" },
  "onboarded": "<YYYY-MM-DD>",
  "reviewed": null,
  "dimensions_run": [],
  "findings": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "evidence_gaps": 0,
  "notes": ""
}
```

`tier` comes from the profile's tier table. It drives which review dimensions apply — a config repo and
a public-client SPA get very different passes.

### 2. Map to Dynatrace — or declare it blind

Set `dynatrace.status` to one of:

| Status | Meaning |
|---|---|
| `mapped` | A named service/application entity exists. Record `entity` and `type` (`SERVICE`, `APPLICATION`, `PROCESS_GROUP`). |
| `blind` | No runtime entity — a library, config repo, or genuinely uninstrumented service. |
| `unmapped` | Not yet determined. **A temporary state.** Resolve it before the first correlation run. |

This single field decides how correlation reads silence later. `blind` means absence of telemetry proves
nothing; `mapped` with a clean window is real evidence. Leaving everything `unmapped` quietly converts
the whole correlation report into noise, so resolve it deliberately.

If the profile has no naming convention, find the entity by searching Dynatrace for the service's actual
runtime name — usually from the deployment descriptor, `application.yml`, `package.json` name, or the
`Dynatrace-*` env vars in the pipeline config. Record how you found it in `notes`; that is how the
convention eventually gets written down.

### 3. Build the source index

Write `<workspace>/source-index/<repo>.md`. Aim for the smallest document that lets a reviewer who has
never opened the repo know where to look. Cover:

- **Entry points** — HTTP routes, message consumers, scheduled jobs, exported public API, CLI
- **Outbound calls** — every downstream this repo talks to, and *how* (client class, timeout, retry policy)
- **Auth touchpoints** — anywhere a token, credential, key, cookie or session is read, written or validated
- **State** — caches, session stores, local/session storage, in-memory singletons, DB access
- **Config** — files, env vars, remote/dynamic config; flag anything security-relevant that is remotely mutable
- **Third-party** — dependencies doing crypto, JWT, HTTP, or serialisation
- **Hot paths** — what runs on every request or every page load

Record file:line for each. Everything downstream cites this index, so an imprecise index produces
uncitable findings.

### 4. Place it in the architecture

Write a short interaction note into `<workspace>/interaction-map/<repo>.md`: who calls this repo, what
it calls, which trust boundaries it sits behind, and which flows in the profile it participates in.

If the repo cannot be placed in the profile's architecture, that is a finding in itself — either the
profile is incomplete or the repo is orphaned. Say which.

### 5. Queue the dimensions

Using `references/tier-dimensions.md`, list which review dimensions apply to this repo's `tier` and
`kind`, and write them into `dimensions_run` as pending. Do not run them here.

### 6. Report

Tell the user, briefly:

- what the repo is and where it sits
- its Dynatrace mapping status (and if `blind`, say plainly what that costs the review)
- how many entry points, outbound calls and auth touchpoints were indexed
- which dimensions are queued
- anything already visibly wrong — but as an *observation*, not a finding. Findings come from `issue-hunt`.

## Onboarding several repos

Do them one at a time and register each before moving on. A half-registered batch is worse than a
smaller complete one, because `review-status` will report coverage that does not exist.

If the user asks to onboard many at once, onboard them in tier order — gateway/identity first, then
services, then clients, then config and libraries. Earlier tiers give the vocabulary that makes the
later ones fast to read.
