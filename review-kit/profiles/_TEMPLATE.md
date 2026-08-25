# Profile: <CLIENT / ESTATE NAME>

> A **profile** is the only place client-specific knowledge lives. Skills read this file and stay generic.
> To take this framework to a new client: copy this template, fill it in, point `config/repos.json` at it. Nothing else changes.
>
> Keep this file honest. Everything here is asserted context that the review will trust — a wrong entry
> here produces wrong findings everywhere downstream.

---

## 1. Estate

| | |
|---|---|
| **Client / org** | |
| **Programme** | |
| **Repo root** | `` |
| **Review workspace** | `` |
| **Ticketing system** | (e.g. Jira project key, SECOPS) |
| **Reviewer(s)** | |

## 2. Architecture in one paragraph

<!-- The thing a new reviewer must understand before their first finding is worth reading.
     Who authenticates, who authorises, where the gateway sits, what the data stores are,
     what the event/telemetry backbone is. Six sentences maximum. -->

## 3. Tiers and trust boundaries

| Tier | Components | What crossing this boundary means |
|---|---|---|
| Client | | |
| Gateway / identity | | |
| Services | | |
| Data / events | | |

**The hard rule of this estate:** <!-- e.g. "no security decision happens outside the IdP" -->

## 4. Vocabulary

<!-- Internal acronyms a reviewer will hit in code and in Dynatrace entity names.
     Getting these wrong is the fastest way to file a nonsense finding. -->

| Term | Means |
|---|---|
| | |

## 5. Known-sensitive paths

<!-- Code paths where a bug is materially worse than average: auth, money movement,
     PII, anything regulator-visible. Findings here get severity uplift. -->

- 

## 6. Dynatrace

| | |
|---|---|
| **Tenant URL** | `https://<env>.<region>.dynatrace.com` (or Managed URL) |
| **Management zone(s)** | |
| **Default window** | last 30 days |
| **Login method** | SSO through an already-authenticated browser — see the `dynatrace-pull` skill |

**Entity naming convention:** <!-- how a repo name maps to a Dynatrace service/process-group name.
     If there is no convention, say so — that is itself a finding about observability hygiene. -->

## 7. Repo → Dynatrace entity map

> Every repo must be mapped or explicitly marked `blind`. **`blind` is not a shortcut** — it means
> absence of telemetry proves nothing for that repo, and every correlation verdict there will say so.

| Repo | Dynatrace entity / service | Notes |
|---|---|---|
| | | |

## 8. Severity policy for this estate

| Level | Means here |
|---|---|
| Critical | |
| High | |
| Medium | |
| Low | |

**Uplift rules:** <!-- e.g. "+1 level if the path is in §5", "+1 if corroboration is OBSERVED" -->

## 9. Out of scope

<!-- What this review explicitly does not cover, so absence of findings is never read as a pass.
     e.g. gateway config repos not in the workspace, infrastructure, third-party vendor code. -->

- 
