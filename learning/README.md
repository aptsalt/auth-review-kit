# Identity Mastery

Everything reconstructed from the 32 photos of `04-identity-r3-architecture-explainer.md`
(captured from source architecture screenshots, 2026-08-22).

| File | What it's for | When to open it |
|---|---|---|
| **`explainer.html`** | **Trace Walker** — step through a flow one hop at a time. Each step answers *what / why / what it defeats / what it does NOT defeat*, shows the live state of every token store, and flags **what Atlas lacks** right there. Four flows: Login, API call + refresh, High-risk step-up, Logout + cleanup. | **Start here.** This is the one that actually teaches. |
| **`index.html`** | Interactive study console — three modes: **Architecture** (all 12 sections + both appendices, with sequence diagrams), **Drill** (14 flip cards), **Study plan** (12 modules). Progress checkboxes persist in the browser. | Daily reference and recall. |
| **`00-MASTER-ARCHITECTURE.md`** | The complete reference. Every section, every repo file:line, every evidence marker. Mermaid diagrams render in VS Code preview / Obsidian. | When you need the exact detail or a code reference. |
| **`01-STUDY-PLAN.md`** | The full curriculum — 12 modules with RFC mappings, architect questions, 6-week schedule, ranked reading list. | Weekly planning. |
| **`02-CHEATSHEET.md`** | One page. The sentence, the three numbers, the five gaps, the standards map. | Before a meeting, a review, or an interview. |
| **`corroborated-review.html`** | **Corroborated Review** — the review method as a briefing, plus a per-audience presentation playbook. | Presenting the method to a team or a lead. |
| **`guardrail-loop.html`** | **Guardrail Loop** — turning findings into SDLC change: pattern→control map, intervention ladder, the agentic telemetry→PR→guardrail loop, maturity model, 90-day sequence. | Proposing process change or building the agentic pipeline. |

## Start here

1. Open `explainer.html` → **Login** flow. Walk all 19 steps with the arrow keys. Watch the state panel — that's the token lifecycle becoming intuition.
2. Walk **High-risk step-up**. Stop at the TXSUB comparison step; that's open gap #1 and the highest-severity control in the system.
3. Open `index.html` → **Drill**, try five cards out loud. You'll fail some. That's the point.
4. Go settle **open gap #2** (`LogoutService` cleanup on the failure path) — the only one you can close today with the repos you already have.

**How to study one concept in depth:** find it in the Trace Walker first (it gives you the *why* and the boundary), then read the matching section in `00-MASTER-ARCHITECTURE.md` for the full detail and code references, then do the matching module in `01-STUDY-PLAN.md` for the RFC and the architect question.

## Evidence discipline

✅ verified in-repo · 🟡 one side only · ❌ **NEEDS-EVIDENCE**

❌ is not "probably fine" and it is not "a finding." It is a request for a named artifact.
Keeping that distinction is the habit that reads as architect-level in a review.

## Note on sharing

These files contain internal architecture detail and un-ticketed vulnerabilities.
They are local only — nothing has been published or uploaded.
