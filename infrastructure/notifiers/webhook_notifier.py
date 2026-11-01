"""Webhook notification dispatcher (Teams / Slack / Generic HTTP)."""

from pathlib import Path

import requests

from config.logger_config import get_logger
from config.security import get_notifier_credentials
from infrastructure.notifiers.base_notifier import BaseNotifier

logger = get_logger()


class WebhookNotifier(BaseNotifier):
    """Dispatches JSON alert messages to an Incoming Webhook endpoint."""

    def __init__(self, webhook_url: str | None = None) -> None:
        """Initializes WebhookNotifier from argument or DPAPI configuration."""
        if webhook_url:
            self.webhook_url = webhook_url
        else:
            config = get_notifier_credentials()
            if not config or "webhook_url" not in config:
                raise ValueError("Webhook URL not found in configuration or DPAPI.")
            self.webhook_url = config["webhook_url"]

    def send_notification(
        self,
        subject: str,
        body_html: str,
        attachments: list[Path] | None = None,
    ) -> bool:
        """Sends an adaptive card / markdown payload to the configured webhook."""
        try:
            # Simple standard adaptive card / text payload
            payload = {
                "title": subject,
                "text": body_html,
            }
            response = requests.post(self.webhook_url, json=payload, timeout=15)
            response.raise_for_status()
            logger.info("Notification delivered successfully via Webhook.")
            return True
        except Exception as e:
            logger.error("Failed to send webhook notification: %s", e)
            return False
