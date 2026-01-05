from __future__ import annotations

import json
from pathlib import Path

import pytest

from zeroveil_gateway.tenants import TenantConfig, TenantRegistry, sha256_hex


def test_tenant_config_validation() -> None:
    good = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("test-api-key")],
        rate_limit_rpm=60,
        rate_limit_tpd=1000,
        enabled=True,
    )
    assert good.tenant_id == "default"

    with pytest.raises(ValueError):
        TenantConfig(
            tenant_id="",
            api_keys=[sha256_hex("test-api-key")],
            rate_limit_rpm=1,
            rate_limit_tpd=1,
            enabled=True,
        )

    with pytest.raises(ValueError):
        TenantConfig(
            tenant_id="t1",
            api_keys=["not-a-sha"],
            rate_limit_rpm=1,
            rate_limit_tpd=1,
            enabled=True,
        )

    with pytest.raises(ValueError):
        TenantConfig(
            tenant_id="t1",
            api_keys=[sha256_hex("k")],
            rate_limit_rpm=-1,
            rate_limit_tpd=1,
            enabled=True,
        )


def test_key_hashing_and_verification() -> None:
    tenant = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("test-api-key")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"default": tenant})

    assert registry.authenticate("test-api-key") is tenant
    assert registry.authenticate("wrong") is None


def test_constant_time_comparison_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    import zeroveil_gateway.tenants as tenants_mod

    def fake_compare_digest(a: str, b: str) -> bool:
        calls.append((a, b))
        return a == b

    monkeypatch.setattr(tenants_mod.secrets, "compare_digest", fake_compare_digest)

    tenant = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("test-api-key")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"default": tenant})

    assert registry.authenticate("wrong") is None
    assert calls, "secrets.compare_digest should be used for hash comparison"


def test_disabled_tenant_rejected() -> None:
    tenant = TenantConfig(
        tenant_id="disabled",
        api_keys=[sha256_hex("test-api-key")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,
        enabled=False,
    )
    registry = TenantRegistry({"disabled": tenant})
    assert registry.authenticate("test-api-key") is None


def test_multiple_keys_per_tenant_rotation_support() -> None:
    tenant = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("old-key"), sha256_hex("new-key")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"default": tenant})
    assert registry.authenticate("old-key") is tenant
    assert registry.authenticate("new-key") is tenant


def test_rate_limit_tracking_and_enforcement() -> None:
    now = 0.0

    def fake_time() -> float:
        return now

    tenant = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=2,
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"default": tenant}, now=fake_time)

    assert registry.check_rate_limit("default") is True
    assert registry.check_rate_limit("default") is True
    assert registry.check_rate_limit("default") is False

    remaining = registry.rpm_remaining("default")
    assert remaining == 0

    now = 61.0
    assert registry.check_rate_limit("default") is True


def test_rate_limit_window_reset() -> None:
    now = 0.0

    def fake_time() -> float:
        return now

    tenant = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=1,
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"default": tenant}, now=fake_time)

    assert registry.check_rate_limit("default") is True
    assert registry.check_rate_limit("default") is False

    now = 60.1
    assert registry.check_rate_limit("default") is True


def test_load_valid_and_invalid_json(tmp_path: Path) -> None:
    good = {
        "tenants": [
            {
                "tenant_id": "default",
                "api_key_hashes": [sha256_hex("test-api-key")],
                "rate_limit_rpm": 60,
                "rate_limit_tpd": 1000,
                "enabled": True,
            }
        ]
    }
    good_path = tmp_path / "tenants.json"
    good_path.write_text(json.dumps(good), encoding="utf-8")

    registry = TenantRegistry.load(str(good_path))
    assert registry.get("default") is not None

    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        TenantRegistry.load(str(bad_path))

    missing_key_path = tmp_path / "missing.json"
    missing_key_path.write_text(json.dumps({"nope": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        TenantRegistry.load(str(missing_key_path))


def test_tokens_per_day_tracking_and_reset() -> None:
    now = 0.0

    def fake_time() -> float:
        return now

    tenant = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=10,
        enabled=True,
    )
    registry = TenantRegistry({"default": tenant}, now=fake_time)

    assert registry.check_rate_limit("default") is True
    assert registry.tpd_remaining("default") == 10

    registry.record_usage("default", 7)
    assert registry.tpd_remaining("default") == 3
    assert registry.check_rate_limit("default") is True

    registry.record_usage("default", 3)
    assert registry.tpd_remaining("default") == 0
    assert registry.check_rate_limit("default") is False

    now = 86400.1
    assert registry.check_rate_limit("default") is True
    assert registry.tpd_remaining("default") == 10


def test_record_usage_negative_tokens_raises() -> None:
    tenant = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=10,
        enabled=True,
    )
    registry = TenantRegistry({"default": tenant})
    with pytest.raises(ValueError):
        registry.record_usage("default", -1)


def test_tenant_config_whitespace_only_tenant_id() -> None:
    """Test that whitespace-only tenant_id is rejected."""
    with pytest.raises(ValueError, match="tenant_id must be non-empty"):
        TenantConfig(
            tenant_id="   ",
            api_keys=[sha256_hex("k")],
            rate_limit_rpm=0,
            rate_limit_tpd=0,
            enabled=True,
        )


def test_tenant_config_api_keys_not_list() -> None:
    """Test that non-list api_keys is rejected."""
    with pytest.raises(ValueError, match="api_keys must be a list"):
        TenantConfig(
            tenant_id="t1",
            api_keys="not-a-list",  # type: ignore[arg-type]
            rate_limit_rpm=0,
            rate_limit_tpd=0,
            enabled=True,
        )


def test_tenant_config_api_keys_contains_non_string() -> None:
    """Test that api_keys containing non-strings is rejected."""
    with pytest.raises(ValueError, match="api_keys must contain strings"):
        TenantConfig(
            tenant_id="t1",
            api_keys=[123],  # type: ignore[list-item]
            rate_limit_rpm=0,
            rate_limit_tpd=0,
            enabled=True,
        )


def test_tenant_config_negative_rate_limit_tpd() -> None:
    """Test that negative rate_limit_tpd is rejected."""
    with pytest.raises(ValueError, match="rate_limit_tpd must be >= 0"):
        TenantConfig(
            tenant_id="t1",
            api_keys=[sha256_hex("k")],
            rate_limit_rpm=0,
            rate_limit_tpd=-1,
            enabled=True,
        )


def test_authenticate_empty_token() -> None:
    """Test that empty token returns None."""
    tenant = TenantConfig(
        tenant_id="default",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"default": tenant})
    assert registry.authenticate("") is None
    assert registry.authenticate("   ") is None


def test_load_entry_not_dict(tmp_path: Path) -> None:
    """Test that non-dict tenant entry is rejected."""
    bad = {"tenants": ["not-a-dict"]}
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="Each tenant entry must be an object"):
        TenantRegistry.load(str(bad_path))


def test_load_rate_limit_rpm_not_int(tmp_path: Path) -> None:
    """Test that non-int rate_limit_rpm is rejected."""
    bad = {
        "tenants": [
            {
                "tenant_id": "t1",
                "api_key_hashes": [sha256_hex("k")],
                "rate_limit_rpm": "not-an-int",
                "rate_limit_tpd": 0,
                "enabled": True,
            }
        ]
    }
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="rate_limit_rpm must be an int"):
        TenantRegistry.load(str(bad_path))


def test_load_rate_limit_tpd_not_int(tmp_path: Path) -> None:
    """Test that non-int rate_limit_tpd is rejected."""
    bad = {
        "tenants": [
            {
                "tenant_id": "t1",
                "api_key_hashes": [sha256_hex("k")],
                "rate_limit_rpm": 0,
                "rate_limit_tpd": "not-an-int",
                "enabled": True,
            }
        ]
    }
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="rate_limit_tpd must be an int"):
        TenantRegistry.load(str(bad_path))


def test_load_enabled_not_bool(tmp_path: Path) -> None:
    """Test that non-bool enabled is rejected."""
    bad = {
        "tenants": [
            {
                "tenant_id": "t1",
                "api_key_hashes": [sha256_hex("k")],
                "rate_limit_rpm": 0,
                "rate_limit_tpd": 0,
                "enabled": "yes",
            }
        ]
    }
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="enabled must be a bool"):
        TenantRegistry.load(str(bad_path))


def test_load_duplicate_tenant_id(tmp_path: Path) -> None:
    """Test that duplicate tenant_id is rejected."""
    bad = {
        "tenants": [
            {
                "tenant_id": "duplicate",
                "api_key_hashes": [sha256_hex("k1")],
                "rate_limit_rpm": 0,
                "rate_limit_tpd": 0,
                "enabled": True,
            },
            {
                "tenant_id": "duplicate",
                "api_key_hashes": [sha256_hex("k2")],
                "rate_limit_rpm": 0,
                "rate_limit_tpd": 0,
                "enabled": True,
            },
        ]
    }
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate tenant_id"):
        TenantRegistry.load(str(bad_path))


def test_rpm_remaining_unknown_tenant() -> None:
    """Test that rpm_remaining returns 0 for unknown tenant."""
    registry = TenantRegistry({})
    assert registry.rpm_remaining("unknown") == 0


def test_tpd_remaining_unknown_tenant() -> None:
    """Test that tpd_remaining returns 0 for unknown tenant."""
    registry = TenantRegistry({})
    assert registry.tpd_remaining("unknown") == 0


def test_rpm_remaining_disabled_tenant() -> None:
    """Test that rpm_remaining returns 0 for disabled tenant."""
    tenant = TenantConfig(
        tenant_id="disabled",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=100,
        rate_limit_tpd=0,
        enabled=False,
    )
    registry = TenantRegistry({"disabled": tenant})
    assert registry.rpm_remaining("disabled") == 0


def test_tpd_remaining_disabled_tenant() -> None:
    """Test that tpd_remaining returns 0 for disabled tenant."""
    tenant = TenantConfig(
        tenant_id="disabled",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=1000,
        enabled=False,
    )
    registry = TenantRegistry({"disabled": tenant})
    assert registry.tpd_remaining("disabled") == 0


def test_check_rate_limit_unknown_tenant() -> None:
    """Test that check_rate_limit returns False for unknown tenant."""
    registry = TenantRegistry({})
    assert registry.check_rate_limit("unknown") is False


def test_record_usage_unknown_tenant() -> None:
    """Test that record_usage is a no-op for unknown tenant."""
    registry = TenantRegistry({})
    # Should not raise
    registry.record_usage("unknown", 100)


def test_record_usage_disabled_tenant() -> None:
    """Test that record_usage is a no-op for disabled tenant."""
    tenant = TenantConfig(
        tenant_id="disabled",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=1000,
        enabled=False,
    )
    registry = TenantRegistry({"disabled": tenant})
    # Should not raise
    registry.record_usage("disabled", 100)


def test_record_usage_tpd_disabled() -> None:
    """Test that record_usage is a no-op when tpd=0 (disabled)."""
    tenant = TenantConfig(
        tenant_id="t1",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,  # TPD disabled
        enabled=True,
    )
    registry = TenantRegistry({"t1": tenant})
    # Should not raise, and should not track
    registry.record_usage("t1", 100)
    assert registry.tpd_remaining("t1") is None


def test_get_method() -> None:
    """Test the get() method."""
    tenant = TenantConfig(
        tenant_id="t1",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"t1": tenant})
    assert registry.get("t1") is tenant
    assert registry.get("unknown") is None


def test_tenants_property() -> None:
    """Test the tenants property returns a copy."""
    tenant = TenantConfig(
        tenant_id="t1",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"t1": tenant})
    tenants = registry.tenants
    assert "t1" in tenants
    # Should be a copy, not the internal dict
    tenants["t2"] = tenant  # type: ignore[assignment]
    assert "t2" not in registry.tenants


def test_rpm_remaining_returns_none_when_unlimited() -> None:
    """Test that rpm_remaining returns None when rate_limit_rpm=0 (unlimited)."""
    tenant = TenantConfig(
        tenant_id="t1",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,  # Unlimited
        rate_limit_tpd=0,
        enabled=True,
    )
    registry = TenantRegistry({"t1": tenant})
    assert registry.rpm_remaining("t1") is None


def test_tpd_remaining_returns_none_when_unlimited() -> None:
    """Test that tpd_remaining returns None when rate_limit_tpd=0 (unlimited)."""
    tenant = TenantConfig(
        tenant_id="t1",
        api_keys=[sha256_hex("k")],
        rate_limit_rpm=0,
        rate_limit_tpd=0,  # Unlimited
        enabled=True,
    )
    registry = TenantRegistry({"t1": tenant})
    assert registry.tpd_remaining("t1") is None
