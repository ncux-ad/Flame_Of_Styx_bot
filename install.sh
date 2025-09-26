#!/bin/bash
# Главный установочный скрипт для AntiSpam Bot (модульная архитектура)
# Main installation script for AntiSpam Bot (modular architecture)

set -euo pipefail

# =============================================================================
# КОНФИГУРАЦИЯ И ПЕРЕМЕННЫЕ
# =============================================================================

# Версия скрипта
readonly SCRIPT_VERSION="3.0.0"
readonly SCRIPT_NAME="AntiSpam Bot Modular Installer"

# Цвета для вывода
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Пути к модулям
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MODULES_DIR="${SCRIPT_DIR}/scripts/install"

# =============================================================================
# ФУНКЦИИ ЛОГИРОВАНИЯ
# =============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# ФУНКЦИИ ПРОВЕРКИ
# =============================================================================

check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "Не запускайте этот скрипт от root!"
        error "Скрипт автоматически запросит sudo при необходимости"
        exit 1
    fi
}

check_dependencies() {
    local missing_deps=()
    
    for cmd in curl wget git; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "Отсутствуют необходимые зависимости: ${missing_deps[*]}"
        error "Установите их и повторите попытку"
        exit 1
    fi
}

# =============================================================================
# ФУНКЦИИ ЗАГРУЗКИ МОДУЛЕЙ
# =============================================================================

load_module() {
    local module_name="$1"
    local module_path="${MODULES_DIR}/${module_name}"
    
    if [[ -f "$module_path" ]]; then
        log "Загружаем модуль: $module_name"
        source "$module_path"
    else
        error "Модуль не найден: $module_path"
        exit 1
    fi
}

# =============================================================================
# ФУНКЦИИ ОТОБРАЖЕНИЯ
# =============================================================================

show_header() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ANTI-SPAM BOT INSTALLER                   ║"
    echo "║                                                              ║"
    echo "║  🚀 Модульная архитектура v${SCRIPT_VERSION}                        ║"
    echo "║  🛡️  Система защиты от Dependabot                          ║"
    echo "║  🔧 Поддержка Docker и systemd                              ║"
    echo "║  📦 Автоматическая установка зависимостей                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_help() {
    cat << EOF
ИСПОЛЬЗОВАНИЕ:
    $0 [ОПЦИИ]

ОПЦИИ:
    --profile <prod|user>     - Профиль установки (по умолчанию: user)
    --type <docker|systemd>   - Тип установки (по умолчанию: systemd)
    --ssh-port <port>         - SSH порт (по умолчанию: 22)
    --domain <domain>         - Домен для SSL
    --email <email>           - Email для Let's Encrypt
    --bot-token <token>       - Токен бота
    --admin-ids <ids>         - ID администраторов (через запятую)
    --non-interactive         - Неинтерактивный режим
    --dry-run                 - Режим проверки без установки
    --skip-docker             - Пропустить установку Docker
    --base-dir <path>         - Директория установки
    --help                    - Показать эту справку

ПРИМЕРЫ:
    $0                                    # Интерактивная установка
    $0 --profile prod --type docker      # Продакшн с Docker
    $0 --non-interactive --type systemd  # Автоматическая установка
    $0 --dry-run                         # Проверка без установки

ОПИСАНИЕ:
    Модульный установщик AntiSpam Bot с поддержкой различных
    конфигураций и автоматической защитой от проблем с правами доступа.
EOF
}

# =============================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# =============================================================================

main() {
    # Парсинг аргументов
    local PROFILE="user"
    local INSTALLATION_TYPE="systemd"
    local SSH_PORT="22"
    local DOMAIN=""
    local EMAIL=""
    local BOT_TOKEN=""
    local ADMIN_IDS=""
    local NON_INTERACTIVE="false"
    local DRY_RUN="false"
    local SKIP_DOCKER="false"
    local BASE_DIR=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --profile)
                PROFILE="$2"
                shift 2
                ;;
            --type)
                INSTALLATION_TYPE="$2"
                shift 2
                ;;
            --ssh-port)
                SSH_PORT="$2"
                shift 2
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --email)
                EMAIL="$2"
                shift 2
                ;;
            --bot-token)
                BOT_TOKEN="$2"
                shift 2
                ;;
            --admin-ids)
                ADMIN_IDS="$2"
                shift 2
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
                BASE_DIR="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Неизвестная опция: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Экспорт переменных для модулей
    export PROFILE INSTALLATION_TYPE SSH_PORT DOMAIN EMAIL BOT_TOKEN ADMIN_IDS
    export NON_INTERACTIVE DRY_RUN SKIP_DOCKER BASE_DIR
    
    # Проверки
    check_root
    check_dependencies
    
    # Отображение заголовка
    show_header
    
    # Загрузка модулей
    load_module "install-utils.sh"
    load_module "install-config.sh"
    load_module "install-system.sh"
    load_module "install-telegram.sh"
    load_module "install-core.sh"
    
    # Запуск установки
    if [[ "$DRY_RUN" == "true" ]]; then
        info "Режим проверки: установка не будет выполнена"
        # Здесь можно добавить проверки без установки
    else
        info "Начинаем установку AntiSpam Bot..."
        # Основная логика установки будет в install-core.sh
    fi
    
    success "Установка завершена успешно!"
}

# Запуск
main "$@"
