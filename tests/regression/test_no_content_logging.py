from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from zeroveil_gateway.app import create_app


def test_audit_log_never_contains_message_content(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    audit_path = tmp_path / "audit.jsonl"
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "version": "0",
                "enforce_zdr_only": True,
                "require_scrubbed_attestation": True,
                "allowed_providers": ["openrouter"],
                "allowed_models": ["*"],
                "limits": {"max_messages": 50, "max_chars_per_message": 16000},
                "logging": {"mode": "metadata_only", "sink": "jsonl", "path": str(audit_path)},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))

    secret_marker = "SECRET_PII_12345"
    client = TestClient(create_app())

    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": secret_marker}],
            "zdr_only": True,
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 200

    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert lines, "expected at least one audit log line"
    assert secret_marker not in audit_path.read_text(encoding="utf-8")


def test_audit_log_records_deny_events(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Test that deny events are recorded in the audit log."""
    audit_path = tmp_path / "audit.jsonl"
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "version": "0",
                "enforce_zdr_only": True,
                "require_scrubbed_attestation": True,
                "allowed_providers": ["openrouter"],
                "allowed_models": ["allowed-only"],
                "limits": {"max_messages": 50, "max_chars_per_message": 16000},
                "logging": {"mode": "metadata_only", "sink": "jsonl", "path": str(audit_path)},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))

    client = TestClient(create_app())

    secret_content = "DENY_SECRET_XYZ_99887"
    # This should be denied (model not allowed)
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "blocked-model",
            "messages": [{"role": "user", "content": secret_content}],
            "zdr_only": True,
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 403

    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert lines, "expected at least one audit log line for deny"

    deny_event = json.loads(lines[0])
    assert deny_event["action"] == "deny"
    assert deny_event["reason"] == "policy_denied"
    # Model name is metadata (ok to log), message content is not
    assert deny_event["model"] == "blocked-model"
    assert secret_content not in json.dumps(deny_event)  # Message content should not be logged


def test_audit_log_deny_does_not_contain_message_content(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Test that deny events don't leak message content to audit log."""
    audit_path = tmp_path / "audit.jsonl"
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "version": "0",
                "enforce_zdr_only": True,
                "require_scrubbed_attestation": True,
                "allowed_providers": ["openrouter"],
                "allowed_models": ["*"],
                "limits": {"max_messages": 1, "max_chars_per_message": 16000},
                "logging": {"mode": "metadata_only", "sink": "jsonl", "path": str(audit_path)},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ZEROVEIL_POLICY_PATH", str(policy_path))

    secret_marker = "SECRET_DENY_MARKER_67890"
    client = TestClient(create_app())

    # This should be denied (too many messages)
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": secret_marker},
                {"role": "user", "content": "second message"},
            ],
            "zdr_only": True,
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 403

    audit_content = audit_path.read_text(encoding="utf-8")
    assert secret_marker not in audit_content

