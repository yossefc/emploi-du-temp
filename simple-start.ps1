Write-Host "=== Démarrage Simple ==="
Write-Host "Arrêt des services existants..."
docker compose down 2>$null

Write-Host "Démarrage des services essentiels..."
docker compose up -d postgres redis backend frontend

Write-Host "Attente du démarrage..."
Start-Sleep -Seconds 30

Write-Host "État des services:"
docker compose ps

Write-Host ""
Write-Host "🌐 Application: http://localhost:3000"
Write-Host "🔧 API: http://localhost:8000"
Write-Host "👤 Login: admin / admin123" 