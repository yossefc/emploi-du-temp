Write-Host "Demarrage de l'application School Timetable Generator..."

# Creation du fichier .env pour le backend si necessaire
if (!(Test-Path "backend\.env")) {
    Write-Host "Creation du fichier .env pour SQLite..."
    "DATABASE_URL=sqlite:///./school_timetable.db" | Out-File -FilePath "backend\.env" -Encoding UTF8
    "SECRET_KEY=dev-secret-key-123" | Add-Content -Path "backend\.env" -Encoding UTF8
    "DEBUG=true" | Add-Content -Path "backend\.env" -Encoding UTF8
}

Write-Host "Configuration SQLite prete"
Write-Host ""
Write-Host "Services configures pour demarrer sur :"
Write-Host "Backend API: http://localhost:8000"
Write-Host "Documentation API: http://localhost:8000/api/v1/docs"
Write-Host "Frontend: http://localhost:3001"
Write-Host ""
Write-Host "Identifiants de test:"
Write-Host "Email: admin@example.com"
Write-Host "Mot de passe: password123"
Write-Host ""

# Demarrer le backend
Write-Host "Demarrage du backend..."
$backendPath = Join-Path $PWD "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Attendre un peu
Start-Sleep -Seconds 3

# Demarrer le frontend
Write-Host "Demarrage du frontend..."
$frontendPath = Join-Path $PWD "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; `$env:PORT='3001'; yarn start"

Write-Host ""
Write-Host "Services en cours de demarrage !"
Write-Host "Attendez quelques instants..."
Write-Host "Fermez les fenetres PowerShell pour arreter les services" 