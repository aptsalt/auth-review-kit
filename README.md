# auth-review-kit

Three things that travel together: a way to **learn** a modern identity architecture, a repeatable
method to **review** an estate of repos against it, and the **house style** that makes the output
readable.

All names in here are fictional. The architecture, the method and the design system are the real
content — the estate they came from is not identified anywhere.

---

## The three parts

### `learning/` — understand the architecture

| File | What it's for |
|---|---|
| **`explainer.html`** | **Trace Walker.** Step through a flow one hop at a time. Each step answers *what / why / what it defeats / what it does NOT defeat*, shows the live state of every token store, and flags where the system is thin. Four flows: Login, API call + refresh, High-risk step-up, Logout + cleanup. **Start here.** |
| **`index.html`** | **Identity Flight Deck.** Full reference — 12 sections + appendices with sequence diagrams, a 14-card recall drill, and a 12-module study plan. Progress persists in the browser. |
| **`corroborated-review.html`** | **Corroborated Review.** The review method as a briefing you can screen-share, plus a per-audience presentation playbook. |
| `00-MASTER-ARCHITECTURE.md` | Complete written reference with evidence markers and code citations. |
| `01-STUDY-PLAN.md` | 12 modules mapped to RFCs, six-week schedule, ranked reading list. |
| `02-CHEATSHEET.md` | One page. The sentence, the three numbers, the standards map. |

Covers OAuth 2.0 authorization-code, PKCE, DPoP (RFC 9449), token storage threat models, session and
logout design, step-up authentication and dynamic linking, SSO patterns, and identifier migration.

### `review-kit/` — run the review

A Claude Code plugin: 5 skills, 3 commands, 2 scripts.

| | |
|---|---|
| **Skills** | `repo-onboard` · `issue-hunt` · `dynatrace-pull` · `dynatrace-correlate` · `review-status` |
| **Commands** | `/review-repo` · `/correlate` · `/review-status` |
| **Scripts** | `dt_pull.py` — pulls telemetry through an already-authenticated browser over CDP, no API token. `render_status.py` — coverage dashboard. |
| **Dimensions** | 19 review lenses, each declaring the production symptom class it would produce |

Install as a plugin, or copy `skills/` and `commands/` into a repo's `.claude/` folder — the second
path needs no install and is reviewable in a PR.

**Design rule:** skills are generic, profiles are specific. A new client is a new
`profiles/<name>.md` plus a new `config/repos.json`. No skill changes.

### `html-style/` — make the output not ugly

The **Plex Console** design system. `CLAUDE-BLOCK.md` pastes into any machine's `CLAUDE.md`;
`base.css` is the validated token system; `template.html` is a working skeleton.

The rule that matters most: *every color is a token on `:root`, and no color is ever declared only
inside a media query or a `[data-theme]` block.* That single rule prevents the unreadable-artifact
failure entirely.

---

## The idea worth keeping

Static review says what *could* fail. Production telemetry says what *did*. Joining them gives each
finding one of five verdicts:

| Verdict | Means |
|---|---|
| **OBSERVED** | Telemetry names this exact defect. Not a hypothesis. |
| **CONSISTENT** | The symptom this defect would produce is present on the right service. |
| **NO SIGNAL** | Instrumented, in scope, quiet. Low frequency — **not disproved**. |
| **BLIND** | Uninstrumented or unmapped. Absence proves nothing. |
| **UNOBSERVABLE** | Produces no telemetry even when exploited. |

```
priority = severity × corroboration × blast_radius
```

`OBSERVED` ×2.0 · `CONSISTENT` ×1.4 · `UNOBSERVABLE` ×1.0 · `BLIND` ×1.0 · `NO SIGNAL` ×0.8

The asymmetry is deliberate:

> **Production telemetry is allowed to raise the alarm on a finding. It is never allowed to grant absolution.**

A forged token returns `200`. A leaked secret throws no exception. A missing authorization check
succeeds every time it is exploited. The most severe findings in most systems are exactly the ones a
green dashboard is silent about — so silence can promote a finding hard, but can barely demote one,
and for some classes it gets no opinion at all.

---

## Getting started

```bash
git clone <this repo>
```

Open `learning/explainer.html` in a browser. Everything is self-contained — no build, no install, no
network calls except Google Fonts (delete the `<link>` tags if that host is blocked; the fallback
stack is built to hold up alone).
