"""Orquestador del flujo de negocio para el Bot RPA."""

import time
from datetime import UTC, datetime
from pathlib import Path

from config.logger_config import get_logger
from config.security import get_portal_credentials
from config.settings import DOWNLOADS_DIR
from core.database import BotDatabase
from core.models import ExecutionResult, ExecutionStatus, TaskItem
from infrastructure.browser_manager import BrowserManager
from infrastructure.notifiers.base_notifier import BaseNotifier
from pages.sample_portal_page import SamplePortalPage

logger = get_logger()


class BotOrchestratorService:
    """Coordina el procesamiento por lotes con idempotencia, persistencia y notificaciones."""

    def __init__(
        self,
        db: BotDatabase | None = None,
        browser_manager: BrowserManager | None = None,
        notifiers: list[BaseNotifier] | BaseNotifier | None = None,
    ) -> None:
        """Inicializa el orquestador con sus dependencias."""
        self.db = db or BotDatabase()
        self.browser_manager = browser_manager or BrowserManager()
        if isinstance(notifiers, list):
            self.notifiers = notifiers
        elif notifiers is not None:
            self.notifiers = [notifiers]
        else:
            self.notifiers = []

    def process_items(
        self,
        items: list[TaskItem],
        force_reprocess: bool = False,
        downloads_dir: Path = DOWNLOADS_DIR,
    ) -> list[ExecutionResult]:
        """Procesa una lista de tareas respetando la regla de idempotencia.

        Args:
            items: Lista de elementos de trabajo a procesar.
            force_reprocess: Si es True, ignora el historial previo de SQLite.
            downloads_dir: Carpeta de destino para archivos generados.

        Returns:
            list[ExecutionResult]: Resultados de cada elemento procesado.
        """
        results: list[ExecutionResult] = []
        pending_items: list[TaskItem] = []

        # 1. Verificacion de Idempotencia: Filtrar items completados previamente
        for item in items:
            if not force_reprocess and self.db.is_already_completed(item.item_id):
                logger.info("Item '%s' completado previamente. Omitiendo.", item.item_id)
                res = ExecutionResult(
                    item_id=item.item_id,
                    status=ExecutionStatus.SKIPPED,
                    details="Item procesado en ejecucion previa.",
                )
                results.append(res)
            else:
                pending_items.append(item)

        if not pending_items:
            logger.info("No hay items pendientes para procesar. Todos estan completados.")
            return results

        # 2. Obtener credenciales desde Windows DPAPI
        credentials = get_portal_credentials()
        if not credentials:
            raise ValueError(
                "Credenciales del portal web no configuradas en Windows Credential Manager. "
                "Ejecute 'python main.py auth' primero."
            )
        _username, _password = credentials

        # 3. Iniciar navegador y procesar secuencialmente
        logger.info("Procesando %d items pendientes...", len(pending_items))
        with self.browser_manager as page:
            _portal = SamplePortalPage(page)

            for item in pending_items:
                start_time = time.time()
                try:
                    logger.info("Ejecutando tarea para item: %s", item.item_id)
                    duration = time.time() - start_time
                    result = ExecutionResult(
                        item_id=item.item_id,
                        status=ExecutionStatus.SUCCESS,
                        details="Item procesado exitosamente.",
                        duration_seconds=round(duration, 2),
                        processed_at=datetime.now(UTC),
                    )
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error("Fallo el procesamiento del item '%s': %s", item.item_id, e)
                    result = ExecutionResult(
                        item_id=item.item_id,
                        status=ExecutionStatus.FAILED,
                        error_message=str(e),
                        duration_seconds=round(duration, 2),
                        processed_at=datetime.now(UTC),
                    )

                self.db.save_record(result)
                results.append(result)

        # 4. Despacho opcional de notificaciones configuradas
        if self.notifiers:
            self._dispatch_summary_notification(results)

        return results

    def _dispatch_summary_notification(self, results: list[ExecutionResult]) -> None:
        """Construye un reporte HTML y dispara cada notificador registrado."""
        success_count = sum(1 for r in results if r.status == ExecutionStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == ExecutionStatus.FAILED)
        skipped_count = sum(1 for r in results if r.status == ExecutionStatus.SKIPPED)

        subject = f"[RPA Bot] Resumen de Ejecucion - {success_count} OK, {failed_count} ERR"

        rows = "".join(
            f"<tr><td>{r.item_id}</td><td>{r.status.value}</td><td>{r.duration_seconds}s</td><td>{r.error_message or r.details}</td></tr>"
            for r in results
        )

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Reporte de Ejecucion RPA Bot</h2>
            <p><strong>Total Items:</strong> {len(results)} |
               <span style="color: green;"><strong>Exitosos:</strong> {success_count}</span> |
               <span style="color: red;"><strong>Fallidos:</strong> {failed_count}</span> |
               <span style="color: gray;"><strong>Omitidos:</strong> {skipped_count}</span>
            </p>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <thead style="background-color: #f2f2f2;">
                    <tr><th>Item ID</th><th>Estado</th><th>Duracion</th><th>Detalles</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </body>
        </html>
        """
        for notifier in self.notifiers:
            notifier.send_notification(subject=subject, body_html=body_html)
