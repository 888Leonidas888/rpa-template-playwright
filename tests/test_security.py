"""Pruebas del modulo de seguridad: validacion HTTPS y credenciales DPAPI."""

from unittest.mock import patch

import pytest

from config.security import (
    SecurityValidationError,
    get_db_credentials,
    get_graph_credentials,
    get_outlook_recipients,
    get_portal_credentials,
    has_db_credentials,
    has_graph_credentials,
    has_outlook_recipients,
    has_portal_credentials,
    save_db_credentials,
    save_graph_credentials,
    save_outlook_recipients,
    save_portal_credentials,
    validate_url,
)


def test_validate_url_success() -> None:
    """Verifica que una URL HTTPS con dominio autorizado pase la validacion."""
    assert validate_url("https://example.com/login", allowed_domains=["example.com"])
    assert validate_url("https://sub.example.com/api", allowed_domains=["example.com"])


def test_validate_url_rejects_http() -> None:
    """Verifica que protocolos no seguros HTTP disparen SecurityValidationError."""
    with pytest.raises(SecurityValidationError, match="Protocolo inseguro detectado"):
        validate_url("http://example.com/login", allowed_domains=["example.com"])


def test_validate_url_rejects_unauthorized_domain() -> None:
    """Verifica que dominios no autorizados disparen SecurityValidationError."""
    with pytest.raises(SecurityValidationError, match="no pertenece a la lista blanca"):
        validate_url("https://sitio-no-autorizado.com", allowed_domains=["example.com"])


def test_validate_url_rejects_empty() -> None:
    """Verifica que una URL vacia dispare SecurityValidationError."""
    with pytest.raises(SecurityValidationError, match="no puede estar vacia"):
        validate_url("")


def test_portal_credentials_roundtrip() -> None:
    """Verifica el guardado y recuperacion de credenciales del portal web."""
    fake_storage: dict[tuple[str, str], str] = {}

    def mock_set(service: str, username: str, password: str) -> None:
        fake_storage[(service, username)] = password

    def mock_get(service: str, username: str):
        return fake_storage.get((service, username))

    with patch("keyring.set_password", side_effect=mock_set), patch(
        "keyring.get_password", side_effect=mock_get
    ):
        save_portal_credentials("operador@empresa.com", "ClaveSecreta123!")
        assert has_portal_credentials()
        creds = get_portal_credentials()
        assert creds == ("operador@empresa.com", "ClaveSecreta123!")


def test_db_credentials_roundtrip() -> None:
    """Verifica el guardado y recuperacion de configuracion de base de datos."""
    fake_storage: dict[tuple[str, str], str] = {}

    def mock_set(service: str, username: str, password: str) -> None:
        fake_storage[(service, username)] = password

    def mock_get(service: str, username: str):
        return fake_storage.get((service, username))

    with patch("keyring.set_password", side_effect=mock_set), patch(
        "keyring.get_password", side_effect=mock_get
    ):
        save_db_credentials("10.0.0.1", "BD_PRODUCCION", "usr_bot", "pass_bd")
        assert has_db_credentials()
        db = get_db_credentials()
        assert db is not None
        assert db["host"] == "10.0.0.1"
        assert db["database"] == "BD_PRODUCCION"


def test_graph_and_outlook_recipients() -> None:
    """Verifica guardado y separacion de correos con ';' para Graph y Outlook."""
    fake_storage: dict[tuple[str, str], str] = {}

    def mock_set(service: str, username: str, password: str) -> None:
        fake_storage[(service, username)] = password

    def mock_get(service: str, username: str):
        return fake_storage.get((service, username))

    with patch("keyring.set_password", side_effect=mock_set), patch(
        "keyring.get_password", side_effect=mock_get
    ):
        # Graph
        save_graph_credentials(
            "tenant-123", "client-123", "secret-123", "bot@empresa.com", ["a@empresa.com", "b@empresa.com"]
        )
        assert has_graph_credentials()
        g_data = get_graph_credentials()
        assert g_data is not None
        assert len(g_data["recipient_emails"]) == 2

        # Outlook
        save_outlook_recipients(["jefe@empresa.com", "equipo@empresa.com"])
        assert has_outlook_recipients()
        out_emails = get_outlook_recipients()
        assert len(out_emails) == 2
        assert "jefe@empresa.com" in out_emails
