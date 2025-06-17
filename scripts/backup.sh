#!/bin/bash

# =============================================================================
# Script de Backup Complet - École Emploi du Temps
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Variables d'environnement avec valeurs par défaut
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-school_timetable}"
DB_USER="${DB_USER:-school_user}"
DB_PASSWORD="${DB_PASSWORD:-}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
COMPRESS_BACKUPS="${COMPRESS_BACKUPS:-true}"
S3_BUCKET="${S3_BUCKET:-}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

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
                    \"title\": \"Backup School Timetable - $status\",
                    \"text\": \"$message\",
                    \"footer\": \"$(hostname)\",
                    \"ts\": $(date +%s)
                }]
            }" || true
    fi
}

check_dependencies() {
    local missing_deps=()
    
    for cmd in pg_dump gzip tar aws; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "ERROR" "Missing dependencies: ${missing_deps[*]}"
        return 1
    fi
    
    return 0
}

cleanup_old_backups() {
    log "INFO" "Cleaning up backups older than $BACKUP_RETENTION_DAYS days"
    
    find "$BACKUP_DIR" -name "backup_*" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
    
    log "SUCCESS" "Old backups cleaned up"
}

# =============================================================================
# FONCTIONS DE BACKUP
# =============================================================================

backup_database() {
    local timestamp="$1"
    local db_backup_file="${BACKUP_DIR}/database_${timestamp}.sql"
    
    log "INFO" "Starting database backup..."
    
    # Vérifier la connectivité à la base de données
    if ! PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
        log "ERROR" "Cannot connect to database"
        return 1
    fi
    
    # Dump de la base de données
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --file="$db_backup_file"; then
        
        log "SUCCESS" "Database backup completed: $db_backup_file"
        
        # Compresser si demandé
        if [[ "$COMPRESS_BACKUPS" == "true" ]]; then
            gzip "$db_backup_file"
            db_backup_file="${db_backup_file}.gz"
            log "INFO" "Database backup compressed: $db_backup_file"
        fi
        
        # Calculer la taille
        local size=$(du -h "$db_backup_file" | cut -f1)
        log "INFO" "Database backup size: $size"
        
        return 0
    else
        log "ERROR" "Database backup failed"
        return 1
    fi
}

backup_uploads() {
    local timestamp="$1"
    local uploads_backup_file="${BACKUP_DIR}/uploads_${timestamp}.tar"
    local uploads_dir="${PROJECT_DIR}/uploads"
    
    if [[ ! -d "$uploads_dir" ]]; then
        log "WARN" "Uploads directory not found: $uploads_dir"
        return 0
    fi
    
    log "INFO" "Starting uploads backup..."
    
    if tar -cf "$uploads_backup_file" -C "$PROJECT_DIR" uploads/; then
        log "SUCCESS" "Uploads backup completed: $uploads_backup_file"
        
        # Compresser si demandé
        if [[ "$COMPRESS_BACKUPS" == "true" ]]; then
            gzip "$uploads_backup_file"
            uploads_backup_file="${uploads_backup_file}.gz"
            log "INFO" "Uploads backup compressed: $uploads_backup_file"
        fi
        
        # Calculer la taille
        local size=$(du -h "$uploads_backup_file" | cut -f1)
        log "INFO" "Uploads backup size: $size"
        
        return 0
    else
        log "ERROR" "Uploads backup failed"
        return 1
    fi
}

backup_configuration() {
    local timestamp="$1"
    local config_backup_file="${BACKUP_DIR}/config_${timestamp}.tar"
    
    log "INFO" "Starting configuration backup..."
    
    # Créer un répertoire temporaire pour la configuration
    local temp_config_dir=$(mktemp -d)
    
    # Copier les fichiers de configuration
    cp "$PROJECT_DIR/.env" "$temp_config_dir/" 2>/dev/null || true
    cp "$PROJECT_DIR/docker-compose.prod.yml" "$temp_config_dir/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/docker/" "$temp_config_dir/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/scripts/" "$temp_config_dir/" 2>/dev/null || true
    
    # Créer l'archive
    if tar -cf "$config_backup_file" -C "$temp_config_dir" .; then
        log "SUCCESS" "Configuration backup completed: $config_backup_file"
        
        # Compresser si demandé
        if [[ "$COMPRESS_BACKUPS" == "true" ]]; then
            gzip "$config_backup_file"
            config_backup_file="${config_backup_file}.gz"
            log "INFO" "Configuration backup compressed: $config_backup_file"
        fi
        
        # Nettoyer le répertoire temporaire
        rm -rf "$temp_config_dir"
        
        # Calculer la taille
        local size=$(du -h "$config_backup_file" | cut -f1)
        log "INFO" "Configuration backup size: $size"
        
        return 0
    else
        log "ERROR" "Configuration backup failed"
        rm -rf "$temp_config_dir"
        return 1
    fi
}

create_backup_manifest() {
    local timestamp="$1"
    local manifest_file="${BACKUP_DIR}/manifest_${timestamp}.json"
    
    log "INFO" "Creating backup manifest..."
    
    cat > "$manifest_file" << EOF
{
    "timestamp": "$timestamp",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "version": "$(cd "$PROJECT_DIR" && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "branch": "$(cd "$PROJECT_DIR" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "environment": "${ENVIRONMENT:-production}",
    "files": [
EOF

    local first=true
    for file in "$BACKUP_DIR"/*_${timestamp}.*; do
        if [[ -f "$file" ]]; then
            [[ "$first" == "false" ]] && echo "," >> "$manifest_file"
            echo -n "        {" >> "$manifest_file"
            echo -n "\"name\": \"$(basename "$file")\", " >> "$manifest_file"
            echo -n "\"size\": $(stat -c%s "$file"), " >> "$manifest_file"
            echo -n "\"md5\": \"$(md5sum "$file" | cut -d' ' -f1)\"" >> "$manifest_file"
            echo -n "}" >> "$manifest_file"
            first=false
        fi
    done

    cat >> "$manifest_file" << EOF

    ],
    "statistics": {
        "total_files": $(find "$BACKUP_DIR" -name "*_${timestamp}.*" -type f | wc -l),
        "total_size": $(find "$BACKUP_DIR" -name "*_${timestamp}.*" -type f -exec stat -c%s {} + | awk '{sum+=$1} END {print sum}')
    }
}
EOF

    log "SUCCESS" "Backup manifest created: $manifest_file"
}

upload_to_s3() {
    local timestamp="$1"
    
    if [[ -z "$S3_BUCKET" ]]; then
        log "INFO" "S3 bucket not configured, skipping upload"
        return 0
    fi
    
    log "INFO" "Uploading backups to S3 bucket: $S3_BUCKET"
    
    local upload_success=true
    
    for file in "$BACKUP_DIR"/*_${timestamp}.*; do
        if [[ -f "$file" ]]; then
            local s3_path="s3://$S3_BUCKET/backups/$(date +%Y/%m/%d)/$(basename "$file")"
            
            if aws s3 cp "$file" "$s3_path"; then
                log "SUCCESS" "Uploaded: $(basename "$file")"
            else
                log "ERROR" "Failed to upload: $(basename "$file")"
                upload_success=false
            fi
        fi
    done
    
    if [[ "$upload_success" == "true" ]]; then
        log "SUCCESS" "All backups uploaded to S3"
        return 0
    else
        log "ERROR" "Some backups failed to upload to S3"
        return 1
    fi
}

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

main() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local start_time=$(date +%s)
    
    log "INFO" "Starting backup process with timestamp: $timestamp"
    
    # Créer le répertoire de backup
    mkdir -p "$BACKUP_DIR"
    
    # Vérifier les dépendances
    if ! check_dependencies; then
        send_notification "error" "Backup failed: missing dependencies"
        exit 1
    fi
    
    # Variables pour suivre les échecs
    local database_success=false
    local uploads_success=false
    local config_success=false
    local s3_success=false
    
    # Backup de la base de données
    if backup_database "$timestamp"; then
        database_success=true
    fi
    
    # Backup des uploads
    if backup_uploads "$timestamp"; then
        uploads_success=true
    fi
    
    # Backup de la configuration
    if backup_configuration "$timestamp"; then
        config_success=true
    fi
    
    # Créer le manifest
    create_backup_manifest "$timestamp"
    
    # Upload vers S3
    if upload_to_s3 "$timestamp"; then
        s3_success=true
    fi
    
    # Nettoyer les anciens backups
    cleanup_old_backups
    
    # Calculer le temps d'exécution
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Rapport final
    local total_size=$(find "$BACKUP_DIR" -name "*_${timestamp}.*" -type f -exec stat -c%s {} + | awk '{sum+=$1} END {print sum/1024/1024}')
    
    log "INFO" "Backup process completed in ${duration}s"
    log "INFO" "Total backup size: ${total_size:-0} MB"
    
    # Vérifier les résultats
    if [[ "$database_success" == "true" && "$uploads_success" == "true" && "$config_success" == "true" ]]; then
        local status_message="Backup completed successfully in ${duration}s (${total_size:-0} MB)"
        log "SUCCESS" "$status_message"
        
        if [[ "$s3_success" == "true" ]]; then
            status_message="$status_message - Uploaded to S3"
        fi
        
        send_notification "success" "$status_message"
        exit 0
    else
        local failed_components=()
        [[ "$database_success" == "false" ]] && failed_components+=("database")
        [[ "$uploads_success" == "false" ]] && failed_components+=("uploads")
        [[ "$config_success" == "false" ]] && failed_components+=("config")
        
        local error_message="Backup partially failed. Failed components: ${failed_components[*]}"
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
        echo "Usage: $0 [--help|--dry-run]"
        echo "  --help    Show this help message"
        echo "  --dry-run Simulate backup without actually creating files"
        exit 0
        ;;
    "--dry-run")
        log "INFO" "Running in dry-run mode"
        export DRY_RUN=true
        ;;
    "")
        # Mode normal
        ;;
    *)
        log "ERROR" "Unknown argument: $1"
        exit 1
        ;;
esac

# Exécuter le backup
main "$@" 