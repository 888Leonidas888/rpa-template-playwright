"""Pruebas de la interfaz de linea de comandos (CLI) y renderizado Rich."""

import argparse
from unittest.mock import patch

import pytest

from cli.commands import _resolve_notifiers, handle_auth, handle_status


def test_resolve_notifiers_fails_when_graph_emails_missing() -> None:
    """Verifica que --notify-graph aborte inmediatamente si no hay correos con ';'."""
    args = argparse.Namespace(notify_graph=True, notify_outlook=False, emails="")

    with patch("cli.commands.get_graph_credentials", return_value={"recipient_emails": []}):
        with pytest.raises(SystemExit) as exc:
            _resolve_notifiers(args, [])
        assert exc.value.code == 1


def test_resolve_notifiers_success_with_command_emails() -> None:
    """Verifica que los correos pasados por argumento --emails resuelvan correctamente."""
    args = argparse.Namespace(notify_graph=True, notify_outlook=False, emails="a@empresa.com;b@empresa.com")

    fake_config = {
        "tenant_id": "tenant-123",
        "client_id": "client-123",
        "client_secret": "secret-123",
        "sender_email": "bot@empresa.com",
    }
    with patch("cli.commands.get_graph_credentials", return_value=fake_config), patch(
        "infrastructure.notifiers.graph_notifier.get_graph_credentials", return_value=fake_config
    ):
        notifiers = _resolve_notifiers(args, ["a@empresa.com", "b@empresa.com"])
        assert len(notifiers) == 1


def test_handle_auth_verify_runs_cleanly() -> None:
    """Verifica que la salida de verify con Rich se renderice sin errores."""
    args = argparse.Namespace(auth_action="verify")
    with patch("cli.commands.has_portal_credentials", return_value=True), patch(
        "cli.commands.get_portal_credentials", return_value=("usr", "pwd")
    ):
        handle_auth(args)


def test_handle_status_runs_cleanly() -> None:
    """Verifica que el reporte status con Rich se ejecute sin excepciones."""
    with patch("core.database.BotDatabase.get_summary_stats", return_value={"SUCCESS": 2, "TOTAL": 2}):
        handle_status()
