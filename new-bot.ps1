<#
.SYNOPSIS
    Genera un nuevo proyecto de Bot RPA a partir de esta plantilla.

.PARAMETER Name
    Nombre del nuevo bot (ejemplo: bot-sunat-retenciones).

.PARAMETER Destination
    Ruta destino donde se creara el proyecto.
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [Parameter(Mandatory=$true)]
    [string]$Destination
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Generador de Proyectos RPA (Scaffolding)            " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Nombre del Bot : $Name" -ForegroundColor Yellow
Write-Host "Destino        : $Destination" -ForegroundColor Yellow

if (Test-Path $Destination) {
    Write-Error "La carpeta destino '$Destination' ya existe. Elija una ruta inexistente o limpiela antes."
    exit 1
}

$TemplateDir = $PSScriptRoot

# 1. Copiar archivos excluyendo basura, .venv y .git
Write-Host "`nPaso 1: Copiando estructura base..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $Destination -Force | Out-Null

$ExcludeItems = @(".git", ".venv", "dist", "build", "__pycache__", ".pytest_cache", ".ruff_cache", "browsers", "user_data", "bot_memory.db", ".trash", "*.spec")

Get-ChildItem -Path $TemplateDir -Force | Where-Object {
    $item = $_
    $skip = $false
    foreach ($ex in $ExcludeItems) {
        if ($item.Name -eq $ex) { $skip = $true; break }
    }
    -not $skip
} | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $Destination -Recurse -Force
}

# 2. Personalizar nombres en build.ps1, cli/commands.py y config/settings.py (DPAPI isolation)
Write-Host "Paso 2: Personalizando configuraciones y aislamiento DPAPI con el nombre '$Name'..." -ForegroundColor Yellow

$buildFile = Join-Path $Destination "build.ps1"
if (Test-Path $buildFile) {
    (Get-Content $buildFile) -replace '\$AppName = "rpa-bot"', "`$AppName = `"$Name`"" | Set-Content $buildFile
}

$commandsFile = Join-Path $Destination "cli\commands.py"
if (Test-Path $commandsFile) {
    (Get-Content $commandsFile) -replace 'prog="rpa-bot"', "prog=`"$Name`"" | Set-Content $commandsFile
}

$settingsFile = Join-Path $Destination "config\settings.py"
if (Test-Path $settingsFile) {
    $CleanPrefix = ($Name -replace '[^a-zA-Z0-9]', '_').ToUpper()
    (Get-Content $settingsFile) -replace 'CRED_SERVICE_PORTAL: str = "RPA_', "CRED_SERVICE_PORTAL: str = `"${CleanPrefix}_" `
                                -replace 'CRED_SERVICE_DB: str = "RPA_', "CRED_SERVICE_DB: str = `"${CleanPrefix}_" `
                                -replace 'CRED_SERVICE_GRAPH: str = "RPA_', "CRED_SERVICE_GRAPH: str = `"${CleanPrefix}_" `
                                -replace 'CRED_SERVICE_OUTLOOK: str = "RPA_', "CRED_SERVICE_OUTLOOK: str = `"${CleanPrefix}_" | Set-Content $settingsFile
}

# 3. Inicializar repositorio Git y rama inicial
Write-Host "Paso 3: Inicializando repositorio Git y rama de trabajo..." -ForegroundColor Yellow
Push-Location $Destination
try {
    git init | Out-Null
    git checkout -b "caracteristica/scaffold-inicial" | Out-Null
    git add .
    git commit -m "feat(scaffold): initial project structure from rpa-playwright-template" | Out-Null
} finally {
    Pop-Location
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "[OK] Proyecto '$Name' creado exitosamente!" -ForegroundColor Green
Write-Host "Ubicacion: $Destination" -ForegroundColor Green
Write-Host "`nPara comenzar a trabajar:" -ForegroundColor Cyan
Write-Host "  1. cd `"$Destination`"" -ForegroundColor White
Write-Host "  2. python -m venv .venv" -ForegroundColor White
Write-Host "  3. .\.venv\Scripts\activate" -ForegroundColor White
Write-Host "  4. pip install -r requirements.txt" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
