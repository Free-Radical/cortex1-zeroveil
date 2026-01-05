# Cortex1-ZeroVeil - Community Gateway Plan (Weekly)

This file tracks the **weekly execution plan** for the **Community Gateway** (this repo).

## Best practices (edition boundary)

- Community is for **proving core value with minimal trust + minimal ops**:
  - an auditable policy gateway + relay primitives, safe defaults, and a working reference integration
- Pro/Hosted is for **advanced features** that expand trust/compliance/ops surface:
  - tier escalation, automated cost/pricing policy, enterprise auth/RBAC, compliance exports, signed logs, hosted relay identity at scale

## Week 1 (Done)

- v0 contract: `docs/spec-v0.md`
- Policy + enforcement stub: `policies/default.json`, `src/zeroveil_gateway/app.py`
- CI + tests: `.github/workflows/ci.yml`, `tests/test_gateway_v0.py`
- Community vs Pro boundary + contribution/legal docs: `docs/editions.md`, `CLA.md`, `CONTRIBUTING.md`

## Week 2 (MVP Hardening)

- Multi-tenant auth model (tenant IDs + per-tenant keys + rate limits)
- Request validation hardening (size limits, role validation, better errors)
- Metadata-only audit event schema v1 + retention defaults
- Optional PII/PHI reject-only gate (detect and reject unsafely-scrubbed requests; never "scrub-as-a-service") - Pro/Hosted first
- Threat model doc v1 (conservative claims, abuse cases, non-goals)

## Week 3 (First Real Provider)

- Implement provider adapter (start with OpenRouter) behind policy gates
- Enforce ZDR allowlist as a first-class policy rule
- Consistent upstream error mapping + timeouts + retries

## Week 4 (Policy + Normalization)

- Prompt normalization rules (system preamble injection, tool constraints)
- Policy packs/examples (regulated vs general)
- Conformance tests proving invariants (no content logging by default, scrub attestation required, ZDR enforced)

## Week 5 (Mixer Primitives)

Full mixer implementation for both Community and Pro editions. See `docs/mixer-design.md` for technical details.

**Mixer Primitives (both editions):**
- Request batching with configurable windows (min_batch, max_wait)
- Shuffle dispatch (randomized order within batches)
- Timing jitter (50-200ms random delays)
- Header stripping (remove tenant-identifying metadata)
- Request normalization (strip fingerprinting vectors)
- One-time response tokens (unlinkable return routing)

**Cloud-Hosted (both editions):**
- Shared relay identity (ZeroVeil-operated API keys)
- Network effect: larger mixing pool = stronger correlation resistance

**Pro additions:**
- Advanced abuse resistance controls
- Multi-region routing options
- Stronger tenant isolation guarantees

## Week 6 (Operational telemetry — metadata-only)

- Community: operational metrics without content (latency, token counts if available, error rates).
- Pro/Hosted: compliance exports and signed/immutable logs (see `docs/editions.md`).

## Week 7 (Showcase Integration)

- One reference client integration proving infrastructure value
- Reproducible demo script + short walkthrough

## Week 8 (Security + Release)

- Abuse resistance pass + key-handling review
- Public MVP release notes + grant applications kickoff

## ZeroVeil SDK Visibility

- SDK is source-available under BSL (same as gateway)
- Early access is invite-only during initial development
- TODO: Open public access when ready for broad adoption
