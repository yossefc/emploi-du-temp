# School Timetable Generator - Docker Quick Start
# Simple PowerShell script for Windows

Write-Host "=============================================================================" -ForegroundColor Blue
Write-Host "           School Timetable Generator - Quick Start" -ForegroundColor Blue
Write-Host "=============================================================================" -ForegroundColor Blue

# Check if Docker is available
$dockerExists = $false
try {
    docker --version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dockerExists = $true
        Write-Host "✓ Docker is available" -ForegroundColor Green
    }
} catch {
    $dockerExists = $false
}

if (-not $dockerExists) {
    Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "2. Download Docker Desktop for Windows" -ForegroundColor White
    Write-Host "3. Install and restart your computer" -ForegroundColor White
    Write-Host "4. Start Docker Desktop" -ForegroundColor White
    Write-Host "5. Run this script again" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Creating .env file from template..." -ForegroundColor Yellow
    if (Test-Path "environment.example") {
        Copy-Item "environment.example" ".env"
        Write-Host "✓ Created .env file" -ForegroundColor Green
    } else {
        Write-Host "❌ No environment template found" -ForegroundColor Red
        exit 1
    }
}

# Create directories
Write-Host "📁 Creating directories..." -ForegroundColor Blue
$dirs = @("docker\nginx\ssl", "docker\nginx\conf.d", "docker\redis", "backend\logs", "backend\uploads")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "✓ Directories created" -ForegroundColor Green

# Function to run docker compose command
function Run-DockerCompose {
    param([string]$Command)
    
    Write-Host "Executing: $Command" -ForegroundColor Cyan
    
    # Try docker compose (new version)
    try {
        Invoke-Expression $Command
        return $LASTEXITCODE -eq 0
    } catch {
        Write-Host "Command failed: $_" -ForegroundColor Red
        return $false
    }
}

# Try to determine which docker compose command to use
$composeCmd = ""
try {
    docker compose version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $composeCmd = "docker compose"
        Write-Host "Using: docker compose (new version)" -ForegroundColor Green
    }
} catch {
    try {
        docker-compose --version | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $composeCmd = "docker-compose"
            Write-Host "Using: docker-compose (legacy version)" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Neither 'docker compose' nor 'docker-compose' is available" -ForegroundColor Red
        Write-Host "Please make sure Docker Desktop is properly installed and running" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

if ($composeCmd -eq "") {
    Write-Host "❌ No Docker Compose command found" -ForegroundColor Red
    exit 1
}

# Pull images
Write-Host ""
Write-Host "📥 Pulling latest images..." -ForegroundColor Blue
$pullResult = Run-DockerCompose "$composeCmd pull"
if (-not $pullResult) {
    Write-Host "⚠️  Pull failed, but continuing..." -ForegroundColor Yellow
}

# Build services
Write-Host ""
Write-Host "🔨 Building services..." -ForegroundColor Blue
$buildResult = Run-DockerCompose "$composeCmd build"
if (-not $buildResult) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start services
Write-Host ""
Write-Host "🚀 Starting services..." -ForegroundColor Blue
$startResult = Run-DockerCompose "$composeCmd up -d"

if ($startResult) {
    Write-Host ""
    Write-Host "✅ Services started successfully!" -ForegroundColor Green
    
    # Wait for initialization
    Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    # Show status
    Write-Host ""
    Write-Host "📊 Checking service status..." -ForegroundColor Blue
    Run-DockerCompose "$composeCmd ps"
    
    Write-Host ""
    Write-Host "🌐 Application URLs:" -ForegroundColor Blue
    Write-Host "  📱 Frontend App:      http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  🚀 Backend API:       http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  🌸 Celery Monitor:    http://localhost:5555" -ForegroundColor Cyan
    Write-Host "  🐘 Database Admin:    http://localhost:5050" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "👤 Default Login Credentials:" -ForegroundColor Blue
    Write-Host "  Username: admin" -ForegroundColor Yellow
    Write-Host "  Password: admin123" -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "🎉 Your School Timetable Generator is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Useful Commands:" -ForegroundColor White
    Write-Host "  Stop all:     $composeCmd down" -ForegroundColor Gray
    Write-Host "  View logs:    $composeCmd logs -f" -ForegroundColor Gray
    Write-Host "  Check status: $composeCmd ps" -ForegroundColor Gray
    Write-Host "  Restart:      $composeCmd restart" -ForegroundColor Gray
    
} else {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔍 Troubleshooting Steps:" -ForegroundColor Yellow
    Write-Host "1. Make sure Docker Desktop is running" -ForegroundColor White
    Write-Host "2. Check if required ports are free (3000, 5432, 6379, 8000)" -ForegroundColor White
    Write-Host "3. Try: $composeCmd logs" -ForegroundColor White
    Write-Host "4. Restart Docker Desktop and try again" -ForegroundColor White
}

Write-Host ""
Read-Host "Press Enter to exit" 