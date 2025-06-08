# Script PowerShell pour installer toutes les dependances

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Installation de l'application" -ForegroundColor Cyan
Write-Host "Generateur d'Emplois du Temps avec IA" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Verifier si Python est installe
Write-Host "Verification de Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python trouve: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Python n'est pas installe ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host "Veuillez installer Python 3.8+ depuis https://www.python.org" -ForegroundColor Yellow
    exit 1
}

# Verifier si Node.js est installe
Write-Host ""
Write-Host "Verification de Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js trouve: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERREUR: Node.js n'est pas installe ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host "Veuillez installer Node.js 14+ depuis https://nodejs.org" -ForegroundColor Yellow
    exit 1
}

# Installation des dependances Backend
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Installation du Backend" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

Set-Location -Path "backend"

# Creer l'environnement virtuel si necessaire
if (-not (Test-Path ".\venv")) {
    Write-Host "Creation de l'environnement virtuel Python..." -ForegroundColor Yellow
    python -m venv venv
}

# Activer l'environnement virtuel
Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Installer les dependances
Write-Host "Installation des dependances Python..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Backend installe avec succes!" -ForegroundColor Green

# Installation des dependances Frontend
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Installation du Frontend" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

Set-Location -Path "..\frontend"

Write-Host "Installation des dependances npm..." -ForegroundColor Yellow
npm install

Write-Host "Frontend installe avec succes!" -ForegroundColor Green

# Retour au repertoire principal
Set-Location -Path ".."

# Creation du fichier .env si necessaire
if (-not (Test-Path "backend\.env")) {
    Write-Host ""
    Write-Host "Creation du fichier .env..." -ForegroundColor Yellow
    Copy-Item "env.example" "backend\.env"
    Write-Host "Fichier .env cree. N'oubliez pas d'ajouter vos cles API!" -ForegroundColor Yellow
}

# Afficher les instructions finales
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Installation terminee avec succes!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Pour demarrer l'application:" -ForegroundColor Cyan
Write-Host "  .\start_simple.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Pour configurer l'agent IA:" -ForegroundColor Cyan
Write-Host "  1. Editez backend\.env" -ForegroundColor White
Write-Host "  2. Ajoutez votre cle API Anthropic ou OpenAI" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - Guide de demarrage: QUICK_START.md" -ForegroundColor White
Write-Host "  - Architecture: ARCHITECTURE.md" -ForegroundColor White
Write-Host "  - Etat du projet: IMPLEMENTATION_STATUS.md" -ForegroundColor White
Write-Host ""
Write-Host "Bon developpement!" -ForegroundColor Green 