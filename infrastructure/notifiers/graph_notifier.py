"""Despachador de notificaciones por correo utilizando Microsoft Graph API (Azure AD)."""

import base64
from pathlib import Path

import requests

from config.logger_config import get_logger
from config.security import get_graph_credentials
from infrastructure.notifiers.base_notifier import BaseNotifier

logger = get_logger()


class GraphNotifier(BaseNotifier):
    """Envia correos electronicos corporativos mediante Microsoft Graph API."""

    def __init__(self, recipients: list[str] | None = None) -> None:
        """Inicializa el notificador recuperando las credenciales de Graph en DPAPI.

        Args:
            recipients: Lista opcional de correos destinatarios. Si se omite,
                        se utilizan los guardados en la configuracion DPAPI.
        """
        config = get_graph_credentials()
        if not config:
            raise ValueError(
                "Credenciales de Microsoft Graph no configuradas en Windows Credential Manager. "
                "Ejecute 'python main.py auth' para configurarlas."
            )

        self.tenant_id: str = config["tenant_id"]
        self.client_id: str = config["client_id"]
        self.client_secret: str = config["client_secret"]
        self.sender_email: str = config["sender_email"]

        resolved_recipients = recipients or config.get("recipient_emails", [])
        if not resolved_recipients:
            raise ValueError(
                "No se especificaron destinatarios para Microsoft Graph. "
                "Proporcione correos separados por ';' mediante --emails o configúrelos en 'auth'."
            )
        self.recipient_emails: list[str] = resolved_recipients

    def _get_access_token(self) -> str:
        """Solicita un token OAuth2 client_credentials a Azure AD."""
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
            raise ValueError("Azure AD no retorno un token de acceso valido.")
        return str(token)

    def send_notification(
        self,
        subject: str,
        body_html: str,
        attachments: list[Path] | None = None,
    ) -> bool:
        """Envia un correo electronico HTML con adjuntos opcionales mediante Graph API.

        Args:
            subject: Asunto del mensaje.
            body_html: Contenido HTML del cuerpo del correo.
            attachments: Lista opcional de rutas a archivos adjuntos.

        Returns:
            bool: True si el envio fue confirmado por la API, False en caso contrario.
        """
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
            logger.info("Notificacion entregada exitosamente mediante Microsoft Graph API.")
            return True
        except Exception as e:
            logger.error("Fallo el envio de notificacion mediante Microsoft Graph: %s", e)
            return False
