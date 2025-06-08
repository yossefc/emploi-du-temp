#!/usr/bin/env powershell
"""
Script de démarrage pour l'application School Timetable Generator avec Yarn
"""

Write-Host "🚀 Démarrage de l'application School Timetable Generator avec Yarn..."
Write-Host "📁 Répertoire: $PWD"

# Vérifier si yarn est installé
if (!(Get-Command yarn -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Yarn n'est pas installé. Installation..."
    npm install -g yarn
}

# Variables d'environnement pour le développement
$env:DATABASE_URL = "sqlite:///./school_timetable.db"
$env:SECRET_KEY = "dev-secret-key-123"
$env:DEBUG = "true"

Write-Host "🔧 Variables d'environnement configurées"
Write-Host "📊 Base de données: SQLite (développement)"

# Fonction pour démarrer le frontend
$frontendScript = {
    Set-Location "frontend"
    Write-Host "🎨 Démarrage du frontend avec Yarn sur http://localhost:3000..."
    yarn start
}

# Fonction pour démarrer le backend
$backendScript = {
    Set-Location "backend"
    Write-Host "⚡ Démarrage du backend sur http://localhost:8000..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

Write-Host ""
Write-Host "🌐 Services en cours de démarrage..."
Write-Host "Backend API: http://localhost:8000"
Write-Host "Documentation API: http://localhost:8000/api/v1/docs" 
Write-Host "Frontend: http://localhost:3000"
Write-Host ""
Write-Host "Fermez les fenêtres PowerShell pour arrêter les services"

# Démarrer les services en parallèle
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$frontendScript}"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$backendScript}"

Write-Host "✅ Services démarrés !" 