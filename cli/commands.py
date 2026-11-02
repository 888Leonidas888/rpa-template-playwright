"""Implementacion de la interfaz de linea de comandos (CLI) para el Bot RPA."""

import argparse
import sys

from config.logger_config import get_logger
from config.security import (
    get_db_credentials,
    get_graph_credentials,
    get_outlook_recipients,
    get_portal_credentials,
    get_sige_credentials,
    has_db_credentials,
    has_graph_credentials,
    has_outlook_recipients,
    has_portal_credentials,
    has_sige_credentials,
    prompt_credentials_menu,
)
from core.database import BotDatabase
from core.models import TaskItem
from infrastructure.browser_manager import BrowserManager, BrowserNotFoundError
from infrastructure.notifiers.base_notifier import BaseNotifier
from infrastructure.notifiers.graph_notifier import GraphNotifier
from infrastructure.notifiers.outlook_notifier import OutlookNotifier
from services.bot_service import BotOrchestratorService

logger = get_logger()


def handle_auth(args: argparse.Namespace) -> None:
    """Gestiona el menu o verificacion de credenciales en Windows DPAPI."""
    action = args.auth_action or "menu"

    if action in ("setup", "menu"):
        prompt_credentials_menu()

    elif action == "verify":
        print("======================================================")
        print("          ESTADO DE CREDENCIALES EN WINDOWS (DPAPI)   ")
        print("======================================================")
        if has_portal_credentials():
            creds = get_portal_credentials()
            user = creds[0] if creds else "Desconocido"
            print(f"[OK] App Web: CONFIGURADO (Usuario: {user})")
        else:
            print("[PENDIENTE] App Web: NO CONFIGURADO")

        if has_sige_credentials():
            creds = get_sige_credentials()
            user = creds[0] if creds else "Desconocido"
            print(f"[OK] App SIGE: CONFIGURADO (Usuario: {user})")
        else:
            print("[INFO] App SIGE: NO CONFIGURADO (Opcional)")

        if has_db_credentials():
            db_conf = get_db_credentials() or {}
            host = db_conf.get("host", "<DB_SERVER>")
            db_name = db_conf.get("database", "<DB_NAME>")
            print(f"[OK] Base de Datos: CONFIGURADO (Host: {host}, BD: {db_name})")
        else:
            print("[INFO] Base de Datos: NO CONFIGURADO (Opcional)")

        if has_graph_credentials():
            g_conf = get_graph_credentials() or {}
            sender = g_conf.get("sender_email", "-")
            recipients = "; ".join(g_conf.get("recipient_emails", []))
            print(f"[OK] Microsoft Graph: CONFIGURADO (Remitente: {sender}, Destinatarios: {recipients})")
        else:
            print("[INFO] Microsoft Graph: NO CONFIGURADO (Opcional)")

        if has_outlook_recipients():
            recipients = "; ".join(get_outlook_recipients())
            print(f"[OK] Microsoft Outlook Local: CONFIGURADO (Destinatarios: {recipients})")
        else:
            print("[INFO] Microsoft Outlook Local: NO CONFIGURADO (Opcional)")


def handle_status() -> None:
    """Muestra estadisticas y estado de ejecuciones desde la base SQLite."""
    db = BotDatabase()
    stats = db.get_summary_stats()
    print("======================================================")
    print("          ESTADO DE MEMORIA DEL BOT (SQLITE)          ")
    print("======================================================")
    for status_name, count in stats.items():
        print(f" {status_name:15}: {count}")


def handle_run(args: argparse.Namespace) -> None:
    """Ejecuta el flujo automatizado del bot validando credenciales y notificaciones."""
    # 1. Validacion estricta de credenciales de portal
    if not has_portal_credentials():
        logger.error("Credenciales del portal web no configuradas. Ejecute 'python main.py auth'.")
        print("\n[ERROR] Las credenciales del portal no estan configuradas en Windows Credential Manager.")
        print("Ejecute: python main.py auth (Opcion 1)")
        sys.exit(1)

    # 2. Parseo de correos destinatarios si se pasaron por flag
    cmd_emails: list[str] = []
    if args.emails:
        cmd_emails = [e.strip() for e in args.emails.split(";") if e.strip()]

    # 3. Validacion y configuracion de notificaciones
    notifiers: list[BaseNotifier] = []

    if args.notify_graph:
        resolved_graph_emails = cmd_emails or (get_graph_credentials() or {}).get("recipient_emails", [])
        if not resolved_graph_emails:
            logger.error("El flag --notify-graph requiere destinatarios especificados con ';' mediante --emails o en 'auth'.")
            print("\n[ERROR] Flag --notify-graph: No se detectaron correos destinatarios.")
            print("Especifique los correos separados por ';' usando: --emails \"correo1@stn.com;correo2@stn.com\"")
            print("O configurelos interactivamente ejecutando: python main.py auth (Opcion 4)")
            sys.exit(1)

        try:
            notifiers.append(GraphNotifier(recipients=resolved_graph_emails))
        except Exception as e:
            logger.error("Error al inicializar Microsoft Graph Notifier: %s", e)
            print(f"\n[ERROR] No se pudo inicializar Microsoft Graph: {e}")
            sys.exit(1)

    if args.notify_outlook:
        resolved_outlook_emails = cmd_emails or get_outlook_recipients()
        if not resolved_outlook_emails:
            logger.error("El flag --notify-outlook requiere destinatarios especificados con ';' mediante --emails o en 'auth'.")
            print("\n[ERROR] Flag --notify-outlook: No se detectaron correos destinatarios.")
            print("Especifique los correos separados por ';' usando: --emails \"correo1@stn.com;correo2@stn.com\"")
            print("O configurelos interactivamente ejecutando: python main.py auth (Opcion 5)")
            sys.exit(1)

        try:
            notifiers.append(OutlookNotifier(recipients=resolved_outlook_emails))
        except Exception as e:
            logger.error("Error al inicializar Outlook Notifier: %s", e)
            print(f"\n[ERROR] No se pudo inicializar Microsoft Outlook Local: {e}")
            sys.exit(1)

    # 4. Parseo de elementos de trabajo
    item_ids = [item.strip() for item in args.items.split(",") if item.strip()] if args.items else ["DEMO-1001", "DEMO-1002"]
    task_items = [TaskItem(item_id=item_id) for item_id in item_ids]

    # 5. Iniciar orquestador
    headless = args.headless
    browser_manager = BrowserManager(headless=headless)
    orchestrator = BotOrchestratorService(browser_manager=browser_manager, notifiers=notifiers)

    logger.info("Iniciando ejecucion para %d items (headless=%s)...", len(task_items), headless)
    try:
        results = orchestrator.process_items(task_items, force_reprocess=args.force)
    except BrowserNotFoundError as e:
        logger.error("Fallo el arranque del navegador: %s", e)
        print(f"\n[ERROR] {e}")
        for notifier in notifiers:
            notifier.send_notification(
                subject="[RPA Bot Error] Fallo al Iniciar Navegador",
                body_html=f"<p><strong>Ejecucion Abortada:</strong> {e}</p>",
            )
        sys.exit(1)

    # 6. Imprimir resumen en consola
    print("\n================== RESUMEN DE EJECUCION ==================")
    for r in results:
        status_symbol = "[OK]" if r.status.value in ("SUCCESS", "SKIPPED") else "[ERR]"
        print(f"{status_symbol} {r.item_id:15} | Estado: {r.status.value:8} | Tiempo: {r.duration_seconds:4.1f}s | {r.details or r.error_message}")
    print("==========================================================\n")


def main() -> None:
    """Punto de entrada del procesador de argumentos CLI."""
    parser = argparse.ArgumentParser(
        prog="rpa-bot",
        description="CLI Estandar para Bots RPA con Playwright y Python (STN)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcomandos disponibles")

    # 1. run command
    run_parser = subparsers.add_parser("run", help="Ejecutar flujo automatizado del bot")
    run_parser.add_argument("--items", type=str, help="IDs separados por coma para procesar")
    run_parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Ejecutar navegador en segundo plano (por defecto: visible)",
    )
    run_parser.add_argument(
        "--notify-graph",
        action="store_true",
        default=False,
        help="Enviar reporte al finalizar mediante Microsoft Graph API",
    )
    run_parser.add_argument(
        "--notify-outlook",
        action="store_true",
        default=False,
        help="Enviar reporte al finalizar mediante Microsoft Outlook local",
    )
    run_parser.add_argument(
        "--emails",
        type=str,
        help="Correos destinatarios separados por ';' para las notificaciones",
    )
    run_parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar reprocesamiento de items ya completados en SQLite",
    )

    # 2. auth command
    auth_parser = subparsers.add_parser("auth", help="Gestionar credenciales en Windows DPAPI")
    auth_parser.add_argument(
        "auth_action",
        nargs="?",
        choices=["setup", "verify", "menu"],
        default="menu",
        help="Accion a ejecutar: menu (por defecto), setup o verify",
    )

    # 3. status command
    subparsers.add_parser("status", help="Mostrar estadisticas de ejecucion de la base SQLite")

    # 4. clear-memory command
    subparsers.add_parser("clear-memory", help="Limpiar la base de datos de memoria SQLite")

    args = parser.parse_args()

    if args.command == "auth":
        handle_auth(args)
    elif args.command == "status":
        handle_status()
    elif args.command == "clear-memory":
        db = BotDatabase()
        count = db.clear_memory()
        print(f"[OK] Se eliminaron {count} registros de la memoria del bot.")
    elif args.command == "run":
        handle_run(args)
    else:
        parser.print_help()
