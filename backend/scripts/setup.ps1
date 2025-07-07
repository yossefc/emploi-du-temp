# Script de configuration automatique pour School Timetable Generator
# Ce script lance setup.py avec Python

Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  SCHOOL TIMETABLE GENERATOR - CONFIGURATION" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

# Vérifier que Python est installé
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python non trouvé"
    }
    Write-Host "Python détecté: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Python n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host "Veuillez installer Python 3.11+ depuis https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour continuer..."
    exit 1
}

# Obtenir le répertoire du script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$setupScript = Join-Path $scriptDir "setup.py"

# Vérifier que le script setup.py existe
if (-not (Test-Path $setupScript)) {
    Write-Host "ERREUR: Script setup.py non trouvé dans $scriptDir" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour continuer..."
    exit 1
}

# Exécuter le script de configuration
Write-Host "Lancement du script de configuration..." -ForegroundColor Cyan
Write-Host ""

try {
    & python $setupScript
    if ($LASTEXITCODE -ne 0) {
        throw "Le script de configuration a échoué"
    }
    
    Write-Host ""
    Write-Host "Configuration terminée avec succès!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "ERREUR: La configuration a échoué" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour continuer..."
    exit 1
}

Read-Host "Appuyez sur Entrée pour continuer..." 