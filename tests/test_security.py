"""Tests for security module: URL validation and DPAPI credential helpers."""

from unittest.mock import patch

import pytest

from config.security import (
    SecurityValidationError,
    get_portal_credentials,
    has_portal_credentials,
    save_portal_credentials,
    validate_url,
)


def test_validate_url_success() -> None:
    """Verifies valid HTTPS URL within authorized domains passes."""
    assert validate_url("https://example.com/login", allowed_domains=["example.com"])
    assert validate_url("https://sub.example.com/api", allowed_domains=["example.com"])


def test_validate_url_rejects_http() -> None:
    """Verifies unencrypted HTTP URLs raise SecurityValidationError."""
    with pytest.raises(SecurityValidationError, match="Insecure protocol detected"):
        validate_url("http://example.com/login", allowed_domains=["example.com"])


def test_validate_url_rejects_unauthorized_domain() -> None:
    """Verifies unauthorized domains raise SecurityValidationError."""
    with pytest.raises(SecurityValidationError, match="not in the authorized domains"):
        validate_url("https://malicious-site.com", allowed_domains=["example.com"])


def test_validate_url_rejects_empty() -> None:
    """Verifies empty URL raises SecurityValidationError."""
    with pytest.raises(SecurityValidationError, match="cannot be empty"):
        validate_url("")


def test_portal_credentials_roundtrip() -> None:
    """Tests saving and retrieving portal credentials with mocked keyring."""
    fake_storage: dict[tuple[str, str], str] = {}

    def mock_set(service: str, username: str, password: str) -> None:
        fake_storage[(service, username)] = password

    def mock_get(service: str, username: str):
        return fake_storage.get((service, username))

    with patch("keyring.set_password", side_effect=mock_set), patch(
        "keyring.get_password", side_effect=mock_get
    ):
        save_portal_credentials("operator@stn.com", "SecretPass123!")
        assert has_portal_credentials()
        creds = get_portal_credentials()
        assert creds == ("operator@stn.com", "SecretPass123!")
