#!/usr/bin/env pwsh
# Script PowerShell pour démarrer le serveur backend correctement

Write-Host "🚀 Démarrage du serveur School Timetable Generator..." -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Blue

# Aller dans le répertoire backend
Set-Location "backend"

# Configuration de l'environnement
Write-Host "📝 Configuration de la base de données..." -ForegroundColor Yellow
$env:DATABASE_URL = "sqlite:///./school_timetable.db"

# Vérifier que Python est disponible
if (Get-Command py -ErrorAction SilentlyContinue) {
    Write-Host "✅ Python trouvé" -ForegroundColor Green
} else {
    Write-Host "❌ Python non trouvé! Installez Python 3.12+" -ForegroundColor Red
    exit 1
}

# Vérifier les fichiers
if (-not (Test-Path "app/main.py")) {
    Write-Host "❌ Fichier app/main.py non trouvé!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "school_timetable.db")) {
    Write-Host "⚠️  Base de données non trouvée, elle sera créée au démarrage" -ForegroundColor Yellow
}

Write-Host "🔧 Démarrage d'Uvicorn..." -ForegroundColor Blue
Write-Host "   Serveur: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "   Documentation: http://127.0.0.1:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host "   Health check: http://127.0.0.1:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arrêter le serveur" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Blue

# Démarrer le serveur
try {
    py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
} catch {
    Write-Host "❌ Erreur lors du démarrage: $_" -ForegroundColor Red
    exit 1
} 