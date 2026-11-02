"""Manejo de seguridad y credenciales mediante Windows Credential Manager (DPAPI)."""

import getpass
import json
from typing import Any
from urllib.parse import urlparse

import keyring

from config.settings import (
    ALLOWED_DOMAINS,
    CRED_SERVICE_DB,
    CRED_SERVICE_GRAPH,
    CRED_SERVICE_OUTLOOK,
    CRED_SERVICE_PORTAL,
    CRED_SERVICE_SIGE,
)


class SecurityValidationError(Exception):
    """Excepcion disparada cuando una URL o configuracion no cumple las politicas de seguridad."""


def validate_url(url: str, allowed_domains: list[str] | None = None) -> bool:
    """Valida que una URL utilice protocolo seguro HTTPS y pertenezca a la lista de dominios autorizados.

    Args:
        url: Cadena con la URL a verificar.
        allowed_domains: Lista opcional de dominios permitidos.

    Returns:
        bool: True si la URL es valida y permitida.

    Raises:
        SecurityValidationError: Si la URL no es HTTPS o su dominio no esta autorizado.
    """
    if not url:
        raise SecurityValidationError("La URL proporcionada no puede estar vacia.")

    check_url = url[5:] if url.lower().startswith("blob:") else url
    parsed = urlparse(check_url)

    if parsed.scheme.lower() != "https":
        raise SecurityValidationError(
            f"Protocolo inseguro detectado: '{parsed.scheme}'. Solo se permite HTTPS."
        )

    domains = allowed_domains or ALLOWED_DOMAINS
    hostname = (parsed.hostname or "").lower()

    if not hostname:
        raise SecurityValidationError("No se pudo extraer el dominio de la URL proporcionada.")

    is_allowed = any(
        hostname == domain or hostname.endswith(f".{domain}") for domain in domains
    )
    if not is_allowed:
        raise SecurityValidationError(
            f"El dominio '{hostname}' no pertenece a la lista blanca de destinos autorizados."
        )

    return True


# ============================================================================
# 1. Credenciales de App Web (Portal Objetivo)
# ============================================================================


def save_portal_credentials(username: str, password: str) -> None:
    """Guarda usuario y contrasena de la aplicacion web en Windows Credential Manager."""
    clean_user = username.strip()
    keyring.set_password(CRED_SERVICE_PORTAL, "_active_user", clean_user)
    keyring.set_password(CRED_SERVICE_PORTAL, clean_user, password)


def get_portal_credentials() -> tuple[str, str] | None:
    """Recupera las credenciales de la aplicacion web desde Windows Credential Manager."""
    username = keyring.get_password(CRED_SERVICE_PORTAL, "_active_user")
    if not username:
        return None
    password = keyring.get_password(CRED_SERVICE_PORTAL, username)
    return (username, password) if password else None


def has_portal_credentials() -> bool:
    """Determina si existen credenciales configuradas para el portal web."""
    creds = get_portal_credentials()
    return creds is not None and len(creds[0]) > 0 and len(creds[1]) > 0


# ============================================================================
# 2. Credenciales de App SIGE (Sistema Interno)
# ============================================================================


def save_sige_credentials(username: str, password: str) -> None:
    """Guarda usuario y contrasena de SIGE en Windows Credential Manager."""
    clean_user = username.strip()
    keyring.set_password(CRED_SERVICE_SIGE, "_active_user", clean_user)
    keyring.set_password(CRED_SERVICE_SIGE, clean_user, password)


def get_sige_credentials() -> tuple[str, str] | None:
    """Recupera credenciales de SIGE desde Windows Credential Manager."""
    username = keyring.get_password(CRED_SERVICE_SIGE, "_active_user")
    if not username:
        return None
    password = keyring.get_password(CRED_SERVICE_SIGE, username)
    return (username, password) if password else None


def has_sige_credentials() -> bool:
    """Determina si existen credenciales configuradas para SIGE."""
    creds = get_sige_credentials()
    return creds is not None and len(creds[0]) > 0 and len(creds[1]) > 0


# ============================================================================
# 3. Credenciales de Conexion a Base de Datos
# ============================================================================


def save_db_credentials(host: str, database: str, user: str, password: str) -> None:
    """Almacena la configuracion de conexion a base de datos en DPAPI."""
    payload = {
        "host": host.strip(),
        "database": database.strip(),
        "user": user.strip(),
        "password": password.strip(),
    }
    keyring.set_password(CRED_SERVICE_DB, "config", json.dumps(payload))


def get_db_credentials() -> dict[str, Any] | None:
    """Recupera la configuracion de base de datos desde Windows Credential Manager."""
    raw = keyring.get_password(CRED_SERVICE_DB, "config")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def has_db_credentials() -> bool:
    """Indica si existe una configuracion de base de datos almacenada."""
    data = get_db_credentials()
    return bool(data and data.get("host") and data.get("database"))


# ============================================================================
# 4. Credenciales de Microsoft Graph API
# ============================================================================


def save_graph_credentials(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    sender_email: str,
    recipient_emails: list[str],
) -> None:
    """Almacena credenciales de Azure AD y buzones de Graph en DPAPI."""
    payload = {
        "tenant_id": tenant_id.strip(),
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
        "sender_email": sender_email.strip(),
        "recipient_emails": [r.strip() for r in recipient_emails if r.strip()],
    }
    keyring.set_password(CRED_SERVICE_GRAPH, "config", json.dumps(payload))


def get_graph_credentials() -> dict[str, Any] | None:
    """Recupera credenciales de Microsoft Graph desde Windows Credential Manager."""
    raw = keyring.get_password(CRED_SERVICE_GRAPH, "config")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def has_graph_credentials() -> bool:
    """Verifica si existen credenciales completas de Microsoft Graph."""
    data = get_graph_credentials()
    if not data:
        return False
    required = ["tenant_id", "client_id", "client_secret", "sender_email", "recipient_emails"]
    return all(data.get(k) for k in required) and len(data.get("recipient_emails", [])) > 0


# ============================================================================
# 5. Destinatarios de Microsoft Outlook Local
# ============================================================================


def save_outlook_recipients(recipients: list[str]) -> None:
    """Almacena la lista de destinatarios predeterminados para Outlook en DPAPI."""
    payload = {"recipient_emails": [r.strip() for r in recipients if r.strip()]}
    keyring.set_password(CRED_SERVICE_OUTLOOK, "config", json.dumps(payload))


def get_outlook_recipients() -> list[str]:
    """Recupera los destinatarios de Outlook configurados en DPAPI."""
    raw = keyring.get_password(CRED_SERVICE_OUTLOOK, "config")
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data.get("recipient_emails", []) if isinstance(data, dict) else []
    except Exception:
        return []


def has_outlook_recipients() -> bool:
    """Determina si hay destinatarios configurados para Microsoft Outlook."""
    return len(get_outlook_recipients()) > 0


# ============================================================================
# Menu Interactivo de Configuracion
# ============================================================================


def prompt_credentials_menu() -> None:
    """Despliega un menu interactivo en consola para seleccionar que credencial configurar."""
    while True:
        print("\n========================================================")
        print("    MENU DE GESTION DE CREDENCIALES EN WINDOWS (DPAPI)   ")
        print("========================================================")
        print(" 1. Configurar Credenciales App Web (Portal Objetivo)")
        print(" 2. Configurar Credenciales App SIGE (Sistema Interno)")
        print(" 3. Configurar Conexion de Base de Datos")
        print(" 4. Configurar Microsoft Graph API (Correos con ';')")
        print(" 5. Configurar Destinatarios Microsoft Outlook Local")
        print(" 6. Salir")
        print("========================================================")

        opcion = input("Seleccione una opcion (1-6): ").strip()

        if opcion == "1":
            print("\n--- Configuracion de App Web ---")
            user = input("Usuario / Correo: ").strip()
            pwd = getpass.getpass("Contrasena: ").strip()
            if user and pwd:
                save_portal_credentials(user, pwd)
                print("[OK] Credenciales de App Web guardadas en Windows Credential Manager.")
            else:
                print("[AVISO] Usuario y contrasena no pueden estar vacios.")

        elif opcion == "2":
            print("\n--- Configuracion de App SIGE ---")
            user = input("Usuario SIGE: ").strip()
            pwd = getpass.getpass("Contrasena SIGE: ").strip()
            if user and pwd:
                save_sige_credentials(user, pwd)
                print("[OK] Credenciales de SIGE guardadas exitosamente.")
            else:
                print("[AVISO] Los campos no pueden estar vacios.")

        elif opcion == "3":
            print("\n--- Configuracion de Base de Datos ---")
            host = input("Servidor / Host: ").strip()
            database = input("Nombre de Base de Datos: ").strip()
            user = input("Usuario BD: ").strip()
            pwd = getpass.getpass("Contrasena BD: ").strip()
            if host and database and user:
                save_db_credentials(host, database, user, pwd)
                print("[OK] Parametros de base de datos guardados exitosamente.")
            else:
                print("[AVISO] Host, Base de Datos y Usuario son obligatorios.")

        elif opcion == "4":
            print("\n--- Configuracion de Microsoft Graph API ---")
            tenant_id = input("Azure AD Tenant ID: ").strip()
            client_id = input("Azure AD Client ID: ").strip()
            client_secret = getpass.getpass("Azure AD Client Secret: ").strip()
            sender_email = input("Buzon remitente: ").strip()
            recipients_raw = input("Destinatarios (separados exclusivamente por ';'): ").strip()
            recipients = [r.strip() for r in recipients_raw.split(";") if r.strip()]

            if tenant_id and client_id and client_secret and sender_email and recipients:
                save_graph_credentials(tenant_id, client_id, client_secret, sender_email, recipients)
                print("[OK] Credenciales de Microsoft Graph guardadas exitosamente.")
            else:
                print("[AVISO] Todos los campos y al menos un destinatario son obligatorios.")

        elif opcion == "5":
            print("\n--- Configuracion de Destinatarios Outlook Local ---")
            recipients_raw = input("Destinatarios (separados por ';'): ").strip()
            recipients = [r.strip() for r in recipients_raw.split(";") if r.strip()]
            if recipients:
                save_outlook_recipients(recipients)
                print("[OK] Destinatarios de Outlook guardados exitosamente.")
            else:
                print("[AVISO] Ingrese al menos un correo destinatario.")

        elif opcion == "6":
            print("Saliendo del menu de configuracion de credenciales.")
            break
        else:
            print("[ERROR] Opcion no valida. Elija un numero entre 1 y 6.")
