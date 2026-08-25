# CIAM / OAuth / DPoP → Architect-Level Mastery Track

**Goal:** be the person in the room who can (a) draw this system from memory, (b) name the RFC and the threat behind every control in it, (c) say precisely which claims are *evidenced* vs *assumed*, and (d) design the next version — including the parts Northwind got wrong.

**Anchor artifact:** `00-MASTER-ARCHITECTURE.md` in this folder. Every module below points back into it. You are not studying OAuth in the abstract; you are studying **the system you already work on**, and using the standards to explain *why it is shaped that way*.

---

## The three levels you're moving through

| Level | You can... | Test |
|---|---|---|
| **1. Operator** | Follow the flow, find the code, explain what a step does | Redraw §3 and §7 sequence diagrams from memory |
| **2. Reviewer** | Say *what breaks* if a step is removed or reordered, and cite the threat | For every control, state the attack it defeats and the attack it does *not* |
| **3. Architect** | Design an alternative, defend the trade-off, and know the migration path | Given a greenfield bank, justify DPoP vs mTLS vs BFF, with cost/latency/ops impact |

Most engineers stall at Level 1 because they learn the *flow* and not the *threat model*. The drill that moves you to Level 3 is at the bottom: **"remove one control, name the exploit."**

---

## Module 0 — Foundations you must not skip (2–3 hours)

You cannot reason about token binding without these primitives cold:

- **Symmetric vs asymmetric crypto**, signature vs encryption, why "signed" ≠ "confidential".
- **Hash functions**: preimage resistance — *this* is why sending SHA-256(`code_verifier`) is safe (§2.2).
- **Nonce vs timestamp vs counter** as replay defences, and why DPoP uses `jti` *and* `iat` (§2.3).
- **The browser security model**: same-origin policy, XSS vs CSRF (different attacks, different defences), CSP, `SameSite`, why `localStorage` is readable by any injected script but memory-only variables are only readable while the page lives.
- **TLS**: what it protects (transport) and what it does not (the endpoints, the logs, the browser).

**Self-check:** Why does storing the access token in memory help against XSS *at all*, given an XSS payload runs in the same page? (Answer: it doesn't stop an active exploit, it stops *persistence and exfiltration after reload* — which is why it's a mitigation, not a fix. Being able to say this precisely is a Level-2 marker.)

---

## Module 1 — OAuth 2.0 core (§2.1)

**Read:** RFC 6749 (§1, §4.1, §10 — skip the grant types nobody uses), RFC 6750 (bearer tokens), **RFC 9700 (OAuth 2.0 Security Best Current Practice)** ← the single highest-value document on this list. Then RFC 8252 (OAuth for native apps).

**Master:**
- Roles: resource owner / client / authorization server / resource server. Map them onto §1: customer / Atlas UI / Sentinel / Atlas APIs behind Gateway.
- **Why authorization code and nothing else.** Implicit grant is dead (token in URL fragment → browser history, referrer, logs). ROPC is dead (client sees the password). Be able to explain *why* each died.
- Public vs confidential clients — Atlas UI is **public** (no secret it can protect), which is the whole reason PKCE exists.
- `redirect_uri` exact-match registration, `state` parameter, open redirect → the classic authorization-code interception chain.
- Refresh token rotation and reuse detection (family invalidation).

**Map to our system:** §2.1, §2.4, §6.1. Note that Northwind refreshes proactively at a 15s buffer — ask yourself what happens under clock skew between browser and Sentinel.

**Architect question:** Northwind uses refresh tokens in `sessionStorage`. What does the **BFF (Backend-for-Frontend) pattern** do instead, and why is it now the OAuth WG's recommendation for browser apps? What does Northwind gain and lose by *not* using it, given they already have Atlas BFF sitting right there as a BFF-shaped component?

---

## Module 2 — OpenID Connect (§2.1, §6.3, Appendix B #1)

**Read:** OIDC Core (§2 ID token, §3.1 auth code flow, §15.1 signature validation), OIDC Discovery, **OIDC RP-Initiated Logout**, OIDC Front-Channel and Back-Channel Logout.

**Master:**
- ID token vs access token — **audience is the whole point**. ID token audience = the client; access token audience = the resource server. Using one where the other belongs is a classic architecture smell.
- **ID token validation rules** (iss, aud, exp, nonce, signature, `alg` allow-list). Then read Appendix B row 1 again: a server decoding `id_token_hint` with `indexOf('.')` + base64 + `JSON.parse` and trusting `sub` is exactly the failure this checklist exists to prevent. **This is the most instructive line in the entire codebase — study it until you can explain the exploit in 30 seconds.**
- `id_token_hint` semantics in logout — why it exists, and why it must be *verified* before its `sub` is trusted.
- Session management: front-channel vs back-channel logout, and why single logout is genuinely hard.

**Architect question:** Northwind's logout is client-orchestrated (UI calls BFF, then Sentinel, then clears). What would **back-channel logout** change, and how would it fix the "failed logout leaves tokens behind" risk in §6.4 structurally rather than by convention?

---

## Module 3 — PKCE and request integrity (§2.2, Appendix B #2/#3)

**Read:** RFC 7636 (PKCE), RFC 9101 (JAR — JWT-Secured Authorization Request), RFC 9126 (PAR — Pushed Authorization Requests), RFC 9207 (`iss` in authorization response — mix-up attack defence).

**Master:**
- The `S256` vs `plain` challenge methods and why `plain` must be rejected server-side.
- **What PKCE protects and what it does not.** PKCE binds *the code exchange*. It does **not** protect the integrity of the `/authorize` request parameters — which is precisely why Northwind's `alg:none` request object (§2.2) is still a real finding even though PKCE is correctly implemented. Being able to draw that boundary is a Level-2/3 distinction most candidates fail.
- **JAR**: signing the request object. `request_object_signing_alg: none` vs `RS256` — read `clients.j2#L25` vs the `idp_v2` template. This is a *live config drift* in your own system: one template fixed, one not.
- **PAR**: pushing the request server-side removes front-channel parameter tampering entirely. Know it as the strategic answer to the JAR finding.

**Architect question:** Given `idp_v2/oidcp/clients.j2` already uses RS256, what's the migration risk in flipping `spapublicclient` off `none`? (Client must actually sign; key distribution/JWKS; rollback path; staged per-client cutover.) Write the migration plan — that's the deliverable an architect is asked for, not the finding.

---

## Module 4 — JWT / JOSE and the `alg:none` family (Appendix B, all rows)

**Read:** RFC 7519 (JWT), 7515 (JWS), 7517 (JWK), 7518 (JWA), and **RFC 8725 (JWT Best Current Practices)**.

**Master:**
- The `alg:none` attack, the **HS256/RS256 confusion attack** (public key used as HMAC secret), `kid` injection/path traversal, `jku`/`x5u` SSRF.
- **Always use an algorithm allow-list; never trust the header's `alg`.** Then re-read `JWTtoMap.js#L36` accepting `alg=="none"`.
- JWKS endpoints, key rotation, `kid` selection, caching and rotation races.
- Claims: `iss`, `sub`, `aud`, `exp`, `nbf`, `iat`, `jti`. Clock skew tolerance and why it's a security parameter, not a convenience.
- JWT vs opaque tokens + introspection (RFC 7662) — the revocation trade-off. **Note Northwind has it both ways:** DPoP-bound JWT access tokens *and* a Sentinel token cache that gets invalidated on logout (§6.3). Understand why that hybrid exists.

**Architect question:** Where should signature verification live in a system with a gateway (Gateway) *and* an IdP (Sentinel) *and* backend services? Argue for gateway-terminated verification vs defence-in-depth verification at each hop, with the cost.

---

## Module 5 — DPoP and sender-constrained tokens (§2.3, §7) ← **your differentiator**

**Read:** **RFC 9449 (DPoP)** end to end — this is the one to know cold. Then RFC 8705 (mTLS-bound tokens) for the alternative, and the OAuth token-binding history (RFC 8471, deprecated) for why the industry landed here.

**Master:**
- The proof JWT structure: `typ: dpop+jwt`, `jwk` in the header, claims `htm`, `htu`, `iat`, `jti`, and **`ath`** (hash of the access token). Know why each exists. §2.3 in our doc lists `htm/htu/iat/jti/ath` — `ath` is what stops a proof minted for one token being paired with another.
- **Token binding at issuance**: the `cnf`/`jkt` thumbprint claim in the access token is what ties it to the key. Without it, DPoP proves possession of *a* key, not *the bound* key.
- **`DPoP-Nonce`** (server-provided nonce): the stronger replay defence vs a time window. Northwind uses a **60-second `iat` window** instead. Know the trade-off: a nonce requires server state and an extra round trip on first use; a time window requires clock sync and tolerates replay *within* the window.
- **Replay caches:** a correct time-window implementation still needs `jti` uniqueness tracking within the window. Ask: does Sentinel/Gateway actually keep a `jti` cache, or only check `iat`? **That question is currently unanswerable from our repos (§2.3 gap) and is a genuinely good thing to go find out.**
- **Key storage:** Northwind's code is stronger than its own doc — a native plugin puts the private key in the OS keystore, not IndexedDB. Compare to non-extractable `CryptoKey` in WebCrypto + IndexedDB (the standard web answer). Know why non-extractable keys still don't stop an XSS attacker from *using* the key (signing oracle) — only from stealing it.
- **The DPoP lifecycle lock** (`auth.service.ts#L1178-L1200`): concurrency in key minting. This is an availability/correctness concern that most security engineers miss entirely.

**Architect question:** Compare DPoP vs mTLS vs BFF-with-cookies for a retail bank SPA + mobile app. Score them on: XSS resilience, token-theft blast radius, ops complexity (cert lifecycle!), mobile support, gateway support, and latency. Then state which one you'd pick and the condition under which you'd change your mind. **Have this answer rehearsed — it is the archetypal senior-architect interview question in this domain.**

---

## Module 6 — Browser token storage and the client threat model (§2.1, §2.4)

**Read:** OWASP ASVS v5 chapters on session management and authentication; OAuth for Browser-Based Applications (the IETF BCP draft); OWASP Top 10 A01/A02/A07.

**Master:**
- The storage matrix: memory / `sessionStorage` / `localStorage` / cookies (`HttpOnly`, `Secure`, `SameSite=Lax|Strict|None`) / IndexedDB / OS keystore. For each: who can read it, does it survive reload, does it survive tab close, is it sent automatically.
- Why "automatically sent" (cookies) creates CSRF, and why "manually attached" (bearer headers) creates XSS exposure. **There is no storage location that is safe against both — the choice is which attack you'd rather defend elsewhere.** Say this sentence in an interview and you sound like an architect.
- CSP as the actual XSS control; subresource integrity; the risk surface of a **micro-frontend federating third-party code into the auth page** (§1 — `authkit-mfe` runs inside Atlas UI; module federation means a compromise of the MFE build pipeline is a compromise of the login screen).

**Architect question:** Northwind's MFE owns the password screen and is federated into Atlas UI at runtime. Threat-model that supply chain. What controls (SRI, pinned versions, CSP, build provenance, isolated origin/iframe) would you require?

---

## Module 7 — Session management, timeouts, and logout (§6)

**Read:** OWASP Session Management Cheat Sheet; NIST SP 800-63B (§4 AAL reauthentication requirements, §7 session management).

**Master:**
- **Idle vs absolute timeout** — and why you need both. Northwind: 10 min idle / 60 min absolute. NIST 800-63B AAL2 says 12h absolute / 30 min inactivity; **Northwind is stricter than the baseline** — know that, so you can defend the UX cost.
- **Two-session architectures** (security session in Sentinel vs application session in BFF). Correlation IDs, orphaned sessions, and the failure mode where one outlives the other.
- Revocation: RFC 7009 token revocation, refresh-token family invalidation, and the gap between "token revoked at IdP" and "token still accepted by a gateway with a cached decision" — **note Gateway caches PDP results (§7)**. That cache is a revocation-latency hole. Quantify it.
- Config-driven timeouts (`app-config.service.ts`) → **a config regression is a security regression**. Where's the test? This is a real gap worth owning.

**Architect question:** Design a logout that is correct even when three of four calls fail. (Hint: back-channel logout + short access-token TTL + refresh revocation + unconditional local clear. Note how each layer covers a different failure.)

---

## Module 8 — Step-up authentication and risk (§7)

**Read:** **RFC 9470 (OAuth 2.0 Step-Up Authentication Challenge)**, OIDC `acr`/`amr` claims, `acr_values` and `max_age`; PSD2 SCA **dynamic linking** requirements; the OpenID **Shared Signals / CAEP** framework for continuous access evaluation.

**Master:**
- Step-up as a *token property* (`acr` in the token) vs step-up as a *transaction property* (a cached transaction re-bound after OTP). **Northwind does the second.** Understand why: the transaction payload is parked in Gateway's cache and re-bound via `sub`/TXSUB comparison. That is essentially hand-rolled **dynamic linking** — the PSD2 requirement that the authentication be cryptographically tied to the *specific amount and payee*.
- The `sub`/TXSUB compare-and-invalidate (§7 step 4) is the anti-hijack control. Model the attack it defeats: attacker gets a step-up completed against a transaction they didn't initiate. Then note Appendix B says **this block could not be located in code**. Own that gap.
- **Fail-open vs fail-closed asymmetry**: hard-fail on the risk-assessment call, soft-fail on the notify/EventBus publish. This is a deliberate availability/security trade. Be able to defend it *and* to say what monitoring makes it safe (if the notify path silently fails forever, your fraud analytics go dark while transactions sail through).

**Architect question:** Northwind fails a transaction outright when RiskEngine returns "Review" — no retry, no soft-decline. Defend that decision to a product manager whose false-positive rate is hurting conversion, then propose the design that keeps the security property while improving UX (e.g. escalate to a stronger factor rather than decline).

---

## Module 9 — Federation and SSO (§8)

**Read:** SAML 2.0 Web Browser SSO profile (enough to review it), **RFC 8693 (OAuth Token Exchange)**, OIDC federation basics.

**Master:**
- SAML vs OIDC: XML-DSig vs JWS, why SAML signature-wrapping (XSW) attacks exist, why SAML persists in enterprise/partner integrations (LegacyWealth, §8).
- **Token exchange** (RFC 8693) — the mechanism behind "SSO into Wealth platform".
- **Atlas as an external IdP** for National Sign-In (GovPortal, TaxPortal). That's a completely different trust direction: Northwind is the *asserting party*. Different threat model, different obligations.
- Deep links → the authorization-code interception threat on mobile (RFC 8252, claimed HTTPS redirects vs custom schemes).
- The §8 lesson to internalise: **"SSO doesn't use DPoP" is not automatically a finding** — some paths are outside the token boundary by design. An architect distinguishes an architectural boundary from a gap.

---

## Module 10 — Credentials, identifiers, and directories (§3, §9)

**Master:**
- Password storage (bcrypt/scrypt/Argon2id), the fact that this system delegates it to Directory/LDAP, and what you'd still verify.
- **Identifier design** — the heart of §9. Card number as login = **enumerable and guessable**; migration to User ID + GUID-based alias is a *security architecture* change driven by a regulator (the prudential regulator). Understand pairwise/sectoral identifiers in OIDC as the same idea.
- Credential migration with a **backup branch + rollback** (§9) — a pattern worth stealing. Any identity migration needs a reversible checkpoint.
- The 64-byte **hashed-card alias** that preserves biometric registration across conversion: a nice example of *identity continuity across a credential change*.
- Client-side credential encryption before `/auth` (RSA + AES envelope, `payload-encryption.service.ts`). Ask the sharp question: **what does this add on top of TLS?** (Defence against TLS-terminating middleboxes and against the credential appearing in gateway logs — a legitimate but narrow benefit. Know the honest answer, including that it does *not* protect against a compromised page.)

---

## Module 11 — Event-driven security telemetry (§1, §3, §4, §6.3)

**Master:**
- Every security event lands on EventBus → Splunk / IdP Datamart / Warehouse. Understand this as the **audit and detection layer**, which is a first-class architectural concern, not plumbing.
- What must never be in an event: `code_verifier`, tokens, raw PAN, biometric material. §2.2 explicitly warns about logging the `code_verifier`.
- Event-driven prefetch (§4) as a *pre-authorization* action — the trust boundary question from `00-MASTER-ARCHITECTURE.md` §4.
- Ordering, at-least-once delivery, and what a duplicated `LogoutEvent.L0` or a lost `LoginFailure` does to lockout counting and fraud models.

---

## Module 12 — Where this is all going (so you can talk about the *next* architecture)

- **FIDO2 / WebAuthn / passkeys** — phishing-resistant auth, origin binding, and why they subsume NativeMFA's model (§5) more cleanly.
- **Continuous access evaluation** (CAEP/SSF) — replacing "60-minute absolute timeout" with real-time revocation signals.
- **BFF pattern + `HttpOnly` cookies** as the mainstream browser-app recommendation vs Northwind's DPoP-in-the-browser bet.
- **Zero-trust / token-per-hop** service architectures, workload identity (SPIFFE), and where a gateway-terminated token model stops being enough.
- **Wallet/verifiable credentials** — where CIAM is heading for identity proofing.

Being able to say "here's what we built, here's what's replacing it, here's the migration cost" is exactly what separates an architect from a senior engineer.

---

## The core drill: "remove one control, name the exploit"

Do this out loud, one row per sitting. It is worth more than re-reading the RFCs.

| Remove this control | What breaks | Which §/RFC |
|---|---|---|
| PKCE `code_verifier` | Stolen auth code is redeemable by the attacker | §2.2 / RFC 7636 |
| Signed request object (already missing!) | `redirect_uri`/`scope` tampering at `/authorize` | §2.2 / RFC 9101 |
| DPoP entirely | Any leaked access token is replayable from anywhere | §2.3 / RFC 9449 |
| `ath` claim in the DPoP proof | A proof can be paired with a *different* access token | §2.3 / RFC 9449 |
| 60-second `iat` window | Captured proofs replayable indefinitely | §2.3 |
| `jti` uniqueness tracking | Replay *within* the 60s window | §2.3 |
| Access-token-in-memory rule | Token persists across reload, exfiltratable post-XSS | §2.1 |
| DPoP key cleanup on logout | Stale key reusable after "logout" | §6.3/§6.4 |
| Unconditional local clear on logout failure | Tokens survive a failed logout | §6.4 / Appendix B |
| `sub`/TXSUB transaction compare | Step-up hijack: OTP completed against another user's parked transaction | §7 |
| Transaction-cache 60-min TTL | Stale step-up outlives its session | §6.2/§7 |
| ID-token signature verification server-side | **Forge any `sub` → full auth bypass** | Appendix B #1 |
| Absolute 60-min timeout | Indefinite session on a compromised device | §6.2 |
| Client-side credential encryption | Credential visible to TLS-terminating middleboxes and gateway logs | §3 |

---

## Suggested 6-week schedule (~6–8 h/week)

| Week | Modules | Output you produce (do not skip the output) |
|---|---|---|
| 1 | 0, 1 | Redraw §1 context + §2.1 sequence from memory. Write one page: "why authorization code and nothing else." |
| 2 | 2, 3 | Write the **JAR/alg:none migration plan** for `spapublicclient`. This is a real deliverable for your actual job. |
| 3 | 4, 5 | Implement a toy DPoP client + verifier (WebCrypto + a small Node verifier) with `htm/htu/iat/jti/ath`, a `jti` replay cache, and a `DPoP-Nonce` mode. **Building it once beats reading it five times.** |
| 4 | 6, 7 | Write the "correct logout under partial failure" design. Map it onto the `LogoutService` gap in Appendix B. |
| 5 | 8, 9 | Threat-model the HRT step-up; write the `sub`/TXSUB evidence request (what exactly you need from the Gateway policy to close that gap). |
| 6 | 10, 11, 12 | Write the **"CIAM R4" one-pager**: what you'd change, in what order, with the risk of each. Then run the whole "remove one control" table cold. |

---

## Evidence discipline (the habit that actually marks you as an architect)

The explainer's best feature is that it **refuses to claim a control is present when the config isn't in the repo**. Copy that habit exactly:

- **✅ verified** = you have read the code path end to end.
- **🟡 partial** = one side present (client sets `iat`; server window unproven).
- **❌ NEEDS-EVIDENCE** = not in scope of what you can see. **This is not "probably fine" and it is not "a finding."** It is a request for evidence with a named artifact attached ("I need `AccessPolicyFunctions.js` and the Gateway transaction-cache policy").

Open gaps in this system right now, worth chasing in priority order:

1. **`sub`/TXSUB compare-and-invalidate** (§7) — high severity if genuinely missing. Need: transaction-cache access policy.
2. **`LogoutService` cleanup on the failure path** (§6.4) — verifiable *today* in the repos you have. **Start here.**
3. **60-second `iat` window + `jti` replay cache, server-side** (§2.3) — need Gateway policy.
4. **`BusinessAPI_pre_token_generation.js` unverified `id_token_hint`** (Appendix B) — critical and **un-ticketed**.
5. **`alg:none` request objects** (§2.2) — config drift, fix already exists in `idp_v2`.

---

## Reading list, ranked by value-per-hour

1. **RFC 9700** — OAuth 2.0 Security BCP. If you read one thing, this.
2. **RFC 9449** — DPoP. Your differentiator; know it cold.
3. **RFC 8725** — JWT BCP. Explains every row of Appendix B.
4. **RFC 7636** — PKCE. Short, and you'll be asked about it.
5. **OAuth 2.0 for Browser-Based Applications** (IETF BCP) — the BFF-vs-DPoP argument.
6. **NIST SP 800-63B** — AALs, session and reauthentication requirements; the vocabulary regulators and auditors use.
7. **OWASP ASVS v5** — auth + session chapters as a review checklist.
8. **RFC 9470** — step-up challenge; directly relevant to §7.
9. **RFC 8693** — token exchange; directly relevant to §8.
10. **OIDC Core §15** + **RP-Initiated Logout** — relevant to §6.3 and Appendix B #1.
