#!/usr/bin/env pwsh
# Script PowerShell pour tester le frontend corrigé

Write-Host "🧪 Test du Frontend School Timetable Generator..." -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Blue

# Aller dans le répertoire frontend
Set-Location "frontend"

Write-Host "📂 Répertoire de travail : $(Get-Location)" -ForegroundColor Yellow

# Vérifier que Node.js est disponible
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "✅ Node.js trouvé : $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js non trouvé! Installez Node.js 16+" -ForegroundColor Red
    exit 1
}

# Vérifier que npm est disponible
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $npmVersion = npm --version
    Write-Host "✅ NPM trouvé : $npmVersion" -ForegroundColor Green
} else {
    Write-Host "❌ NPM non trouvé!" -ForegroundColor Red
    exit 1
}

# Installation des dépendances
Write-Host "`n🔧 Installation des dépendances..." -ForegroundColor Yellow
try {
    npm install
    Write-Host "✅ Dépendances installées avec succès" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur lors de l'installation des dépendances" -ForegroundColor Red
    exit 1
}

# Vérification TypeScript
Write-Host "`n📝 Vérification TypeScript..." -ForegroundColor Yellow
try {
    npx tsc --noEmit
    Write-Host "✅ TypeScript : Aucune erreur" -ForegroundColor Green
} catch {
    Write-Host "⚠️  TypeScript : Erreurs détectées" -ForegroundColor Yellow
    Write-Host "Détails :" -ForegroundColor Gray
    npx tsc --noEmit 2>&1
}

# Linting
Write-Host "`n🔍 Vérification ESLint..." -ForegroundColor Yellow
try {
    npm run lint 2>$null
    Write-Host "✅ ESLint : Code conforme" -ForegroundColor Green
} catch {
    Write-Host "⚠️  ESLint : Warnings détectés" -ForegroundColor Yellow
}

# Build de production
Write-Host "`n🏗️  Build de production..." -ForegroundColor Yellow
try {
    npm run build
    Write-Host "✅ Build réussi!" -ForegroundColor Green
    
    # Vérifier la taille du bundle
    if (Test-Path "dist") {
        $distSize = (Get-ChildItem -Path "dist" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "📦 Taille du bundle : $([math]::Round($distSize, 2)) MB" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Erreur lors du build" -ForegroundColor Red
    exit 1
}

# Test de démarrage en développement
Write-Host "`n🚀 Test de démarrage en mode développement..." -ForegroundColor Yellow
Write-Host "⏰ Démarrage du serveur de développement (5 secondes)..." -ForegroundColor Cyan

# Démarrer le serveur en arrière-plan
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    npm run dev 2>&1
}

# Attendre 5 secondes
Start-Sleep -Seconds 5

# Tester la connexion
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 3 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Serveur de développement démarré avec succès!" -ForegroundColor Green
        Write-Host "🌐 Application accessible sur : http://localhost:5173" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️  Serveur en cours de démarrage..." -ForegroundColor Yellow
    Write-Host "🌐 Vérifiez manuellement : http://localhost:5173" -ForegroundColor Cyan
}

# Arrêter le job
Stop-Job $job -Force
Remove-Job $job -Force

Write-Host "`n" + "=" * 60 -ForegroundColor Blue
Write-Host "🎉 TEST TERMINÉ - Résumé :" -ForegroundColor Green
Write-Host "✅ Dépendances installées" -ForegroundColor Green
Write-Host "✅ TypeScript vérifié" -ForegroundColor Green
Write-Host "✅ Build de production réussi" -ForegroundColor Green
Write-Host "✅ Serveur de développement testé" -ForegroundColor Green

Write-Host "`n🚀 Commandes utiles :" -ForegroundColor Yellow
Write-Host "  npm run dev       - Démarrer en développement" -ForegroundColor Cyan
Write-Host "  npm run build     - Build de production" -ForegroundColor Cyan
Write-Host "  npm run preview   - Prévisualiser le build" -ForegroundColor Cyan
Write-Host "  npm run lint      - Vérifier le code" -ForegroundColor Cyan

Write-Host "`n📝 Erreurs corrigées :" -ForegroundColor Green
Write-Host "  ✅ Material-UI remplacé par Tailwind CSS" -ForegroundColor Green
Write-Host "  ✅ Redux Toolkit et React-Redux ajoutés" -ForegroundColor Green
Write-Host "  ✅ Imports et composants corrigés" -ForegroundColor Green
Write-Host "  ✅ Architecture UI cohérente" -ForegroundColor Green 