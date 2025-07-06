Write-Host "=============================================================================" -ForegroundColor Blue
Write-Host "           School Timetable Generator - Quick Start" -ForegroundColor Blue
Write-Host "=============================================================================" -ForegroundColor Blue

Write-Host "Checking Docker..." -ForegroundColor Yellow

# Simple Docker check
$dockerError = $null
docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not installed or not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "2. Download and install Docker Desktop for Windows" -ForegroundColor White
    Write-Host "3. Restart your computer" -ForegroundColor White
    Write-Host "4. Start Docker Desktop" -ForegroundColor White
    Write-Host "5. Run this script again" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host "✓ Docker is available" -ForegroundColor Green

# Create .env file
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item "environment.example" ".env"
    Write-Host "✓ .env file created" -ForegroundColor Green
}

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "docker\nginx\ssl" -Force | Out-Null
New-Item -ItemType Directory -Path "docker\nginx\conf.d" -Force | Out-Null
New-Item -ItemType Directory -Path "docker\redis" -Force | Out-Null
New-Item -ItemType Directory -Path "backend\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "backend\uploads" -Force | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

# Try docker compose commands
Write-Host ""
Write-Host "Testing Docker Compose..." -ForegroundColor Yellow

$useNewCompose = $false
docker compose version 2>$null
if ($LASTEXITCODE -eq 0) {
    $useNewCompose = $true
    Write-Host "✓ Using 'docker compose' (new version)" -ForegroundColor Green
} else {
    docker-compose --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Using 'docker-compose' (legacy version)" -ForegroundColor Green
    } else {
        Write-Host "❌ No Docker Compose found!" -ForegroundColor Red
        Write-Host "Make sure Docker Desktop is installed and running" -ForegroundColor Yellow
        pause
        exit 1
    }
}

Write-Host ""
Write-Host "Building and starting services..." -ForegroundColor Blue
Write-Host "This may take several minutes on first run..." -ForegroundColor Yellow

if ($useNewCompose) {
    # New docker compose syntax
    docker compose pull
    docker compose build
    docker compose up -d
} else {
    # Legacy docker-compose syntax
    docker-compose pull
    docker-compose build
    docker-compose up -d
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Services started successfully!" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
    
    Write-Host ""
    Write-Host "🌐 Your application is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access URLs:" -ForegroundColor Blue
    Write-Host "  Frontend:         http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  Backend API:      http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  Celery Monitor:   http://localhost:5555" -ForegroundColor Cyan
    Write-Host "  Database Admin:   http://localhost:5050" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "Default Login:" -ForegroundColor Blue
    Write-Host "  Username: admin" -ForegroundColor Yellow
    Write-Host "  Password: admin123" -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "🎉 School Timetable Generator is ready to use!" -ForegroundColor Green
    
} else {
    Write-Host ""
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Make sure Docker Desktop is running" -ForegroundColor White
    Write-Host "2. Check if ports 3000, 5432, 6379, 8000 are available" -ForegroundColor White
    Write-Host "3. Restart Docker Desktop and try again" -ForegroundColor White
}

Write-Host ""
pause 