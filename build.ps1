# build.ps1 - Automated PyInstaller compilation script for RPA Bots
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Iniciando compilacion de ejecutable RPA Bot        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Definir nombres y rutas
$AppName = "rpa-bot"
$DistPath = "dist\$AppName"

# 2. Compilar con PyInstaller en modalidad --onedir
Write-Host "Paso 1: Ejecutando PyInstaller (--onedir)..." -ForegroundColor Yellow

pyinstaller --noconfirm --onedir --console `
    --name "$AppName" `
    --add-data "config;config" `
    --add-data "core;core" `
    --add-data "infrastructure;infrastructure" `
    --add-data "pages;pages" `
    --add-data "services;services" `
    --add-data "cli;cli" `
    --hidden-import "keyring.backends.Windows" `
    --hidden-import "playwright" `
    --hidden-import "playwright.sync_api" `
    --hidden-import "sqlite3" `
    --hidden-import "requests" `
    --hidden-import "rich" `
    main.py

# 3. Informar sobre operacion con navegadores nativos locales
Write-Host "Paso 2: Operacion configurada con navegadores nativos del sistema (Google Chrome / Microsoft Edge)." -ForegroundColor Yellow

# 4. Crear estructura de carpetas operativas junto al binario
Write-Host "Paso 3: Creando carpetas de operacion en distribucion..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$DistPath\downloads" | Out-Null
New-Item -ItemType Directory -Force -Path "$DistPath\logs" | Out-Null

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "[OK] Compilacion finalizada exitosamente en: $DistPath" -ForegroundColor Green
Write-Host "Ejecutable listo: $DistPath\$AppName.exe" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
