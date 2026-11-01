"""Microsoft Graph API email notification dispatcher."""

import base64
from pathlib import Path

import requests

from config.logger_config import get_logger
from config.security import get_notifier_credentials
from infrastructure.notifiers.base_notifier import BaseNotifier

logger = get_logger()


class GraphNotifier(BaseNotifier):
    """Dispatches corporate email notifications using Microsoft Graph API."""

    def __init__(self) -> None:
        """Initializes GraphNotifier loading DPAPI credentials."""
        config = get_notifier_credentials()
        if not config or config.get("provider") != "graph":
            raise ValueError(
                "Microsoft Graph credentials not found or invalid in Windows Credential Manager."
            )

        self.tenant_id: str = config["tenant_id"]
        self.client_id: str = config["client_id"]
        self.client_secret: str = config["client_secret"]
        self.sender_email: str = config["sender_email"]
        self.recipient_emails: list[str] = config.get("recipient_emails", [])

    def _get_access_token(self) -> str:
        """Requests an OAuth2 client_credentials token from Azure AD."""
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        response = requests.post(token_url, data=data, timeout=15)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ValueError("No access token returned by Azure AD.")
        return str(token)

    def send_notification(
        self,
        subject: str,
        body_html: str,
        attachments: list[Path] | None = None,
    ) -> bool:
        """Sends an HTML email with optional attachments via Microsoft Graph API."""
        try:
            token = self._get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            send_url = f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail"

            to_recipients = [
                {"emailAddress": {"address": email}} for email in self.recipient_emails
            ]

            message_payload: dict = {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_html},
                "toRecipients": to_recipients,
            }

            if attachments:
                attached_items = []
                for file_path in attachments:
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            content_bytes = base64.b64encode(f.read()).decode("utf-8")
                        attached_items.append(
                            {
                                "@odata.type": "#microsoft.graph.fileAttachment",
                                "name": file_path.name,
                                "contentBytes": content_bytes,
                            }
                        )
                if attached_items:
                    message_payload["attachments"] = attached_items

            response = requests.post(
                send_url,
                headers=headers,
                json={"message": message_payload, "saveToSentItems": True},
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Notification email delivered successfully via Microsoft Graph.")
            return True
        except Exception as e:
            logger.error("Failed to send notification via Microsoft Graph: %s", e)
            return False
