# Identity R3 — One-Page Cheatsheet

> Quick recall. Full detail in `00-MASTER-ARCHITECTURE.md`, drills and modules in `01-STUDY-PLAN.md`, interactive in `index.html`.

---

## The sentence

> Atlas UI never makes a security decision. Password, biometric, token issuance, DPoP validation, fraud scoring — all Sentinel. BFF and Gateway handle business data, **but Gateway still checks token + DPoP on every call.**

## The two sessions (don't conflate them)

| | Security session | Application session |
|---|---|---|
| Owner | **Sentinel** | **Atlas BFF** |
| Holds | tokens, grants, token cache | account summary, business state |
| Started by | `/authorize` → `/token` | `/initAppSession` |
| Linked by | ← `IDP_Correlation_ID` → | |
| Ended by | `unified_logout` | `/logout` |

Ending one does **not** end the other. That's why logout is three-sided.

---

## Flow in 8 beats

```
1  credential encrypted client-side  →  CIAM MFE  →  Sentinel /auth
2  Sentinel validates vs Directory   (User ID → look up card + CIF)
3  Sentinel publishes password-validation event → EventBus   [prefetch starts HERE]
4  Sentinel returns authorization code + callback URL
5  /authorize with code + PKCE code_verifier  →  access + refresh tokens
6  Sentinel publishes SignIn events (+ RiskEngine fraud results)
7  Atlas UI generates DPoP key pair, signs everything from here on
8  /initAppSession → BFF: IDP_Correlation_ID, credential record, account summary
```

## Token storage

| Token | Where | Life |
|---|---|---|
| ID token | not persisted | one use per login |
| **Access** | **memory only** | minutes · refresh at **−15s** |
| **Refresh** | **sessionStorage** | session |
| Remember Me | device cookie/local | long, device-scoped |
| **DPoP private key** | **OS keystore** (doc says IndexedDB) | session |

## The three numbers

| | |
|---|---|
| **15 s** | proactive token-refresh buffer before expiry |
| **60 s** | DPoP `iat` replay window (Sentinel *and* Gateway, independently) |
| **10 / 60 min** | idle timeout / absolute timeout — also = Gateway transaction-cache TTL |

## DPoP proof claims

| Claim | Job |
|---|---|
| `htm` | HTTP method |
| `htu` | target URL — no cross-endpoint reuse |
| `iat` | checked against the 60s window |
| `jti` | unique nonce — replay detection *within* the window |
| `ath` | SHA-256 of the access token — pins proof to *that* token |

## PKCE in four lines

1. invent `code_verifier`
2. send **only** `code_challenge` = SHA-256(verifier) to `/authorize`
3. send the **verifier** at `/token`
4. server re-hashes and compares → stolen code alone is worthless

**PKCE protects the code exchange. It does NOT protect `/authorize` request parameters.** ← that's why the `alg:none` request object is still a finding.

## Logout — the rule

```
/logout (BFF)  →  unified_logout (Sentinel)  →  CLEAR LOCALLY REGARDLESS
                                                 access + refresh + DPoP keys + all client data
```
On a **token-alteration** error: remove DPoP keys → clear tokens + storage → session-expiry page.
**Gateway error only:** call logout on Sentinel **first**.

## High-risk transaction

```
DPoP-signed request → Gateway validates proof, caches PDP result,
parks payload in Transaction Cache (60 min, sub from TXSUB)
   → Sentinel → RiskEngine/the risk vendors
       "Review"          → FAIL outright, no retry
       vendor analyze fails → FAIL (hard)
       notify/EventBus fails  → LOG AND CONTINUE   ← intentional asymmetry
   → OTP step-up → compare token TXSUB vs cached sub
       mismatch → kill token + tx entry + ALL grants (web AND mobile)
```

---

## Evidence markers

| | Meaning |
|---|---|
| ✅ | code path read end to end |
| 🟡 | one side present only |
| ❌ | **NEEDS-EVIDENCE** — not "probably fine", not "a finding" |

## Top 5 open gaps

| # | Gap | § |
|---|---|---|
| 1 | `sub`/TXSUB compare-and-invalidate **not located** | 7 |
| 2 | **`LogoutService` cleanup on failure path — verifiable today, start here** | 6.4 |
| 3 | Server-side 60s window + `jti` cache (Gateway config) | 2.3 |
| 4 | `BusinessAPI_pre_token_generation.js` unverified `id_token_hint` — **critical, un-ticketed** | App. B |
| 5 | `alg:none` request objects — fix already exists in `idp_v2` | 2.2 |

## Review heuristics (§12)

1. token/session/DPoP → **which lifecycle?** (§2.4)
2. replay → 60s window; **is it enforced at Sentinel, Gateway, or both?** they drift
3. logout not clearing → "clear no matter what"; success-only = contradiction
4. HRT failing oddly → check the asymmetry before calling it a bug
5. WealthDesk → timeouts are **overridden**, must not regress

---

## Standards map

| Our thing | Standard |
|---|---|
| code flow | RFC 6749 · **RFC 9700** (Security BCP) |
| `code_verifier` | RFC 7636 (PKCE) |
| signed request object | RFC 9101 (JAR) · RFC 9126 (PAR) |
| DPoP proof | **RFC 9449** |
| mTLS alternative | RFC 8705 |
| `alg:none` family | RFC 8725 (JWT BCP) |
| step-up | RFC 9470 · `acr`/`amr` · PSD2 dynamic linking |
| Wealth SSO | RFC 8693 (token exchange) |
| revocation | RFC 7009 · RFC 7662 (introspection) |
| timeouts / AALs | NIST SP 800-63B |
| biometric direction | FIDO2 / WebAuthn / passkeys |

## The question to have rehearsed

> **DPoP vs mTLS vs BFF-with-cookies for a retail bank SPA + mobile app.**
> Score: XSS resilience · theft blast radius · ops complexity (cert lifecycle) · mobile support · gateway support · latency.
> Pick one. State what would change your mind.
