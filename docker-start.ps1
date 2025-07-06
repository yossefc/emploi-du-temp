# =============================================================================
# Docker Startup Script for School Timetable Generator (PowerShell)
# =============================================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "logs", "status", "cleanup", "build", "pull")]
    [string]$Command = "start",
    
    [Parameter()]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",
    
    [Parameter()]
    [string]$Profile = "",
    
    [Parameter()]
    [switch]$Detached,
    
    [Parameter()]
    [switch]$Help
)

# Color functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Header {
    Write-Host ""
    Write-Host "=============================================================================" -ForegroundColor Blue
    Write-Host "           School Timetable Generator - Docker Environment" -ForegroundColor Blue
    Write-Host "=============================================================================" -ForegroundColor Blue
    Write-Host ""
}

function Show-Help {
    Write-Host "Usage: .\docker-start.ps1 [OPTIONS] [COMMAND]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start     Start all services (default)"
    Write-Host "  stop      Stop all services"
    Write-Host "  restart   Restart all services"
    Write-Host "  logs      Show service logs"
    Write-Host "  status    Show service status"
    Write-Host "  cleanup   Stop services and clean up"
    Write-Host "  build     Build services only"
    Write-Host "  pull      Pull images only"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Environment ENV     Set environment (development, staging, production)"
    Write-Host "  -Profile PROFILE     Use specific docker-compose profile"
    Write-Host "  -Detached           Run in background"
    Write-Host "  -Help               Show this help"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\docker-start.ps1                              # Start in development mode"
    Write-Host "  .\docker-start.ps1 -Environment production      # Start in production mode"
    Write-Host "  .\docker-start.ps1 -Profile tools -Detached     # Start with tools profile in background"
    Write-Host "  .\docker-start.ps1 logs                        # Show logs"
    Write-Host "  .\docker-start.ps1 cleanup                     # Clean up everything"
}

function Test-Requirements {
    Write-Info "Checking requirements..."
    
    # Check if Docker is installed
    try {
        $null = docker --version
        Write-Info "✓ Docker is installed"
    } catch {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        Write-Host "Download from: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    # Check if Docker is running
    try {
        $null = docker info 2>$null
        Write-Info "✓ Docker is running"
    } catch {
        Write-Error "Docker is not running. Please start Docker Desktop first."
        exit 1
    }
    
    # Check if Docker Compose is available
    try {
        $null = docker-compose --version
        Write-Info "✓ Docker Compose is available"
    } catch {
        Write-Error "Docker Compose is not available. Please ensure Docker Desktop is properly installed."
        exit 1
    }
}

function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found. Creating from template..."
        if (Test-Path "environment.example") {
            Copy-Item "environment.example" ".env"
            Write-Info "✓ Created .env file from template"
            Write-Warning "Please review and update the .env file with your configuration"
        } else {
            Write-Error "No environment template found. Please create a .env file manually."
            exit 1
        }
    } else {
        Write-Info "✓ .env file found"
    }
}

function New-Directories {
    Write-Info "Creating necessary directories..."
    
    # Create Docker-related directories
    $dirs = @(
        "docker\nginx\ssl",
        "docker\nginx\conf.d",
        "docker\redis",
        "docker\pgadmin",
        "backend\logs",
        "backend\uploads",
        "backend\exports",
        "frontend\dist"
    )
    
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Info "✓ Directories created"
}

function New-SslCertificates {
    if (-not (Test-Path "docker\nginx\ssl\cert.pem")) {
        Write-Info "Generating self-signed SSL certificates..."
        
        try {
            # Try to generate SSL certificates using OpenSSL if available
            openssl req -x509 -newkey rsa:4096 -keyout docker\nginx\ssl\key.pem -out docker\nginx\ssl\cert.pem -days 365 -nodes -subj "/C=IL/ST=Central/L=TelAviv/O=School/CN=localhost" 2>$null
            
            if (Test-Path "docker\nginx\ssl\cert.pem") {
                Write-Info "✓ SSL certificates generated"
            }
        } catch {
            Write-Warning "Could not generate SSL certificates. HTTPS will not be available."
            Write-Info "To enable HTTPS, install OpenSSL or manually place cert.pem and key.pem in docker\nginx\ssl\"
        }
    }
}

function Invoke-PullImages {
    Write-Info "Pulling latest Docker images..."
    
    $composeArgs = @()
    if ($Profile) {
        $composeArgs += "--profile", $Profile
    }
    $composeArgs += "pull"
    
    & docker-compose @composeArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "✓ Images pulled"
    } else {
        Write-Error "Failed to pull images"
        exit 1
    }
}

function Invoke-BuildServices {
    Write-Info "Building application services..."
    
    $composeArgs = @()
    if ($Profile) {
        $composeArgs += "--profile", $Profile
    }
    $composeArgs += "build", "--no-cache"
    
    & docker-compose @composeArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "✓ Services built"
    } else {
        Write-Error "Failed to build services"
        exit 1
    }
}

function Start-Services {
    Write-Info "Starting services..."
    
    $composeArgs = @()
    if ($Profile) {
        $composeArgs += "--profile", $Profile
    }
    $composeArgs += "up"
    if ($Detached) {
        $composeArgs += "-d"
    }
    
    & docker-compose @composeArgs
    
    if ($Detached -and $LASTEXITCODE -eq 0) {
        Write-Info "✓ Services started in background"
    }
}

function Wait-ForServices {
    if (-not $Detached) {
        return
    }
    
    Write-Info "Waiting for services to be healthy..."
    
    $maxAttempts = 60
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        $attempt++
        
        # Check if services are running
        $runningServices = docker-compose ps --services --filter "status=running" | Measure-Object | Select-Object -ExpandProperty Count
        $totalServices = docker-compose ps --services | Measure-Object | Select-Object -ExpandProperty Count
        
        if ($runningServices -eq $totalServices) {
            Write-Info "✓ All services are running"
            break
        }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Error "Services did not start within expected time"
        docker-compose logs --tail=20
        exit 1
    }
}

function Show-Status {
    Write-Info "Service Status:"
    docker-compose ps
    
    Write-Host ""
    Write-Info "Access URLs:"
    Write-Host "  🌐 Frontend:         http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  🚀 Backend API:      http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  📚 API Docs:         http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  🌸 Flower Monitor:   http://localhost:5555" -ForegroundColor Cyan
    Write-Host "  🐘 pgAdmin:          http://localhost:5050" -ForegroundColor Cyan
    Write-Host "  🔴 Redis Commander:  http://localhost:8081" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Info "Default Credentials:"
    Write-Host "  Admin User:    admin / admin123" -ForegroundColor Yellow
    Write-Host "  pgAdmin:       admin@school.edu / admin123" -ForegroundColor Yellow
    Write-Host "  Flower:        admin / password" -ForegroundColor Yellow
    Write-Host "  Redis Cmd:     admin / admin123" -ForegroundColor Yellow
}

function Invoke-Cleanup {
    Write-Info "Cleaning up..."
    docker-compose down -v
    docker system prune -f
    Write-Info "✓ Cleanup completed"
}

# =============================================================================
# MAIN SCRIPT
# =============================================================================

if ($Help) {
    Show-Help
    exit 0
}

Write-Header

# Set environment variables
$env:ENVIRONMENT = $Environment
if ($Profile) {
    $env:PROFILE = $Profile
}

# Execute command
switch ($Command) {
    "start" {
        Test-Requirements
        Test-EnvFile
        New-Directories
        New-SslCertificates
        Invoke-PullImages
        Invoke-BuildServices
        Start-Services
        
        if ($Detached) {
            Wait-ForServices
            Show-Status
        }
    }
    
    "stop" {
        Write-Info "Stopping services..."
        docker-compose down
        Write-Info "✓ Services stopped"
    }
    
    "restart" {
        Write-Info "Restarting services..."
        docker-compose down
        Start-Services
    }
    
    "logs" {
        docker-compose logs -f --tail=100
    }
    
    "status" {
        Show-Status
    }
    
    "cleanup" {
        Invoke-Cleanup
    }
    
    "build" {
        Test-Requirements
        Invoke-BuildServices
    }
    
    "pull" {
        Test-Requirements
        Invoke-PullImages
    }
    
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}

Write-Info "Operation completed successfully!" 