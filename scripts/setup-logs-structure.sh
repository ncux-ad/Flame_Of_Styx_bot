#!/bin/bash

# Скрипт для настройки структуры логов на сервере
# Использование: ./scripts/setup-logs-structure.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав администратора
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Скрипт запущен с правами root. Это может быть небезопасно."
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Создание структуры директорий
create_log_structure() {
    log_info "Создание структуры директорий для логов..."
    
    # Основные директории
    local log_dirs=(
        "/var/log/flame-of-styx"
        "/var/log/flame-of-styx/general"
        "/var/log/flame-of-styx/encrypted"
        "/var/log/flame-of-styx/security"
        "/var/log/flame-of-styx/reports"
        "/opt/flame-of-styx/logs"
        "/opt/flame-of-styx/logs/general"
        "/opt/flame-of-styx/logs/encrypted"
        "/opt/flame-of-styx/logs/security"
        "/opt/flame-of-styx/logs/reports"
    )
    
    for dir in "${log_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            sudo mkdir -p "$dir"
            log_success "Создана директория: $dir"
        else
            log_info "Директория уже существует: $dir"
        fi
    done
}

# Настройка прав доступа
setup_permissions() {
    log_info "Настройка прав доступа для логов..."
    
    # Получаем пользователя бота
    local bot_user="flame-bot"
    if id "$bot_user" &>/dev/null; then
        log_info "Пользователь $bot_user найден"
    else
        log_warning "Пользователь $bot_user не найден. Создаем..."
        sudo useradd -r -s /bin/false -d /opt/flame-of-styx "$bot_user"
        log_success "Создан пользователь $bot_user"
    fi
    
    # Устанавливаем права
    sudo chown -R "$bot_user:$bot_user" /opt/flame-of-styx/logs
    sudo chown -R "$bot_user:$bot_user" /var/log/flame-of-styx
    
    # Права для разных типов логов
    sudo chmod 755 /opt/flame-of-styx/logs
    sudo chmod 755 /var/log/flame-of-styx
    
    # Общие логи - доступны для чтения
    sudo chmod 644 /opt/flame-of-styx/logs/general
    sudo chmod 644 /var/log/flame-of-styx/general
    
    # Зашифрованные логи - только для бота
    sudo chmod 600 /opt/flame-of-styx/logs/encrypted
    sudo chmod 600 /var/log/flame-of-styx/encrypted
    
    # Отчеты безопасности - только для админов
    sudo chmod 640 /opt/flame-of-styx/logs/security
    sudo chmod 640 /var/log/flame-of-styx/security
    
    log_success "Права доступа настроены"
}

# Настройка logrotate
setup_logrotate() {
    log_info "Настройка logrotate для автоматической ротации логов..."
    
    local logrotate_config="/etc/logrotate.d/flame-of-styx"
    
    sudo tee "$logrotate_config" > /dev/null << EOF
# Logrotate configuration for Flame of Styx Bot
/var/log/flame-of-styx/general/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 flame-bot flame-bot
    postrotate
        systemctl reload flame-of-styx-bot || true
    endscript
}

/var/log/flame-of-styx/encrypted/*.log {
    daily
    missingok
    rotate 90
    compress
    delaycompress
    notifempty
    create 600 flame-bot flame-bot
    postrotate
        systemctl reload flame-of-styx-bot || true
    endscript
}

/var/log/flame-of-styx/security/*.log {
    weekly
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 640 flame-bot flame-bot
    postrotate
        systemctl reload flame-of-styx-bot || true
    endscript
}

/opt/flame-of-styx/logs/general/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 flame-bot flame-bot
    postrotate
        systemctl reload flame-of-styx-bot || true
    endscript
}

/opt/flame-of-styx/logs/encrypted/*.log {
    daily
    missingok
    rotate 90
    compress
    delaycompress
    notifempty
    create 600 flame-bot flame-bot
    postrotate
        systemctl reload flame-of-styx-bot || true
    endscript
}

/opt/flame-of-styx/logs/security/*.log {
    weekly
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 640 flame-bot flame-bot
    postrotate
        systemctl reload flame-of-styx-bot || true
    endscript
}
EOF

    log_success "Конфигурация logrotate создана: $logrotate_config"
    
    # Тестируем конфигурацию
    if sudo logrotate -d "$logrotate_config" > /dev/null 2>&1; then
        log_success "Конфигурация logrotate корректна"
    else
        log_error "Ошибка в конфигурации logrotate"
        exit 1
    fi
}

# Создание символических ссылок
create_symlinks() {
    log_info "Создание символических ссылок для удобства..."
    
    # Создаем ссылки в домашней директории проекта
    local project_dir=$(pwd)
    
    if [[ -d "$project_dir/logs" ]]; then
        sudo rm -rf "$project_dir/logs"
    fi
    
    sudo ln -sf /opt/flame-of-styx/logs "$project_dir/logs"
    sudo chown -h "$(whoami):$(whoami)" "$project_dir/logs"
    
    log_success "Созданы символические ссылки"
}

# Настройка мониторинга логов
setup_log_monitoring() {
    log_info "Настройка мониторинга логов..."
    
    # Создаем скрипт для мониторинга
    local monitor_script="/opt/flame-of-styx/scripts/monitor-logs.sh"
    
    sudo mkdir -p "$(dirname "$monitor_script")"
    
    sudo tee "$monitor_script" > /dev/null << 'EOF'
#!/bin/bash

# Скрипт мониторинга логов Flame of Styx Bot
# Проверяет размер логов и отправляет уведомления

LOG_DIR="/var/log/flame-of-styx"
MAX_SIZE_MB=100
ADMIN_EMAIL="admin@example.com"

# Проверяем размер логов
check_log_size() {
    local log_file="$1"
    local size_mb=$(du -m "$log_file" 2>/dev/null | cut -f1)
    
    if [[ $size_mb -gt $MAX_SIZE_MB ]]; then
        echo "WARNING: Log file $log_file is ${size_mb}MB (max: ${MAX_SIZE_MB}MB)"
        # Здесь можно добавить отправку уведомления
        return 1
    fi
    return 0
}

# Проверяем все лог файлы
for log_file in "$LOG_DIR"/*/*.log; do
    if [[ -f "$log_file" ]]; then
        check_log_size "$log_file"
    fi
done

echo "Log monitoring completed at $(date)"
EOF

    sudo chmod +x "$monitor_script"
    
    # Добавляем в crontab
    local cron_job="0 2 * * * $monitor_script >> /var/log/flame-of-styx/monitor.log 2>&1"
    
    if ! sudo crontab -l 2>/dev/null | grep -q "$monitor_script"; then
        (sudo crontab -l 2>/dev/null; echo "$cron_job") | sudo crontab -
        log_success "Добавлена задача в crontab для мониторинга логов"
    else
        log_info "Задача мониторинга логов уже существует в crontab"
    fi
}

# Создание конфигурации для приложения
create_app_config() {
    log_info "Создание конфигурации путей логов для приложения..."
    
    local config_file="/opt/flame-of-styx/logs_config.py"
    
    sudo tee "$config_file" > /dev/null << 'EOF'
"""
Конфигурация путей логов для Flame of Styx Bot
"""

import os
from pathlib import Path

# Определяем окружение
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Базовые пути
if ENVIRONMENT == 'production':
    # Продакшн пути
    LOGS_BASE_DIR = Path('/var/log/flame-of-styx')
    APP_LOGS_DIR = Path('/opt/flame-of-styx/logs')
else:
    # Разработка
    LOGS_BASE_DIR = Path('logs')
    APP_LOGS_DIR = Path('logs')

# Конкретные пути
GENERAL_LOGS_DIR = LOGS_BASE_DIR / 'general'
ENCRYPTED_LOGS_DIR = LOGS_BASE_DIR / 'encrypted'
SECURITY_LOGS_DIR = LOGS_BASE_DIR / 'security'
REPORTS_DIR = LOGS_BASE_DIR / 'reports'

# Создаем директории если не существуют
for dir_path in [GENERAL_LOGS_DIR, ENCRYPTED_LOGS_DIR, SECURITY_LOGS_DIR, REPORTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Настройки ротации
LOG_ROTATION = {
    'general': {
        'max_bytes': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5
    },
    'encrypted': {
        'max_bytes': 50 * 1024 * 1024,  # 50MB
        'backup_count': 10
    },
    'security': {
        'max_bytes': 5 * 1024 * 1024,   # 5MB
        'backup_count': 3
    }
}
EOF

    sudo chmod 644 "$config_file"
    log_success "Конфигурация путей логов создана: $config_file"
}

# Основная функция
main() {
    log_info "Настройка структуры логов для Flame of Styx Bot"
    log_info "================================================"
    
    check_root
    create_log_structure
    setup_permissions
    setup_logrotate
    create_symlinks
    setup_log_monitoring
    create_app_config
    
    log_success "Настройка структуры логов завершена!"
    log_info ""
    log_info "Созданные директории:"
    log_info "  - /var/log/flame-of-styx/ (системные логи)"
    log_info "  - /opt/flame-of-styx/logs/ (логи приложения)"
    log_info "  - logs/ (символическая ссылка для разработки)"
    log_info ""
    log_info "Настроена автоматическая ротация логов через logrotate"
    log_info "Добавлен мониторинг размера логов в crontab"
    log_info ""
    log_info "Для применения изменений перезапустите бота:"
    log_info "  sudo systemctl restart flame-of-styx-bot"
}

# Запуск
main "$@"
