from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zeroveil_gateway.app import create_app
from zeroveil_gateway.policy import Policy


def make_policy(*, allowed_models: list[str] | None = None) -> Policy:
    return Policy(
        version="0",
        enforce_zdr_only=True,
        require_scrubbed_attestation=True,
        allowed_providers=["openrouter"],
        allowed_models=allowed_models if allowed_models is not None else ["*"],
        max_messages=50,
        max_chars_per_message=16000,
        logging_mode="metadata_only",
        logging_sink="stdout",
        logging_path=None,
    )


def make_client(monkeypatch: pytest.MonkeyPatch, *, policy: Policy) -> TestClient:
    import zeroveil_gateway.app as app_mod

    monkeypatch.setattr(app_mod.Policy, "load", staticmethod(lambda _path: policy))
    return TestClient(create_app())


def test_invalid_role_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(monkeypatch, policy=make_policy())
    resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "bad_role", "content": "hi"}], "metadata": {"scrubbed": True}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "invalid_request"
    assert body["error"]["details"] == {
        "field": "messages[0].role",
        "value": "bad_role",
        "allowed": ["system", "user", "assistant", "tool", "function"],
    }


def test_valid_roles_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(monkeypatch, policy=make_policy())
    for role in ["system", "user", "assistant", "tool", "function"]:
        resp = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": role, "content": "hi"}], "metadata": {"scrubbed": True}},
        )
        assert resp.status_code == 200, (role, resp.json())


def test_model_not_in_allowlist_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(monkeypatch, policy=make_policy(allowed_models=["allowed-model"]))
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "blocked-model",
            "messages": [{"role": "user", "content": "hi"}],
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "policy_denied"
    assert body["error"]["details"] == {
        "field": "model",
        "value": "blocked-model",
        "allowed": ["allowed-model"],
    }


def test_null_bytes_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(monkeypatch, policy=make_policy())
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hi\x00there"}],
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "invalid_request"
    assert body["error"]["details"] == {"field": "messages[0].content"}


def test_none_content_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(monkeypatch, policy=make_policy())
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": None}],
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "invalid_request"
    assert body["error"]["details"] == {"field": "messages[0].content"}


def test_empty_messages_list_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that empty messages list is rejected with 400."""
    client = make_client(monkeypatch, policy=make_policy())
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [],
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "invalid_request"
    assert "messages must be non-empty" in body["error"]["message"]


def test_wildcard_model_allows_any(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that wildcard '*' in allowed_models permits any model."""
    client = make_client(monkeypatch, policy=make_policy(allowed_models=["*"]))
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "any-model-name",
            "messages": [{"role": "user", "content": "hi"}],
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 200


def test_model_none_with_restricted_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that model=None is accepted even with restricted allowlist."""
    client = make_client(monkeypatch, policy=make_policy(allowed_models=["specific-model"]))
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "metadata": {"scrubbed": True},
            # model is omitted (None)
        },
    )
    # Should be accepted - model validation only applies when model is specified
    assert resp.status_code == 200


def test_multiple_invalid_roles_reports_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that multiple invalid roles reports the first one."""
    client = make_client(monkeypatch, policy=make_policy())
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "bad1", "content": "hi"},
                {"role": "bad2", "content": "there"},
            ],
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "invalid_request"
    assert body["error"]["details"]["field"] == "messages[0].role"
    assert body["error"]["details"]["value"] == "bad1"


def test_legacy_mode_no_auth_required(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Test that legacy mode without API key requires no auth."""
    import zeroveil_gateway.app as app_mod

    monkeypatch.setattr(app_mod.Policy, "load", staticmethod(lambda _path: make_policy()))
    # Ensure no API key is set
    monkeypatch.delenv("ZEROVEIL_API_KEY", raising=False)
    # Point to a non-existent tenants file so it falls back to legacy mode
    monkeypatch.setenv("ZEROVEIL_TENANTS_PATH", str(tmp_path / "nonexistent.json"))

    client = TestClient(create_app())
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "metadata": {"scrubbed": True},
        },
    )
    # No auth required in legacy mode without API key
    assert resp.status_code == 200


def test_message_size_limit_reports_index(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that oversized message reports correct index."""
    policy = Policy(
        version="0",
        enforce_zdr_only=True,
        require_scrubbed_attestation=True,
        allowed_providers=["openrouter"],
        allowed_models=["*"],
        max_messages=50,
        max_chars_per_message=5,  # Very small limit
        logging_mode="metadata_only",
        logging_sink="stdout",
        logging_path=None,
    )
    client = make_client(monkeypatch, policy=policy)
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "ok"},  # Fine
                {"role": "user", "content": "this is too long"},  # Over limit
            ],
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "policy_denied"
    assert body["error"]["details"]["index"] == 1
    assert body["error"]["details"]["limit"] == 5


def test_zdr_only_false_rejected_when_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that zdr_only=false is rejected when enforce_zdr_only is true."""
    client = make_client(monkeypatch, policy=make_policy())
    resp = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "zdr_only": False,
            "metadata": {"scrubbed": True},
        },
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "policy_denied"
    assert body["error"]["details"]["field"] == "zdr_only"
