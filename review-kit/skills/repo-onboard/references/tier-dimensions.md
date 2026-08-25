# Which dimensions apply to which repo

Run the dimensions that can actually produce a finding for this repo's shape. Running all of them
everywhere produces volume, not signal — and a reviewer who files "no CSP" against a config repo loses
credibility for the findings that matter.

Dimension definitions live in `skills/issue-hunt/references/dimensions.md`.

## By tier

| Tier | Always run | Usually run | Rarely relevant |
|---|---|---|---|
| **client** (SPA, MFE, mobile) | token-storage, client-crypto, secret-leak, xss-surface, supply-chain | perf-render, error-taxonomy, state-cleanup | outbound-resilience, concurrency |
| **gateway-identity** | token-integrity, authz-decision, session-lifecycle, secret-leak, fail-mode | outbound-resilience, cache-correctness, config-drift | perf-render |
| **service** | outbound-resilience, authz-decision, fail-mode, secret-leak, data-access-perf | concurrency, cache-correctness, error-taxonomy, resource-leak | xss-surface, perf-render |
| **data-events** | secret-leak, data-access-perf, delivery-semantics | resource-leak, concurrency | xss-surface, token-storage |

## By kind

| Kind | Emphasis | Notes |
|---|---|---|
| `spa` | token-storage, xss-surface, supply-chain | The build pipeline is part of the attack surface — a federated module executes in the host origin. |
| `service` | outbound-resilience, fail-mode, data-access-perf | Every outbound call without a timeout is a latent availability finding. |
| `library` | api-misuse, token-integrity, concurrency | Usually `blind` in Dynatrace. Findings surface as behaviour in consumers, so cite a consumer. |
| `config` | config-drift, fail-mode, secret-leak | Compare templates against each other — drift between two templates of the same thing is the highest-yield pattern here. |
| `adapter` | delivery-semantics, error-taxonomy, secret-leak | What it publishes is what audit sees; what it drops is invisible. |
| `infra` | secret-leak, config-drift | Usually out of scope — check the profile's §9 before spending time. |

## Ordering within a repo

1. **secret-leak** first. It is cheap, mechanical, and the highest-severity thing you can find by
   grepping. Do it before you understand the codebase, because it needs no understanding.
2. **The tier's "always run" set** next, while the source index is fresh.
3. **Performance dimensions** last. They benefit from knowing the hot paths, and they are the ones
   most improved by having Dynatrace data in hand — consider deferring them until after a
   `dynatrace-pull`, so you hunt where production actually hurts.

## A note on scope discipline

If a dimension cannot be evaluated from this repo alone — the enforcement lives in gateway config, or
the counterpart service is not in the workspace — do **not** mark it clean. Record it as an evidence
gap with the artifact you would need. The profile's §9 and §10 exist for exactly this.

Marking something clean that you could not actually see is the one failure mode that discredits the
entire review.
