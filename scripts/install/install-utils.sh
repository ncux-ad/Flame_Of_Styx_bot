#!/bin/bash
# =============================================================================
# УТИЛИТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

# Функция логирования с временными метками
log() {
    local level="${1:-INFO}"
    local message="${2:-}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Цвета для разных уровней
    case "$level" in
        "ERROR")
            echo -e "\033[31m[$timestamp] ERROR: $message\033[0m" >&2
            ;;
        "WARNING")
            echo -e "\033[33m[$timestamp] WARNING: $message\033[0m" >&2
            ;;
        "SUCCESS")
            echo -e "\033[32m[$timestamp] SUCCESS: $message\033[0m"
            ;;
        "INFO")
            echo -e "\033[36m[$timestamp] INFO: $message\033[0m"
            ;;
        *)
            echo -e "[$timestamp] $level: $message"
            ;;
    esac
}

# Удобные функции для разных уровней логирования
error() { log "ERROR" "$1"; }
warning() { log "WARNING" "$1"; }
success() { log "SUCCESS" "$1"; }
info() { log "INFO" "$1"; }

# Функция проверки прав root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "Этот скрипт должен запускаться с правами root (sudo)"
        exit 1
    fi
}

# Функция проверки зависимостей
check_dependencies() {
    info "Проверка системных зависимостей..."
    
    local missing_deps=()
    
    # Проверяем необходимые команды
    for cmd in git curl wget python3 pip3; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Отсутствуют необходимые зависимости: ${missing_deps[*]}"
        error "Установите их командой: apt install -y ${missing_deps[*]}"
        exit 1
    fi
    
    success "Все зависимости найдены"
}

# Функция валидации входных данных
validate_input() {
    info "Валидация входных данных..."
    
    # Проверяем профиль
    if [ "$PROFILE" != "user" ] && [ "$PROFILE" != "prod" ]; then
        error "Неверный профиль: $PROFILE. Используйте 'user' или 'prod'"
        exit 1
    fi
    
    # Проверяем тип установки
    if [ "$INSTALLATION_TYPE" != "docker" ] && [ "$INSTALLATION_TYPE" != "systemd" ]; then
        error "Неверный тип установки: $INSTALLATION_TYPE. Используйте 'docker' или 'systemd'"
        exit 1
    fi
    
    # Проверяем SSH порт
    if ! [[ "$SSH_PORT" =~ ^[0-9]+$ ]] || [ "$SSH_PORT" -lt 1 ] || [ "$SSH_PORT" -gt 65535 ]; then
        error "Неверный SSH порт: $SSH_PORT. Используйте число от 1 до 65535"
        exit 1
    fi
    
    success "Валидация завершена"
}

# Функция создания директорий
create_directories() {
    local dirs=("$BASE_DIR" "$CONFIG_DIR" "$LOG_DIR")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            info "Создание директории: $dir"
            mkdir -p "$dir"
        fi
    done
}

# Функция установки прав
set_permissions() {
    if [ -n "$RUN_USER" ]; then
        info "Установка прав для пользователя: $RUN_USER"
        chown -R "$RUN_USER:$RUN_USER" "$BASE_DIR"
        chmod -R 755 "$BASE_DIR"
    fi
}

# Функция проверки существования файла
file_exists() {
    local file="$1"
    [ -f "$file" ]
}

# Функция проверки существования директории
dir_exists() {
    local dir="$1"
    [ -d "$dir" ]
}

# Функция безопасного удаления файла
safe_remove() {
    local file="$1"
    if [ -f "$file" ]; then
        info "Удаление файла: $file"
        rm -f "$file"
    fi
}

# Функция безопасного удаления директории
safe_remove_dir() {
    local dir="$1"
    if [ -d "$dir" ]; then
        info "Удаление директории: $dir"
        rm -rf "$dir"
    fi
}

# Функция создания символической ссылки
create_symlink() {
    local target="$1"
    local link="$2"
    
    if [ -L "$link" ]; then
        info "Удаление существующей ссылки: $link"
        rm -f "$link"
    fi
    
    info "Создание символической ссылки: $link -> $target"
    ln -sf "$target" "$link"
}

# Функция проверки статуса сервиса
check_service_status() {
    local service="$1"
    if systemctl is-active --quiet "$service"; then
        return 0
    else
        return 1
    fi
}

# Функция перезапуска сервиса
restart_service() {
    local service="$1"
    info "Перезапуск сервиса: $service"
    systemctl restart "$service"
    systemctl enable "$service"
}

# Функция проверки порта
check_port() {
    local port="$1"
    if netstat -tuln | grep -q ":$port "; then
        return 0
    else
        return 1
    fi
}

# Функция ожидания
wait_for() {
    local condition="$1"
    local timeout="${2:-30}"
    local count=0
    
    while [ $count -lt $timeout ]; do
        if eval "$condition"; then
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    
    return 1
}

# Функция генерации случайного пароля
generate_password() {
    local length="${1:-32}"
    openssl rand -base64 $((length * 3 / 4)) | tr -d "=+/" | cut -c1-"$length"
}

# Функция проверки валидности email
is_valid_email() {
    local email="$1"
    if [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Функция проверки валидности домена
is_valid_domain() {
    local domain="$1"
    if [[ "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
        return 0
    else
        return 1
    fi
}

# Функция проверки валидности Telegram токена
is_valid_bot_token() {
    local token="$1"
    if [[ "$token" =~ ^[0-9]+:[a-zA-Z0-9_-]{35}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Функция проверки валидности Telegram ID
is_valid_telegram_id() {
    local id="$1"
    if [[ "$id" =~ ^-?[0-9]+$ ]]; then
        return 0
    else
        return 1
    fi
}

# Функция форматирования размера файла
format_file_size() {
    local size="$1"
    local units=("B" "KB" "MB" "GB" "TB")
    local unit=0
    
    while [ $size -gt 1024 ] && [ $unit -lt 4 ]; do
        size=$((size / 1024))
        unit=$((unit + 1))
    done
    
    echo "${size}${units[$unit]}"
}

# Функция получения размера директории
get_dir_size() {
    local dir="$1"
    if [ -d "$dir" ]; then
        du -sh "$dir" | cut -f1
    else
        echo "0B"
    fi
}

# Функция очистки временных файлов
cleanup_temp_files() {
    info "Очистка временных файлов..."
    find /tmp -name "install-*" -type f -mtime +1 -delete 2>/dev/null || true
    success "Очистка завершена"
}

# Функция создания резервной копии
create_backup() {
    local source="$1"
    local backup_dir="$2"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_name="backup_$(basename "$source")_$timestamp"
    
    if [ -e "$source" ]; then
        info "Создание резервной копии: $source -> $backup_dir/$backup_name"
        mkdir -p "$backup_dir"
        cp -r "$source" "$backup_dir/$backup_name"
        echo "$backup_dir/$backup_name"
    else
        warning "Источник для резервного копирования не найден: $source"
        return 1
    fi
}

# Функция восстановления из резервной копии
restore_from_backup() {
    local backup_path="$1"
    local target="$2"
    
    if [ -e "$backup_path" ]; then
        info "Восстановление из резервной копии: $backup_path -> $target"
        rm -rf "$target"
        cp -r "$backup_path" "$target"
        success "Восстановление завершено"
    else
        error "Резервная копия не найдена: $backup_path"
        return 1
    fi
}
