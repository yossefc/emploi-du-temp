#!/usr/bin/env pwsh
# Script de démarrage rapide pour l'application d'emplois du temps
# avec données de test israéliennes

Write-Host "🏫 ÉCOLE ISRAÉLIENNE - GÉNÉRATEUR D'EMPLOIS DU TEMPS" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Yellow

# Configuration
$env:DATABASE_URL = "sqlite:///./school_timetable.db"

Write-Host "📊 Configuration:" -ForegroundColor Cyan
Write-Host "   Database: SQLite (school_timetable.db)" -ForegroundColor White
Write-Host "   Données: École israélienne complète" -ForegroundColor White

# Vérifier que nous sommes dans le bon répertoire
if (-not (Test-Path "backend/app")) {
    Write-Host "❌ Erreur: Veuillez exécuter ce script depuis la racine du projet" -ForegroundColor Red
    exit 1
}

# Aller dans le répertoire backend
Set-Location backend

Write-Host "`n🔍 Vérification des données de test..." -ForegroundColor Yellow
try {
    $stats = python scripts/populate_test_data.py stats 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Données de test présentes" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Création des données de test..." -ForegroundColor Yellow
        python scripts/populate_test_data.py reset --force
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Données de test créées" -ForegroundColor Green
        } else {
            Write-Host "❌ Erreur lors de la création des données" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "❌ Erreur lors de la vérification: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n📈 Données disponibles:" -ForegroundColor Cyan
Write-Host "   👥 Utilisateurs: 4 (admin, principal, coordinateur, secrétaire)" -ForegroundColor White
Write-Host "   👨‍🏫 Enseignants: 11 spécialisés (bilingues HE/FR)" -ForegroundColor White
Write-Host "   📚 Matières: 15 (langues, sciences, religieux, arts)" -ForegroundColor White
Write-Host "   🎓 Classes: 12 (grades 7-12, collège/lycée)" -ForegroundColor White
Write-Host "   🏢 Salles: 16 (standard + laboratoires + spécialisées)" -ForegroundColor White
Write-Host "   ⚙️ Contraintes: Système scolaire israélien complet" -ForegroundColor White

Write-Host "`n🔐 Identifiants de test:" -ForegroundColor Cyan
Write-Host "   Username: admin" -ForegroundColor White
Write-Host "   Password: password123" -ForegroundColor White

Write-Host "`n🚀 Démarrage du serveur..." -ForegroundColor Green
Write-Host "📚 Documentation API: http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host "🔧 API Teachers: http://localhost:8000/api/v1/teachers/" -ForegroundColor Cyan
Write-Host "🛑 Appuyez sur Ctrl+C pour arrêter" -ForegroundColor Yellow

Write-Host "`n" + "=" * 60 -ForegroundColor Yellow

# Démarrer le serveur
try {
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host "`n❌ Erreur lors du démarrage du serveur: $_" -ForegroundColor Red
    exit 1
} 