# Compliance & Security Controls

ZeroVeil Pro is architected to support enterprise compliance programs across major security frameworks.

---

## Supported Frameworks

| Framework | Focus Area | ZeroVeil Relevance |
|-----------|------------|-------------------|
| **HITRUST CSF** | Healthcare security | PHI never reaches relay (client scrubs) |
| **SOC 2 Type II** | Service organization controls | Audit logging, access controls, availability |
| **ISO 27001/27002** | Information security management | Comprehensive security controls |
| **ISO 27701** | Privacy management | Privacy-by-design architecture |
| **NIST CSF** | Cybersecurity framework | US enterprise baseline |
| **NIST AI RMF** | AI risk management | AI-specific privacy and security controls |
| **HIPAA** | Healthcare privacy | Supports BAA requirements (PHI scrubbed client-side) |
| **GDPR** | EU data protection | Data minimization, DPA support |
| **FedRAMP** | Federal cloud security | On roadmap for government customers |

---

## Controls Implementation

How ZeroVeil addresses common control requirements across frameworks:

### Access Control

| Requirement | ZeroVeil Implementation |
|-------------|------------------------|
| Role-based access | Pro: SSO/SAML/OIDC + fine-grained RBAC |
| API authentication | SHA-256 hashed API keys, per-tenant isolation |
| Least privilege | Tenant-scoped permissions, policy-based restrictions |
| Access reviews | Audit logs exportable for periodic review |

### Audit & Logging

| Requirement | ZeroVeil Implementation |
|-------------|------------------------|
| Activity logging | Metadata-only audit events (no content logging) |
| Log integrity | Pro: Signed/immutable audit logs |
| Log retention | Configurable retention, compliance exports |
| SIEM integration | Pro: Splunk, Datadog, custom webhook support |

### Data Protection

| Requirement | ZeroVeil Implementation |
|-------------|------------------------|
| Encryption in transit | TLS 1.3 on all endpoints |
| Encryption at rest | Encrypted database storage |
| Data minimization | No prompt/response content stored |
| PII handling | Client-side scrubbing (never touches relay) |

### Incident Response

| Requirement | ZeroVeil Implementation |
|-------------|------------------------|
| Incident detection | Anomaly monitoring, rate limit alerts |
| Response procedures | Documented runbooks, contact procedures |
| Breach notification | Commitment to timely disclosure |
| Post-incident review | Published post-mortems for significant events |

### Vendor Management

| Requirement | ZeroVeil Implementation |
|-------------|------------------------|
| Third-party assessment | LLM providers vetted for ZDR policies |
| Provider allow-list | Only ZDR-verified providers in routing |
| Contractual controls | Provider agreements reviewed for data handling |

### Change Management

| Requirement | ZeroVeil Implementation |
|-------------|------------------------|
| Version control | Git-based, all changes tracked |
| Code review | PR-based workflow, required reviews |
| Testing | Automated CI/CD, conformance tests |
| Rollback capability | Immutable deployments, instant rollback |

---

## NIST AI RMF Alignment

ZeroVeil specifically addresses AI-related risks per the NIST AI Risk Management Framework:

| AI RMF Function | ZeroVeil Controls |
|-----------------|-------------------|
| **GOVERN** | Privacy policy enforcement, tenant governance |
| **MAP** | Threat model documentation, risk identification |
| **MEASURE** | Audit logging, correlation resistance metrics |
| **MANAGE** | ZDR enforcement, provider vetting, abuse controls |

### AI-Specific Risk Mitigations

| Risk Category | Mitigation |
|---------------|-----------|
| Privacy | Mixer architecture reduces provider-side correlation |
| Security | No content logging, encrypted transport |
| Accountability | Audit trails, tenant isolation |
| Transparency | Open-source Community gateway, published policies |

---

## Compliance Evidence Bundles (Pro)

ZeroVeil Pro provides pre-built documentation packages for customer audits:

**Included artifacts:**
- System architecture diagrams
- Data flow documentation
- Control matrices (SOC 2, ISO 27001, HITRUST)
- Access control policies
- Incident response procedures
- Vendor assessment summaries
- Audit log samples and schemas

**Pre-built templates:**
- HIPAA Business Associate Agreement (BAA)
- GDPR Data Processing Agreement (DPA)
- Security questionnaire responses (SIG, CAIQ)

---

## Certification Roadmap

| Certification | Status | Timeline |
|---------------|--------|----------|
| SOC 2 Type I | Planned | Post-revenue |
| SOC 2 Type II | Planned | +6 months after Type I |
| ISO 27001 | Planned | Post-SOC 2 |
| HITRUST | Planned | Customer-driven |
| FedRAMP | Future | Government contract dependent |

*Note: ZeroVeil Pro is designed to support customers' compliance programs today. Formal certifications for ZeroVeil Hosted will be pursued as scale justifies audit costs.*

---

## Customer Compliance Support

ZeroVeil helps customers meet their own compliance requirements:

| Customer Need | How ZeroVeil Helps |
|---------------|-------------------|
| "We need to use AI but can't send PII to cloud providers" | Client-side scrubbing + relay keeps PII in your environment |
| "We need audit trails for AI usage" | Metadata-only logging tracks usage without content |
| "We need to prove AI providers don't retain our data" | ZDR-only routing with provider verification |
| "We need SOC 2 evidence for our AI tools" | Compliance evidence bundles for your auditors |

---

*For compliance questions or custom requirements, contact: Saqib.Khan@Me.com*
