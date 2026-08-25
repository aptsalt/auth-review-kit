# reliability-review

A repeatable performance + security review across an estate of repos, corroborated against Dynatrace
production telemetry.

Built out of three weeks of review across 21 repos on the the Atlas identity estate. The point of packaging
it is that the *method* is the asset — the findings are perishable, the mechanism is not.

---

## What's in it

| | |
|---|---|
| **5 skills** | `repo-onboard` · `issue-hunt` · `dynatrace-pull` · `dynatrace-correlate` · `review-status` |
| **3 commands** | `/review-repo` · `/correlate` · `/review-status` |
| **2 scripts** | `dt_pull.py` (Playwright/CDP against your logged-in Dynatrace) · `render_status.py` |
| **Profiles** | Client-specific knowledge, swappable. `northwind-atlas.md` + a blank `_TEMPLATE.md`. |
| **Registry** | `config/repos.json` — the one piece of state everything else reads |

**The design rule:** skills are generic, profiles are specific. Taking this to a new client is a new
profile plus a new registry — no skill changes.

---

## Install

### As a plugin (portable across every repo)

```bash
# from any Claude Code session
/plugin marketplace add <git-url-of-this-repo>
/plugin install reliability-review@reviewer-tools
```

### As a committed folder (zero install, works on clone)

Copy `skills/` and `commands/` into the review workspace's `.claude/` directory:

```
review-workspace/
├── .claude/
│   ├── skills/      <- copy skills/* here
│   └── commands/    <- copy commands/* here
├── CLAUDE.md        <- copy this repo's CLAUDE.md
├── config/
├── profiles/
└── scripts/
```

Teammates clone and the skills are live. **This is the more reliable path for a bank** — nothing to
install, nothing to trust, everything reviewable in a PR.

### Dependencies

```bash
pip install playwright && playwright install chromium
```

Only needed for the Dynatrace pull.

---

## First run

```bash
cp config/repos.example.json config/repos.json
# point "profile" and "workspace" at yours
```

Then in Claude Code:

```
/review-repo atlas-ui        # onboards if new, then reviews
/correlate 30d                # pulls Dynatrace, correlates, writes the report
/review-status                # renders the coverage index
```

---

## The Dynatrace mechanism

No API token. No credentials in the repo. `dt_pull.py` attaches over the DevTools protocol to a browser
**you** logged into through SSO, and reuses that session.

```bash
python scripts/dt_pull.py --launch          # starts Chrome/Edge on an isolated profile
# log into Dynatrace in that window
python scripts/dt_pull.py --mode capture --minutes 3
# browse to Problems, set 30d, scroll — it records what the UI fetches
```

`capture` works on any tenant version because it never needs to know an endpoint. Once a working
endpoint is discovered it is remembered, and later pulls can use `--mode api --window 30d`.

---

## The correlation model

This is the part worth keeping. Each finding gets one verdict:

| Verdict | Means |
|---|---|
| **OBSERVED** | Telemetry names this exact defect. Not a hypothesis any more. |
| **CONSISTENT** | The symptom this defect would produce is present on the right service. |
| **NO SIGNAL** | Instrumented, in scope, quiet for 30 days. Low frequency — **not disproved**. |
| **BLIND** | Uninstrumented or unmapped. Absence proves nothing. |
| **UNOBSERVABLE** | Produces no telemetry even when exploited. APM cannot corroborate it by design. |

```
priority = severity × corroboration × blast_radius
```

`OBSERVED` doubles priority. `NO SIGNAL` removes only 20%. `BLIND` and `UNOBSERVABLE` remove nothing.

**That asymmetry is the whole ethic:** the dashboard is allowed to raise alarm, never to grant
absolution. A forged token returns 200. A leaked secret throws no exception. A missing authorization
check succeeds every single time it is exploited. Those are the highest-severity findings in most
estates and they are exactly the ones a green dashboard would quietly bury.

The correlation also runs **backwards** — problems matching no finding mean either a missed finding, a
repo worth reviewing next, or an entity nobody has mapped. That direction is where the new information
lives.

---

## Taking it to a new client

1. `cp profiles/_TEMPLATE.md profiles/<client>.md` and fill it in
2. New `config/repos.json` with `"profile": "<client>"`
3. Onboard repos

Nothing in `skills/` changes. If you find yourself editing a skill to fit a client, that content
belongs in the profile instead.

---

## Files that must never be committed

- `config/dynatrace.local.json` — tenant URL and discovered endpoints
- `_dynatrace/` — raw problem payloads can carry customer-identifying detail

Both are in `.gitignore`. Check before the first push anyway.
