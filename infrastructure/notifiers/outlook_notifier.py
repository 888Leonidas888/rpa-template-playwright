"""Despachador de notificaciones por correo utilizando el perfil local de Microsoft Outlook."""

from pathlib import Path

import win32com.client

from config.logger_config import get_logger
from config.security import get_outlook_recipients
from infrastructure.notifiers.base_notifier import BaseNotifier

logger = get_logger()


class OutlookNotifier(BaseNotifier):
    """Envia correos electronicos utilizando el motor COM de Microsoft Outlook local.

    No requiere que la aplicacion Microsoft Outlook este abierta visiblemente
    en el escritorio del usuario.
    """

    def __init__(self, recipients: list[str] | None = None) -> None:
        """Inicializa el notificador de Outlook.

        Args:
            recipients: Lista opcional de destinatarios. Si no se pasa,
                        se recupera de Windows Credential Manager.
        """
        if recipients:
            self.recipients = recipients
        else:
            saved_recipients = get_outlook_recipients()
            if not saved_recipients:
                raise ValueError(
                    "No se configuraron destinatarios para Outlook. "
                    "Configurelos con 'python main.py auth' o use el argumento --emails."
                )
            self.recipients = saved_recipients

    def send_notification(
        self,
        subject: str,
        body_html: str,
        attachments: list[Path] | None = None,
    ) -> bool:
        """Envia un correo electronico formateado en HTML mediante el cliente Outlook COM.

        Args:
            subject: Asunto del mensaje.
            body_html: Cuerpo del correo en formato HTML.
            attachments: Lista opcional de rutas a archivos adjuntos.

        Returns:
            bool: True si el envio fue exitoso, False en caso de error.
        """
        try:
            # Dispatch inicia Outlook en segundo plano si no esta en ejecucion
            outlook_app = win32com.client.Dispatch("Outlook.Application")
            mail = outlook_app.CreateItem(0)  # 0 = olMailItem

            mail.Subject = subject
            mail.HTMLBody = body_html
            mail.To = ";".join(self.recipients)

            if attachments:
                for attachment_path in attachments:
                    if attachment_path.exists():
                        mail.Attachments.Add(str(attachment_path.resolve()))

            mail.Send()
            logger.info("Notificacion enviada exitosamente mediante Microsoft Outlook local.")
            return True
        except Exception as e:
            logger.error("Error al enviar notificacion mediante Outlook COM: %s", e)
            return False
