#!/bin/bash
# Главный установочный скрипт для AntiSpam Bot
# Main installation script for AntiSpam Bot

set -euo pipefail

# =============================================================================
# КОНФИГУРАЦИЯ И ПЕРЕМЕННЫЕ
# =============================================================================

# Версия скрипта
readonly SCRIPT_VERSION="2.0.0"
readonly SCRIPT_NAME="AntiSpam Bot Installer"

# Цвета для вывода (без переопределения уже заданных/readonly переменных)
[ -z "${RED+x}" ] && readonly RED='\033[0;31m'
[ -z "${GREEN+x}" ] && readonly GREEN='\033[0;32m'
[ -z "${YELLOW+x}" ] && readonly YELLOW='\033[1;33m'
[ -z "${BLUE+x}" ] && readonly BLUE='\033[0;34m'
[ -z "${PURPLE+x}" ] && readonly PURPLE='\033[0;35m'
[ -z "${CYAN+x}" ] && readonly CYAN='\033[0;36m'
[ -z "${NC+x}" ] && readonly NC='\033[0m' # No Color

# Константы приложения
readonly APP_NAME="antispam-bot"
readonly DEFAULT_SSH_PORT="2022"
readonly DEFAULT_PROFILE="prod"
readonly DEFAULT_INSTALLATION_TYPE="systemd"

# Глобальные переменные
PROFILE="${DEFAULT_PROFILE}"
SSH_PORT="${DEFAULT_SSH_PORT}"
NON_INTERACTIVE="false"
DRY_RUN="false"
SKIP_DOCKER="false"
COMPOSE_CMD="docker compose"
INSTALLATION_TYPE=""
DOMAIN=""
EMAIL=""
BOT_TOKEN=""
ADMIN_IDS=""
CHANNEL_LINKS=""
REDIS_PASSWORD=""
NOTIFICATION_WEBHOOK=""

# Пути (будут установлены в resolve_paths_by_profile)
BASE_DIR=""
CONFIG_DIR=""
LOG_DIR=""
RUN_USER=""
CUSTOM_BASE_DIR=""  # Пользовательская директория установки

# =============================================================================
# УТИЛИТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

# Функция логирования с временными метками
log() {
    local level="${1:-INFO}"
    local message="${2:-}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "ERROR") echo -e "${RED}[ERROR]${NC} $timestamp - $message" >&2 ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $timestamp - $message" >&2 ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $timestamp - $message" ;;
        "INFO") echo -e "${BLUE}[INFO]${NC} $timestamp - $message" ;;
        *) echo -e "${CYAN}[$level]${NC} $timestamp - $message" ;;
    esac
    
    # Записываем в лог файл если он доступен
    if [ -n "${LOG_DIR:-}" ] && [ -d "$LOG_DIR" ]; then
        echo "[$level] $timestamp - $message" >> "${LOG_DIR}/install.log"
    fi
}

# Функции для цветного вывода
error() { log "ERROR" "$1"; }
warning() { log "WARNING" "$1"; }
success() { log "SUCCESS" "$1"; }
info() { log "INFO" "$1"; }

# Функция проверки прав root
check_root() {
if [ "$EUID" -ne 0 ]; then
    error "Этот скрипт должен быть запущен с правами root (sudo)"
        echo "Использование: sudo bash $0"
    exit 1
fi
}

# Функция проверки зависимостей
check_dependencies() {
    local deps=("curl" "wget" "git" "jq" "ufw" "fail2ban" "nginx" "certbot")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        warning "Отсутствуют зависимости: ${missing[*]}"
        info "Они будут установлены автоматически"
    fi
}

# Функция валидации входных данных
validate_input() {
    local errors=()
    
    # Валидация токена бота
    if [ -n "${BOT_TOKEN:-}" ]; then
        if ! [[ "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
            errors+=("Неверный формат BOT_TOKEN")
        fi
    fi
    
    # Валидация email
    if [ -n "${EMAIL:-}" ]; then
        if ! [[ "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            errors+=("Неверный формат EMAIL")
        fi
    fi
    
    # Валидация домена
    if [ -n "${DOMAIN:-}" ]; then
        if ! [[ "$DOMAIN" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]] && [ "$DOMAIN" != "localhost" ]; then
            errors+=("Неверный формат DOMAIN")
        fi
    fi
    
    # Валидация SSH порта
    if ! [[ "$SSH_PORT" =~ ^[0-9]+$ ]] || [ "$SSH_PORT" -lt 1 ] || [ "$SSH_PORT" -gt 65535 ]; then
        errors+=("SSH_PORT должен быть числом от 1 до 65535")
    fi
    
    if [ ${#errors[@]} -gt 0 ]; then
        error "Ошибки валидации:"
        for err in "${errors[@]}"; do
            error "  - $err"
        done
        exit 1
    fi
}

# =============================================================================
# ФУНКЦИИ УСТАНОВКИ
# =============================================================================

# Функция установки системных зависимостей
install_system_dependencies() {
    info "Обновление пакетов и установка зависимостей..."
    
    apt-get update -y

    # Базовые зависимости для всех типов установки
    local base_deps=(
        curl
        wget
        git
        jq
        ufw
        fail2ban
        nginx
        python3
        python3-pip
        python3-venv
        python3-dev
        python3-cffi
        python3-cryptography
        build-essential
        libssl-dev
        libffi-dev
        software-properties-common
        ca-certificates
        gnupg
        lsb-release
    )
    
    # Docker-специфичные зависимости только если нужны
    if [ "$INSTALLATION_TYPE" = "docker" ] && [ "$SKIP_DOCKER" != "true" ]; then
        base_deps+=(
            apt-transport-https
        )
    fi
    
    apt-get install -y "${base_deps[@]}"

    success "Системные зависимости установлены"
}

# Функция установки Docker (только если нужен)
install_docker() {
    # Пропускаем Docker если явно отключен или не нужен
    if [ "$SKIP_DOCKER" = "true" ]; then
        info "Docker пропущен (--skip-docker)"
        return 0
    fi
    
    if [ "$INSTALLATION_TYPE" != "docker" ]; then
        info "Docker не требуется для установки типа: $INSTALLATION_TYPE"
        return 0
    fi
    
    if command -v docker >/dev/null 2>&1; then
        info "Docker уже установлен"
        return 0
    fi
    
    info "Установка Docker..."
    
    # Добавляем официальный GPG ключ Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Добавляем репозиторий Docker
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Обновляем пакеты и устанавливаем Docker
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Запускаем и включаем Docker
    systemctl start docker
    systemctl enable docker

    success "Docker установлен и запущен"
}

# Функция настройки UFW
setup_firewall() {
    info "Настройка файрвола UFW..."
    
    # Сбрасываем правила
    ufw --force reset
    
    # Устанавливаем политики по умолчанию
    ufw default deny incoming
    ufw default allow outgoing
    
    # Разрешаем SSH на указанном порту
    ufw allow "${SSH_PORT}/tcp"
    
    # Разрешаем HTTP и HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Включаем файрвол
    ufw --force enable

    success "Файрвол UFW настроен (SSH порт: $SSH_PORT)"
}

# Функция настройки fail2ban
setup_fail2ban() {
    info "Настройка fail2ban..."
    
    # Создаем конфигурацию fail2ban
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ${SSH_PORT}
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[sshd-${SSH_PORT}]
enabled = true
port = ${SSH_PORT}
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

    # Исправляем совместимость с Python 3.11+
    fix_fail2ban_python3_compatibility
    
    # Перезапускаем fail2ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    success "fail2ban настроен"
}

# Функция исправления совместимости fail2ban с Python 3.11+
fix_fail2ban_python3_compatibility() {
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    if [[ "$python_version" =~ ^3\.(11|12|13)$ ]]; then
        info "Python $python_version обнаружен, создаем патч для fail2ban..."
        
        # Создаем wrapper для fail2ban
        cat > /usr/local/bin/fail2ban-server << 'EOF'
#!/usr/bin/env python3
# Wrapper для fail2ban с патчем для Python 3.11+
import sys
import os
sys.path.insert(0, '/usr/lib/python3/dist-packages')
try:
    from collections import MutableMapping
except ImportError:
    import collections
    import collections.abc
    collections.MutableMapping = collections.abc.MutableMapping
from fail2ban.server import main
if __name__ == '__main__':
    main()
EOF
        
        chmod +x /usr/local/bin/fail2ban-server
        
        # Создаем override для systemd
        mkdir -p /etc/systemd/system/fail2ban.service.d
        cat > /etc/systemd/system/fail2ban.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/local/bin/fail2ban-server -xf start
EOF
        
        systemctl daemon-reload
        success "Патч для fail2ban создан для Python $python_version"
    fi
}

# =============================================================================
# ФУНКЦИИ КОНФИГУРАЦИИ
# =============================================================================

# Функция определения путей по профилю
resolve_paths_by_profile() {
    # Если указана пользовательская директория, используем её
    if [ -n "$CUSTOM_BASE_DIR" ]; then
        BASE_DIR="$CUSTOM_BASE_DIR"
        CONFIG_DIR="${BASE_DIR}/config"
        LOG_DIR="${BASE_DIR}/logs"
        if [ "$PROFILE" = "user" ]; then
            RUN_USER="${SUDO_USER:-$(whoami)}"
        else
            RUN_USER="root"
        fi
        log "Используем пользовательскую директорию: $BASE_DIR"
        return
    fi
    
    if [ "$PROFILE" = "user" ]; then
        local current_user=${SUDO_USER:-$(whoami)}
        local user_home=$(getent passwd "$current_user" | cut -d: -f6)
        
        # Определяем текущую директорию проекта
        local current_dir=$(pwd)
        local project_name=$(basename "$current_dir")
        
        # Если мы в папке с проектом, используем её
        if [ -f "bot.py" ] && [ -f "requirements.txt" ]; then
            BASE_DIR="$current_dir"
            log "Используем текущую директорию проекта: $BASE_DIR"
        else
            # Иначе используем стандартную папку
            BASE_DIR="${user_home}/bots/${project_name}"
            log "Используем стандартную директорию: $BASE_DIR"
        fi
        
        CONFIG_DIR="${BASE_DIR}/config"
        LOG_DIR="${BASE_DIR}/logs"
        RUN_USER="$current_user"
    else
        # Для prod профиля тоже проверяем текущую директорию
        local current_dir=$(pwd)
        local project_name=$(basename "$current_dir")
        
        # Если мы в папке с проектом и это не стандартная папка, используем её
        if [ -f "bot.py" ] && [ -f "requirements.txt" ] && [ "$current_dir" != "/opt/${APP_NAME}" ]; then
            BASE_DIR="$current_dir"
            CONFIG_DIR="${BASE_DIR}/config"
            LOG_DIR="${BASE_DIR}/logs"
            RUN_USER="root"  # Для prod в нестандартной папке используем root
            log "Используем текущую директорию проекта для prod: $BASE_DIR"
        else
            # Иначе используем стандартную папку
            BASE_DIR="/opt/${APP_NAME}"
            CONFIG_DIR="/etc/${APP_NAME}"
            LOG_DIR="/var/log/${APP_NAME}"
            RUN_USER="${APP_NAME}"
            log "Используем стандартную директорию для prod: $BASE_DIR"
        fi
    fi
}

# Функция загрузки существующих переменных из .env
load_existing_env() {
    if [ -f ".env" ]; then
        info "Загрузка существующих переменных из .env..."
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^[[:space:]]*# ]] && [[ -n "$key" ]]; then
                value=$(echo "$value" | sed 's/^"//;s/"$//')
                export "$key"="$value"
            fi
        done < .env
    fi
}

# Функция безопасного обновления .env
update_env_key() {
    local key="$1"
    local value="$2"
    local interactive="${3:-false}"
    
    [ -f .env ] || echo "# Auto-generated by install.sh" > .env
    
    if grep -qE "^${key}=" .env; then
        local current
        current=$(grep -E "^${key}=" .env | sed -E "s/^${key}=//")
        
        if [ -z "$current" ]; then
            sed -i "s|^${key}=.*$|${key}=${value}|" .env
        elif [ "$interactive" = "true" ] && [ "$NON_INTERACTIVE" != "true" ]; then
            echo -e "${YELLOW}Переменная $key уже установлена: $current${NC}"
            echo -e "${CYAN}Новое значение: $value${NC}"
            echo -e "${YELLOW}Заменить? (y/N) [таймер 5 сек]:${NC} "
            if read -t 5 -n 1 response; then
                echo ""
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    info "Обновляем $key: $current -> $value"
                    sed -i "s|^${key}=.*$|${key}=${value}|" .env
                else
                    info "Оставляем $key: $current"
                fi
            else
                echo ""
                info "Таймер истек, оставляем $key: $current"
            fi
        else
            info "Переменная $key уже установлена: $current (оставляем без изменений)"
        fi
    else
        echo "${key}=${value}" >> .env
    fi
}

# Функция создания локального .env файла
create_local_env() {
    info "Создание локального .env файла..."
    
    # Проверяем существующие переменные
    check_existing_env
    
    cat > .env << EOF
# Telegram Bot Configuration
BOT_TOKEN=${BOT_TOKEN}
ADMIN_IDS=${ADMIN_IDS}

# Native Channels (каналы, где бот является администратором)
NATIVE_CHANNEL_IDS=-10000000000

# Database Configuration
DB_PATH=db.sqlite3

# Logging Configuration
LOG_LEVEL=INFO

# Rate Limiting Configuration
RATE_LIMIT=5
RATE_INTERVAL=60

# Optional: Custom Rate Limit Message
RATE_LIMIT_MESSAGE="⏳ Слишком часто пишешь, притормози."

# Additional Configuration
DOMAIN=${DOMAIN}
EMAIL=${EMAIL}
REDIS_PASSWORD=${REDIS_PASSWORD}
NOTIFICATION_WEBHOOK=${NOTIFICATION_WEBHOOK}
EOF
    
    success "Локальный .env файл создан"
}

# Функция проверки существующих переменных в .env
check_existing_env() {
    if [ -f ".env" ]; then
        info "Существующие переменные в .env:"
        grep -E "^(BOT_TOKEN|ADMIN_IDS|DOMAIN|EMAIL|REDIS_PASSWORD|NOTIFICATION_WEBHOOK)=" .env | while read -r line; do
            local key=$(echo "$line" | cut -d'=' -f1)
            local value=$(echo "$line" | cut -d'=' -f2-)
            if [ ${#value} -gt 20 ]; then
                value="${value:0:20}..."
            fi
            info "  $key=$value"
        done
    fi
}

# =============================================================================
# ФУНКЦИИ РАБОТЫ С TELEGRAM API
# =============================================================================

# Функция определения группы комментариев для канала
get_channel_comment_group() {
    local channel_link="$1"
    local bot_token="$2"
    
    if [ -z "$bot_token" ] || [ -z "$channel_link" ]; then
        return 1
    fi
    
    # Очищаем ссылку от @ и https://
    local channel_username=$(echo "$channel_link" | sed 's|https://t.me/||g' | sed 's|@||g' | sed 's|^t.me/||g')
    
    info "Определение группы комментариев для канала: $channel_username" >&2
    
    # Получаем информацию о канале через Telegram Bot API
    local response=$(curl -s "https://api.telegram.org/bot${bot_token}/getChat?chat_id=@${channel_username}")
    
    if echo "$response" | grep -q '"ok":true'; then
        # Извлекаем ID канала более безопасно (только первое совпадение)
        local channel_id=$(echo "$response" | grep -o '"id":[^,}]*' | head -1 | cut -d':' -f2 | tr -d ' "')
        
        if [ -n "$channel_id" ] && [ "$channel_id" != "null" ]; then
            info "ID канала $channel_username: $channel_id" >&2
            
            # Проверяем, есть ли связанная группа комментариев
            if echo "$response" | grep -q '"linked_chat"'; then
                local linked_chat_id=$(echo "$response" | grep -o '"linked_chat":[^,}]*' | head -1 | cut -d':' -f2 | tr -d ' "')
                if [ -n "$linked_chat_id" ] && [ "$linked_chat_id" != "null" ]; then
                    info "Найдена группа комментариев: $linked_chat_id для канала $channel_username" >&2
                    echo "$linked_chat_id"
                    return 0
                fi
            fi
            
            info "Группа комментариев не найдена для канала $channel_username, используем ID канала" >&2
            echo "$channel_id"
            return 0
        else
            error "Не удалось извлечь ID канала $channel_username" >&2
            return 1
        fi
    else
        error "Ошибка получения информации о канале $channel_username" >&2
        error "Ответ API: $response" >&2
        return 1
    fi
}

# Функция обработки каналов и определения групп комментариев
process_channels() {
    if [ -n "${CHANNEL_LINKS:-}" ]; then
        info "Обработка каналов: $CHANNEL_LINKS"
        
        local channel_ids=""
        IFS=',' read -ra CHANNELS <<< "$CHANNEL_LINKS"
        
        for channel in "${CHANNELS[@]}"; do
            # Убираем пробелы
            channel=$(echo "$channel" | xargs)
            
            if [ -n "$channel" ]; then
                info "Обработка канала: $channel"
                
                # Определяем ID канала и группы комментариев
                local channel_info
                channel_info=$(get_channel_comment_group "$channel" "$BOT_TOKEN" 2>/dev/null)
                local result_code=$?
                
                # Убираем лишние пробелы и переносы строк
                channel_info=$(echo "$channel_info" | tr -d '\n\r' | xargs)
                
                info "Результат для канала $channel: код=$result_code, ID='$channel_info'"
                
                if [ $result_code -eq 0 ] && [ -n "$channel_info" ]; then
                    if [ -n "$channel_ids" ]; then
                        channel_ids="${channel_ids},${channel_info}"
                    else
                        channel_ids="$channel_info"
                    fi
                    success "Канал $channel -> ID: $channel_info"
                else
                    warning "Не удалось определить ID для канала: $channel"
                fi
            fi
        done
        
        if [ -n "$channel_ids" ]; then
            info "Обновляем NATIVE_CHANNEL_IDS: $channel_ids"
            update_env_key "NATIVE_CHANNEL_IDS" "$channel_ids"
            success "NATIVE_CHANNEL_IDS обновлен: $channel_ids"
        fi
    fi
}

# =============================================================================
# ФУНКЦИИ УСТАНОВКИ ПРИЛОЖЕНИЯ
# =============================================================================

# Функция установки Python зависимостей
install_python_dependencies() {
    info "Установка Python зависимостей..."
    
    # Создаем виртуальное окружение
    python3 -m venv --upgrade-deps "${BASE_DIR}/venv"
    
    # Устанавливаем права
    chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}/venv"
    
    # Активируем виртуальное окружение и устанавливаем зависимости
    sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install --upgrade pip setuptools
    sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install -r requirements.txt
    
    success "Python зависимости установлены"
}

# Функция установки systemd версии
install_systemd_version() {
    info "Установка через systemd..."
    
    # Создаем директории
    mkdir -p "${BASE_DIR}" "${CONFIG_DIR}" "${LOG_DIR}"
    
    # Копируем файлы если нужно
    if [ "$(pwd)" != "${BASE_DIR}" ]; then
        cp -r . "${BASE_DIR}/"
        chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}"
    else
        warning "Уже находимся в целевой директории ${BASE_DIR}, пропускаем копирование"
        chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}"
    fi
    
    # Устанавливаем Python зависимости
    install_python_dependencies
    
    # Создаем systemd unit файл
    create_systemd_unit
    
    success "Установка через systemd завершена"
}

# Функция создания systemd unit файла
create_systemd_unit() {
    info "Создание systemd unit файла..."
    
    cat > "/etc/systemd/system/${APP_NAME}.service" << EOF
[Unit]
Description=AntiSpam Telegram Bot
After=network.target

[Service]
Type=simple
User=${RUN_USER}
Group=${RUN_USER}
WorkingDirectory=${BASE_DIR}
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${BASE_DIR}/venv/bin
Environment=PYTHONPATH=${BASE_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=${BASE_DIR}/venv/bin/python ${BASE_DIR}/bot.py
Restart=always
RestartSec=10
TimeoutStartSec=30

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=antispam-bot

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    success "Systemd unit файл создан"
}

# =============================================================================
# ФУНКЦИИ КОНФИГУРАЦИИ
# =============================================================================

# Функция получения конфигурации
get_configuration() {
    info "Получение конфигурации..."
    
    # Загружаем существующие переменные
    load_existing_env
    
    # Получаем конфигурацию
    get_domain
    get_email
    get_bot_token
    get_admin_ids
    get_channel_links
    get_redis_password
    get_notification_webhook
    
    # Обрабатываем каналы
    process_channels
    
    # Создаем локальный .env
    create_local_env
    
    success "Конфигурация получена"
}

# Функции получения отдельных параметров
get_domain() {
    if [ -n "${DOMAIN:-}" ]; then
        success "Домен: $DOMAIN (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Домен: $DOMAIN (из аргументов)"
    else
        read -p "Введите домен (например, example.com): " DOMAIN
    fi
}

get_email() {
    if [ -n "${EMAIL:-}" ]; then
        success "Email: $EMAIL (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Email: $EMAIL (из аргументов)"
    else
        read -p "Введите email для Let's Encrypt: " EMAIL
    fi
}

get_bot_token() {
    if [ -n "${BOT_TOKEN:-}" ]; then
        success "Bot Token: ${BOT_TOKEN:0:10}... (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Bot Token: ${BOT_TOKEN:0:10}... (из аргументов)"
    else
        read -p "Введите токен бота: " BOT_TOKEN
    fi
}

get_admin_ids() {
    if [ -n "${ADMIN_IDS:-}" ]; then
        success "Admin IDs: $ADMIN_IDS (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Admin IDs: $ADMIN_IDS (из аргументов)"
    else
        read -p "Введите ID администраторов (через запятую): " ADMIN_IDS
    fi
}

get_channel_links() {
    if [ -n "${CHANNEL_LINKS:-}" ]; then
        success "Channel Links: $CHANNEL_LINKS (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Channel Links: $CHANNEL_LINKS (из аргументов)"
    else
        read -p "Введите ссылки на каналы (через запятую, опционально): " CHANNEL_LINKS
    fi
}

get_redis_password() {
    if [ -n "${REDIS_PASSWORD:-}" ]; then
        success "Redis Password: ${REDIS_PASSWORD:0:10}... (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Redis Password: ${REDIS_PASSWORD:0:10}... (из аргументов)"
    else
        REDIS_PASSWORD=$(openssl rand -base64 32)
        success "Redis Password сгенерирован автоматически"
    fi
}

get_notification_webhook() {
    if [ -n "${NOTIFICATION_WEBHOOK:-}" ]; then
        success "Notification Webhook: ${NOTIFICATION_WEBHOOK:0:50}... (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Notification Webhook: ${NOTIFICATION_WEBHOOK:0:50}... (из аргументов)"
    else
        if [ -n "${BOT_TOKEN:-}" ] && [ -n "${ADMIN_IDS:-}" ]; then
            local first_admin_id=$(echo "$ADMIN_IDS" | cut -d',' -f1)
            NOTIFICATION_WEBHOOK="https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${first_admin_id}&parse_mode=HTML"
            success "Webhook настроен автоматически для админа $first_admin_id"
        else
            read -p "Введите webhook для уведомлений (опционально): " NOTIFICATION_WEBHOOK
        fi
    fi
}

# =============================================================================
# ФУНКЦИИ ЗАВЕРШЕНИЯ УСТАНОВКИ
# =============================================================================

# Функция финализации установки
finalize_installation() {
    info "Финализация установки..."
    
    # Включаем и запускаем сервис
    systemctl enable "${APP_NAME}"
    systemctl start "${APP_NAME}"
    
    # Проверяем статус
    health_check
    
    # Отправляем тестовое уведомление
    send_test_notification
    
    success "Установка завершена успешно!"
}

# Функция проверки здоровья сервиса
health_check() {
    info "Проверка статуса сервиса..."
    
    sleep 5
    
    if systemctl is-active --quiet "${APP_NAME}"; then
        success "Сервис ${APP_NAME} активен"
    else
        error "Сервис ${APP_NAME} неактивен"
        systemctl status "${APP_NAME}"
        return 1
    fi
}

# Функция отправки тестового уведомления
send_test_notification() {
    if [ -n "${NOTIFICATION_WEBHOOK:-}" ] && [[ "$NOTIFICATION_WEBHOOK" =~ https://api.telegram.org ]]; then
        info "Отправка тестового уведомления в Telegram..."
        
        local message="🤖 <b>AntiSpam Bot установлен!</b>%0A%0A"
        message+="📋 <b>Информация об установке:</b>%0A"
        message+="• Профиль: <code>$PROFILE</code>%0A"
        message+="• Тип: <code>$INSTALLATION_TYPE</code>%0A"
        message+="• Домен: <code>$DOMAIN</code>%0A"
        message+="• Директория: <code>$BASE_DIR</code>%0A"
        message+="• SSH порт: <code>$SSH_PORT</code>%0A%0A"
        message+="✅ Бот готов к работе!"
        
        local url="${NOTIFICATION_WEBHOOK}&text=${message}"
        
        if curl -s --max-time 10 "$url" >/dev/null 2>&1; then
            success "Тестовое уведомление отправлено в Telegram"
        else
            warning "Не удалось отправить тестовое уведомление в Telegram"
        fi
    fi
}

# Функция отображения финальной информации
show_final_info() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    УСТАНОВКА ЗАВЕРШЕНА                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📋 Информация об установке:"
    echo "  • Профиль: $PROFILE"
    echo "  • Тип: $INSTALLATION_TYPE"
    echo "  • Домен: $DOMAIN"
    echo "  • Директория: $BASE_DIR"
    echo "  • SSH порт: $SSH_PORT"
    echo ""
    echo "🔧 Управление сервисом:"
    echo "  • Статус: systemctl status $APP_NAME"
    echo "  • Логи: journalctl -u $APP_NAME -f"
    echo "  • Перезапуск: systemctl restart $APP_NAME"
    echo "  • Остановка: systemctl stop $APP_NAME"
    echo ""
    echo "🛡️ Статус сервисов:"
    
    # Проверяем статус сервисов
    if systemctl is-active --quiet "${APP_NAME}"; then
        echo "  ✅ $APP_NAME: активен"
    else
        echo "  ❌ $APP_NAME: неактивен"
    fi
    
    if systemctl is-active --quiet ufw; then
        echo "  ✅ UFW: активен"
    else
        echo "  ❌ UFW: неактивен"
    fi
    
    if systemctl is-active --quiet fail2ban; then
        echo "  ✅ fail2ban: активен"
    else
        echo "  ❌ fail2ban: неактивен"
        warning "Попытка исправления fail2ban..."
        fix_fail2ban_python3_compatibility
        systemctl restart fail2ban
    fi
    
    echo ""
    echo "📁 Файлы конфигурации:"
    echo "  • .env: $BASE_DIR/.env"
    echo "  • Логи: $LOG_DIR/"
    echo "  • Конфиг: $CONFIG_DIR/"
    echo ""
    echo "🌐 Доступ к боту:"
    if [ "$DOMAIN" != "localhost" ] && [ "$DOMAIN" != "127.0.0.1" ]; then
        echo "  • Webhook: https://$DOMAIN/webhook"
    else
        echo "  • Локальный режим (webhook не настроен)"
    fi
    echo ""
    echo "✅ Установка завершена! Бот готов к работе."
}

# =============================================================================
# ФУНКЦИИ ПАРСИНГА АРГУМЕНТОВ
# =============================================================================

# Функция парсинга аргументов командной строки
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --profile)
                PROFILE="$2"
                shift 2
                ;;
            --profile=*)
                PROFILE="${1#*=}"
                shift
                ;;
            --type)
                INSTALLATION_TYPE="$2"
                shift 2
                ;;
            --type=*)
                INSTALLATION_TYPE="${1#*=}"
                shift
                ;;
            --ssh-port)
                SSH_PORT="$2"
                shift 2
                ;;
            --ssh-port=*)
                SSH_PORT="${1#*=}"
                shift
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --domain=*)
                DOMAIN="${1#*=}"
                shift
                ;;
            --email)
                EMAIL="$2"
                shift 2
                ;;
            --email=*)
                EMAIL="${1#*=}"
                shift
                ;;
            --bot-token)
                BOT_TOKEN="$2"
                shift 2
                ;;
            --bot-token=*)
                BOT_TOKEN="${1#*=}"
                shift
                ;;
            --admin-ids)
                ADMIN_IDS="$2"
                shift 2
                ;;
            --admin-ids=*)
                ADMIN_IDS="${1#*=}"
                shift
                ;;
            --channel-links)
                CHANNEL_LINKS="$2"
                shift 2
                ;;
            --channel-links=*)
                CHANNEL_LINKS="${1#*=}"
                shift
                ;;
            --non-interactive)
                NON_INTERACTIVE="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --skip-docker)
                SKIP_DOCKER="true"
                shift
                ;;
            --base-dir)
                CUSTOM_BASE_DIR="$2"
                shift 2
                ;;
            --base-dir=*)
                CUSTOM_BASE_DIR="${1#*=}"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            --version)
                echo "$SCRIPT_NAME v$SCRIPT_VERSION"
                exit 0
                ;;
            *)
                error "Неизвестный аргумент: $1"
                show_help
        exit 1
        ;;
esac
    done
}

# Функция отображения справки
show_help() {
    cat << EOF
$SCRIPT_NAME v$SCRIPT_VERSION

Использование: sudo bash $0 [ОПЦИИ]

ОПЦИИ:
    --profile PROFILE          Профиль установки (prod|user) [по умолчанию: $DEFAULT_PROFILE]
    --type TYPE               Тип установки (systemd|docker) [по умолчанию: $DEFAULT_INSTALLATION_TYPE]
    --ssh-port PORT           SSH порт [по умолчанию: $DEFAULT_SSH_PORT]
    --domain DOMAIN           Домен для Let's Encrypt
    --email EMAIL             Email для Let's Encrypt
    --bot-token TOKEN         Токен Telegram бота
    --admin-ids IDS           ID администраторов (через запятую)
    --channel-links LINKS     Ссылки на каналы (через запятую)
    --non-interactive         Неинтерактивный режим
    --dry-run                 Режим проверки без изменений
    --skip-docker             Пропустить установку Docker (для слабых VPS)
    --base-dir DIR            Указать директорию установки
    --help                    Показать эту справку
    --version                 Показать версию

ПРИМЕРЫ:
    sudo bash $0 --profile=user --type=systemd --domain=example.com --email=admin@example.com
    sudo bash $0 --non-interactive --bot-token=123:ABC --admin-ids=123456789
    sudo bash $0 --skip-docker --type=systemd --domain=example.com --email=admin@example.com
    sudo bash $0 --profile=user --base-dir=/home/user/my-bot --type=systemd
    sudo bash $0 --profile=prod --base-dir=/opt/my-custom-bot --type=systemd
EOF
}

# =============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# =============================================================================

main() {
    # Парсим аргументы в самом начале
    parse_args "$@"
    
    # Показываем заголовок
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ANTI-SPAM BOT INSTALLER                   ║"
    echo "║                                                              ║"
    echo "║  🤖 Автоматическая установка Telegram бота                  ║"
    echo "║  🔐 С поддержкой Let's Encrypt SSL сертификатов             ║"
    echo "║  🐳 Docker и systemd варианты установки                     ║"
    echo "║  🛡️ Встроенная система безопасности                         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Проверяем права root
    check_root
    
    # Проверяем зависимости
    check_dependencies
    
    # Валидируем входные данные
    validate_input
    
    # Определяем пути по профилю
    resolve_paths_by_profile
    
    # Получаем конфигурацию
    get_configuration
    
    # Если dry-run, выходим
    if [ "$DRY_RUN" = "true" ]; then
        info "Режим проверки завершен. Изменения не внесены."
        exit 0
    fi
    
    # Устанавливаем зависимости
    install_system_dependencies
            install_docker
    
    # Настраиваем систему
    setup_firewall
    setup_fail2ban
    
    # Устанавливаем приложение
    case "$INSTALLATION_TYPE" in
        "systemd")
            install_systemd_version
            ;;
        "docker")
            # TODO: Реализовать установку через Docker
            error "Установка через Docker пока не реализована"
            exit 1
            ;;
        *)
            error "Неизвестный тип установки: $INSTALLATION_TYPE"
            exit 1
            ;;
    esac
    
    # Финализируем установку
        finalize_installation

    # Показываем финальную информацию
    show_final_info
}

# Запускаем главную функцию
main "$@"
