# Cortex1-ZeroVeil Architecture

## Executive Summary

Cortex1-ZeroVeil is a privacy-preserving relay layer for LLM interactions. Its core innovation is a **multi-tenant aggregation architecture** (mixer) that breaks user-to-prompt correlation at the cloud provider level, combined with strict Zero Data Retention enforcement.

**Important:** PII/PHI scrubbing is explicitly NOT part of the relay service. Users must scrub content locally before sending to ZeroVeil. Sending raw PII to any third party — including us — defeats the purpose of privacy protection.

---

## Problem Statement

Current LLM API usage has a fundamental privacy flaw:

```
User → API Key → Cloud Provider
```

Even with "zero data retention" promises, the provider knows:
- Which API key sent each prompt
- Timing and frequency patterns
- Content of each request (even if not stored long-term)

**Result:** User↔prompt correlation is fully visible to the provider.

Existing solutions address content privacy (PII scrubbing) but not **identity privacy** at the provider level.

---

## Solution: Mixer Architecture

### Core Concept

```
User A ─┐                                    ┌─→ Response A
User B ─┼─→ [Aggregation Layer] ─→ [Shared Identity] ─→ Cloud ─┼─→ Response B
User C ─┘                                    └─→ Response C
```

**Analogy:** Mix networks (a concept from anonymous communication research, similar in principle to cryptocurrency tumblers) break the sender↔receiver link by pooling messages through intermediate nodes. Cortex1-ZeroVeil applies this principle to LLM interactions, breaking the user↔prompt link by pooling requests through a shared relay identity.

### Privacy Properties

| Property | Mechanism |
|----------|-----------|
| Provider-side anonymity | Single relay identity for all requests |
| User↔prompt unlinkability | Aggregation breaks correlation |
| Timing obfuscation | Batching windows reduce fingerprinting |
| Reduced metadata exposure | Shared patterns across tenants |

### Trust Model

The relay operator (Cortex1-ZeroVeil) sees individual requests. Users must trust:
1. Relay does not log prompt content
2. Relay does not correlate users to prompts
3. Relay enforces stated ZDR policies

This is a **trust tradeoff**, not trustless privacy. Users who cannot accept this should self-host or use direct API access.

---

## Why We Don't Offer PII Scrubbing

### The Privacy Paradox

Many "privacy" services offer to scrub your PII before forwarding to LLMs. This is backwards.

**If you send raw PII to a third party for scrubbing, you've already exposed it.**

It doesn't matter if they promise ZDR, encryption, or compliance certifications. The moment your unredacted data leaves your environment, you've trusted someone else with it.

### Separation of Concerns

| Responsibility | Owner | Rationale |
|----------------|-------|-----------|
| Content privacy (PII/PHI removal) | User | Your data, your environment, your control |
| Identity privacy (user↔prompt unlinking) | ZeroVeil | Requires aggregation infrastructure |

This separation is intentional:
- Minimizes what you trust us with
- Keeps sensitive data in your environment
- Makes our security posture simpler (we never see raw PII)

### Future Tooling

If market demand exists, we may provide scrubbing tools — but they would be:
- **Local-only**: Runs in your environment
- **Open source**: Auditable by you
- **Optional**: Not part of the relay service

We will never ask you to send raw PII to our servers.

---

## Architecture Components

### 1. Aggregation Layer (Core)

The central mixer component:

- Receives requests from multiple tenants
- Strips/replaces identifying metadata
- Batches requests within configurable windows
- Routes through shared provider credentials
- Demultiplexes responses back to originators

**Design Considerations:**
- Latency impact of batching windows
- Tenant isolation within aggregation
- Request ordering and priority handling
- Failure isolation (one tenant's error doesn't affect others)

### 2. ZDR Enforcement

Strict Zero Data Retention policy enforcement:

- Provider allow-list based on contractual ZDR commitments
- Runtime verification where provider APIs support it (currently limited; most verification is policy-based)
- Audit logging of provider selection (without content)
- Fallback behavior when ZDR cannot be verified

**Supported Providers (must verify ZDR):**
- Providers with contractual ZDR guarantees
- Self-hosted endpoints
- Custom deployments with verified retention policies

**Provider Optimization:**
We are implementing periodic reviews of supported LLM providers to optimize routing decisions based on:
- Cost efficiency (price per token/request)
- Response latency and throughput
- Task-specific performance (coding, analysis, creative, etc.)
- ZDR policy compliance status
- Reliability and uptime history

The reference client SDK ([cortex1-core](https://github.com/Free-Radical/cortex1-core)) already implements 3-tier cost-optimized escalation with monthly pricing reviews. This approach will be extended to relay-side provider selection to deliver optimal price-performance while maintaining strict ZDR requirements.

**Aggregation Benefits:**
The multi-tenant architecture provides compounding advantages:

*Privacy & Anonymity:*
- Larger user base = larger anonymity set = stronger privacy guarantees
- More traffic = better timing obfuscation through natural batching
- Diverse usage patterns make individual fingerprinting harder

*Economic:*
- Aggregated volume qualifies for better provider pricing tiers
- Collective buying power enables enterprise rate negotiations
- Shared infrastructure and compliance costs

This creates a virtuous network effect: more users → stronger anonymity AND lower costs for everyone.

### 3. Client SDK (Reference Implementation)

ZeroVeil provides a reference client SDK (see [cortex1-core](https://github.com/Free-Radical/cortex1-core)) that handles client-side responsibilities before relay submission:

**Device-Aware Routing:**
| Mode | Hardware | Strategy |
|------|----------|----------|
| LOCAL_PREFERRED | GPU (8GB+ VRAM) | Local models preferred, relay fallback |
| HYBRID | CPU (16GB+ RAM) | Local preprocessing, relay for complex tasks |
| CLOUD_ONLY | Minimal | Relay with mandatory local PII scrubbing |

**Cost-Optimized Escalation (when using relay):**
| Tier | Purpose | Trigger |
|------|---------|---------|
| Tier 1 | Default | Initial attempt (~80% of requests) |
| Tier 2 | Fallback | Tier 1 failure |
| Tier 3 | Critical | VIP items or Tier 2 failure |

Tier 3 failure → flag for human review.

*Note: Device detection and local-first routing occur client-side. The relay service handles aggregation and provider routing for cloud-bound requests only.*

---

## Security Model

**Guiding Principle:** We aspire to maximize user privacy and anonymity at all times. When facing design tradeoffs, privacy and anonymity considerations take precedence over convenience, cost optimization, or operational simplicity.

### Threat Mitigation

| Threat | Mitigation |
|--------|------------|
| Provider-side user correlation | Aggregation through shared identity |
| PII exposure to providers | User scrubs locally before sending |
| Metadata fingerprinting | Batching, timing normalization |
| Relay operator logging | Policy + audit (trust required) |

### What This Does NOT Protect Against

- Malicious relay operator (requires trust)
- Content-based fingerprinting (if content is unique enough)
- Legal compulsion of relay operator
- Side-channel attacks on relay infrastructure
- PII in content (user responsibility to scrub)

### Logging Policy

**Principle:** Minimize logging to operational necessity. Content is never persisted.

| Category | Policy | Retention | Rationale |
|----------|--------|-----------|-----------|
| Prompt/response content | Never persisted | N/A | Core privacy guarantee |
| User↔request correlation | Not retained beyond session | N/A | Defeats mixer purpose |
| Operational metrics | TBD | TBD | Error rates, latency (aggregate only) |
| Security events | TBD | TBD | Auth failures, anomalies |
| Provider routing | TBD | TBD | Which provider handled request (no content) |

*Specific retention periods and operational logging scope to be defined during implementation. Session-scoped correlation (required for response routing) is ephemeral and not persisted.*

**Jurisdictional Intent:** We plan to operate infrastructure in privacy-respecting jurisdictions with strong data protection laws and limited compelled disclosure regimes, to the extent commercially feasible. Specific jurisdictions to be determined.

### Trust Boundaries

```
┌─────────────────────────────────────────────────────────┐
│ USER ENVIRONMENT (full trust)                           │
│   - Raw content with PII                                │
│   - PII scrubbing happens HERE                          │
│   - User identity                                       │
└─────────────────────┬───────────────────────────────────┘
                      │ (scrubbed content only)
┌─────────────────────▼───────────────────────────────────┐
│ CORTEX1-ZEROVEIL (trust required)                       │
│   - Sees scrubbed requests only                         │
│   - Performs aggregation                                │
│   - Enforces ZDR                                        │
│   - Never sees raw PII                                  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│ CLOUD PROVIDER (zero trust)                             │
│   - Sees only relay identity                            │
│   - Cannot correlate to individual users                │
│   - ZDR policy enforced                                 │
└─────────────────────────────────────────────────────────┘
```

### Abuse Prevention

**Challenge:** Preventing abuse while preserving anonymity requires privacy-preserving techniques.

**Approach:**
- **Rate limiting:** Token-based limits without persistent identity correlation
- **Content policy:** Provider-side content policies apply; relay does not inspect content
- **Terms of Service:** Users agree to acceptable use; violations may result in token revocation
- **Cryptographic accountability:** Privacy-preserving mechanisms (e.g., blind signatures) may enable revocation without identification

**What we will NOT do:**
- Content inspection or logging for abuse detection
- User identification based on content patterns
- Proactive monitoring of request content

**Legal compliance:** We will respond to valid legal process in operating jurisdictions. See Transparency & Trust Commitments for warrant canary and disclosure policies.

*Specific abuse prevention mechanisms to be finalized during implementation, balancing privacy preservation with operational necessity.*

---

## Deployment Models

### Hosted Relay (Default)

Cortex1-ZeroVeil operates the relay:
- Simplest setup
- Requires trust in operator
- Shared infrastructure, economies of scale

### Self-Hosted Relay

Organization runs own relay:
- Full control
- No external trust required
- Higher operational burden

---

## Compliance Considerations

- **GDPR**: Data minimization, purpose limitation, processor agreements
- **HIPAA**: PHI must be scrubbed before reaching relay; architectural intent is to avoid PHI exposure (consult qualified legal counsel for BAA requirements in your specific use case)
- **SOC 2**: Audit logging, access controls on relay
- **CCPA**: User rights, disclosure requirements

Note: By requiring local PII scrubbing, compliance burden is simplified — we are not a processor of personal data.

---

## Transparency & Trust Commitments

Policy commitments we intend to uphold from day one of operation:

### Warrant Canary

Where legally permitted in our operating jurisdictions, we will maintain a regularly updated warrant canary to signal whether we have received legal demands that we cannot disclose. Absence of update or removal of the canary should be treated as a potential compromise indicator.

*Note: Warrant canary legality and effectiveness varies by jurisdiction. Users should understand the limitations of this mechanism in their specific legal context.*

### Incident Response

In the event of a security incident affecting user privacy or anonymity:
- Users will be notified promptly through published channels
- Scope and nature of the incident will be disclosed to the extent legally permitted
- Post-incident analysis will be published

### Service Termination

If ZeroVeil ceases operation:
- Users will receive advance notice (minimum period TBD)
- Any ephemeral data will be securely destroyed
- Clear documentation of shutdown procedures will be provided

*Specific procedures and timelines to be formalized before production launch.*

---

## Future Directions

- Differential privacy for statistical queries
- Cryptographic mixing protocols (reduce trust requirements)
- Multi-relay chaining for enhanced anonymity
- Formal verification of privacy properties (long-term goal, as resources permit)
- Independent security audits
- Local-only, open-source scrubbing toolkit (if demand exists)
- PII/PHI leak detection to identify insufficient or failed data scrubbing before relay
- Transparency reports (periodic publication of aggregate statistics, legal request counts)
- Open source roadmap (timeline for code auditability)
- Federated relay architecture (multiple trusted operators for distributed trust)

---

*Document Version: 1.2*
*Date: December 2025*
*Author: Saqib Ali Khan*
*Part of the Cortex1 family*
