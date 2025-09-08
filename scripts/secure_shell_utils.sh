#!/bin/bash
# Secure shell utilities with proper error handling and input validation

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_error "Command failed with exit code $exit_code at line $line_number"
    exit $exit_code
}

# Set error trap
trap 'handle_error $LINENO' ERR

# Input validation functions
validate_domain() {
    local domain="$1"

    if [[ -z "$domain" ]]; then
        log_error "Domain cannot be empty"
        return 1
    fi

    # Check domain format
    if [[ ! "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
        log_error "Invalid domain format: $domain"
        return 1
    fi

    # Check length
    if [[ ${#domain} -gt 253 ]]; then
        log_error "Domain too long: $domain"
        return 1
    fi

    return 0
}

validate_email() {
    local email="$1"

    if [[ -z "$email" ]]; then
        log_error "Email cannot be empty"
        return 1
    fi

    # Basic email validation
    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        log_error "Invalid email format: $email"
        return 1
    fi

    return 0
}

validate_user_id() {
    local user_id="$1"

    if [[ -z "$user_id" ]]; then
        log_error "User ID cannot be empty"
        return 1
    fi

    # Check if it's a positive integer
    if [[ ! "$user_id" =~ ^[1-9][0-9]*$ ]]; then
        log_error "Invalid user ID format: $user_id"
        return 1
    fi

    return 0
}

validate_bot_token() {
    local token="$1"

    if [[ -z "$token" ]]; then
        log_error "Bot token cannot be empty"
        return 1
    fi

    # Check bot token format: number:alphanumeric_string
    if [[ ! "$token" =~ ^[0-9]+:[a-zA-Z0-9_-]+$ ]]; then
        log_error "Invalid bot token format: $token"
        return 1
    fi

    return 0
}

# Safe file operations
safe_create_file() {
    local file_path="$1"
    local content="$2"
    local permissions="${3:-644}"

    # Validate file path
    if [[ -z "$file_path" ]]; then
        log_error "File path cannot be empty"
        return 1
    fi

    # Check for path traversal
    if [[ "$file_path" =~ \.\. ]]; then
        log_error "Path traversal detected in file path: $file_path"
        return 1
    fi

    # Create directory if it doesn't exist
    local dir_path
    dir_path=$(dirname "$file_path")
    if [[ ! -d "$dir_path" ]]; then
        if ! mkdir -p "$dir_path"; then
            log_error "Failed to create directory: $dir_path"
            return 1
        fi
    fi

    # Create file with content
    if ! echo "$content" > "$file_path"; then
        log_error "Failed to create file: $file_path"
        return 1
    fi

    # Set permissions
    if ! chmod "$permissions" "$file_path"; then
        log_error "Failed to set permissions on file: $file_path"
        return 1
    fi

    log_success "Created file: $file_path"
    return 0
}

safe_backup_file() {
    local file_path="$1"
    local backup_dir="${2:-./backups}"

    if [[ ! -f "$file_path" ]]; then
        log_warn "File does not exist, skipping backup: $file_path"
        return 0
    fi

    # Create backup directory
    if ! mkdir -p "$backup_dir"; then
        log_error "Failed to create backup directory: $backup_dir"
        return 1
    fi

    # Create backup filename with timestamp
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$backup_dir/$(basename "$file_path")_$timestamp"

    # Copy file
    if ! cp "$file_path" "$backup_file"; then
        log_error "Failed to backup file: $file_path"
        return 1
    fi

    log_success "Backed up file: $file_path -> $backup_file"
    return 0
}

# Safe command execution
safe_execute() {
    local command="$1"
    local description="${2:-Executing command}"

    log_info "$description: $command"

    if ! eval "$command"; then
        log_error "Command failed: $command"
        return 1
    fi

    log_success "Command completed successfully: $command"
    return 0
}

# Safe Docker operations
safe_docker_exec() {
    local container_name="$1"
    local command="$2"

    # Validate container name
    if [[ -z "$container_name" ]]; then
        log_error "Container name cannot be empty"
        return 1
    fi

    # Check if container exists
    if ! docker ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
        log_error "Container does not exist: $container_name"
        return 1
    fi

    # Execute command
    if ! docker exec "$container_name" sh -c "$command"; then
        log_error "Failed to execute command in container $container_name: $command"
        return 1
    fi

    log_success "Command executed in container $container_name: $command"
    return 0
}

# Safe file reading
safe_read_file() {
    local file_path="$1"
    local max_size="${2:-1048576}"  # 1MB default

    if [[ ! -f "$file_path" ]]; then
        log_error "File does not exist: $file_path"
        return 1
    fi

    # Check file size
    local file_size
    file_size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "0")

    if [[ $file_size -gt $max_size ]]; then
        log_error "File too large: $file_path (${file_size} bytes, max: ${max_size} bytes)"
        return 1
    fi

    # Read file
    cat "$file_path"
    return 0
}

# Safe environment variable handling
safe_get_env() {
    local var_name="$1"
    local default_value="${2:-}"
    local required="${3:-false}"

    local value
    value="${!var_name:-$default_value}"

    if [[ "$required" == "true" && -z "$value" ]]; then
        log_error "Required environment variable not set: $var_name"
        return 1
    fi

    echo "$value"
    return 0
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    # Add cleanup logic here
}

# Set cleanup trap
trap cleanup EXIT

# Export functions for use in other scripts
export -f log_info log_warn log_error log_success
export -f validate_domain validate_email validate_user_id validate_bot_token
export -f safe_create_file safe_backup_file safe_execute safe_docker_exec safe_read_file safe_get_env
