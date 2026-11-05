"""Implementacion de la interfaz de linea de comandos (CLI) con formato profesional Rich."""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.logger_config import get_logger
from config.security import (
    get_graph_credentials,
    get_internal_app_credentials,
    get_outlook_recipients,
    get_portal_credentials,
    has_db_credentials,
    has_graph_credentials,
    has_internal_app_credentials,
    has_outlook_recipients,
    has_portal_credentials,
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
console = Console()


def handle_auth(args: argparse.Namespace) -> None:
    """Gestiona el menu o la verificacion de credenciales en Windows DPAPI."""
    action = args.auth_action or "menu"

    if action in ("setup", "menu"):
        prompt_credentials_menu()

    elif action == "verify":
        table = Table(title="Estado de Credenciales en Windows (DPAPI)", border_style="cyan")
        table.add_column("Servicio", style="bold white", width=22)
        table.add_column("Estado", width=14)
        table.add_column("Detalle Seguro", style="dim")

        # 1. App Web
        if has_portal_credentials():
            creds = get_portal_credentials()
            user = creds[0] if creds else "Configurado"
            table.add_row("App Web", "[bold green]CONFIGURADO[/]", f"Usuario: {user}")
        else:
            table.add_row("App Web", "[bold red]PENDIENTE[/]", "Requerido para navegacion")

        # 2. App Interna / ERP
        if has_internal_app_credentials():
            creds = get_internal_app_credentials()
            user = creds[0] if creds else "Configurado"
            table.add_row("App Interna / ERP", "[bold green]CONFIGURADO[/]", f"Usuario: {user}")
        else:
            table.add_row("App Interna / ERP", "[yellow]NO CONFIGURADO[/]", "Opcional")

        # 3. Base de Datos (Ocultando infraestructura sensible)
        if has_db_credentials():
            table.add_row("Base de Datos", "[bold green]CONFIGURADO[/]", "Parametros seguros en DPAPI")
        else:
            table.add_row("Base de Datos", "[yellow]NO CONFIGURADO[/]", "Opcional")

        # 4. Microsoft Graph
        if has_graph_credentials():
            g_conf = get_graph_credentials() or {}
            sender = g_conf.get("sender_email", "-")
            recipients_count = len(g_conf.get("recipient_emails", []))
            table.add_row("Microsoft Graph", "[bold green]CONFIGURADO[/]", f"Buzon: {sender} ({recipients_count} destinatarios)")
        else:
            table.add_row("Microsoft Graph", "[yellow]NO CONFIGURADO[/]", "Opcional")

        # 5. Microsoft Outlook Local
        if has_outlook_recipients():
            count = len(get_outlook_recipients())
            table.add_row("Outlook Local", "[bold green]CONFIGURADO[/]", f"{count} destinatarios predeterminados")
        else:
            table.add_row("Outlook Local", "[yellow]NO CONFIGURADO[/]", "Opcional")

        console.print(table)


def handle_status() -> None:
    """Muestra estadisticas de ejecucion de la base SQLite en una tabla Rich."""
    db = BotDatabase()
    stats = db.get_summary_stats()

    table = Table(title="Memoria de Ejecuciones del Bot (SQLite)", border_style="cyan")
    table.add_column("Estado de Ejecucion", style="bold white", width=25)
    table.add_column("Cantidad", justify="right", style="cyan", width=12)

    for status_name, count in stats.items():
        color = "green" if status_name == "SUCCESS" else "red" if status_name == "FAILED" else "yellow" if status_name == "SKIPPED" else "white"
        table.add_row(f"[{color}]{status_name}[/]", str(count))

    console.print(table)


def _resolve_notifiers(args: argparse.Namespace, cmd_emails: list[str]) -> list[BaseNotifier]:
    """Valida y resuelve los notificadores requeridos por el usuario."""
    notifiers: list[BaseNotifier] = []

    if args.notify_graph:
        graph_emails = cmd_emails or (get_graph_credentials() or {}).get("recipient_emails", [])
        if not graph_emails:
            console.print("[bold red]ERROR:[/] El flag [cyan]--notify-graph[/] requiere destinatarios separados por ';' (use [yellow]--emails[/] o configurelos en [yellow]auth[/]).")
            sys.exit(1)
        try:
            notifiers.append(GraphNotifier(recipients=graph_emails))
        except Exception as e:
            console.print(f"[bold red]ERROR:[/] No se pudo inicializar Microsoft Graph: {e}")
            sys.exit(1)

    if args.notify_outlook:
        outlook_emails = cmd_emails or get_outlook_recipients()
        if not outlook_emails:
            console.print("[bold red]ERROR:[/] El flag [cyan]--notify-outlook[/] requiere destinatarios separados por ';' (use [yellow]--emails[/] o configurelos en [yellow]auth[/]).")
            sys.exit(1)
        try:
            notifiers.append(OutlookNotifier(recipients=outlook_emails))
        except Exception as e:
            console.print(f"[bold red]ERROR:[/] No se pudo inicializar Microsoft Outlook Local: {e}")
            sys.exit(1)

    return notifiers


def handle_run(args: argparse.Namespace) -> None:
    """Ejecuta el flujo automatizado del bot validando credenciales y notificaciones."""
    if not has_portal_credentials():
        console.print(Panel("[bold red]ERROR: Credenciales No Configuradas[/]\nLas credenciales del portal web no existen en Windows DPAPI.\nEjecute: [cyan]python main.py auth[/] (Opcion 1)", border_style="red"))
        sys.exit(1)

    cmd_emails = [e.strip() for e in args.emails.split(";") if e.strip()] if args.emails else []
    notifiers = _resolve_notifiers(args, cmd_emails)

    item_ids = [item.strip() for item in args.items.split(",") if item.strip()] if args.items else ["DEMO-1001", "DEMO-1002"]
    task_items = [TaskItem(item_id=item_id) for item_id in item_ids]

    headless = args.headless
    browser_manager = BrowserManager(headless=headless)
    orchestrator = BotOrchestratorService(
        browser_manager=browser_manager,
        notifiers=notifiers,
        use_persistence=True,
    )

    console.print(f"[cyan]Iniciando procesamiento de {len(task_items)} items[/] (Modo Headless: [bold]{headless}[/])...")

    try:
        results = orchestrator.process_items(task_items, force_reprocess=args.force)
    except BrowserNotFoundError as e:
        console.print(Panel(f"[bold red]ERROR DE NAVEGADOR:[/] {e}", border_style="red"))
        for n in notifiers:
            n.send_notification(
                subject="[RPA Bot Error] Fallo al Iniciar Navegador",
                body_html=f"<p><strong>Ejecucion Abortada:</strong> {e}</p>",
            )
        sys.exit(1)

    # Tabla resumen de ejecucion con Rich
    summary_table = Table(title="Resumen de Ejecucion RPA", border_style="green")
    summary_table.add_column("Item ID", style="bold white", width=18)
    summary_table.add_column("Estado", width=12)
    summary_table.add_column("Tiempo", justify="right", width=10)
    summary_table.add_column("Detalle / Error", style="dim")

    for r in results:
        status_tag = "[bold green]OK[/]" if r.status.value == "SUCCESS" else "[bold yellow]SKIP[/]" if r.status.value == "SKIPPED" else "[bold red]ERR[/]"
        summary_table.add_row(r.item_id, status_tag, f"{r.duration_seconds:.1f}s", r.details or r.error_message or "-")

    console.print(summary_table)


def main() -> None:
    """Punto de entrada del procesador de argumentos CLI."""
    parser = argparse.ArgumentParser(
        prog="rpa-bot",
        description="CLI Estandar para Bots RPA con Playwright y Python",
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
        console.print(f"[bold green]OK:[/] Se eliminaron {count} registros de la memoria del bot.")
    elif args.command == "run":
        handle_run(args)
    else:
        parser.print_help()
