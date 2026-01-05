# Editions (Community vs Pro)

This repository is the **Community Gateway**: the auditable core that enforces policy, defines the trust posture, and implements mixer primitives.

Both editions are available **self-hosted** or **cloud-hosted** (operated by ZeroVeil).

## Deployment Options

| Option | Who Operates | Relay Identity | Best For |
|--------|--------------|----------------|----------|
| **Self-Hosted** | You | Your own API keys | Full control, air-gapped environments |
| **Cloud-Hosted** | ZeroVeil | Shared (ZeroVeil-operated) | Network effect benefits, lower ops burden |

**Recommendation:** For small-to-medium organizations, **cloud-hosted is preferable** because larger mixing pools provide stronger correlation resistance. Self-hosting makes sense for air-gapped environments or organizations with strict data sovereignty requirements.

---

## Community (Free, BSL)

Core privacy relay with full mixer functionality.

**Gateway Features:**
- FastAPI gateway implementing `/v1/chat/completions`
- Policy schema + enforcement (ZDR-only, allowlists, limits, tool constraints)
- Scrub attestation enforcement (reject unsafely-marked requests)
- Prompt normalization and policy preambles
- Provider adapters (community-maintained)
- Metadata-only audit events by default (no prompt/response logging)
- Conformance tests proving policy + logging invariants
- Threat model and conservative claim framing ("risk reduction")

**Mixer Primitives:**
- Request batching with configurable windows
- Shuffle dispatch (randomized order within batches)
- Timing jitter (50-200ms random delays)
- Header stripping (remove tenant-identifying metadata)
- One-time response tokens (unlinkable return routing)
- Shared relay identity (cloud-hosted only)

**Available as:** Self-hosted or ZeroVeil Cloud

---

## Pro (Paid)

Enterprise features on top of Community.

**Enterprise Auth & Governance:**
- SSO/SAML/OIDC and SCIM provisioning
- Fine-grained RBAC, per-app policies, change control workflows
- Advanced governance packs and admin UI

**Compliance & Audit:**
- Architecture aligned with:
  - HITRUST CSF, SOC 2 Type II, ISO 27001/27002
  - ISO 27701 (privacy management)
  - NIST Cybersecurity Framework (CSF)
  - NIST AI Risk Management Framework (AI RMF)
- Compliance evidence bundles for customer audits (access logs, data flow diagrams, control matrices)
- Signed/immutable audit log integrations and exports
- Security integrations (SIEM, KMS/HSM, key rotation tooling)
- Pre-built documentation for HIPAA BAA, GDPR DPA requirements

*See [docs/compliance.md](compliance.md) for detailed control mappings across all frameworks.*

*Note: ZeroVeil Pro is designed to support customers' compliance programs. Formal certifications (SOC 2, HITRUST, ISO 27001, FedRAMP) for ZeroVeil Hosted are on the roadmap pending scale.*

**Advanced Privacy:**
- Optional PII/PHI **reject-only** ingress checks (detect and reject unsafely-scrubbed requests; never "scrub-as-a-service")
- Advanced abuse resistance / multi-region routing controls
- Tier escalation and automated cost/pricing policy

**SDK Pro Features:**
- Deterministic and non-deterministic scrubbing modes
- Reversible token mapping (recover original values post-processing)
- Multiple scrubbing backends (Presidio, regex, scrubadub)
- Audit logging for compliance

**Available as:** Self-hosted or ZeroVeil Cloud (with SLAs, monitoring, incident response)

---

## Network Effect: Why Cloud Beats Self-Hosted for Privacy

The mixer's effectiveness depends on the size of the mixing pool:

| Pool Size | Correlation Resistance | Timing Obfuscation |
|-----------|------------------------|-------------------|
| 1 tenant (self-hosted, solo) | None | None |
| 5-10 tenants | Weak | Basic |
| 100+ tenants | Strong | Good |
| 1000+ tenants | Very strong | Excellent |

**Cloud-hosted Community** benefits from the aggregate traffic of all ZeroVeil users. Self-hosting only makes sense when:
- You have strict air-gap requirements
- Data sovereignty prevents any external relay
- You operate multiple internal tenants yourself

For everyone else: the shared mixing pool provides better privacy than isolated self-hosting.
