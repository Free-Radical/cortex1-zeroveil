from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from zeroveil_gateway.audit import AuditEvent, AuditLogger
from zeroveil_gateway.policy import RetentionConfig


def test_auditlogger_jsonl_writes_one_json_per_line(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    audit = AuditLogger(sink="jsonl", path=str(log_path))

    audit.log(
        AuditEvent.now(
            request_id="zv_test",
            tenant_id="t1",
            action="allow",
            reason="ok",
            provider="stub",
            model="stub",
            message_count=1,
            total_chars=5,
            zdr_only=True,
            scrubbed_attested=True,
            latency_ms=1,
            extra={"k": "v"},
        )
    )

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["request_id"] == "zv_test"
    assert data["action"] == "allow"


def test_audit_schema_v1_has_schema_version_first_and_ts_iso_parseable(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    audit = AuditLogger(sink="jsonl", path=str(log_path))

    audit.log(
        AuditEvent(
            ts=1_700_000_000,
            request_id="zv_test",
            tenant_id="t1",
            action="allow",
            reason="ok",
        )
    )

    line = log_path.read_text(encoding="utf-8").splitlines()[0]
    assert line.startswith('{"schema_version":'), line
    data = json.loads(line)
    assert data["schema_version"] == "1"
    dt = datetime.fromisoformat(data["ts_iso"])
    assert int(dt.timestamp()) == 1_700_000_000
    assert "client_ip" in data
    assert "user_agent" in data
    assert "tokens_prompt" in data
    assert "tokens_completion" in data


def test_auditlogger_rotates_and_cleans_up_old_files(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    # Exceed 1MB threshold.
    log_path.write_bytes(b"a" * (1024 * 1024 + 1))

    # A rotated file that is old enough to be deleted on rotation (and won't be overwritten).
    old_rotated = tmp_path / "audit.jsonl.5"
    old_rotated.write_text("old", encoding="utf-8")
    old_ts = time.time() - (2 * 86400)
    os.utime(old_rotated, (old_ts, old_ts))

    # A stray file beyond rotate_count should be removed.
    stray = tmp_path / "audit.jsonl.99"
    stray.write_text("stray", encoding="utf-8")

    audit = AuditLogger(
        sink="jsonl",
        path=str(log_path),
        retention=RetentionConfig(max_size_mb=1, max_age_days=1, rotate_count=5),
    )

    audit.log(
        AuditEvent(
            ts=1_700_000_001,
            request_id="zv_test",
            tenant_id="t1",
            action="allow",
            reason="ok",
        )
    )

    rotated = tmp_path / "audit.jsonl.1"
    assert rotated.exists()
    assert log_path.exists()
    assert log_path.stat().st_size < 10_000

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    assert not old_rotated.exists()
    assert not stray.exists()


def test_auditlogger_stdout_sink(capsys) -> None:
    """Test that stdout sink prints JSON lines to stdout."""
    audit = AuditLogger(sink="stdout", path=None)

    audit.log(
        AuditEvent(
            ts=1_700_000_000,
            request_id="zv_stdout_test",
            tenant_id="t1",
            action="allow",
            reason="ok",
        )
    )

    captured = capsys.readouterr()
    assert "zv_stdout_test" in captured.out
    data = json.loads(captured.out.strip())
    assert data["request_id"] == "zv_stdout_test"
    assert data["action"] == "allow"


def test_auditlogger_no_path_noop() -> None:
    """Test that jsonl sink with no path is a no-op (doesn't crash)."""
    audit = AuditLogger(sink="jsonl", path=None)
    # Should not raise
    audit.log(
        AuditEvent(
            ts=1_700_000_000,
            request_id="zv_noop",
            tenant_id="t1",
            action="allow",
            reason="ok",
        )
    )


def test_maybe_rotate_file_not_exists(tmp_path: Path) -> None:
    """Test that rotation handles non-existent log file gracefully."""
    log_path = tmp_path / "nonexistent.jsonl"
    audit = AuditLogger(
        sink="jsonl",
        path=str(log_path),
        retention=RetentionConfig(max_size_mb=1, max_age_days=1, rotate_count=5),
    )

    # Should not raise - creates file
    audit.log(
        AuditEvent(
            ts=1_700_000_000,
            request_id="zv_new",
            tenant_id="t1",
            action="allow",
            reason="ok",
        )
    )

    assert log_path.exists()


def test_maybe_rotate_disabled_rotate_count_zero(tmp_path: Path) -> None:
    """Test that rotation is skipped when rotate_count=0."""
    log_path = tmp_path / "audit.jsonl"
    # Create a file that would normally trigger rotation
    log_path.write_bytes(b"a" * (2 * 1024 * 1024))

    audit = AuditLogger(
        sink="jsonl",
        path=str(log_path),
        retention=RetentionConfig(max_size_mb=1, max_age_days=1, rotate_count=0),
    )

    audit.log(
        AuditEvent(
            ts=1_700_000_000,
            request_id="zv_no_rotate",
            tenant_id="t1",
            action="allow",
            reason="ok",
        )
    )

    # No rotation should have occurred
    assert not (tmp_path / "audit.jsonl.1").exists()


def test_maybe_rotate_disabled_max_size_zero(tmp_path: Path) -> None:
    """Test that rotation is skipped when max_size_mb=0."""
    log_path = tmp_path / "audit.jsonl"
    log_path.write_bytes(b"a" * (2 * 1024 * 1024))

    audit = AuditLogger(
        sink="jsonl",
        path=str(log_path),
        retention=RetentionConfig(max_size_mb=0, max_age_days=1, rotate_count=5),
    )

    audit.log(
        AuditEvent(
            ts=1_700_000_000,
            request_id="zv_no_rotate",
            tenant_id="t1",
            action="allow",
            reason="ok",
        )
    )

    # No rotation should have occurred
    assert not (tmp_path / "audit.jsonl.1").exists()


def test_audit_event_now_factory() -> None:
    """Test that AuditEvent.now() creates event with current timestamp."""
    before = int(time.time())
    event = AuditEvent.now(
        request_id="zv_now",
        tenant_id="t1",
        action="allow",
        reason="ok",
    )
    after = int(time.time())

    assert before <= event.ts <= after
    assert event.request_id == "zv_now"
    assert event.ts_iso  # Should be populated by __post_init__


def test_audit_event_to_dict_contains_all_fields() -> None:
    """Test that to_dict() includes all expected fields."""
    event = AuditEvent(
        ts=1_700_000_000,
        request_id="zv_dict",
        tenant_id="t1",
        action="deny",
        reason="rate_limited",
        client_ip="192.168.1.1",
        user_agent="TestClient/1.0",
        provider="openrouter",
        model="gpt-4",
        tokens_prompt=100,
        tokens_completion=50,
        message_count=3,
        total_chars=500,
        zdr_only=True,
        scrubbed_attested=True,
        latency_ms=42,
        extra={"custom": "field"},
    )

    d = event.to_dict()
    assert d["schema_version"] == "1"
    assert d["ts"] == 1_700_000_000
    assert d["request_id"] == "zv_dict"
    assert d["tenant_id"] == "t1"
    assert d["action"] == "deny"
    assert d["reason"] == "rate_limited"
    assert d["client_ip"] == "192.168.1.1"
    assert d["user_agent"] == "TestClient/1.0"
    assert d["provider"] == "openrouter"
    assert d["model"] == "gpt-4"
    assert d["tokens_prompt"] == 100
    assert d["tokens_completion"] == 50
    assert d["message_count"] == 3
    assert d["total_chars"] == 500
    assert d["zdr_only"] is True
    assert d["scrubbed_attested"] is True
    assert d["latency_ms"] == 42
    assert d["extra"] == {"custom": "field"}
