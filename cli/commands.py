"""Command Line Interface (CLI) implementation for the RPA Bot."""

import argparse
import os
import subprocess
import sys

from config.logger_config import get_logger
from config.security import (
    clear_portal_credentials,
    get_notifier_credentials,
    get_portal_credentials,
    has_notifier_credentials,
    has_portal_credentials,
    prompt_and_save_notifier_credentials,
    prompt_and_save_portal_credentials,
)
from config.settings import BROWSERS_DIR
from core.database import BotDatabase
from core.models import TaskItem
from infrastructure.browser_manager import BrowserManager
from infrastructure.notifiers.base_notifier import BaseNotifier
from infrastructure.notifiers.graph_notifier import GraphNotifier
from infrastructure.notifiers.webhook_notifier import WebhookNotifier
from services.bot_service import BotOrchestratorService

logger = get_logger()


def handle_auth(args: argparse.Namespace) -> None:
    """Manages DPAPI stored credentials."""
    action = args.auth_action

    if action == "setup":
        prompt_and_save_portal_credentials()
        print("\nDo you want to configure notification credentials? (y/n)")
        resp = input("> ").strip().lower()
        if resp in ("y", "yes", "s", "si"):
            prompt_and_save_notifier_credentials()

    elif action == "verify":
        print("======================================================")
        print("          WINDOWS DPAPI CREDENTIAL STATUS            ")
        print("======================================================")
        if has_portal_credentials():
            creds = get_portal_credentials()
            user = creds[0] if creds else "Unknown"
            print(f"[OK] Target Portal: CONFIGURED (User: {user})")
        else:
            print("[MISSING] Target Portal: NOT CONFIGURED (Run: python main.py auth setup)")

        if has_notifier_credentials():
            data = get_notifier_credentials()
            prov = data.get("provider", "unknown") if data else "unknown"
            print(f"[OK] Notification Service: CONFIGURED (Provider: {prov})")
        else:
            print("[INFO] Notification Service: NOT CONFIGURED (Optional)")

    elif action == "clear":
        clear_portal_credentials()
        print("[OK] Target Portal credentials removed from Windows Credential Manager.")


def handle_install_browser() -> None:
    """Installs Chromium directly into the portable browsers/ directory."""
    print(f"Installing portable Chromium in: {BROWSERS_DIR}...")
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(BROWSERS_DIR)

    cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
    try:
        subprocess.run(cmd, env=env, check=True)
        print("[OK] Portable Chromium installed successfully in browsers/")
    except Exception as e:
        print(f"[ERROR] Failed to install portable browser: {e}")
        sys.exit(1)


def handle_status() -> None:
    """Prints SQLite execution statistics and audit summary."""
    db = BotDatabase()
    stats = db.get_summary_stats()
    print("======================================================")
    print("          RPA BOT EXECUTION MEMORY STATUS            ")
    print("======================================================")
    for status_name, count in stats.items():
        print(f" {status_name:15}: {count}")


def handle_run(args: argparse.Namespace) -> None:
    """Executes the bot processing flow."""
    # Check for credentials
    if not has_portal_credentials():
        logger.error("Missing portal credentials. Please run 'python main.py auth setup'.")
        print("[ERROR] Portal credentials not configured in Windows Credential Manager.")
        print("Run: python main.py auth setup")
        sys.exit(1)

    # Resolve notification adapter if requested
    notifier: BaseNotifier | None = None
    if args.notify:
        if not has_notifier_credentials():
            logger.error("Notification requested via --notify but no notifier credentials configured.")
            print("[ERROR] Flag --notify requires configured notification credentials.")
            print("Run: python main.py auth setup")
            sys.exit(1)
        conf = get_notifier_credentials() or {}
        if conf.get("provider") == "graph":
            notifier = GraphNotifier()
        elif conf.get("provider") == "webhook":
            notifier = WebhookNotifier()

    # Parse input items
    item_ids = [item.strip() for item in args.items.split(",") if item.strip()] if args.items else ["DEMO-1001", "DEMO-1002"]
    task_items = [TaskItem(item_id=item_id) for item_id in item_ids]

    headless = not args.no_headless
    browser_manager = BrowserManager(headless=headless)
    orchestrator = BotOrchestratorService(browser_manager=browser_manager, notifier=notifier)

    logger.info("Starting run for %d items (headless=%s)...", len(task_items), headless)
    results = orchestrator.process_items(task_items, force_reprocess=args.force)

    # Print summary table to console
    print("\n================== EXECUTION SUMMARY ==================")
    for r in results:
        status_symbol = "[OK]" if r.status.value in ("SUCCESS", "SKIPPED") else "[ERR]"
        print(f"{status_symbol} {r.item_id:15} | Status: {r.status.value:8} | Time: {r.duration_seconds:4.1f}s | {r.details or r.error_message}")
    print("=======================================================\n")


def main() -> None:
    """CLI Argument Parser entrypoint."""
    parser = argparse.ArgumentParser(
        prog="rpa-bot",
        description="Standard STN RPA Playwright Bot CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. run command
    run_parser = subparsers.add_parser("run", help="Execute bot automated workflow")
    run_parser.add_argument("--items", type=str, help="Comma-separated IDs of items to process")
    run_parser.add_argument("--no-headless", action="store_true", help="Launch browser with visible window")
    run_parser.add_argument("--notify", action="store_true", help="Send alert upon completion")
    run_parser.add_argument("--force", action="store_true", help="Force re-processing of already completed items")

    # 2. auth command
    auth_parser = subparsers.add_parser("auth", help="Manage DPAPI credentials")
    auth_parser.add_argument(
        "auth_action",
        choices=["setup", "verify", "clear"],
        help="Action to perform: setup, verify, or clear",
    )

    # 3. status command
    subparsers.add_parser("status", help="Show SQLite database execution status")

    # 4. install-browser command
    subparsers.add_parser("install-browser", help="Download portable Chromium for distribution")

    # 5. clear-memory command
    subparsers.add_parser("clear-memory", help="Clear SQLite audit and memory database")

    args = parser.parse_args()

    if args.command == "auth":
        handle_auth(args)
    elif args.command == "install-browser":
        handle_install_browser()
    elif args.command == "status":
        handle_status()
    elif args.command == "clear-memory":
        db = BotDatabase()
        count = db.clear_memory()
        print(f"[OK] Cleared {count} records from bot memory database.")
    elif args.command == "run":
        handle_run(args)
    else:
        parser.print_help()
