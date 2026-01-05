# Cortex1-ZeroVeil

**Zero Data Retention LLM Privacy Relay**

Part of the Cortex1 family of privacy-first AI infrastructure.

---

## What Is This?

Cortex1-ZeroVeil is a privacy-preserving relay layer for Large Language Model interactions. It breaks the correlation between users and their prompts at the cloud provider level — applying mix network principles from anonymous communication research (similar in concept to cryptocurrency tumblers).

**The problem:** When you call OpenAI/Anthropic/Google APIs, they know exactly who sent each prompt via your API key. Even with "zero data retention" promises, they see the link.

**The solution:** Cortex1-ZeroVeil aggregates prompts from multiple tenants through a shared relay identity. The cloud provider sees one anonymous source, not individual users.

---

## Core Product: Privacy Relay (Mixer)

```
User A --->
User B --+--> [Cortex1-ZeroVeil] ---> Shared Identity ---> Cloud LLM
User C --->
```

**What it does:**
- Aggregates prompts from multiple users/tenants
- Routes through shared relay identity
- Breaks user<->prompt correlation at provider level
- Enforces Zero Data Retention (ZDR) provider policies

**What it does NOT do:**
- Scrub your content (see below — this is intentional)
- Guarantee absolute anonymity (risk reduction, not magic)
- Replace your security practices

---

## Why We Don't Scrub Your Data

**If you send us PII/PHI to scrub, you've already compromised your privacy.**

Think about it: sending sensitive data to a third party for "privacy processing" defeats the purpose. You'd be trusting us with your most sensitive information — names, SSNs, health records — before we "protect" it.

**True privacy = minimizing trust.**

### The Privacy-Correct Approach

| Step | Where | Who Controls |
|------|-------|--------------|
| 1. Scrub PII/PHI | YOUR environment | You |
| 2. Send scrubbed content | To ZeroVeil | You |
| 3. Anonymize & relay | ZeroVeil | Us |

We handle **identity privacy** (reducing user<->prompt correlation). You handle **content privacy** (removing PII before it leaves your environment).

### Local Scrubbing Tooling (Client-Side)

ZeroVeil SDK is an open-source (BSL) client library for local PII scrubbing and relay access. It runs **entirely in your environment**—your data never leaves. We will never ask you to send raw PII to us.

*Note: The `zeroveil-sdk` repository is source-available under BSL. Early access is invite-only during initial development.*

Anyone offering cloud-based PII scrubbing as a "privacy feature" is asking you to trust them with the very data you're trying to protect. That's not privacy — that's outsourcing risk.

---

## Additional Features

### ZDR Enforcement
- Only routes to providers with verified Zero Data Retention policies
- Provider allow-list maintained and auditable

### Routing (Best practices)

- Community gateway: enforce policy and provide provider adapters; keep routing logic conservative and auditable.
- Pro/Hosted: advanced routing policy (e.g., tier escalation and automated cost/pricing controls) lives in Pro.

### Local-First Option
- Prefer local models when hardware permits
- Cloud only when necessary or beneficial

---

## Trust Model

**Be clear about what you're trusting:**

| Component | You Trust |
|-----------|-----------|
| Relay/Mixer | ZeroVeil operator to not log prompts (already scrubbed by you) |
| ZDR Providers | Provider's retention policy claims |
| Your Local Scrubber | Your own implementation |

We designed this so you trust us with **less**, not more.

---

## Getting Started

### ZeroVeil SDK (Free, Source-Available)

Install the client SDK for local PII scrubbing and relay access:

```bash
pip install zeroveil
```

**Features:**
- Local PII/PHI scrubbing via Presidio
- ZeroVeil relay client
- Simple API for privacy-preserving LLM interactions

*SDK repo: source-available (BSL), early access invite-only*

### Deployment Options

Both Community and Pro are available **self-hosted** or **cloud-hosted**:

| Option | Relay Identity | Mixing Benefit | Best For |
|--------|----------------|----------------|----------|
| **Cloud-Hosted** | Shared (ZeroVeil-operated) | High (network effect) | Most users |
| **Self-Hosted** | Your own API keys | None (unless multi-tenant) | Air-gap, data sovereignty |

**Recommendation:** For small-to-medium organizations, **cloud-hosted is preferable** because larger mixing pools provide stronger correlation resistance.

### ZeroVeil Pro

Enterprise features on top of Community:

- Enterprise auth (SSO/SAML/OIDC) and RBAC
- Architecture aligned with HITRUST CSF, ISO 27001/27701, SOC 2, NIST CSF, NIST AI RMF
- Compliance evidence bundles for customer audits
- Signed/immutable audit logs
- PII/PHI reject-only ingress checks
- Deterministic/non-deterministic scrubbing modes (SDK)
- Reversible token mapping (SDK)

*Formal certifications for ZeroVeil Hosted on roadmap pending scale.*

See [docs/compliance.md](docs/compliance.md) for detailed control mappings.

Contact: Saqib.Khan@Me.com for access.

---

## Status

Week 1 complete: v0 spec + policy enforcement stub gateway (FastAPI). Provider routing is stubbed; policy and logging contracts are implemented and test-covered.

---

## Week 1: Gateway Spec + Skeleton

The community gateway is defined by `docs/spec-v0.md` and includes a minimal FastAPI stub implementation.

- Spec (API/policy/logging): `docs/spec-v0.md`
- Editions (Community vs Pro): `docs/editions.md`
- Example policy: `policies/default.json`
- FastAPI stub: `src/zeroveil_gateway/app.py` (returns `stubbed_response`)

Local run (dev):

```bash
python -m pip install -e .[dev]
set ZEROVEIL_POLICY_PATH=policies/default.json
python -m zeroveil_gateway
python scripts/demo_gateway.py
```

---

## Contributing

Looking for contributors interested in privacy-first AI infrastructure. If you care about:
- LLM privacy and correlation risk reduction
- Zero-trust architecture
- Building the missing privacy layer for AI

See `CONTRIBUTING.md` and `CLA.md`.

Open an issue or reach out: Saqib.Khan@Me.com

---

## License

**Business Source License 1.1**

- **Non-commercial use**: Permitted
- **Commercial/production use**: Requires explicit license
- **Change Date**: January 1, 2030
- **Change License**: Apache License 2.0

Intent: Transition to permissive open-source earlier if community adoption and responsible governance are achieved.

See [LICENSE](LICENSE) for full terms.

---

## Prior Art

This repository constitutes a public disclosure of the described techniques. See [NOTICE](NOTICE) for details.

---

## Author

Saqib Ali Khan
Contact: Saqib.Khan@Me.com

---

*The privacy layer for AI that should have existed from day one.*
