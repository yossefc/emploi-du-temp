Write-Host "=============================================================================" -ForegroundColor Blue
Write-Host "           School Timetable Generator - Setup" -ForegroundColor Blue  
Write-Host "=============================================================================" -ForegroundColor Blue

Write-Host "Step 1: Checking Docker..." -ForegroundColor Yellow
docker --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker not found!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "Docker is available!" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Creating environment file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item "environment.example" ".env"
    Write-Host ".env file created!" -ForegroundColor Green
} else {
    Write-Host ".env file already exists!" -ForegroundColor Green  
}

Write-Host ""
Write-Host "Step 3: Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "docker\nginx\ssl" -Force | Out-Null
New-Item -ItemType Directory -Path "docker\nginx\conf.d" -Force | Out-Null  
New-Item -ItemType Directory -Path "docker\redis" -Force | Out-Null
New-Item -ItemType Directory -Path "backend\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "backend\uploads" -Force | Out-Null
Write-Host "Directories created!" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Testing Docker Compose..." -ForegroundColor Yellow
docker compose version
if ($LASTEXITCODE -eq 0) {
    Write-Host "Using docker compose (new version)" -ForegroundColor Green
    $composeCmd = "docker compose"
} else {
    docker-compose --version
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Using docker-compose (legacy version)" -ForegroundColor Green
        $composeCmd = "docker-compose"
    } else {
        Write-Host "ERROR: No Docker Compose found!" -ForegroundColor Red
        pause
        exit 1
    }
}

Write-Host ""
Write-Host "Step 5: Starting application..." -ForegroundColor Blue
Write-Host "This will take several minutes..." -ForegroundColor Yellow

if ($composeCmd -eq "docker compose") {
    Write-Host "Running: docker compose up -d" -ForegroundColor Cyan
    docker compose up -d
} else {
    Write-Host "Running: docker-compose up -d" -ForegroundColor Cyan  
    docker-compose up -d
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS! Application is starting..." -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
    
    Write-Host ""
    Write-Host "APPLICATION READY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access your application:" -ForegroundColor Blue
    Write-Host "Frontend:      http://localhost:3000" -ForegroundColor Cyan
    Write-Host "Backend API:   http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Login with:" -ForegroundColor Blue  
    Write-Host "Username: admin" -ForegroundColor Yellow
    Write-Host "Password: admin123" -ForegroundColor Yellow
    
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to start application!" -ForegroundColor Red
    Write-Host "Make sure Docker Desktop is running and try again." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
pause 