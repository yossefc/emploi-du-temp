#!/usr/bin/env powershell
"""
Script de démarrage FONCTIONNEL pour l'application School Timetable Generator
"""

Write-Host "Demarrage de l'application School Timetable Generator..."
Write-Host "Repertoire: $PWD"

# Vérifier et créer le fichier .env pour le backend
if (!(Test-Path "backend\.env")) {
    Write-Host "Creation du fichier .env pour SQLite..."
    @"
DATABASE_URL=sqlite:///./school_timetable.db
SECRET_KEY=dev-secret-key-123
DEBUG=true
"@ | Out-File -FilePath "backend\.env" -Encoding UTF8
}

Write-Host "Configuration SQLite prete"

# Fonction pour démarrer le frontend
$frontendScript = @"
Set-Location '$PWD\frontend'
Write-Host 'Demarrage du frontend sur http://localhost:3001...'
`$env:PORT = '3001'
yarn start
"@

# Fonction pour démarrer le backend  
$backendScript = @"
Set-Location '$PWD\backend'
Write-Host 'Demarrage du backend sur http://localhost:8000...'
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"@

Write-Host ""
Write-Host "Services configures pour demarrer sur :"
Write-Host "Backend API: http://localhost:8000"
Write-Host "Documentation API: http://localhost:8000/api/v1/docs" 
Write-Host "Frontend: http://localhost:3001 (port modifié pour éviter les conflits)"
Write-Host ""
Write-Host "📧 Identifiants de test:"
Write-Host "Email: admin@example.com"
Write-Host "Mot de passe: password123"
Write-Host ""

# Démarrer le backend en premier
Write-Host "Demarrage du backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# Attendre un peu avant de démarrer le frontend
Start-Sleep -Seconds 3

# Démarrer le frontend
Write-Host "Demarrage du frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript

Write-Host ""
Write-Host "Services en cours de demarrage !"
Write-Host "Attendez quelques instants que les services se lancent..."
Write-Host "Fermez les fenetres PowerShell pour arreter les services" 