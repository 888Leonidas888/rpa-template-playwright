"""Configuracion de la aplicacion y definicion de rutas en el sistema de archivos."""

import sys
from pathlib import Path

# Detecta si se ejecuta como binario compilado de PyInstaller o script de origen
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Carpetas operativas
LOGS_DIR: Path = BASE_DIR / "logs"
DOWNLOADS_DIR: Path = BASE_DIR / "downloads"
USER_DATA_DIR: Path = BASE_DIR / "user_data"

# Ruta de base de datos para persistencia e idempotencia opcional
DB_PATH: Path = BASE_DIR / "bot_memory.db"

# Asegurar existencia de directorios operacionales basicos
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Tiempos de espera (timeouts) en milisegundos
DEFAULT_TIMEOUT_MS: int = 30000
NAVIGATION_TIMEOUT_MS: int = 45000
PAGE_TIMEOUT_MS: int = 30000

# Reintentos de navegacion
MAX_RETRY_ATTEMPTS: int = 3
RETRY_DELAY_SECONDS: float = 2.0

# Nombres de Servicio en Windows Credential Manager (DPAPI)
CRED_SERVICE_PORTAL: str = "RPA_TARGET_PORTAL"
CRED_SERVICE_DB: str = "RPA_DATABASE"
CRED_SERVICE_GRAPH: str = "RPA_GRAPH"
CRED_SERVICE_OUTLOOK: str = "RPA_OUTLOOK"

# Dominios permitidos para navegacion segura (fail-fast ante redirecciones)
ALLOWED_DOMAINS: list[str] = [
    "example.com",
]
