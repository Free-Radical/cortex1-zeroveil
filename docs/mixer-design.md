# Mixer Design

Technical specification for ZeroVeil's request mixing system.

**Goal:** Break the correlation between tenant identity and request content at the provider level.

---

## Overview

```
Tenant A ──┐
Tenant B ──┼──→ [Auth + Validate] ──→ [Mixer Queue] ──→ [Shared API Key] ──→ Provider
Tenant C ──┘         │                      │
                     │                      │
              Verify attestation     Batch + Shuffle
              Rate limit check       Random delays
              Strip tenant headers   Normalize requests
```

**Provider sees:** Requests from "ZeroVeil" with no tenant-identifying information.

**Provider cannot easily determine:** Which tenant sent which request.

---

## Mixer Primitives

### 1. Request Batching

Collect multiple requests before dispatching to reduce timing correlation.

```python
@dataclass
class MixerConfig:
    min_batch_size: int = 3         # Wait for N requests before dispatch
    max_wait_ms: int = 500          # Or timeout, whichever comes first
    jitter_range_ms: tuple = (50, 200)  # Random delay per request
```

**Trade-off:** Larger batches = better mixing, but higher latency.

| Setting | Latency Impact | Mixing Quality |
|---------|----------------|----------------|
| min_batch=1, max_wait=0 | None | None (pass-through) |
| min_batch=3, max_wait=500ms | Up to 500ms | Basic |
| min_batch=10, max_wait=2000ms | Up to 2s | Good |

**Default (Community):** min_batch=3, max_wait=500ms (balance latency vs. privacy)

### 2. Request Normalization

Strip all tenant-identifying metadata before forwarding.

```python
def normalize_request(req: dict, tenant: TenantConfig) -> dict:
    """Remove fingerprinting vectors from request."""
    return {
        "messages": req["messages"],        # Already scrubbed by client
        "model": req.get("model", "default"),
        "metadata": {
            "scrubbed": req.get("metadata", {}).get("scrubbed", False),
            # DROP: tenant_id, client IP, timestamps, custom headers
            # DROP: scrubber version (could fingerprint SDK version)
        },
    }
```

**Stripped fields:**
- `X-ZeroVeil-Tenant` header
- Client IP address
- Request timestamps (replaced with batch timestamp)
- Custom metadata beyond scrub attestation

### 3. Shuffle Dispatch

Randomize order within each batch.

```python
import random
import asyncio

async def dispatch_batch(batch: list[NormalizedRequest]) -> list[Response]:
    """Dispatch batch in random order with jitter."""
    random.shuffle(batch)

    responses = []
    for req in batch:
        # Random delay between requests
        jitter = random.uniform(0.05, 0.2)  # 50-200ms
        await asyncio.sleep(jitter)

        response = await send_to_provider(req)
        responses.append(response)

    return responses
```

**Effect:** Request #1 in queue might be sent 3rd. Timing analysis becomes unreliable.

### 4. One-Time Response Tokens

Route responses back without persistent tenant↔request mapping.

```python
import secrets

# On request arrival
correlation_token = secrets.token_hex(16)  # One-time, random
pending_responses[correlation_token] = tenant_connection
request.internal_token = correlation_token

# On provider response
async def handle_response(response, internal_token):
    tenant_conn = pending_responses.pop(internal_token)  # Remove immediately
    await tenant_conn.send(response)
    # Token is now garbage - no persistent link
```

**Key property:** After response delivery, no record exists of which tenant made which request.

### 5. Shared Relay Identity

All requests use ZeroVeil's API credentials (cloud-hosted only).

```python
# Cloud-hosted: shared credentials
PROVIDER_API_KEY = os.getenv("ZEROVEIL_PROVIDER_KEY")  # One key for all tenants

# Self-hosted: tenant provides their own
# (No mixing benefit, but still get policy enforcement)
```

---

## What This Defeats

| Attack Vector | Mitigated | Mechanism |
|---------------|-----------|-----------|
| Provider sees tenant ID | Yes | Header stripping, shared credentials |
| Timing correlation | Yes | Batching + jitter + shuffle |
| Request ordering analysis | Yes | Shuffle within batch |
| Volume fingerprinting | Partial | Batching smooths bursts |
| API key breach → user history | Yes | Shared key has no per-user history |

## What This Does NOT Defeat

| Attack Vector | Why Not | Mitigation |
|---------------|---------|------------|
| Stylometry (writing style) | Content-based | User must vary prompts |
| Semantic fingerprinting | Unique topics leak identity | User responsibility |
| Low-volume correlation | Few tenants = weak mixing | Cloud hosting (larger pool) |
| Compromised ZeroVeil | Operator collusion | Self-host if untrusted |
| Legal compulsion | Subpoena to operator | Jurisdiction choice, warrant canary |

---

## Network Effect

Mixing effectiveness scales with tenant count:

```
Mixing Pool Size → Correlation Resistance
─────────────────────────────────────────
     1 tenant   → 0%   (no mixing possible)
     5 tenants  → ~80% (basic protection)
    50 tenants  → ~98% (strong protection)
   500 tenants  → ~99.8% (very strong)
```

**This is why cloud-hosted is recommended for small organizations.**

Self-hosting only provides policy enforcement and ZDR routing — no mixing benefit unless you have multiple internal tenants.

---

## Configuration

### Environment Variables

```bash
# Mixer settings
ZEROVEIL_MIXER_MIN_BATCH=3
ZEROVEIL_MIXER_MAX_WAIT_MS=500
ZEROVEIL_MIXER_JITTER_MIN_MS=50
ZEROVEIL_MIXER_JITTER_MAX_MS=200

# Disable mixing (pass-through mode)
ZEROVEIL_MIXER_ENABLED=false
```

### Policy Integration

```json
{
  "version": "1",
  "mixer": {
    "enabled": true,
    "min_batch_size": 3,
    "max_wait_ms": 500,
    "jitter_ms": [50, 200]
  }
}
```

---

## Implementation Status

| Component | Status | Week |
|-----------|--------|------|
| Request normalization | Planned | 5 |
| Batching queue | Planned | 5 |
| Shuffle dispatch | Planned | 5 |
| Jitter timing | Planned | 5 |
| Response routing | Planned | 5 |
| Config/policy integration | Planned | 5 |

---

## Security Considerations

### Logging

Mixer MUST NOT log:
- Request content (already policy)
- Correlation tokens after response delivery
- Tenant↔request mappings

Mixer MAY log (metadata only):
- Batch sizes
- Aggregate latency stats
- Error rates

### Memory Safety

- Correlation tokens cleared immediately after response
- No persistent tenant↔request state
- Batch queue has bounded size (prevents memory exhaustion)

### Failure Modes

| Failure | Behavior |
|---------|----------|
| Batch timeout | Dispatch partial batch |
| Provider error | Return error to originating tenant only |
| Memory pressure | Reject new requests (429) |

---

*Document Version: 1.0*
*Date: January 2026*
