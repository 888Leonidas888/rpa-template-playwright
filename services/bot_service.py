"""Business workflow orchestrator for the RPA bot."""

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
    """Coordinates batch processing of tasks with idempotency, database logging, and alerts."""

    def __init__(
        self,
        db: BotDatabase | None = None,
        browser_manager: BrowserManager | None = None,
        notifier: BaseNotifier | None = None,
    ) -> None:
        """Initializes the orchestrator with required dependencies."""
        self.db = db or BotDatabase()
        self.browser_manager = browser_manager or BrowserManager()
        self.notifier = notifier

    def process_items(
        self,
        items: list[TaskItem],
        force_reprocess: bool = False,
        downloads_dir: Path = DOWNLOADS_DIR,
    ) -> list[ExecutionResult]:
        """Processes a list of task items following the idempotent workflow.

        Args:
            items: Work items to execute.
            force_reprocess: If True, ignores previous SQLite completion status.
            downloads_dir: Destination folder for output files.

        Returns:
            list[ExecutionResult]: Outcomes for every processed item.
        """
        results: list[ExecutionResult] = []
        pending_items: list[TaskItem] = []

        # 1. Idempotency Check: Filter out already completed items
        for item in items:
            if not force_reprocess and self.db.is_already_completed(item.item_id):
                logger.info("Item '%s' was previously completed. Skipping.", item.item_id)
                res = ExecutionResult(
                    item_id=item.item_id,
                    status=ExecutionStatus.SKIPPED,
                    details="Item was already completed in previous run.",
                )
                results.append(res)
            else:
                pending_items.append(item)

        if not pending_items:
            logger.info("No pending items to process. All items are already completed.")
            return results

        # 2. Retrieve credentials safely from Windows DPAPI
        credentials = get_portal_credentials()
        if not credentials:
            raise ValueError(
                "Target portal credentials are not configured in Windows Credential Manager. "
                "Run 'python main.py auth setup' first."
            )
        username, password = credentials

        # 3. Launch browser and process items sequentially
        logger.info("Processing %d pending items...", len(pending_items))
        with self.browser_manager as page:
            _portal = SamplePortalPage(page)

            # Optional login step
            # _portal.login(username=username, password=password)

            for item in pending_items:
                start_time = time.time()
                try:
                    logger.info("Executing task for item: %s", item.item_id)
                    # Simulated or real page action:
                    # downloaded_file = portal.download_report_by_id(item.item_id, output_dir=downloads_dir)

                    # Mock output for template demonstration
                    duration = time.time() - start_time
                    result = ExecutionResult(
                        item_id=item.item_id,
                        status=ExecutionStatus.SUCCESS,
                        details="Successfully processed item.",
                        duration_seconds=round(duration, 2),
                        processed_at=datetime.now(UTC),
                    )
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error("Processing failed for item '%s': %s", item.item_id, e)
                    result = ExecutionResult(
                        item_id=item.item_id,
                        status=ExecutionStatus.FAILED,
                        error_message=str(e),
                        duration_seconds=round(duration, 2),
                        processed_at=datetime.now(UTC),
                    )

                # Persist outcome immediately in SQLite for traceability & recovery
                self.db.save_record(result)
                results.append(result)

        # 4. Optional Notification Dispatch
        if self.notifier:
            self._dispatch_summary_notification(results)

        return results

    def _dispatch_summary_notification(self, results: list[ExecutionResult]) -> None:
        """Constructs an HTML summary table and triggers the notifier."""
        success_count = sum(1 for r in results if r.status == ExecutionStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == ExecutionStatus.FAILED)
        skipped_count = sum(1 for r in results if r.status == ExecutionStatus.SKIPPED)

        subject = f"[RPA Bot] Execution Summary - {success_count} OK, {failed_count} ERR"

        rows = "".join(
            f"<tr><td>{r.item_id}</td><td>{r.status.value}</td><td>{r.duration_seconds}s</td><td>{r.error_message or r.details}</td></tr>"
            for r in results
        )

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>RPA Bot Execution Report</h2>
            <p><strong>Total Items:</strong> {len(results)} |
               <span style="color: green;"><strong>Success:</strong> {success_count}</span> |
               <span style="color: red;"><strong>Failed:</strong> {failed_count}</span> |
               <span style="color: gray;"><strong>Skipped:</strong> {skipped_count}</span>
            </p>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <thead style="background-color: #f2f2f2;">
                    <tr><th>Item ID</th><th>Status</th><th>Duration</th><th>Details</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </body>
        </html>
        """
        self.notifier.send_notification(subject=subject, body_html=body_html)
