Write-Host "=== Diagnostic Docker ==="

Write-Host "1. Version Docker:"
docker --version

Write-Host "`n2. Version Docker Compose:"
docker compose version

Write-Host "`n3. État des conteneurs:"
docker ps -a

Write-Host "`n4. Images disponibles:"
docker images

Write-Host "`n5. Espace disque Docker:"
docker system df

Write-Host "`n6. Processus Docker:"
docker compose ps

Write-Host "`n=== Fin du diagnostic ===" 