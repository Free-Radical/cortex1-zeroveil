from __future__ import annotations

import pytest

from zeroveil_gateway.policy import Policy, PolicyError


def test_policy_from_dict_defaults_and_required_fields() -> None:
    policy = Policy.from_dict(
        {
            "version": "0",
            "allowed_providers": ["openrouter"],
            "logging": {"mode": "metadata_only", "sink": "stdout"},
        }
    )
    assert policy.enforce_zdr_only is True
    assert policy.require_scrubbed_attestation is True
    assert policy.allowed_models == ["*"]


def test_policy_rejects_missing_allowed_providers() -> None:
    with pytest.raises(PolicyError, match="allowed_providers must be non-empty"):
        Policy.from_dict({"logging": {"mode": "metadata_only", "sink": "stdout"}})


def test_policy_rejects_unsupported_logging_mode() -> None:
    with pytest.raises(PolicyError, match="Unsupported logging\\.mode"):
        Policy.from_dict(
            {
                "allowed_providers": ["openrouter"],
                "logging": {"mode": "content", "sink": "stdout"},
            }
        )


def test_policy_requires_path_for_jsonl_sink() -> None:
    with pytest.raises(PolicyError, match="logging\\.path required"):
        Policy.from_dict(
            {
                "allowed_providers": ["openrouter"],
                "logging": {"mode": "metadata_only", "sink": "jsonl"},
            }
        )


def test_policy_rejects_unsupported_logging_sink() -> None:
    with pytest.raises(PolicyError, match="Unsupported logging\\.sink"):
        Policy.from_dict(
            {
                "allowed_providers": ["openrouter"],
                "logging": {"mode": "metadata_only", "sink": "invalid_sink"},
            }
        )


def test_policy_load_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        Policy.load("/nonexistent/path/to/policy.json")


def test_policy_load_invalid_json(tmp_path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(Exception):  # json.JSONDecodeError
        Policy.load(str(bad_file))


def test_policy_load_non_dict_root(tmp_path) -> None:
    array_file = tmp_path / "array.json"
    array_file.write_text('["not", "a", "dict"]', encoding="utf-8")
    with pytest.raises(PolicyError, match="must be a JSON object"):
        Policy.load(str(array_file))


def test_policy_rejects_negative_retention_max_size_mb() -> None:
    with pytest.raises(PolicyError, match="max_size_mb must be >= 0"):
        Policy.from_dict(
            {
                "allowed_providers": ["openrouter"],
                "logging": {
                    "mode": "metadata_only",
                    "sink": "jsonl",
                    "path": "/tmp/audit.jsonl",
                    "retention": {"max_size_mb": -1},
                },
            }
        )


def test_policy_rejects_negative_retention_max_age_days() -> None:
    with pytest.raises(PolicyError, match="max_age_days must be >= 0"):
        Policy.from_dict(
            {
                "allowed_providers": ["openrouter"],
                "logging": {
                    "mode": "metadata_only",
                    "sink": "jsonl",
                    "path": "/tmp/audit.jsonl",
                    "retention": {"max_age_days": -1},
                },
            }
        )


def test_policy_rejects_negative_retention_rotate_count() -> None:
    with pytest.raises(PolicyError, match="rotate_count must be >= 0"):
        Policy.from_dict(
            {
                "allowed_providers": ["openrouter"],
                "logging": {
                    "mode": "metadata_only",
                    "sink": "jsonl",
                    "path": "/tmp/audit.jsonl",
                    "retention": {"rotate_count": -1},
                },
            }
        )


def test_logpath_fspath_and_str() -> None:
    from zeroveil_gateway.policy import LogPath
    import os

    log_path = LogPath(path="/var/log/audit.jsonl")
    assert os.fspath(log_path) == "/var/log/audit.jsonl"
    assert str(log_path) == "/var/log/audit.jsonl"

