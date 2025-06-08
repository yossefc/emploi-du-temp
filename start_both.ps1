# Script PowerShell pour démarrer frontend et backend simultanément

Write-Host "🚀 Démarrage de l'application School Timetable Generator..." -ForegroundColor Green
Write-Host "📁 Répertoire: $PWD" -ForegroundColor Cyan

# Activer l'environnement virtuel si pas déjà fait
if (-not $env:VIRTUAL_ENV) {
    Write-Host "🐍 Activation de l'environnement virtuel Python..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Définir les variables d'environnement pour le développement
$env:DATABASE_URL = "sqlite:///./school_timetable.db"
$env:SECRET_KEY = "dev-secret-key-123"
$env:DEBUG = "true"
$env:USE_CLAUDE = "false"
$env:ANTHROPIC_API_KEY = "your-api-key"
$env:OPENAI_API_KEY = "your-api-key"

Write-Host "🌐 Variables d'environnement configurées" -ForegroundColor Green

# Fonction pour démarrer le backend
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "backend"
    
    # Activer l'environnement virtuel dans le job
    & "..\venv\Scripts\Activate.ps1"
    
    Write-Host "🔧 Démarrage du backend sur http://localhost:8000..." -ForegroundColor Blue
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Fonction pour démarrer le frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "frontend"
    
    Write-Host "⚛️ Démarrage du frontend sur http://localhost:3000..." -ForegroundColor Magenta
    npm start
}

Write-Host ""
Write-Host "🎯 Services en cours de démarrage..." -ForegroundColor Yellow
Write-Host "📊 Backend API: http://localhost:8000" -ForegroundColor Blue
Write-Host "📖 Documentation API: http://localhost:8000/api/v1/docs" -ForegroundColor Blue
Write-Host "⚛️ Frontend: http://localhost:3000" -ForegroundColor Magenta
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arrêter les services" -ForegroundColor Red

# Attendre et afficher les outputs
try {
    while ($true) {
        # Vérifier si les jobs sont encore en cours
        $backendRunning = $backendJob.State -eq "Running"
        $frontendRunning = $frontendJob.State -eq "Running"
        
        if (-not $backendRunning -and -not $frontendRunning) {
            Write-Host "❌ Les deux services se sont arrêtés" -ForegroundColor Red
            break
        }
        
        # Afficher les outputs des jobs
        Receive-Job -Job $backendJob
        Receive-Job -Job $frontendJob
        
        Start-Sleep -Seconds 2
    }
}
catch {
    Write-Host "⏹️ Arrêt des services..." -ForegroundColor Yellow
}
finally {
    # Nettoyer les jobs
    Stop-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host "✅ Services arrêtés" -ForegroundColor Green
}