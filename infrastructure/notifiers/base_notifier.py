"""Abstract base notifier interface for RPA notifications."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseNotifier(ABC):
    """Abstract interface defining notification delivery capabilities."""

    @abstractmethod
    def send_notification(
        self,
        subject: str,
        body_html: str,
        attachments: list[Path] | None = None,
    ) -> bool:
        """Sends a notification with optional attachments.

        Args:
            subject: Notification title or email subject.
            body_html: Rich text HTML body of the message.
            attachments: Optional list of local file paths to attach.

        Returns:
            bool: True if delivered successfully, False otherwise.
        """
