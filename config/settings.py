"""Application configuration and filesystem path definitions."""

import sys
from pathlib import Path

# Detect if running as a compiled PyInstaller binary or source script
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Operational Directories
LOGS_DIR: Path = BASE_DIR / "logs"
DOWNLOADS_DIR: Path = BASE_DIR / "downloads"
BROWSERS_DIR: Path = BASE_DIR / "browsers"
USER_DATA_DIR: Path = BASE_DIR / "user_data"

# Database path for local state & idempotence
DB_PATH: Path = BASE_DIR / "bot_memory.db"

# Ensure essential runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Timeouts in milliseconds
DEFAULT_TIMEOUT_MS: int = 30000
NAVIGATION_TIMEOUT_MS: int = 45000
PAGE_TIMEOUT_MS: int = 30000

# Retries and navigation
MAX_RETRY_ATTEMPTS: int = 3
RETRY_DELAY_SECONDS: float = 2.0

# Windows Credential Manager (DPAPI) Service Names
CRED_SERVICE_PORTAL: str = "STN_RPA_TARGET_PORTAL"
CRED_SERVICE_NOTIFIER: str = "STN_RPA_NOTIFICATION_SERVICE"

# Allowed web domains for strict navigation validation (fail fast on malicious redirects)
ALLOWED_DOMAINS: list[str] = [
    "example.com",
]
