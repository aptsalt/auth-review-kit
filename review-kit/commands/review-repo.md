---
description: Onboard (if new) and run a full dimensioned review pass over a repo
argument-hint: <repo-name-or-path>
---

Run the reliability review process on: **$ARGUMENTS**

1. Read the active profile named in `config/repos.json`.
2. Check whether this repo already has an entry in `config/repos.json`.
   - **Not registered** → use the `repo-onboard` skill first. Do not skip it; the review depends on
     the source index it produces.
   - **Already registered** → report when it was last reviewed and what has changed since, then
     re-review only the dimensions those changes could plausibly affect.
3. Use the `issue-hunt` skill for the review pass itself.
4. Update `config/repos.json` and tell me: dimensions run, dimensions skipped and why, findings by
   severity, evidence gaps, and what you would look at next.

Hold the evidence discipline: ✅ verified · 🟡 partial · ❌ needs-evidence. Anything you could not
actually see in this workspace is an evidence gap with a named artifact, not a finding and not a pass.
