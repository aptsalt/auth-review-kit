# Findings — `<repo>`

> Reviewed `<YYYY-MM-DD>` · profile `<profile>` · dimensions run: `<list>` · skipped: `<list + reason>`
> Evidence markers: ✅ verified in workspace · 🟡 partial, counterpart elsewhere · ❌ needs evidence

---

## F-<repo>-001 — <one-line statement of the defect>

| | |
|---|---|
| **Severity** | Critical / High / Medium / Low |
| **Dimension** | `<dimension-id>` |
| **Evidence** | ✅ / 🟡 |
| **Where** | `path/to/file.ts#L120-L134` |
| **Correlation** | *(filled by `dynatrace-correlate`)* |

**What the code does**

<!-- Plain description of the actual behaviour, not the fix. Quote the deciding expression. -->

**Failure scenario**

<!-- Concrete inputs or state → the wrong outcome. If you cannot write this sentence, this is not a
     finding. Name the actor where it matters: an attacker with X, or a customer doing Y under Z. -->

**What guards it today**

<!-- The call chain you checked and what you ruled out. This is what makes the finding survive review:
     it shows you looked for the reason it might be fine. If a guard exists elsewhere and you cannot
     see it, this finding is 🟡 and says so here. -->

**Why this severity**

<!-- Cite the profile's severity policy and any uplift rule applied (sensitive path, correlation). -->

**Suggested direction**

<!-- Direction, not a patch — the owning team knows their code better. Where the fix already exists
     somewhere in the estate (a hardened sibling template, a correct implementation in another repo),
     point at it: that turns a finding into a rollout. -->

**Anticipated objection**

<!-- The strongest argument the owning team will make, and your answer. Omit only if there isn't one. -->

---

## Evidence gaps

Not findings. Open questions with an address on each one. This section is the handover to the next
reviewer — and to whoever can grant access to the missing artifact.

| # | Question | Artifact needed | Blocks |
|---|---|---|---|
| 1 | | | F-<repo>-00X |

---

## Observations

Things worth knowing that are not defects — architectural notes, patterns, things that are done well
and should be copied elsewhere. Keeping these separate protects the credibility of the findings list.

- 

---

## Not covered

Dimensions skipped and why, plus anything in the profile's out-of-scope list that touches this repo.
**Absence of findings in these areas is not a pass.**

- 
