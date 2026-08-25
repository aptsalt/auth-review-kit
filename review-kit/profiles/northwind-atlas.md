# Profile: Northwind — Identity Modernization (Release 3)

> Filled from the R3 architecture explainer and three weeks of review across 21 repos.
> Update the repo table as repos are onboarded. Everything client-specific lives here and nowhere else.

---

## 1. Estate

| | |
|---|---|
| **Client / org** | Northwind |
| **Programme** | Identity Modernization, Release 3 |
| **Repo root** | `estate/` |
| **Review workspace** | `estate/review-workspace/` |
| **Ticketing system** | SECOPS |
| **Reviewer(s)** | D. Kandari |

## 2. Architecture in one paragraph

A customer hits the Atlas SPA, which federates in the AuthKit MFE micro-frontend. Credentials are
encrypted client-side and validated by Sentinel against the Directory. Sentinel runs OAuth 2.0 authorization-code with PKCE and issues **DPoP-bound** tokens, so every
API call carries a freshly signed proof checked against a 60-second window by both Sentinel and the Edge Gateway. A **second, separate application session** lives in Atlas BFF, linked only by
`IDP_Correlation_ID`. Sensitive actions escalate to a high-risk-transaction step-up scored by RiskEngine
(VendorScore / DeviceTrust / BehaviorIQ), with the pending payload parked in a Gateway transaction cache and re-bound
to the user by a TXSUB `sub` comparison after OTP. Every login, logout, step-up and fraud verdict is
published to the EventBus and consumed by IdP Datamart, Warehouse and Splunk.

## 3. Tiers and trust boundaries

| Tier | Components | What crossing this boundary means |
|---|---|---|
| Client | Atlas UI (SPA), AuthKit MFE MFE | Public client — cannot hold a secret. Everything downstream compensates for that. |
| Gateway / identity | Sentinel, Edge Gateway | Every security decision happens here. Gateway validates token + DPoP on **every** call. |
| Services | Atlas BFF, profile-service, credential services | Business data only — but BFF owns the app session. |
| Data / events | Directory, GridCache, EventBus, IdP Datamart, Warehouse, Splunk | Audit and detection layer. Never carries tokens, verifiers, PAN or biometric material. |

**The hard rule of this estate:** Atlas UI never makes a security decision. Password check, biometric
check, token issuance, DPoP validation and fraud scoring all happen in Sentinel. A finding that assumes
client-side enforcement is almost always misreading the architecture.

## 4. Vocabulary

| Term | Means |
|---|---|
| Sentinel / the IdP platform | the IdP platform — the IdP, called "Sentinel" internally |
| Gateway | Edge Gateway — the gateway enforcing DPoP + step-up policy |
| BFF | Atlas's backend-for-frontend, owns the **application** session (not the security session) |
| Directory | LDAP-style credential directory |
| GridCache | In-memory data grid used for login-optimization prefetch |
| EventBus | Kafka-like event fabric |
| RiskEngine | Enterprise Risk Assessment — orchestrates VendorScore, DeviceTrust, BehaviorIQ |
| HRT | High-Risk Transaction — needs risk assessment and possible step-up |
| TXSUB | The `sub` claim in the access token, binds a transaction-cache entry to its creator |
| NativeMFA | Mobile Multi-Factor Authentication — Sentinel's native biometric flow |
| CIF | Internal customer identifier formats |
| DPoP | Demonstration of Proof-of-Possession, RFC 9449 |

## 5. Known-sensitive paths

Findings here get a severity uplift.

- Token issuance and validation — `pre_token_generation.js` mapping rules, access policies
- DPoP proof construction and verification
- Logout and cleanup paths (`logout()`, `cleanupTokensAndTimeouts()`, `LogoutService`)
- High-risk transaction step-up and the transaction cache
- Anything reading or writing Directory credentials or aliases
- Client-side credential encryption before `/auth`
- Anything that logs: a `code_verifier`, a token, a PAN, or biometric material

## 6. Dynatrace

| | |
|---|---|
| **Tenant URL** | *(set in `config/dynatrace.local.json` — never commit it)* |
| **Management zone(s)** | *(fill on first pull)* |
| **Default window** | last 30 days |
| **Login method** | SSO through an already-authenticated browser — see the `dynatrace-pull` skill |

**Entity naming convention:** not yet established. Repo names and Dynatrace service names do **not**
align mechanically in this estate, so the map in §7 is maintained by hand. That mismatch is itself worth
raising as an observability-hygiene item — it makes automated correlation impossible for anyone but a
reviewer who already knows the estate.

## 7. Repo → Dynatrace entity map

> Every repo must be mapped or explicitly marked `blind`. **`blind` is not a shortcut.** It means
> absence of telemetry proves nothing there, and every correlation verdict for that repo will say so.

| Repo | Dynatrace entity / service | Notes |
|---|---|---|
| `atlas-ui` | *(unmapped)* | Atlas UI SPA. Front-end — RUM application, not a service. |
| `authkit-mfe` | *(unmapped)* | MFE. RUM. |
| `sentinel-sdk-core` | *(unmapped)* | Library — likely `blind`, surfaces only inside its consumers. |
| `credential-auth-service` | *(unmapped)* | |
| `sentinel-config` | `blind` | Config repo. No runtime entity of its own. |
| `eventbus-adapter` | *(unmapped)* | |
| `customer-info-api` | *(unmapped)* | |
| `channels-auth-api` | *(unmapped)* | |
| *(+ remaining repos of the 21 as they are onboarded)* | | |

## 8. Severity policy for this estate

| Level | Means here |
|---|---|
| **Critical** | Authentication bypass, identity spoof, unauthorised money movement, or credential/PII disclosure |
| **High** | Token or session integrity loss, step-up bypass, state surviving logout, tamperable security parameters |
| **Medium** | Availability or performance degradation on a customer path; fail-open where fail-closed was intended |
| **Low** | Defence-in-depth weakening with no direct exploit path; hygiene |

**Uplift rules:**
- `+1 level` if the code path is listed in §5
- `+1 level` if correlation verdict is `OBSERVED` (there is live production signal behind it)
- `-1 level` if verdict is `NO SIGNAL` **and** the service is well instrumented — but never below Low,
  and **never** apply this when the repo is `blind`

## 9. Out of scope

Absence of findings in these areas is **not** a pass — they are simply not visible from the workspace.

- Gateway gateway policy and config (server-side DPoP window, PDP cache, transaction cache)
- Atlas BFF backend (`/initAppSession`, session handling)
- Directory internals — password hashing, policy, lockout counters
- Credential Management Service, `SecureFormMigrationService`, Client Credential Orchestration API
- Infrastructure, network, and third-party vendor code (VendorScore, DeviceTrust, BehaviorIQ)

## 10. Standing evidence gaps

Carried forward across reviews. These are open questions with named artifacts, not findings.

| # | Gap | Artifact needed |
|---|---|---|
| 1 | TXSUB `sub` compare-and-invalidate not located | transaction-cache access policy; `AccessPolicyFunctions.js` |
| 2 | `LogoutService` cleanup on the failure path | **answerable from the current workspace — settle this first** |
| 3 | Server-side 60s DPoP window; existence of a `jti` replay cache | Gateway policy |
| 4 | `cnf`/`jkt` token-to-key binding at issuance | Sentinel token-issuance config |
| 5 | Gateway PDP cache TTL (= the revocation gap) | Gateway config |
| 6 | Monitoring on the HRT soft-fail path (notify/EventBus) | alerting config — if this fails silently, fraud analytics go dark |
