# Script PowerShell pour demarrer frontend et backend

Write-Host "Demarrage de l'application School Timetable Generator..." -ForegroundColor Green
Write-Host "Repertoire: $PWD" -ForegroundColor Cyan

# Activer l'environnement virtuel si pas deja fait
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activation de l'environnement virtuel Python..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Definir les variables d'environnement pour le developpement
$env:DATABASE_URL = "sqlite:///./school_timetable.db"
$env:SECRET_KEY = "dev-secret-key-123"
$env:DEBUG = "true"
$env:USE_CLAUDE = "false"
$env:ANTHROPIC_API_KEY = "your-api-key"
$env:OPENAI_API_KEY = "your-api-key"

Write-Host "Variables d'environnement configurees" -ForegroundColor Green

# Demarrer le backend dans une nouvelle fenetre
Write-Host "Demarrage du backend sur http://localhost:8000..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Attendre un peu pour que le backend demarre
Start-Sleep -Seconds 3

# Demarrer le frontend dans une nouvelle fenetre
Write-Host "Demarrage du frontend sur http://localhost:3000..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm start"

Write-Host ""
Write-Host "Services en cours de demarrage..." -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Blue
Write-Host "Documentation API: http://localhost:8000/api/v1/docs" -ForegroundColor Blue
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Magenta
Write-Host ""
Write-Host "Fermez les fenetres PowerShell pour arreter les services" -ForegroundColor Red 