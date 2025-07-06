# =============================================================================
# Simple Docker Startup Script for School Timetable Generator
# Works with both docker-compose and docker compose commands
# =============================================================================

Write-Host "=============================================================================" -ForegroundColor Blue
Write-Host "           School Timetable Generator - Quick Start" -ForegroundColor Blue
Write-Host "=============================================================================" -ForegroundColor Blue

# Check if Docker is available
try {
    $null = docker --version 2>$null
    Write-Host "✓ Docker is available" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "Then restart this script." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path "environment.example") {
        Copy-Item "environment.example" ".env"
        Write-Host "✓ Created .env file from template" -ForegroundColor Green
    }
    else {
        Write-Host "❌ No environment template found" -ForegroundColor Red
        exit 1
    }
}

# Create necessary directories
$dirs = @("docker\nginx\ssl", "docker\nginx\conf.d", "docker\redis", "backend\logs", "backend\uploads")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "✓ Directories created" -ForegroundColor Green

# Function to try different Docker Compose commands
function Invoke-DockerCompose {
    param([string[]]$Arguments)
    
    # Try docker compose first (newer version)
    try {
        Write-Host "Trying: docker compose $Arguments" -ForegroundColor Cyan
        $process = Start-Process -FilePath "docker" -ArgumentList ("compose " + ($Arguments -join " ")) -Wait -PassThru -NoNewWindow
        if ($process.ExitCode -eq 0) {
            return $true
        }
    }
    catch {
        Write-Host "docker compose not available, trying docker-compose..." -ForegroundColor Yellow
    }
    
    # Try docker-compose (older version)
    try {
        Write-Host "Trying: docker-compose $Arguments" -ForegroundColor Cyan
        $process = Start-Process -FilePath "docker-compose" -ArgumentList ($Arguments -join " ") -Wait -PassThru -NoNewWindow
        if ($process.ExitCode -eq 0) {
            return $true
        }
    }
    catch {
        Write-Host "docker-compose not available either" -ForegroundColor Red
        return $false
    }
    
    return $false
}

# Pull latest images
Write-Host ""
Write-Host "📥 Pulling latest Docker images..." -ForegroundColor Blue
if (-not (Invoke-DockerCompose @("pull"))) {
    Write-Host "❌ Failed to pull images" -ForegroundColor Red
    Write-Host "Continuing anyway..." -ForegroundColor Yellow
}

# Build services
Write-Host ""
Write-Host "🔨 Building services..." -ForegroundColor Blue
if (-not (Invoke-DockerCompose @("build"))) {
    Write-Host "❌ Failed to build services" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start services
Write-Host ""
Write-Host "🚀 Starting all services..." -ForegroundColor Blue
if (Invoke-DockerCompose @("up", "-d")) {
    Write-Host ""
    Write-Host "✅ Services started successfully!" -ForegroundColor Green
    
    # Wait a moment for services to start
    Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Show status
    Write-Host ""
    Write-Host "📊 Service Status:" -ForegroundColor Blue
    Invoke-DockerCompose @("ps")
    
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor Blue
    Write-Host "  Frontend:         http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  Backend API:      http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API Docs:         http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  Flower Monitor:   http://localhost:5555" -ForegroundColor Cyan
    Write-Host "  pgAdmin:          http://localhost:5050" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "👤 Default Admin Login:" -ForegroundColor Blue
    Write-Host "  Username: admin" -ForegroundColor Yellow
    Write-Host "  Password: admin123" -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "🎉 Your School Timetable Generator is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Commands to manage your application:" -ForegroundColor White
    Write-Host "  Stop:    docker compose down" -ForegroundColor Gray
    Write-Host "  Logs:    docker compose logs -f" -ForegroundColor Gray
    Write-Host "  Status:  docker compose ps" -ForegroundColor Gray
}
else {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Make sure Docker Desktop is running" -ForegroundColor White
    Write-Host "2. Check if ports 3000, 5432, 6379, 8000 are free" -ForegroundColor White
    Write-Host "3. Try: docker compose logs" -ForegroundColor White
}

Write-Host ""
Read-Host "Press Enter to exit" 