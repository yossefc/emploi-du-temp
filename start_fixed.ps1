#!/usr/bin/env powershell
"""
Script de démarrage corrigé pour l'application School Timetable Generator
"""

Write-Host "🚀 Démarrage de l'application School Timetable Generator (Version corrigée)..."
Write-Host "📁 Répertoire: $PWD"

# Vérifier et créer le fichier .env pour le backend
if (!(Test-Path "backend\.env")) {
    Write-Host "🔧 Création du fichier .env pour SQLite..."
    @"
DATABASE_URL=sqlite:///./school_timetable.db
SECRET_KEY=dev-secret-key-123
DEBUG=true
"@ | Out-File -FilePath "backend\.env" -Encoding UTF8
}

Write-Host "🔧 Variables d'environnement configurées"
Write-Host "📊 Base de données: SQLite (développement)"

# Fonction pour démarrer le frontend avec Yarn
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
Write-Host "📧 Identifiants de test:"
Write-Host "Email: admin@example.com"
Write-Host "Mot de passe: password123"
Write-Host ""
Write-Host "Fermez les fenêtres PowerShell pour arrêter les services"

# Démarrer les services en parallèle
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$frontendScript}"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {$backendScript}"

Write-Host "✅ Services démarrés !" 