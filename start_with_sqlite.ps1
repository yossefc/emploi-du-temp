#!/usr/bin/env pwsh
# Script de démarrage pour l'application avec SQLite

Write-Host "🚀 Démarrage de l'application Générateur d'Emplois du Temps" -ForegroundColor Green
Write-Host "📅 Configuration SQLite (développement)" -ForegroundColor Cyan

# Configuration des variables d'environnement
$env:DATABASE_URL = "sqlite:///./school_timetable.db"
$env:DEBUG = "true"

Write-Host "📊 Configuration:" -ForegroundColor Yellow
Write-Host "   Database: SQLite (school_timetable.db)" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor White

# Vérifier les dépendances
Write-Host "🔍 Vérification des dépendances..." -ForegroundColor Yellow

if (-not (Test-Path "backend/school_timetable.db")) {
    Write-Host "⚠️  Base de données non trouvée, création en cours..." -ForegroundColor Yellow
}

if (-not (Test-Path "backend/venv")) {
    Write-Host "❌ Environment virtuel Python non trouvé dans backend/venv" -ForegroundColor Red
    Write-Host "   Exécutez: cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor White
    exit 1
}

if (-not (Test-Path "frontend/node_modules")) {
    Write-Host "❌ Modules Node.js non trouvés dans frontend/node_modules" -ForegroundColor Red
    Write-Host "   Exécutez: cd frontend && npm install" -ForegroundColor White
    exit 1
}

# Tester la base de données
Write-Host "🗄️  Test de la base de données..." -ForegroundColor Yellow
try {
    cd backend
    $env:DATABASE_URL = "sqlite:///./school_timetable.db"
    $result = python -c "from app.db.base import engine; from sqlalchemy import inspect; inspector = inspect(engine); print('OK')" 2>$null
    if ($result -eq "OK") {
        Write-Host "✅ Base de données SQLite opérationnelle" -ForegroundColor Green
    }
    cd ..
} catch {
    Write-Host "❌ Problème avec la base de données" -ForegroundColor Red
}

# Créer utilisateur de test si nécessaire
Write-Host "👤 Vérification utilisateur de test..." -ForegroundColor Yellow
cd backend
python create_simple_user.py
cd ..

Write-Host "`n🚀 Démarrage des services..." -ForegroundColor Green

# Démarrer le backend en arrière-plan
Write-Host "🔧 Démarrage du backend..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    param($projectPath)
    Set-Location "$projectPath\backend"
    $env:DATABASE_URL = "sqlite:///./school_timetable.db"
    $env:DEBUG = "true"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} -ArgumentList (Get-Location)

Start-Sleep -Seconds 3

# Démarrer le frontend
Write-Host "🎨 Démarrage du frontend..." -ForegroundColor Cyan
cd frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm start"
cd ..

Write-Host "`n✅ Application démarrée avec succès!" -ForegroundColor Green
Write-Host "📱 Accédez à l'application: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔐 Connexion de test:" -ForegroundColor Yellow
Write-Host "   Email: admin@example.com" -ForegroundColor White
Write-Host "   Mot de passe: password123" -ForegroundColor White

Write-Host "`n⚠️  Pour arrêter l'application:" -ForegroundColor Yellow
Write-Host "   - Fermez les fenêtres PowerShell ouvertes" -ForegroundColor White
Write-Host "   - Ou tapez Ctrl+C dans chaque terminal" -ForegroundColor White

# Attendre une entrée pour terminer
Write-Host "`nAppuyez sur Entrée pour arrêter les services..." -ForegroundColor Magenta
Read-Host

# Arrêter le backend
Write-Host "🛑 Arrêt des services..." -ForegroundColor Red
Stop-Job $backendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob -ErrorAction SilentlyContinue

Write-Host "✅ Services arrêtés" -ForegroundColor Green 