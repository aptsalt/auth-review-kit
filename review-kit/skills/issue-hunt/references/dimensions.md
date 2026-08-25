# Review dimensions

Each dimension is a lens with its own checklist, its own telltale patterns, and — importantly — its own
**Dynatrace symptom class**, which is what makes correlation possible later. When you file a finding,
record its dimension; `dynatrace-correlate` uses the symptom class to know what live signal would
corroborate it.

## Contents

**Security:** [secret-leak](#secret-leak) · [token-integrity](#token-integrity) · [token-storage](#token-storage) · [authz-decision](#authz-decision) · [session-lifecycle](#session-lifecycle) · [client-crypto](#client-crypto) · [xss-surface](#xss-surface) · [supply-chain](#supply-chain) · [config-drift](#config-drift)

**Reliability:** [outbound-resilience](#outbound-resilience) · [fail-mode](#fail-mode) · [error-taxonomy](#error-taxonomy) · [state-cleanup](#state-cleanup) · [delivery-semantics](#delivery-semantics)

**Performance:** [data-access-perf](#data-access-perf) · [cache-correctness](#cache-correctness) · [concurrency](#concurrency) · [resource-leak](#resource-leak) · [perf-render](#perf-render)

**Interface:** [api-misuse](#api-misuse)

---

## secret-leak

Credentials, tokens, keys or PII reaching a place they should never be.

- Logging calls whose arguments include a token, credential, key, `code_verifier`, PAN, or biometric data
- Full request/response body logging on auth paths
- Secrets in source, test fixtures, `.env` committed, CI config, or default config
- Error messages or stack traces returned to the client carrying internal detail
- Values published to an event bus or analytics SDK — these fan out to many consumers with many retention policies
- URL query parameters carrying anything sensitive (they land in access logs, referrers, browser history)

**Dynatrace symptom class:** `none` — this is invisible in telemetry, which is exactly why it must be
found by reading. Never expect corroboration; a `NO SIGNAL` verdict here means nothing at all.

## token-integrity

Tokens or signed objects that are trusted without being verified.

- JWT decoded by string-splitting, `base64` + `JSON.parse`, or a `*_decode` helper, then its claims trusted
- `alg: none` accepted, or the algorithm taken from the token header rather than an allow-list
- Signature verification available in the codebase but not called on a given path
- Missing `iss` / `aud` / `exp` / `nonce` checks after verification
- Sender-constrained tokens verified against the key *in the proof* rather than the key *bound to the token*
- Signed request objects minted unsigned, or a server configured to accept unsigned

**Dynatrace symptom class:** `auth-failure-rate`, `4xx-spike` — usually **absent**, because successful
forgery looks like success. Treat clean telemetry as no evidence either way.

## token-storage

Where credentials live on the client and how long they survive.

- Long-lived tokens in `localStorage`; tokens in non-`HttpOnly` cookies
- Tokens or keys that survive logout, or survive a security error
- Key material exportable from JS when a non-extractable or OS-keystore option exists
- Tokens in URLs, or logged/persisted anywhere for debugging

**Dynatrace symptom class:** `session-anomaly`, `auth-failure-rate`

## authz-decision

Who is allowed to do what, and where that is decided.

- An authorization decision made client-side, or trusted from a client-supplied value
- Object/row access without an ownership check (IDOR)
- Missing binding between an approval and the specific action it approved
- Role or entitlement checks that vary between channels (web vs mobile) — divergence is the finding
- Cached authorization decisions: **the cache TTL is the revocation gap.** Find the number.

**Dynatrace symptom class:** `4xx-spike`, `unusual-request-pattern`

## session-lifecycle

Creation, extension, expiry and destruction.

- Idle and absolute timeouts — both present? enforced server-side or only in the UI?
- Session identifier regenerated after privilege change (fixation)
- Two-session architectures: does ending one actually end the other?
- Logout that only cleans up on the success path
- Timeout values from remote config with no test guarding them — a config regression becomes a security regression

**Dynatrace symptom class:** `session-anomaly`, `error-rate`

## client-crypto

Cryptography performed in the browser or app.

- Weak or hand-rolled algorithms; ECB; static IV/nonce; `Math.random()` for anything security-relevant
- Key material held in JS when the platform offers non-extractable keys or an OS keystore
- Client-side encryption presented as protection against a threat it does not address — be precise
  about what it actually buys (middleboxes, logs) and what it does not (a compromised page)

**Dynatrace symptom class:** `none` (occasionally `js-error-rate`)

## xss-surface

Injection into the page, and what an injection would reach.

- `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `bypassSecurityTrust*` with non-constant input
- `eval`, `new Function`, dynamic `<script>` injection
- CSP absent, or so permissive it grants nothing (`unsafe-inline`, `unsafe-eval`, wildcard hosts)
- **Then ask the second question:** given an injection, what is reachable? Tokens in memory, a signing
  API, an OS-keystore key that cannot be stolen but *can* be used as a signing oracle. The blast radius
  is the finding, not the sink.

**Dynatrace symptom class:** `js-error-rate`, `rum-anomaly`

## supply-chain

Code you execute but did not write.

- Runtime-federated modules (module federation, remote entry) — they execute in the host origin with
  full DOM access. A compromise of *their* build is a compromise of *your* page.
- Unpinned versions, floating tags, missing lockfile, no integrity/SRI on external assets
- Dependencies with crypto/JWT/HTTP responsibilities — these deserve version-level scrutiny
- Postinstall scripts; build-time network access

**Dynatrace symptom class:** `js-error-rate`, `third-party-latency`

## config-drift

The same thing configured two different ways.

- Compare sibling templates/environments of the same component and diff the security-relevant keys
- A hardened newer template alongside an unhardened older one still in use — **the fix already exists**,
  which makes this a rollout plan rather than a discovery
- Defaults that are unsafe when a key is absent
- Remotely mutable config that changes security behaviour with no test or alert

**Dynatrace symptom class:** `config-change-correlation` — Dynatrace deployment/config events near a
problem onset are strong corroboration here.

## outbound-resilience

Every call that leaves the process.

- **No timeout** — the single highest-yield reliability finding in most estates
- No retry policy, or retries without backoff/jitter, or retries on non-idempotent operations
- No circuit breaker or bulkhead around a dependency that can be slow
- Unbounded connection or thread pools; pools shared between fast and slow dependencies
- A slow dependency able to exhaust the caller's threads (head-of-line blocking)

**Dynatrace symptom class:** `service-slowdown`, `timeout`, `thread-exhaustion`, `connection-pool-saturation`
— this dimension corroborates better than any other. Hunt it *after* a Dynatrace pull and go where
production already hurts.

## fail-mode

What happens when a dependency fails — and whether that was chosen.

- For each failure path: does it fail open or closed? Is that written down anywhere?
- **Asymmetric policies are often deliberate**: fail closed when the failure removes a *security
  decision*, fail open when it removes only a *side effect* (a notification, a telemetry publish).
  Do not "fix" an asymmetry into a blanket policy — read the intent first.
- A soft-fail path that is not monitored is the real finding: it degrades silently and permanently.
- Empty catch blocks; exceptions swallowed and a default returned

**Dynatrace symptom class:** `error-rate`, `failure-rate-degradation`

## error-taxonomy

Whether the system can tell its failures apart.

- Distinct causes collapsed into one status code or one generic handler
- A client that retries every error identically, so a security-relevant rejection triggers a retry loop
  instead of a forced cleanup
- Errors that lose the correlation/trace ID
- Log levels that make a real incident indistinguishable from noise

**Dynatrace symptom class:** `error-rate` — and poor taxonomy actively *degrades* Dynatrace's own
problem detection, which is worth saying in the finding.

## state-cleanup

What is left behind.

- Cleanup only on the success path when the requirement is unconditional
- Cleanup in a `catch` rather than a `finally`
- Multi-store state where one store is missed (memory / session / cookie / IndexedDB / keystore / server)
- Timers, intervals, subscriptions and listeners not torn down

**Dynatrace symptom class:** `memory-growth`, `session-anomaly`

## delivery-semantics

Event and message correctness.

- At-least-once delivery with consumers that are not idempotent
- Ordering assumed but not guaranteed
- Dropped publishes that silently degrade audit or fraud analytics
- No dead-letter handling; poison messages that block a partition
- Events carrying data that should never fan out (see `secret-leak`)

**Dynatrace symptom class:** `queue-depth`, `consumer-lag`, `error-rate`

## data-access-perf

Talking to data stores.

- N+1 queries — a query inside a loop over a result set
- Missing index on a filtered/joined column; full scans on hot paths
- `SELECT *` on wide tables across the network; fetching then filtering in memory
- Unbounded result sets; missing pagination
- Chatty ORM patterns; lazy loading in a serialisation path
- Transactions held open across a network call

**Dynatrace symptom class:** `database-hotspot`, `slow-query`, `service-slowdown` — very high
corroboration rate. Dynatrace names the exact statement.

## cache-correctness

Caches as a correctness surface, not just a speed one.

- What is the TTL, and what does that TTL *mean*? For an authorization cache it is the revocation gap.
- Cache key completeness — is the tenant/user/channel part of the key? A missing key component is a
  cross-user data leak.
- Prefetch or warming that happens **before** authorization completes — the safety usually rests on
  conventions in service code, not on an enforced boundary. Say so.
- Stampede on expiry; no negative caching; unbounded cache growth

**Dynatrace symptom class:** `cache-hit-ratio`, `service-slowdown`, `memory-growth`

## concurrency

- Check-then-act races; non-atomic read-modify-write on shared state
- Shared mutable state without synchronisation; non-thread-safe objects used as singletons
- Missing locks around resources that must be minted once (keys, namespaces, identifiers)
- Async operations racing a teardown; unawaited promises
- Deadlock ordering; lock held across I/O

**Dynatrace symptom class:** `thread-exhaustion`, `deadlock`, `error-rate`, `response-time-variance`

## resource-leak

- Streams, file handles, HTTP clients, DB connections not closed on the error path
- Listeners/subscriptions added without removal
- Unbounded in-memory collections (caches, maps keyed by session or user)
- Native/keystore handles not released

**Dynatrace symptom class:** `memory-growth`, `gc-pressure`, `connection-pool-saturation` — visible as a
sawtooth or steady climb over the 30-day window. Excellent corroboration.

## perf-render

Client-side performance.

- Bundle size; missing code splitting; heavy dependencies on the critical path
- Render-blocking work; long tasks on the main thread
- Waterfalls where requests could be parallel
- Layout thrash; unmemoised expensive renders; unvirtualised long lists

**Dynatrace symptom class:** `rum-lcp`, `rum-long-task`, `page-load-degradation`

## api-misuse

For libraries and SDKs — how the interface invites error.

- Unsafe defaults; a safe path that requires an extra opt-in call
- Ignorable return values that carry failure
- Ambiguous naming that makes the wrong call plausible
- Behaviour that differs between consumers of the same library — check the consumers, since the
  library itself is usually `blind` in telemetry

**Dynatrace symptom class:** inherit from the consumer service.
