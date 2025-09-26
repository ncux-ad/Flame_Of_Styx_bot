#!/bin/bash
# Главный установочный скрипт для AntiSpam Bot
# Main installation script for AntiSpam Bot

set -euo pipefail

# Load secure utilities
source "$(dirname "$0")/scripts/secure_shell_utils.sh"

# Цвета для вывода (без переопределения уже заданных/readonly переменных)
[ -z "${RED+x}" ] && RED='\033[0;31m'
[ -z "${GREEN+x}" ] && GREEN='\033[0;32m'
[ -z "${YELLOW+x}" ] && YELLOW='\033[1;33m'
[ -z "${BLUE+x}" ] && BLUE='\033[0;34m'
[ -z "${PURPLE+x}" ] && PURPLE='\033[0;35m'
[ -z "${CYAN+x}" ] && CYAN='\033[0;36m'
[ -z "${NC+x}" ] && NC='\033[0m' # No Color

# Профиль установки и стандартные пути (prod | user)
PROFILE="prod"
APP_NAME="antispam-bot"
BASE_DIR="/opt/${APP_NAME}"
CONFIG_DIR="/etc/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
RUN_USER="${APP_NAME}"
# Параметры по умолчанию
SSH_PORT="2022"
NON_INTERACTIVE="false"
COMPOSE_CMD="docker compose"
INSTALLATION_TYPE=""
DOMAIN=""
EMAIL=""
BOT_TOKEN=""
ADMIN_IDS=""

resolve_paths_by_profile() {
    if [ "$PROFILE" = "user" ]; then
        local current_user=${SUDO_USER:-$(whoami)}
        # Используем домашнюю директорию пользователя, а не root
        local user_home=$(getent passwd "$current_user" | cut -d: -f6)
        BASE_DIR="${user_home}/bots/Flame_Of_Styx_bot"
        CONFIG_DIR="${BASE_DIR}/config"
        LOG_DIR="${BASE_DIR}/logs"
        RUN_USER="$current_user"
    else
        BASE_DIR="/opt/${APP_NAME}"
        CONFIG_DIR="/etc/${APP_NAME}"
        LOG_DIR="/var/log/${APP_NAME}"
        RUN_USER="${APP_NAME}"
    fi
}

# Определение docker compose команды
detect_compose() {
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    else
        warning "docker compose не найден. Будет установлен плагин compose."
        apt-get update -y && apt-get install -y docker-compose-plugin || true
        if docker compose version >/dev/null 2>&1; then
            COMPOSE_CMD="docker compose"
        elif command -v docker-compose >/dev/null 2>&1; then
            COMPOSE_CMD="docker-compose"
        else
            error "Не удалось найти docker compose после установки"
        fi
    fi
}

# Парсинг аргументов CLI
parse_args() {
    for arg in "$@"; do
        case "$arg" in
            --profile=*) PROFILE="${arg#*=}" ;;
            --type=*) INSTALLATION_TYPE="${arg#*=}" ;;
            --ssh-port=*) SSH_PORT="${arg#*=}" ;;
            --domain=*) DOMAIN="${arg#*=}" ;;
            --email=*) EMAIL="${arg#*=}" ;;
            --bot-token=*) BOT_TOKEN="${arg#*=}" ;;
            --admin-ids=*) ADMIN_IDS="${arg#*=}" ;;
            --non-interactive) NON_INTERACTIVE="true" ;;
            --dry-run) DRY_RUN="true" ;;
        esac
    done
}

# Логирование в файл
setup_logging() {
    mkdir -p "${LOG_DIR}"
    # Перенаправляем вывод в лог и на экран
    exec > >(tee -a "${LOG_DIR}/install.log") 2>&1
}

# Функции логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Заголовок
clear
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ANTI-SPAM BOT INSTALLER                   ║"
echo "║                                                              ║"
echo "║  🤖 Автоматическая установка Telegram бота                  ║"
echo "║  🔐 С поддержкой Let's Encrypt SSL сертификатов             ║"
echo "║  🐳 Docker и systemd варианты установки                     ║"
echo "║  🛡️ Встроенная система безопасности                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Парсинг аргументов CLI
parse_args "$@"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    error "Этот скрипт должен быть запущен с правами root (sudo)"
    echo "Использование: sudo bash install.sh"
    exit 1
fi

# Функция выбора варианта установки
choose_installation_type() {
    echo ""
    info "Выберите тип установки:"
    echo ""
    echo "1) 🐳 Docker (рекомендуется)"
    echo "   - Простая установка и управление"
    echo "   - Автоматическое обновление"
    echo "   - Изоляция сервисов"
    echo ""
    echo "2) ⚙️  systemd (прямая установка)"
    echo "   - Прямая установка на систему"
    echo "   - Больше контроля"
    echo "   - Меньше ресурсов"
    echo ""
    echo "3) 🔧 Только настройка окружения"
    echo "   - Установка зависимостей"
    echo "   - Настройка системы"
    echo "   - Без установки бота"
    echo ""

    if [ "$NON_INTERACTIVE" = "true" ] && [ -n "${INSTALLATION_TYPE:-}" ]; then
        success "Выбран тип установки: $INSTALLATION_TYPE (из аргументов)"
        return
    fi

    while true; do
        read -p "Введите номер варианта (1-3): " choice
        case $choice in
            1)
                INSTALLATION_TYPE="docker"
                success "Выбран Docker вариант установки"
                break
                ;;
            2)
                INSTALLATION_TYPE="systemd"
                success "Выбран systemd вариант установки"
                break
                ;;
            3)
                INSTALLATION_TYPE="env"
                success "Выбрана настройка только окружения"
                break
                ;;
            *)
                error "Неверный выбор. Введите 1, 2 или 3"
                ;;
        esac
    done
}

# Выбор профиля установки (prod/user)
choose_profile() {
    echo ""
    info "Выберите профиль установки:"
    echo ""
    echo "1) 🏭 prod (в /opt,/etc,/var/log; пользователь ${APP_NAME})"
    echo "2) 👤 user (в домашней директории: ~/bots/Flame_Of_Styx_bot)"
    echo ""
    if [ "$NON_INTERACTIVE" = "true" ] && [ -n "${PROFILE:-}" ]; then
        success "Выбран профиль: $PROFILE (из аргументов)"
        resolve_paths_by_profile
        return
    fi

    while true; do
        read -p "Введите номер варианта (1-2): " pchoice
        case $pchoice in
            1)
                PROFILE="prod"
                success "Выбран профиль: prod"
                break
                ;;
            2)
                PROFILE="user"
                success "Выбран профиль: user"
                break
                ;;
            *)
                error "Неверный выбор. Введите 1 или 2"
                ;;
        esac
    done
    resolve_paths_by_profile
}

# Функция загрузки существующих переменных из .env
load_existing_env() {
    if [ -f ".env" ]; then
        log "Загрузка существующих переменных из .env..."
        
        # Загружаем переменные из .env
        while IFS='=' read -r key value; do
            # Убираем комментарии и пустые строки
            if [[ ! "$key" =~ ^[[:space:]]*# ]] && [[ -n "$key" ]]; then
                # Убираем кавычки из значения
                value=$(echo "$value" | sed 's/^"//;s/"$//')
                export "$key"="$value"
                log "Загружена переменная: $key"
            fi
        done < .env
    fi
}

# Функция определения группы комментариев для канала
get_channel_comment_group() {
    local channel_link="$1"
    local bot_token="$2"
    
    if [ -z "$bot_token" ] || [ -z "$channel_link" ]; then
        return 1
    fi
    
    # Очищаем ссылку от @ и https://
    local channel_username=$(echo "$channel_link" | sed 's|https://t.me/||g' | sed 's|@||g' | sed 's|^t.me/||g')
    
    # Логируем в stderr, чтобы не попало в stdout
    log "Определение группы комментариев для канала: $channel_username" >&2
    
    # Получаем информацию о канале через Telegram Bot API
    local response=$(curl -s "https://api.telegram.org/bot${bot_token}/getChat?chat_id=@${channel_username}")
    
    if echo "$response" | grep -q '"ok":true'; then
        # Извлекаем ID канала более безопасно (только первое совпадение)
        local channel_id=$(echo "$response" | grep -o '"id":[^,}]*' | head -1 | cut -d':' -f2 | tr -d ' "')
        
        if [ -n "$channel_id" ] && [ "$channel_id" != "null" ]; then
            log "ID канала $channel_username: $channel_id" >&2
            
            # Проверяем, есть ли связанная группа комментариев
            if echo "$response" | grep -q '"linked_chat"'; then
                local linked_chat_id=$(echo "$response" | grep -o '"linked_chat":[^,}]*' | head -1 | cut -d':' -f2 | tr -d ' "')
                if [ -n "$linked_chat_id" ] && [ "$linked_chat_id" != "null" ]; then
                    log "Найдена группа комментариев: $linked_chat_id для канала $channel_username" >&2
                    echo "$linked_chat_id"
                    return 0
                fi
            fi
            
            log "Группа комментариев не найдена для канала $channel_username, используем ID канала" >&2
            echo "$channel_id"
            return 0
        else
            log "Не удалось извлечь ID канала $channel_username" >&2
            return 1
        fi
    else
        log "Ошибка получения информации о канале $channel_username" >&2
        log "Ответ API: $response" >&2
        return 1
    fi
}

# Функция обработки каналов и определения групп комментариев
process_channels() {
    if [ -n "${CHANNEL_LINKS:-}" ]; then
        log "Обработка каналов: $CHANNEL_LINKS"
        
        local channel_ids=""
        IFS=',' read -ra CHANNELS <<< "$CHANNEL_LINKS"
        
        for channel in "${CHANNELS[@]}"; do
            # Убираем пробелы
            channel=$(echo "$channel" | xargs)
            
            if [ -n "$channel" ]; then
                log "Обработка канала: $channel"
                
                # Определяем ID канала и группы комментариев
                local channel_info
                channel_info=$(get_channel_comment_group "$channel" "$BOT_TOKEN" 2>/dev/null)
                local result_code=$?
                
                # Убираем лишние пробелы и переносы строк
                channel_info=$(echo "$channel_info" | tr -d '\n\r' | xargs)
                
                log "Результат для канала $channel: код=$result_code, ID='$channel_info'"
                
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
            # Обновляем NATIVE_CHANNEL_IDS
            update_env_key "NATIVE_CHANNEL_IDS" "$channel_ids"
            success "Обновлены NATIVE_CHANNEL_IDS: $channel_ids"
        fi
    fi
}

# Функция получения конфигурации
get_configuration() {
    echo ""
    info "Настройка конфигурации:"
    echo ""

    # Сначала загружаем существующие переменные
    load_existing_env

    # Домен
    if [ -n "${DOMAIN:-}" ]; then
        success "Домен: $DOMAIN (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Домен: $DOMAIN (из аргументов)"
    else
        while true; do
            read -p "Введите домен (например: bot.example.com): " DOMAIN
            if [ -n "$DOMAIN" ] && [[ "$DOMAIN" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                success "Домен: $DOMAIN"
                break
            else
                error "Неверный формат домена. Попробуйте снова."
            fi
        done
    fi

    # Email
    if [ -n "${EMAIL:-}" ]; then
        success "Email: $EMAIL (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Email: $EMAIL (из аргументов)"
    else
        while true; do
            read -p "Введите email для Let's Encrypt: " EMAIL
            if [ -n "$EMAIL" ] && [[ "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                success "Email: $EMAIL"
                break
            else
                error "Неверный формат email. Попробуйте снова."
            fi
        done
    fi

    # Bot Token
    if [ -n "${BOT_TOKEN:-}" ]; then
        success "Bot Token: ${BOT_TOKEN:0:10}... (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Bot Token: ${BOT_TOKEN:0:10}... (из аргументов)"
    else
        while true; do
            read -p "Введите Telegram Bot Token: " BOT_TOKEN
            if [ -n "$BOT_TOKEN" ] && [[ "$BOT_TOKEN" =~ ^[0-9]+:[a-zA-Z0-9_-]+$ ]]; then
                success "Bot Token: ${BOT_TOKEN:0:10}..."
                break
            else
                error "Неверный формат Bot Token. Формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            fi
        done
    fi

    # Admin IDs
    if [ -n "${ADMIN_IDS:-}" ]; then
        success "Admin IDs: $ADMIN_IDS (из .env)"
    elif [ "$NON_INTERACTIVE" = "true" ]; then
        success "Admin IDs: $ADMIN_IDS (из аргументов)"
    else
        read -p "Введите Admin IDs через запятую (например: 123456789,987654321): " ADMIN_IDS
        if [ -z "$ADMIN_IDS" ]; then
            ADMIN_IDS="123456789"
            warning "Используется Admin ID по умолчанию: $ADMIN_IDS"
        fi
        success "Admin IDs: $ADMIN_IDS"
    fi

    # Каналы бота (опционально)
    if [ -z "${CHANNEL_LINKS:-}" ]; then
        read -p "Введите ссылки/юзернеймы каналов (через запятую, опционально): " CHANNEL_LINKS
    else
        success "Каналы: $CHANNEL_LINKS (из .env)"
    fi

    # Дополнительные настройки
    echo ""
    info "Дополнительные настройки:"

    if [ -z "${REDIS_PASSWORD:-}" ]; then
        read -p "Введите пароль для Redis (по умолчанию: random): " REDIS_PASSWORD
        if [ -z "$REDIS_PASSWORD" ]; then
            REDIS_PASSWORD=$(openssl rand -base64 32)
            success "Сгенерирован случайный пароль Redis"
        fi
    else
        success "Redis пароль: ${REDIS_PASSWORD:0:10}... (из .env)"
    fi

    if [ -z "${NOTIFICATION_WEBHOOK:-}" ]; then
        read -p "Введите webhook для уведомлений (опционально): " NOTIFICATION_WEBHOOK
        if [ -n "$NOTIFICATION_WEBHOOK" ]; then
            success "Webhook: $NOTIFICATION_WEBHOOK"
        else
            # По умолчанию отправляем уведомления админу через Telegram Bot API
            ADMIN_FIRST_ID=$(echo "$ADMIN_IDS" | cut -d',' -f1 | xargs)
            NOTIFICATION_WEBHOOK="https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${ADMIN_FIRST_ID}&parse_mode=HTML"
            success "Webhook (по умолчанию Telegram админу ${ADMIN_FIRST_ID})"
        fi
    else
        success "Webhook: ${NOTIFICATION_WEBHOOK:0:50}... (из .env)"
    fi

    # Обработка каналов и определение групп комментариев
    process_channels

    # Создание локального .env файла
    create_local_env
}

# Утилита безопасной записи переменных в .env (не перезаписывает непустые)
set_env_default() {
    local key="$1"
    local value="$2"
    local interactive="${3:-false}"

    [ -f .env ] || {
        echo "# Auto-generated by install.sh" > .env
    }

    if grep -qE "^${key}=" .env; then
        local current
        current=$(grep -E "^${key}=" .env | sed -E "s/^${key}=//")
        if [ -z "$current" ]; then
            sed -i "s|^${key}=.*$|${key}=${value}|" .env
        elif [ "$interactive" = "true" ] && [ "$NON_INTERACTIVE" != "true" ]; then
            # Интерактивный режим с таймером
            echo -e "${YELLOW}Переменная $key уже установлена: $current${NC}"
            echo -e "${CYAN}Новое значение: $value${NC}"
            echo -e "${YELLOW}Заменить? (y/N) [таймер 5 сек]:${NC} "
            
            # Таймер 5 секунд
            if read -t 5 -n 1 response; then
                echo ""
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    log "Обновляем $key: $current -> $value"
                    sed -i "s|^${key}=.*$|${key}=${value}|" .env
                else
                    log "Оставляем $key: $current"
                fi
            else
                echo ""
                log "Таймер истек, оставляем $key: $current"
            fi
        else
            # Неинтерактивный режим - оставляем существующее значение
            log "Переменная $key уже установлена: $current (оставляем без изменений)"
        fi
    else
        echo "${key}=${value}" >> .env
    fi
}

# Функция проверки существующих переменных в .env
check_existing_env() {
    if [ -f ".env" ]; then
        log "Обнаружен существующий .env файл"
        
        # Показываем существующие важные переменные
        local important_vars=("BOT_TOKEN" "ADMIN_IDS" "DOMAIN" "EMAIL" "NOTIFICATION_WEBHOOK")
        local found_vars=()
        
        for var in "${important_vars[@]}"; do
            if grep -qE "^${var}=" .env; then
                local value=$(grep -E "^${var}=" .env | sed -E "s/^${var}=//")
                if [ -n "$value" ] && [ "$value" != "" ]; then
                    found_vars+=("$var")
                    if [ "$var" = "BOT_TOKEN" ]; then
                        echo -e "  ${GREEN}✅ $var: ${value:0:10}...${NC}"
                    else
                        echo -e "  ${GREEN}✅ $var: $value${NC}"
                    fi
                fi
            fi
        done
        
        if [ ${#found_vars[@]} -gt 0 ]; then
            echo -e "${YELLOW}Найдено ${#found_vars[@]} существующих переменных${NC}"
            echo -e "${CYAN}При обновлении будет предложено подтвердить изменения${NC}"
        fi
    else
        log "Файл .env не найден, будет создан новый"
    fi
}

# Функция создания/обновления локального .env файла
create_local_env() {
    log "Создание/обновление локального .env файла..."
    
    # Проверяем существующие переменные
    check_existing_env

    # Основные переменные (интерактивные)
    set_env_default "BOT_TOKEN" "$BOT_TOKEN" "true"
    set_env_default "ADMIN_IDS" "$ADMIN_IDS" "true"

    # Значения по умолчанию для базовых настроек (неинтерактивные)
    set_env_default "NATIVE_CHANNEL_IDS" "-10000000000"
    set_env_default "DB_PATH" "db.sqlite3"
    set_env_default "LOG_LEVEL" "INFO"
    set_env_default "RATE_LIMIT" "5"
    set_env_default "RATE_INTERVAL" "60"
    set_env_default "RATE_LIMIT_MESSAGE" "\xE2\x8F\xB3 Слишком часто пишешь, притормози."

    # Дополнительно (интерактивные)
    set_env_default "DOMAIN" "$DOMAIN" "true"
    set_env_default "EMAIL" "$EMAIL" "true"
    set_env_default "REDIS_PASSWORD" "$REDIS_PASSWORD" "true"
    set_env_default "NOTIFICATION_WEBHOOK" "$NOTIFICATION_WEBHOOK" "true"

    success "Локальный .env обновлён (существующие значения сохранены)"
}

# Обновление/установка значения ключа в .env (безусловно)
update_env_key() {
    local key="$1"
    local value="$2"
    [ -f .env ] || echo "# Auto-generated by install.sh" > .env
    
    # Создаем временный файл для безопасной замены
    local temp_file=$(mktemp)
    
    if grep -qE "^${key}=" .env; then
        # Заменяем существующую строку
        grep -v "^${key}=" .env > "$temp_file"
        echo "${key}=${value}" >> "$temp_file"
        mv "$temp_file" .env
    else
        # Добавляем новую строку
        echo "${key}=${value}" >> .env
    fi
}

# Разрешение каналов в ID по Bot API
resolve_native_channels() {
    [ -z "${CHANNEL_LINKS:-}" ] && return 0

    local IFS=','
    local ids=()
    for raw in $CHANNEL_LINKS; do
        local t=$(echo "$raw" | xargs)
        [ -z "$t" ] && continue
        # Нормализуем
        if echo "$t" | grep -qE '^https?://t\.me/'; then
            t=$(echo "$t" | sed -E 's#^https?://t\.me/##; s#/$##')
        fi
        if echo "$t" | grep -qE '^@'; then
            t=${t#@}
        fi

        if echo "$t" | grep -qE '^-?100[0-9]+'; then
            ids+=("$t")
        else
            # Разрешаем @username через getChat
            local resp
            resp=$(curl -s --max-time 10 "https://api.telegram.org/bot${BOT_TOKEN}/getChat?chat_id=@${t}" || true)
            local cid
            cid=$(echo "$resp" | grep -oE '"id"[[:space:]]*:[[:space:]]*-?[0-9]+' | head -1 | grep -oE '-?[0-9]+' || true)
            if [ -n "$cid" ]; then
                ids+=("$cid")
                success "Канал @${t} -> ${cid}"
            else
                warning "Не удалось определить ID канала: ${t}. Убедитесь, что бот имеет доступ или указан публичный @username."
            fi
        fi
    done

    if [ ${#ids[@]} -gt 0 ]; then
        local joined
        joined=$(IFS=','; echo "${ids[*]}")
        update_env_key "NATIVE_CHANNEL_IDS" "$joined"
        success "NATIVE_CHANNEL_IDS обновлён: $joined"
    fi
}

# Функция установки зависимостей
install_dependencies() {
    log "Установка системных зависимостей..."

    # Обновление пакетов
    apt-get update -y

    # Установка базовых пакетов
    apt-get install -y \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        htop \
        nano \
        vim \
        ufw \
        fail2ban \
        logrotate \
        cron \
        openssl \
        dnsutils \
        net-tools

    success "Системные зависимости установлены"
}

# Функция установки Docker
install_docker() {
    log "Установка Docker..."

    # Удаление старых версий
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Установка Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Запуск Docker
    systemctl enable docker
    systemctl start docker

    # Добавление пользователя в группу docker
    usermod -aG docker $SUDO_USER

    success "Docker установлен и запущен"
}

# Функция установки Python и зависимостей
install_python() {
    log "Установка Python и зависимостей..."

    # Установка Python
    apt-get install -y python3 python3-pip python3-venv python3-dev

    # Установка дополнительных пакетов
    apt-get install -y \
        build-essential \
        libssl-dev \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        libjpeg-dev \
        libpng-dev \
        libfreetype6-dev \
        python3-cffi \
        python3-cryptography

    success "Python и зависимости установлены"
}

# Функция настройки системы
setup_system() {
    log "Настройка системы..."

    # Настройка файрвола
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow ${SSH_PORT}/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable

    # Настройка fail2ban
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[sshd-custom]
enabled = true
port = ${SSH_PORT}
logpath = /var/log/auth.log
maxretry = 3
EOF

    # Исправление совместимости fail2ban с Python 3.11+
    fix_fail2ban_python3_compatibility
    
    systemctl enable fail2ban
    systemctl start fail2ban

    # Настройка logrotate
    cat > /etc/logrotate.d/antispam-bot << EOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ${APP_NAME} ${APP_NAME}
    postrotate
        systemctl reload antispam-bot 2>/dev/null || true
    endscript
}
EOF

    # Пользователь/директории по профилю
    if [ "$PROFILE" = "prod" ]; then
        if ! id "$APP_NAME" &>/dev/null; then
            useradd -r -s /bin/bash -d "/opt/$APP_NAME" -m "$APP_NAME"
            success "Создан пользователь $APP_NAME"
        fi
    fi

    mkdir -p "$BASE_DIR" "$LOG_DIR" "$CONFIG_DIR"

    if [ "$PROFILE" = "prod" ]; then
        chown -R "$APP_NAME:$APP_NAME" "$BASE_DIR" "$LOG_DIR" "$CONFIG_DIR"
    else
        current_user=${SUDO_USER:-$(whoami)}
        chown -R "$current_user:$current_user" "$BASE_DIR" "$LOG_DIR" "$CONFIG_DIR"
    fi

    success "Система настроена"
}

# Функция установки через Docker
install_docker_version() {
    log "Установка через Docker..."

    detect_compose

    # Создание конфигурации
    cat > "${BASE_DIR}/.env.prod" << EOF
# Production Environment Variables
DOMAIN=$DOMAIN
EMAIL=$EMAIL
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
DB_PATH=db.sqlite3
REDIS_PASSWORD=$REDIS_PASSWORD
NOTIFICATION_WEBHOOK=$NOTIFICATION_WEBHOOK
RENEWAL_THRESHOLD=30
EOF

    # Создание docker-compose.prod.yml
    cp docker-compose.prod.yml "${BASE_DIR}/"

    # Создание systemd сервиса
    cat > /etc/systemd/system/antispam-bot-docker.service << EOF
[Unit]
Description=AntiSpam Bot Docker Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${BASE_DIR}
ExecStart=/usr/bin/env ${COMPOSE_CMD} -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/env ${COMPOSE_CMD} -f docker-compose.prod.yml down
TimeoutStartSec=0
User=${RUN_USER}
Group=${RUN_USER}

[Install]
WantedBy=multi-user.target
EOF

    # Создание скрипта обновления
    cat > "${BASE_DIR}/update.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
git pull origin main
${COMPOSE_CMD} -f docker-compose.prod.yml pull
${COMPOSE_CMD} -f docker-compose.prod.yml up -d --build
EOF

    chmod +x "${BASE_DIR}/update.sh"

    # Создание cron задачи для обновления
    echo "0 3 * * * ${BASE_DIR}/update.sh >> ${LOG_DIR}/update.log 2>&1" | crontab -u ${RUN_USER} -

    success "Docker версия установлена"
}

# Функция установки через systemd
install_systemd_version() {
    log "Установка через systemd..."

    # Копирование файлов (исключая целевую директорию)
    if [ "$(pwd)" != "${BASE_DIR}" ]; then
        cp -r . "${BASE_DIR}/"
        chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}"
    else
        warning "Уже находимся в целевой директории ${BASE_DIR}, пропускаем копирование"
        chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}"
    fi

    # Создание виртуального окружения
    sudo -u ${RUN_USER} python3 -m venv --upgrade-deps "${BASE_DIR}/venv"
    chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}/venv" || true
    sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install -r "${BASE_DIR}/requirements.txt"

    # Создание конфигурации
    cat > "${CONFIG_DIR}/.env" << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
DB_PATH=${BASE_DIR}/db.sqlite3
REDIS_PASSWORD=$REDIS_PASSWORD
NOTIFICATION_WEBHOOK=$NOTIFICATION_WEBHOOK
EOF

    # Создание systemd сервиса
    cat > /etc/systemd/system/antispam-bot.service << EOF
[Unit]
Description=AntiSpam Bot Service
After=network.target

[Service]
Type=simple
User=${RUN_USER}
Group=${RUN_USER}
WorkingDirectory=${BASE_DIR}
Environment=PATH=${BASE_DIR}/venv/bin
EnvironmentFile=${CONFIG_DIR}/.env
ExecStart=${BASE_DIR}/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=antispam-bot

[Install]
WantedBy=multi-user.target
EOF

    # Создание скрипта обновления
    cat > "${BASE_DIR}/update.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
git pull origin main
"$(pwd)"/venv/bin/pip install -r requirements.txt
systemctl restart antispam-bot
EOF

    chmod +x "${BASE_DIR}/update.sh"

    # Создание cron задачи для обновления
    echo "0 3 * * * ${BASE_DIR}/update.sh >> ${LOG_DIR}/update.log 2>&1" | crontab -u ${RUN_USER} -

    success "systemd версия установлена"
}

# Функция настройки Let's Encrypt
setup_letsencrypt() {
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        log "Настройка Let's Encrypt для Docker..."

        # Запуск nginx для получения сертификатов
        cd ${BASE_DIR}
        ${COMPOSE_CMD} -f docker-compose.prod.yml up -d nginx

        # Ожидание запуска nginx
        sleep 10

        # Получение сертификатов
        ${COMPOSE_CMD} -f docker-compose.prod.yml run --rm certbot /scripts/certbot-init.sh

        # Запуск всех сервисов
        ${COMPOSE_CMD} -f docker-compose.prod.yml up -d

    elif [ "$INSTALLATION_TYPE" = "systemd" ]; then
        log "Настройка Let's Encrypt для systemd..."

        # Проверка, что виртуальное окружение существует
        if [ ! -f "${BASE_DIR}/venv/bin/activate" ]; then
            error "Виртуальное окружение не найдено в ${BASE_DIR}/venv"
            return 1
        fi

        # Установка certbot в виртуальное окружение бота
        sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install --upgrade pip
        sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install certbot certbot-nginx
        
        # Создание символической ссылки для certbot из venv
        ln -sf "${BASE_DIR}/venv/bin/certbot" /usr/bin/certbot

        # Получение сертификатов (только для реальных доменов)
        if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != "127.0.0.1" ]]; then
            log "Попытка получения SSL сертификата для $DOMAIN..."
            if certbot certonly --webroot -w /var/www/html -d $DOMAIN --email $EMAIL --agree-tos --non-interactive; then
                success "SSL сертификат получен для $DOMAIN"
            else
                warning "Не удалось получить SSL сертификат для $DOMAIN, продолжаем без SSL"
            fi
        else
            warning "Пропускаем SSL для localhost/127.0.0.1"
        fi

        # Настройка nginx
        apt-get install -y nginx
        
        # Проверяем, есть ли SSL сертификат
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            # Конфигурация с SSL
            cat > /etc/nginx/sites-available/antispam-bot << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
        else
            # Конфигурация без SSL
            cat > /etc/nginx/sites-available/antispam-bot << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
        fi

        ln -sf /etc/nginx/sites-available/antispam-bot /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        nginx -t && systemctl reload nginx

        # Настройка автообновления сертификатов (только если есть SSL)
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            echo "0 2 * * * certbot renew --quiet && systemctl reload nginx" | crontab -
        fi
    fi

    success "Let's Encrypt настроен"
}

# Функция исправления совместимости fail2ban с Python 3.11+
fix_fail2ban_python3_compatibility() {
    log "Проверка совместимости fail2ban с Python..."
    
    # Проверяем версию Python
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log "Версия Python: $python_version"
    
    # Если Python 3.11+, создаем патч
    if [[ "$python_version" == "3.11" || "$python_version" == "3.12" || "$python_version" == "3.13" ]]; then
        log "Python $python_version обнаружен, создаем патч для fail2ban..."
        
        # Создаем wrapper скрипт для fail2ban
        cat > /usr/local/bin/fail2ban-server << 'EOF'
#!/usr/bin/env python3
# Wrapper для fail2ban с патчем для Python 3.11+
import sys
import os
sys.path.insert(0, '/usr/lib/python3/dist-packages')

# Применяем патч для совместимости
try:
    from collections import MutableMapping
except ImportError:
    # В Python 3.11+ MutableMapping перемещен в collections.abc
    import collections
    import collections.abc
    collections.MutableMapping = collections.abc.MutableMapping

# Запускаем fail2ban
from fail2ban.server import main
if __name__ == '__main__':
    main()
EOF
        
        chmod +x /usr/local/bin/fail2ban-server
        
        # Создаем systemd override
        mkdir -p /etc/systemd/system/fail2ban.service.d
        cat > /etc/systemd/system/fail2ban.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/local/bin/fail2ban-server -xf start
EOF
        
        # Перезагружаем systemd
        systemctl daemon-reload
        
        success "Патч для fail2ban создан для Python $python_version"
    else
        log "Python $python_version не требует патча для fail2ban"
    fi
}

# Функция проверки здоровья сервиса
health_check() {
    local service_name="$1"
    local max_attempts=30
    local attempt=1
    
    log "Проверка здоровья сервиса $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if systemctl is-active --quiet "$service_name"; then
            success "Сервис $service_name активен"
            return 0
        fi
        
        if [ $attempt -eq 1 ]; then
            log "Ожидание запуска сервиса $service_name... (попытка $attempt/$max_attempts)"
        else
            echo -n "."
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error "Сервис $service_name не запустился за $((max_attempts * 2)) секунд"
    systemctl status "$service_name" --no-pager
    return 1
}

# Функция отправки тестового уведомления
send_test_notification() {
    if [ -n "${NOTIFICATION_WEBHOOK:-}" ] && [[ "$NOTIFICATION_WEBHOOK" =~ https://api.telegram.org ]]; then
        log "Отправка тестового уведомления в Telegram..."
        
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

# Функция финальной настройки
finalize_installation() {
    log "Финальная настройка..."

    # Включение сервисов
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        systemctl enable antispam-bot-docker
        systemctl start antispam-bot-docker
        health_check "antispam-bot-docker"
    elif [ "$INSTALLATION_TYPE" = "systemd" ]; then
        systemctl enable antispam-bot
        systemctl start antispam-bot
        health_check "antispam-bot"
    fi

    # Создание скрипта управления
    cat > /usr/local/bin/antispam-bot << 'EOF'
#!/bin/bash
case "$1" in
    start)
        systemctl start antispam-bot-docker 2>/dev/null || systemctl start antispam-bot
        ;;
    stop)
        systemctl stop antispam-bot-docker 2>/dev/null || systemctl stop antispam-bot
        ;;
    restart)
        systemctl restart antispam-bot-docker 2>/dev/null || systemctl restart antispam-bot
        ;;
    status)
        systemctl status antispam-bot-docker 2>/dev/null || systemctl status antispam-bot
        ;;
    logs)
        journalctl -u antispam-bot-docker -f 2>/dev/null || journalctl -u antispam-bot -f
        ;;
    update)
        /opt/antispam-bot/update.sh
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF

    chmod +x /usr/local/bin/antispam-bot

    # Отправка тестового уведомления в Telegram
    send_test_notification

    # Проверка статуса сервиса
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        if systemctl is-active --quiet antispam-bot-docker; then
            success "Docker сервис antispam-bot-docker запущен"
        else
            warning "Docker сервис antispam-bot-docker не запущен"
        fi
    elif [ "$INSTALLATION_TYPE" = "systemd" ]; then
        if systemctl is-active --quiet antispam-bot; then
            success "Systemd сервис antispam-bot запущен"
        else
            warning "Systemd сервис antispam-bot не запущен"
        fi
    fi

    success "Установка завершена"
}

# Функция вывода информации
show_final_info() {
    echo ""
    success "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ИНФОРМАЦИЯ ОБ УСТАНОВКЕ                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}🌐 Домен:${NC} $DOMAIN"
    echo -e "${CYAN}📧 Email:${NC} $EMAIL"
    echo -e "${CYAN}🤖 Bot Token:${NC} ${BOT_TOKEN:0:10}..."
    echo -e "${CYAN}👑 Admin IDs:${NC} $ADMIN_IDS"
    echo -e "${CYAN}🔧 Тип установки:${NC} $INSTALLATION_TYPE"
    echo ""
    echo -e "${YELLOW}📋 Команды управления:${NC}"
    echo "  antispam-bot start    - Запуск бота"
    echo "  antispam-bot stop     - Остановка бота"
    echo "  antispam-bot restart  - Перезапуск бота"
    echo "  antispam-bot status   - Статус бота"
    echo "  antispam-bot logs     - Просмотр логов"
    echo "  antispam-bot update   - Обновление бота"
    echo ""
    
    # Проверка статуса сервисов
    echo -e "${YELLOW}🔍 Статус сервисов:${NC}"
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        if systemctl is-active --quiet antispam-bot-docker; then
            echo -e "  ${GREEN}✅ antispam-bot-docker: активен${NC}"
        else
            echo -e "  ${RED}❌ antispam-bot-docker: неактивен${NC}"
        fi
    elif [ "$INSTALLATION_TYPE" = "systemd" ]; then
        if systemctl is-active --quiet antispam-bot; then
            echo -e "  ${GREEN}✅ antispam-bot: активен${NC}"
        else
            echo -e "  ${RED}❌ antispam-bot: неактивен${NC}"
        fi
    fi
    
    # Проверка UFW и fail2ban
    if systemctl is-active --quiet ufw; then
        echo -e "  ${GREEN}✅ UFW: активен${NC}"
    else
        echo -e "  ${RED}❌ UFW: неактивен${NC}"
    fi
    
    if systemctl is-active --quiet fail2ban; then
        echo -e "  ${GREEN}✅ fail2ban: активен${NC}"
    else
        echo -e "  ${RED}❌ fail2ban: неактивен${NC}"
        echo -e "  ${YELLOW}🔧 Попытка исправления совместимости fail2ban...${NC}"
        fix_fail2ban_python3_compatibility
        systemctl restart fail2ban
        if systemctl is-active --quiet fail2ban; then
            echo -e "  ${GREEN}✅ fail2ban: исправлен и запущен${NC}"
        else
            echo -e "  ${RED}❌ fail2ban: не удалось исправить${NC}"
        fi
    fi
    
    echo ""
    echo -e "${YELLOW}🔗 Полезные ссылки:${NC}"
    echo "  https://$DOMAIN - Веб-интерфейс"
    echo "  $BASE_DIR - Директория бота"
    echo "  $LOG_DIR - Логи бота"
    echo "  $CONFIG_DIR - Конфигурация бота"
    echo ""
    
    # Информация о виртуальном окружении
    if [ -f "${BASE_DIR}/venv/bin/activate" ]; then
        echo -e "${YELLOW}🐍 Виртуальное окружение:${NC}"
        echo "  Активация: source ${BASE_DIR}/venv/bin/activate"
        echo "  Python: ${BASE_DIR}/venv/bin/python"
        echo "  Pip: ${BASE_DIR}/venv/bin/pip"
        echo ""
    fi
    
    # Информация о патчах
    if [ -f "/usr/local/bin/fail2ban-server" ]; then
        echo -e "${YELLOW}🔧 Примененные патчи:${NC}"
        echo "  fail2ban: исправлена совместимость с Python 3.11+"
        echo "  Wrapper: /usr/local/bin/fail2ban-server"
        echo ""
    fi
    
    echo -e "${GREEN}✅ Бот готов к работе!${NC}"
    echo ""
}

# Главная функция
main() {
    choose_installation_type
    choose_profile
    get_configuration
    setup_logging
    install_dependencies

    if [ "$INSTALLATION_TYPE" != "env" ]; then
        install_python
        setup_system

        if [ "$INSTALLATION_TYPE" = "docker" ]; then
            install_docker
            install_docker_version
        elif [ "$INSTALLATION_TYPE" = "systemd" ]; then
            install_systemd_version
        fi

        setup_letsencrypt
        finalize_installation
    fi

    show_final_info
}

# Запуск
main "$@"
