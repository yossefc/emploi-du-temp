#!/bin/bash

# =============================================================================
# Docker Startup Script for School Timetable Generator
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${ENVIRONMENT:-development}
PROFILE=${PROFILE:-""}
DETACHED=${DETACHED:-false}

# =============================================================================
# FUNCTIONS
# =============================================================================

print_header() {
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "           School Timetable Generator - Docker Environment"
    echo "============================================================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_step "Checking requirements..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_step "✓ Docker and Docker Compose are available"
}

check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f "environment.example" ]; then
            cp environment.example .env
            print_step "✓ Created .env file from template"
            print_warning "Please review and update the .env file with your configuration"
        else
            print_error "No environment template found. Please create a .env file manually."
            exit 1
        fi
    else
        print_step "✓ .env file found"
    fi
}

create_directories() {
    print_step "Creating necessary directories..."
    
    # Create Docker-related directories
    mkdir -p docker/nginx/ssl
    mkdir -p docker/nginx/conf.d
    mkdir -p docker/redis
    mkdir -p docker/pgadmin
    
    # Create application directories
    mkdir -p backend/logs
    mkdir -p backend/uploads
    mkdir -p backend/exports
    mkdir -p frontend/dist
    
    print_step "✓ Directories created"
}

generate_ssl_certs() {
    if [ ! -f "docker/nginx/ssl/cert.pem" ]; then
        print_step "Generating self-signed SSL certificates..."
        
        openssl req -x509 -newkey rsa:4096 -keyout docker/nginx/ssl/key.pem \
            -out docker/nginx/ssl/cert.pem -days 365 -nodes \
            -subj "/C=IL/ST=Central/L=TelAviv/O=School/CN=localhost" 2>/dev/null || {
                print_warning "Could not generate SSL certificates. HTTPS will not be available."
            }
        
        if [ -f "docker/nginx/ssl/cert.pem" ]; then
            print_step "✓ SSL certificates generated"
        fi
    fi
}

pull_images() {
    print_step "Pulling latest Docker images..."
    
    if [ "$PROFILE" != "" ]; then
        docker-compose --profile "$PROFILE" pull
    else
        docker-compose pull
    fi
    
    print_step "✓ Images pulled"
}

build_services() {
    print_step "Building application services..."
    
    if [ "$PROFILE" != "" ]; then
        docker-compose --profile "$PROFILE" build --no-cache
    else
        docker-compose build --no-cache
    fi
    
    print_step "✓ Services built"
}

start_services() {
    print_step "Starting services..."
    
    local compose_args=""
    
    if [ "$DETACHED" = true ]; then
        compose_args="$compose_args -d"
    fi
    
    if [ "$PROFILE" != "" ]; then
        compose_args="$compose_args --profile $PROFILE"
    fi
    
    docker-compose up $compose_args
    
    if [ "$DETACHED" = true ]; then
        print_step "✓ Services started in background"
    fi
}

wait_for_services() {
    if [ "$DETACHED" = false ]; then
        return 0
    fi
    
    print_step "Waiting for services to be healthy..."
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        
        # Check if all services are healthy
        local healthy_services=$(docker-compose ps --services --filter "status=running" | wc -l)
        local total_services=$(docker-compose ps --services | wc -l)
        
        if [ "$healthy_services" -eq "$total_services" ]; then
            print_step "✓ All services are running"
            break
        fi
        
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Services did not start within expected time"
        docker-compose logs --tail=20
        return 1
    fi
}

show_status() {
    print_step "Service Status:"
    docker-compose ps
    
    echo ""
    print_step "Access URLs:"
    echo "  🌐 Frontend:         http://localhost:3000"
    echo "  🚀 Backend API:      http://localhost:8000"
    echo "  📚 API Docs:         http://localhost:8000/docs"
    echo "  🌸 Flower Monitor:   http://localhost:5555"
    echo "  🐘 pgAdmin:          http://localhost:5050"
    echo "  🔴 Redis Commander:  http://localhost:8081"
    echo ""
    
    print_step "Default Credentials:"
    echo "  Admin User:    admin / admin123"
    echo "  pgAdmin:       admin@school.edu / admin123"
    echo "  Flower:        admin / password"
    echo "  Redis Cmd:     admin / admin123"
}

cleanup() {
    print_step "Cleaning up..."
    docker-compose down -v
    docker system prune -f
    print_step "✓ Cleanup completed"
}

show_help() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start all services (default)"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  logs      Show service logs"
    echo "  status    Show service status"
    echo "  cleanup   Stop services and clean up"
    echo "  build     Build services only"
    echo "  pull      Pull images only"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Set environment (development, staging, production)"
    echo "  -p, --profile PROFILE    Use specific docker-compose profile"
    echo "  -d, --detached          Run in background"
    echo "  -h, --help              Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                                  # Start in development mode"
    echo "  $0 --environment production         # Start in production mode"
    echo "  $0 --profile tools --detached       # Start with tools profile in background"
    echo "  $0 logs                            # Show logs"
    echo "  $0 cleanup                         # Clean up everything"
}

# =============================================================================
# MAIN SCRIPT
# =============================================================================

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -d|--detached)
            DETACHED=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        start)
            COMMAND="start"
            shift
            ;;
        stop)
            COMMAND="stop"
            shift
            ;;
        restart)
            COMMAND="restart"
            shift
            ;;
        logs)
            COMMAND="logs"
            shift
            ;;
        status)
            COMMAND="status"
            shift
            ;;
        cleanup)
            COMMAND="cleanup"
            shift
            ;;
        build)
            COMMAND="build"
            shift
            ;;
        pull)
            COMMAND="pull"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set default command
COMMAND=${COMMAND:-start}

print_header

# Export environment variables
export ENVIRONMENT
export PROFILE

# Execute command
case $COMMAND in
    start)
        check_requirements
        check_env_file
        create_directories
        generate_ssl_certs
        pull_images
        build_services
        start_services
        
        if [ "$DETACHED" = true ]; then
            wait_for_services
            show_status
        fi
        ;;
    
    stop)
        print_step "Stopping services..."
        docker-compose down
        print_step "✓ Services stopped"
        ;;
    
    restart)
        print_step "Restarting services..."
        docker-compose down
        start_services
        ;;
    
    logs)
        docker-compose logs -f --tail=100
        ;;
    
    status)
        show_status
        ;;
    
    cleanup)
        cleanup
        ;;
    
    build)
        check_requirements
        build_services
        ;;
    
    pull)
        check_requirements
        pull_images
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

print_step "Operation completed successfully!" 