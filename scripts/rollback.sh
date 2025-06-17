#!/bin/bash

# =============================================================================
# Script de Rollback Automatique - École Emploi du Temps
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="${BACKUP_DIR}/rollback.log"

# Variables d'environnement avec valeurs par défaut
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-school_timetable}"
DB_USER="${DB_USER:-school_user}"
DB_PASSWORD="${DB_PASSWORD:-}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
ROLLBACK_TIMEOUT="${ROLLBACK_TIMEOUT:-300}"  # 5 minutes

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${timestamp} ${BLUE}[INFO]${NC} $message" | tee -a "$LOG_FILE" ;;
        "WARN")  echo -e "${timestamp} ${YELLOW}[WARN]${NC} $message" | tee -a "$LOG_FILE" ;;
        "ERROR") echo -e "${timestamp} ${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE" ;;
        "SUCCESS") echo -e "${timestamp} ${GREEN}[SUCCESS]${NC} $message" | tee -a "$LOG_FILE" ;;
    esac
}

send_notification() {
    local status="$1"
    local message="$2"
    
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        local color="good"
        [[ "$status" == "error" ]] && color="danger"
        [[ "$status" == "warning" ]] && color="warning"
        
        curl -s -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"Rollback School Timetable - $status\",
                    \"text\": \"$message\",
                    \"footer\": \"$(hostname)\",
                    \"ts\": $(date +%s)
                }]
            }" || true
    fi
}

check_docker_health() {
    local service="$1"
    local max_attempts="${2:-30}"
    local attempt=0
    
    log "INFO" "Checking health of service: $service"
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker-compose -f docker-compose.prod.yml ps "$service" | grep -q "healthy\|Up"; then
            log "SUCCESS" "Service $service is healthy"
            return 0
        fi
        
        ((attempt++))
        log "INFO" "Waiting for $service to be healthy... ($attempt/$max_attempts)"
        sleep 10
    done
    
    log "ERROR" "Service $service failed to become healthy"
    return 1
}

find_latest_backup() {
    local backup_type="$1"
    local latest_backup
    
    latest_backup=$(find "$BACKUP_DIR" -name "${backup_type}_*.sql*" -o -name "${backup_type}_*.tar*" | sort -r | head -n1)
    
    if [[ -n "$latest_backup" && -f "$latest_backup" ]]; then
        echo "$latest_backup"
        return 0
    else
        log "ERROR" "No backup found for type: $backup_type"
        return 1
    fi
}

# =============================================================================
# FONCTIONS DE ROLLBACK
# =============================================================================

stop_services() {
    log "INFO" "Stopping current services..."
    
    if docker-compose -f docker-compose.prod.yml down --timeout 30; then
        log "SUCCESS" "Services stopped successfully"
        return 0
    else
        log "ERROR" "Failed to stop services gracefully, forcing shutdown..."
        docker-compose -f docker-compose.prod.yml kill
        docker-compose -f docker-compose.prod.yml down --volumes --remove-orphans
        return 1
    fi
}

rollback_database() {
    local backup_file
    
    log "INFO" "Starting database rollback..."
    
    # Trouver le dernier backup de base de données
    if ! backup_file=$(find_latest_backup "database"); then
        return 1
    fi
    
    log "INFO" "Using database backup: $backup_file"
    
    # Décompresser si nécessaire
    local working_file="$backup_file"
    if [[ "$backup_file" == *.gz ]]; then
        working_file="${backup_file%.gz}"
        if [[ ! -f "$working_file" ]]; then
            log "INFO" "Decompressing backup file..."
            gunzip -c "$backup_file" > "$working_file"
        fi
    fi
    
    # Démarrer temporairement le service PostgreSQL
    log "INFO" "Starting PostgreSQL for restoration..."
    docker-compose -f docker-compose.prod.yml up -d postgres
    
    # Attendre que PostgreSQL soit prêt
    local attempts=0
    while [[ $attempts -lt 30 ]]; do
        if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U "$DB_USER" -d "$DB_NAME"; then
            break
        fi
        ((attempts++))
        sleep 2
    done
    
    if [[ $attempts -eq 30 ]]; then
        log "ERROR" "PostgreSQL failed to start"
        return 1
    fi
    
    # Sauvegarder la base actuelle avant rollback
    local emergency_backup="${BACKUP_DIR}/emergency_$(date +%Y%m%d_%H%M%S).sql"
    log "INFO" "Creating emergency backup before rollback..."
    docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U "$DB_USER" -d "$DB_NAME" > "$emergency_backup" || true
    
    # Restaurer la base de données
    log "INFO" "Restoring database from backup..."
    
    # Arrêter les connexions actives
    docker-compose -f docker-compose.prod.yml exec -T postgres psql -U "$DB_USER" -d postgres -c "
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '$DB_NAME'
        AND pid <> pg_backend_pid();" || true
    
    # Supprimer et recréer la base
    docker-compose -f docker-compose.prod.yml exec -T postgres psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker-compose -f docker-compose.prod.yml exec -T postgres psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
    
    # Restaurer à partir du backup
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_restore -U "$DB_USER" -d "$DB_NAME" --verbose --clean --no-acl --no-owner < "$working_file"; then
        log "SUCCESS" "Database rollback completed successfully"
        
        # Nettoyer le fichier temporaire
        [[ "$working_file" != "$backup_file" ]] && rm -f "$working_file"
        
        return 0
    else
        log "ERROR" "Database rollback failed"
        
        # Tenter de restaurer depuis le backup d'urgence
        if [[ -f "$emergency_backup" ]]; then
            log "INFO" "Attempting to restore from emergency backup..."
            docker-compose -f docker-compose.prod.yml exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" < "$emergency_backup" || true
        fi
        
        return 1
    fi
}

rollback_uploads() {
    local backup_file
    
    log "INFO" "Starting uploads rollback..."
    
    # Trouver le dernier backup des uploads
    if ! backup_file=$(find_latest_backup "uploads"); then
        log "WARN" "No uploads backup found, skipping..."
        return 0
    fi
    
    log "INFO" "Using uploads backup: $backup_file"
    
    # Sauvegarder les uploads actuels
    local uploads_dir="${PROJECT_DIR}/uploads"
    if [[ -d "$uploads_dir" ]]; then
        local emergency_backup="${uploads_dir}_emergency_$(date +%Y%m%d_%H%M%S)"
        log "INFO" "Creating emergency backup of current uploads..."
        mv "$uploads_dir" "$emergency_backup" || true
    fi
    
    # Créer le répertoire d'uploads
    mkdir -p "$uploads_dir"
    
    # Restaurer les uploads
    local working_file="$backup_file"
    if [[ "$backup_file" == *.gz ]]; then
        if tar -xzf "$backup_file" -C "$PROJECT_DIR"; then
            log "SUCCESS" "Uploads rollback completed successfully"
            return 0
        else
            log "ERROR" "Failed to extract compressed uploads backup"
            return 1
        fi
    else
        if tar -xf "$backup_file" -C "$PROJECT_DIR"; then
            log "SUCCESS" "Uploads rollback completed successfully"
            return 0
        else
            log "ERROR" "Failed to extract uploads backup"
            return 1
        fi
    fi
}

rollback_configuration() {
    local backup_file
    
    log "INFO" "Starting configuration rollback..."
    
    # Trouver le dernier backup de configuration
    if ! backup_file=$(find_latest_backup "config"); then
        log "WARN" "No configuration backup found, skipping..."
        return 0
    fi
    
    log "INFO" "Using configuration backup: $backup_file"
    
    # Créer un répertoire temporaire
    local temp_dir=$(mktemp -d)
    
    # Extraire la configuration
    local working_file="$backup_file"
    if [[ "$backup_file" == *.gz ]]; then
        if tar -xzf "$backup_file" -C "$temp_dir"; then
            log "INFO" "Configuration backup extracted"
        else
            log "ERROR" "Failed to extract compressed configuration backup"
            rm -rf "$temp_dir"
            return 1
        fi
    else
        if tar -xf "$backup_file" -C "$temp_dir"; then
            log "INFO" "Configuration backup extracted"
        else
            log "ERROR" "Failed to extract configuration backup"
            rm -rf "$temp_dir"
            return 1
        fi
    fi
    
    # Restaurer les fichiers de configuration (avec précaution)
    [[ -f "$temp_dir/.env" ]] && cp "$temp_dir/.env" "$PROJECT_DIR/.env.rollback"
    [[ -f "$temp_dir/docker-compose.prod.yml" ]] && cp "$temp_dir/docker-compose.prod.yml" "$PROJECT_DIR/docker-compose.prod.yml.rollback"
    [[ -d "$temp_dir/docker" ]] && cp -r "$temp_dir/docker" "$PROJECT_DIR/docker.rollback"
    
    # Nettoyer
    rm -rf "$temp_dir"
    
    log "SUCCESS" "Configuration rollback completed (files backed up with .rollback extension)"
    log "WARN" "Please review and manually activate configuration files if needed"
    
    return 0
}

start_services() {
    log "INFO" "Starting services with previous configuration..."
    
    # Démarrer les services
    if docker-compose -f docker-compose.prod.yml up -d; then
        log "INFO" "Services started, checking health..."
        
        # Vérifier la santé des services
        local services=("postgres" "redis" "app" "frontend")
        local all_healthy=true
        
        for service in "${services[@]}"; do
            if ! check_docker_health "$service" 10; then
                all_healthy=false
                break
            fi
        done
        
        if [[ "$all_healthy" == "true" ]]; then
            log "SUCCESS" "All services are healthy after rollback"
            return 0
        else
            log "ERROR" "Some services are not healthy after rollback"
            return 1
        fi
    else
        log "ERROR" "Failed to start services"
        return 1
    fi
}

verify_rollback() {
    log "INFO" "Verifying rollback..."
    
    # Vérifier l'API
    local api_url="http://localhost:8000/health"
    if curl -f -s "$api_url" >/dev/null 2>&1; then
        log "SUCCESS" "API health check passed"
    else
        log "ERROR" "API health check failed"
        return 1
    fi
    
    # Vérifier la base de données
    if docker-compose -f docker-compose.prod.yml exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
        log "SUCCESS" "Database connectivity check passed"
    else
        log "ERROR" "Database connectivity check failed"
        return 1
    fi
    
    # Vérifier le frontend (si accessible)
    local frontend_url="http://localhost:80/health"
    if curl -f -s "$frontend_url" >/dev/null 2>&1; then
        log "SUCCESS" "Frontend health check passed"
    else
        log "WARN" "Frontend health check failed (may not be critical)"
    fi
    
    log "SUCCESS" "Rollback verification completed"
    return 0
}

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

main() {
    local start_time=$(date +%s)
    local rollback_reason="${1:-manual}"
    
    log "INFO" "Starting rollback process (reason: $rollback_reason)"
    
    # Créer le répertoire de logs
    mkdir -p "$BACKUP_DIR"
    
    # Vérifier qu'il y a des backups disponibles
    if [[ ! -d "$BACKUP_DIR" || -z "$(ls -A "$BACKUP_DIR")" ]]; then
        log "ERROR" "No backups found in $BACKUP_DIR"
        send_notification "error" "Rollback failed: no backups available"
        exit 1
    fi
    
    # Variables pour suivre les résultats
    local stop_success=false
    local db_rollback_success=false
    local uploads_rollback_success=false
    local config_rollback_success=false
    local start_success=false
    local verify_success=false
    
    # Arrêter les services actuels
    if stop_services; then
        stop_success=true
    fi
    
    # Rollback de la base de données
    if rollback_database; then
        db_rollback_success=true
    fi
    
    # Rollback des uploads
    if rollback_uploads; then
        uploads_rollback_success=true
    fi
    
    # Rollback de la configuration
    if rollback_configuration; then
        config_rollback_success=true
    fi
    
    # Redémarrer les services
    if start_services; then
        start_success=true
    fi
    
    # Vérifier le rollback
    if verify_rollback; then
        verify_success=true
    fi
    
    # Calculer le temps d'exécution
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Rapport final
    log "INFO" "Rollback process completed in ${duration}s"
    
    if [[ "$db_rollback_success" == "true" && "$start_success" == "true" && "$verify_success" == "true" ]]; then
        local success_message="Rollback completed successfully in ${duration}s (reason: $rollback_reason)"
        log "SUCCESS" "$success_message"
        send_notification "success" "$success_message"
        exit 0
    else
        local failed_components=()
        [[ "$stop_success" == "false" ]] && failed_components+=("stop")
        [[ "$db_rollback_success" == "false" ]] && failed_components+=("database")
        [[ "$start_success" == "false" ]] && failed_components+=("restart")
        [[ "$verify_success" == "false" ]] && failed_components+=("verification")
        
        local error_message="Rollback failed. Failed components: ${failed_components[*]} (reason: $rollback_reason)"
        log "ERROR" "$error_message"
        send_notification "error" "$error_message"
        exit 1
    fi
}

# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

# Vérifier les arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [reason] [--help]"
        echo "  reason    Reason for rollback (default: manual)"
        echo "  --help    Show this help message"
        exit 0
        ;;
    "")
        main "manual"
        ;;
    *)
        main "$1"
        ;;
esac 