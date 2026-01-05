# Cortex1-ZeroVeil

**Zero Data Retention LLM Privacy Relay**

*A Multi-Tenant Mixer Architecture for Provider-Side Anonymity*

---

**Author:** Saqib Ali Khan
**Date:** December 2025
**Status:** Week 1 complete (v0 spec + policy-enforcing FastAPI stub gateway); provider routing is stubbed.
**Family:** Part of the Cortex1 privacy-first AI infrastructure

---

## Abstract

Large Language Models are being integrated into workflows containing sensitive personal, corporate, and regulated data. While existing solutions address content privacy through PII scrubbing, they fail to address a fundamental problem: **cloud providers can correlate every prompt to a specific user via API keys**, even with "zero data retention" policies.

Cortex1-ZeroVeil introduces a **mix network architecture** for LLM interactions -- applying principles from anonymous communication research (similar in concept to cryptocurrency tumblers) to AI infrastructure. By aggregating prompts from multiple tenants through a shared relay identity, it reduces user-to-prompt correlation at the provider level (risk reduction, not a guarantee).

**Critically, we do not offer PII scrubbing as a service.** Sending raw PII to any third party for "privacy processing" defeats the purpose. Instead, we provide an open-source client-side SDK for local scrubbing—your data never leaves your environment. Users must scrub content locally before it reaches our relay. This separation of concerns—content privacy (your responsibility, with our tooling) vs. identity privacy (ZeroVeil's responsibility)—is foundational to our architecture.

---

## The Problem Nobody Is Solving

### Current State

```
User A -> API Key A -> OpenAI
User B -> API Key B -> OpenAI
User C -> API Key C -> OpenAI
```

OpenAI (or any provider) knows exactly who sent each prompt. Even if they:
- Don't train on your data
- Delete it after 30 days
- Offer "zero data retention" APIs

They still see the **correlation** in real-time.

### Why This Matters

1. **Metadata is data**: Who asked what, when, how often
2. **Legal exposure**: Subpoenas target identifiable records
3. **Breach risk**: API key leaks expose user<->prompt history
4. **Competitive intelligence**: Providers see what you're building

### What Existing Solutions Miss

| Solution | Content Privacy | Identity Privacy |
|----------|-----------------|------------------|
| PII scrubbing services | No (you send them PII) | No |
| ZDR APIs | No (still seen in transit) | No |
| Self-hosting | Yes | Yes (but expensive) |
| **Cortex1-ZeroVeil** | User responsibility | Targets correlation resistance |

---

## The Solution: Mixer Architecture

### Core Concept

```
User A --->
User B --+--> [Cortex1-ZeroVeil] ---> Shared Identity ---> Cloud Provider
User C --->
```

**Analogy:** Mix networks (a concept from anonymous communication research, similar to cryptocurrency tumblers) pool messages through intermediate nodes, breaking the sender<->receiver link. Cortex1-ZeroVeil applies this principle to LLM traffic, pooling prompts through a shared relay identity to reduce the user<->prompt linkability.

### How It Works

1. Users scrub PII locally in their own environment
2. Users send scrubbed requests to Cortex1-ZeroVeil relay
3. Relay strips/replaces identifying metadata
4. Requests batched within configurable windows
5. Batched requests sent via shared provider credentials
6. Responses demultiplexed back to originators

**Result:** Provider sees one source (the relay), not individual users.

### Trust Model

Users must trust the relay operator to:
- Not log prompt content
- Not correlate users to prompts
- Enforce stated policies

This is **risk reduction through trust distribution**, not trustless privacy. Users who cannot accept this should self-host.

---

## Why We Don't Scrub Your Data

### The Privacy Paradox

Many services offer cloud-based PII scrubbing as a "privacy feature." This is fundamentally misguided.

**If you send raw PII to a third party for scrubbing, you've already compromised your privacy.**

Consider what you're doing:
- Sending names, SSNs, health records, financial data to a third party
- Trusting them to handle it correctly
- Trusting their security, their employees, their compliance
- All before any "privacy protection" happens

That's not privacy. That's outsourcing risk while calling it protection.

### The Privacy-Correct Approach

| Responsibility | Owner | Why |
|----------------|-------|-----|
| Content privacy (PII/PHI scrubbing) | User | Your data never leaves your environment |
| Identity privacy (user<->prompt unlinking) | ZeroVeil | Requires multi-tenant aggregation infrastructure |

### Benefits of This Separation

1. **Minimized trust**: We never see your raw PII
2. **Simpler compliance**: We're not a processor of personal data
3. **Better security posture**: Can't leak what we don't have
4. **User control**: You choose your scrubbing approach



We will never operate a cloud PII scrubbing service.

### Local-Only Scrubbing (Already Available)

Client-side scrubbing exists today:

- **ZeroVeil SDK** (open-source, BSL): local-only PII scrubbing using Microsoft Presidio, plus a minimal relay client. Runs entirely in your environment.
- **ZeroVeil Pro** (private, in active development): advanced deterministic/non-deterministic scrubbing, reversible token mapping, multiple backends, and audit logging.

---

## Architecture Overview

### Core: Aggregation Layer

The mixer component that pools and routes requests:
- Multi-tenant request aggregation
- Timing normalization (reduces fingerprinting)
- Shared credential management
- Response routing and isolation

### Enforcement: ZDR Policy

Strict Zero Data Retention requirements:
- Provider allow-list with verified policies
- Runtime verification where supported
- Fallback handling for unverified providers

### Optimization: Provider Reviews

We are implementing periodic evaluation of supported providers to optimize routing:
- Cost efficiency and pricing trends
- Latency and throughput benchmarks
- Task-specific performance (coding, analysis, creative tasks)
- ZDR compliance verification
- Reliability metrics

Tier escalation and pricing/cost policy are **Pro** features; the Community gateway remains conservative and auditable, and the ZeroVeil SDK remains intentionally minimal. Both Community and Pro are available self-hosted or cloud-hosted.

### Aggregation Benefits

The multi-tenant architecture provides compounding advantages:

*Correlation Resistance (Risk Reduction):*
- Larger user base = larger "mixing set" -> lower correlation risk (not a guarantee)
- More traffic = better timing obfuscation
- Diverse patterns make individual fingerprinting harder

*Economic:*
- Aggregated volume qualifies for better pricing tiers
- Collective buying power enables enterprise rate negotiations
- Shared infrastructure and compliance costs

This creates a virtuous network effect: more users -> stronger mixing set and lower costs for everyone.

### Routing

- Device-aware local-first routing can be done client-side.
- Tier escalation and automated cost/pricing policy are Pro/Hosted features.

---

## Market Opportunity

### The Gap

The data privacy and AI security space has seen significant consolidation, including Veeam's $1.73B acquisition of Securiti AI (2025) and multi-billion dollar PE discussions around market leaders like OneTrust. Yet no solution offers:

| Requirement | Current Market |
|-------------|----------------|
| Provider-neutral | Partial (some tools) |
| Provider-side correlation resistance | **Nobody (as a mainstream default)** |
| Privacy-correct architecture | **Nobody** (most offer cloud scrubbing) |
| Honest about trust tradeoffs | Rare |

### Positioning

**"Switzerland of LLM Privacy"**

- Neutral relay, not an LLM provider
- Privacy by architecture, not policy
- Honest about what requires trust
- Never asks for your raw PII
- Works across OpenAI, Anthropic, Google, open-source

---

## Use Cases

### Enterprise

- Aggregate employee LLM usage through corporate relay
- Reduce individual<->prompt correlation for compliance
- Unified ZDR enforcement across providers
- Keep PII scrubbing internal (as it should be)

### SaaS / Multi-Tenant

- Offer privacy guarantees to customers
- Reduce liability from customer data exposure
- Competitive differentiator
- Clear trust boundaries

### Personal / Privacy-Conscious

- Individual users pooling through shared relay
- Reduced fingerprinting surface
- Lower barrier than self-hosting

### Regulated Industries

- Healthcare: Scrub PHI locally, relay handles identity privacy only
- Legal: Privilege protection with clear boundaries
- Finance: Compliance-friendly architecture

---

## Compliance & Security Standards

ZeroVeil Pro supports enterprise compliance across major frameworks:

| Framework | How ZeroVeil Helps |
|-----------|-------------------|
| **HITRUST CSF** | PHI never reaches relay (client scrubs), audit logging |
| **SOC 2 Type II** | Access controls, metadata-only audit trails |
| **ISO 27001/27701** | Information security + privacy management controls |
| **NIST CSF** | US enterprise security baseline alignment |
| **NIST AI RMF** | AI-specific privacy and risk management |
| **HIPAA** | BAA support, architectural PHI avoidance |
| **GDPR** | Data minimization, DPA templates |

**Key compliance advantages:**
- PII/PHI never reaches ZeroVeil (client-side scrubbing) → simplified processor obligations
- No content logging → reduced audit scope
- ZDR-only providers → documented data handling chain

See [docs/compliance.md](compliance.md) for detailed control mappings.

---

## Deployment Models

Both Community and Pro editions support either deployment option.

| Model | Trust | Control | Mixing Benefit | Best For |
|-------|-------|---------|----------------|----------|
| **Cloud-hosted** | Trust operator | Low | High (network effect) | Most users, small-medium orgs |
| **Self-hosted** | Self only | High | None (unless multi-tenant) | Air-gap, data sovereignty |

**Recommendation:** Cloud-hosted is preferable for most organizations because larger mixing pools provide stronger correlation resistance. Self-hosting sacrifices mixing benefits for full control.

---

## Limitations and Honesty

### What This Protects Against

- Provider-side user<->prompt correlation
- API key breach exposing user history
- Metadata accumulation at provider

### What This Does NOT Protect Against

- Malicious relay operator (trust required)
- Content-based fingerprinting (highly unique prompts)
- Legal compulsion of relay operator
- Side-channel attacks
- PII in content (your responsibility)

### The Trust Tradeoff

Users trade provider trust for relay trust. For many threat models, this is favorable:
- Relay is specialized and auditable
- Provider is large target with many interests
- Distributed trust may be preferable to concentrated trust
- Relay never sees raw PII (if users scrub correctly)

---

## Licensing and Governance

**Business Source License 1.1**

- Non-commercial use: Permitted immediately
- Commercial use: Requires license
- Change Date: January 1, 2030
- Change License: Apache 2.0

**Intent:** Transition to permissive open-source earlier if responsible governance established. Potential foundation structure for long-term neutrality.

---

## Conclusion

Cortex1-ZeroVeil addresses the **identity privacy gap** in LLM usage that no current solution fills. By applying mix network principles from anonymous communication research to AI infrastructure, it targets provider-side correlation resistance without requiring full self-hosting.

Unlike competitors who offer to scrub your PII in the cloud — asking you to trust them with sensitive data before "protecting" it — we take the privacy-correct approach: you handle content privacy locally, we handle identity privacy through aggregation.

This is privacy done right.

---

**Author:** Saqib Ali Khan
**Contact:** Saqib.Khan@Me.com
**Repository:** https://github.com/Free-Radical/Cortex1-ZeroVeil

*The privacy layer for AI that should have existed from day one.*
