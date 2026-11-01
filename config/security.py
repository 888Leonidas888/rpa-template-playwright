"""Security and credentials management via Windows Credential Manager (DPAPI)."""

import getpass
import json
from typing import Any
from urllib.parse import urlparse

import keyring

from config.settings import (
    ALLOWED_DOMAINS,
    CRED_SERVICE_NOTIFIER,
    CRED_SERVICE_PORTAL,
)


class SecurityValidationError(Exception):
    """Raised when a security policy or URL validation check fails."""



def validate_url(url: str, allowed_domains: list[str] | None = None) -> bool:
    """Validates that a URL uses HTTPS and matches an authorized domain.

    Args:
        url: The URL string to validate.
        allowed_domains: List of allowed hostnames/domains.

    Returns:
        bool: True if URL is secure and permitted.

    Raises:
        SecurityValidationError: If scheme is not HTTPS or domain is not authorized.
    """
    if not url:
        raise SecurityValidationError("The provided URL cannot be empty.")

    check_url = url
    if check_url.lower().startswith("blob:"):
        check_url = check_url[5:]

    parsed = urlparse(check_url)
    if parsed.scheme.lower() != "https":
        raise SecurityValidationError(
            f"Insecure protocol detected: '{parsed.scheme}'. Only HTTPS is permitted."
        )

    domains = allowed_domains or ALLOWED_DOMAINS
    hostname = (parsed.hostname or "").lower()

    if not hostname:
        raise SecurityValidationError("Could not determine hostname from URL.")

    is_allowed = any(
        hostname == domain or hostname.endswith(f".{domain}") for domain in domains
    )
    if not is_allowed:
        raise SecurityValidationError(
            f"Domain '{hostname}' is not in the authorized domains whitelist."
        )

    return True


# ============================================================================
# Target Portal Credentials (DPAPI)
# ============================================================================


def save_portal_credentials(username: str, password: str) -> None:
    """Saves portal username and password into Windows Credential Manager.

    Args:
        username: Username or email.
        password: Plaintext password (encrypted at rest by Windows DPAPI).
    """
    clean_user = username.strip()
    keyring.set_password(CRED_SERVICE_PORTAL, "_active_user", clean_user)
    keyring.set_password(CRED_SERVICE_PORTAL, clean_user, password)


def get_portal_credentials() -> tuple[str, str] | None:
    """Retrieves target portal credentials from Windows Credential Manager.

    Returns:
        Optional[tuple[str, str]]: (username, password) or None if not configured.
    """
    username = keyring.get_password(CRED_SERVICE_PORTAL, "_active_user")
    if not username:
        return None
    password = keyring.get_password(CRED_SERVICE_PORTAL, username)
    if not password:
        return None
    return username, password


def has_portal_credentials() -> bool:
    """Checks whether valid portal credentials exist in DPAPI."""
    creds = get_portal_credentials()
    return creds is not None and len(creds[0]) > 0 and len(creds[1]) > 0


def clear_portal_credentials() -> bool:
    """Removes stored portal credentials from Windows Credential Manager."""
    username = keyring.get_password(CRED_SERVICE_PORTAL, "_active_user")
    if username:
        try:
            keyring.delete_password(CRED_SERVICE_PORTAL, username)
        except Exception:
            pass
    try:
        keyring.delete_password(CRED_SERVICE_PORTAL, "_active_user")
        return True
    except Exception:
        return False


def prompt_and_save_portal_credentials() -> tuple[str, str]:
    """Interactively prompts the user in console for portal credentials."""
    print("\n--- Configure Target Portal Credentials (DPAPI) ---")
    username = input("Username / Email: ").strip()
    password = getpass.getpass("Password: ").strip()

    if not username or not password:
        raise ValueError("Username and password cannot be empty.")

    save_portal_credentials(username, password)
    print("Portal credentials stored securely in Windows Credential Manager.")
    return username, password


# ============================================================================
# Notification Service Credentials (DPAPI)
# ============================================================================


def save_notifier_credentials(payload: dict[str, Any]) -> None:
    """Saves notification configuration into Windows Credential Manager."""
    keyring.set_password(CRED_SERVICE_NOTIFIER, "config", json.dumps(payload))


def get_notifier_credentials() -> dict[str, Any] | None:
    """Retrieves notification configuration from Windows Credential Manager."""
    raw = keyring.get_password(CRED_SERVICE_NOTIFIER, "config")
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def has_notifier_credentials() -> bool:
    """Checks whether notification configuration is present."""
    data = get_notifier_credentials()
    return bool(data)


def clear_notifier_credentials() -> bool:
    """Deletes notification configuration from Windows Credential Manager."""
    try:
        keyring.delete_password(CRED_SERVICE_NOTIFIER, "config")
        return True
    except Exception:
        return False


def prompt_and_save_notifier_credentials() -> dict[str, Any]:
    """Interactively prompts for notification credentials."""
    print("\n--- Configure Notification Service (DPAPI) ---")
    provider = input("Provider (graph / webhook / smtp) [graph]: ").strip().lower() or "graph"

    if provider == "graph":
        tenant_id = input("Azure AD Tenant ID: ").strip()
        client_id = input("Azure AD Client ID: ").strip()
        client_secret = getpass.getpass("Azure AD Client Secret: ").strip()
        sender_email = input("Sender mailbox email: ").strip()
        recipients_raw = input("Recipient emails (comma separated): ").strip()
        recipients = [r.strip() for r in recipients_raw.replace(";", ",").split(",") if r.strip()]

        payload = {
            "provider": "graph",
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "sender_email": sender_email,
            "recipient_emails": recipients,
        }
    elif provider == "webhook":
        webhook_url = input("Incoming Webhook URL: ").strip()
        payload = {
            "provider": "webhook",
            "webhook_url": webhook_url,
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    save_notifier_credentials(payload)
    print("Notification credentials stored securely in Windows Credential Manager.")
    return payload
