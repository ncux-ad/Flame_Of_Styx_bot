#!/bin/bash
# =============================================================================
# ANTI-SPAM BOT INSTALLER - РЕФАКТОРЕННАЯ ВЕРСИЯ
# =============================================================================

# Метаданные скрипта
SCRIPT_NAME="AntiSpam Bot Installer"
SCRIPT_VERSION="2.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULES_DIR="${SCRIPT_DIR}/scripts/install"

# =============================================================================
# КОНФИГУРАЦИЯ И ПЕРЕМЕННЫЕ
# =============================================================================

# Основные настройки
APP_NAME="antispam-bot"
PROFILE="prod"
INSTALLATION_TYPE="systemd"
SSH_PORT="22"
DRY_RUN="false"
NON_INTERACTIVE="false"
SKIP_DOCKER="false"

# Конфигурация бота
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
# ЗАГРУЗКА МОДУЛЕЙ
# =============================================================================

# Функция загрузки модуля
load_module() {
    local module="$1"
    local module_path="${MODULES_DIR}/${module}"
    
    if [ -f "$module_path" ]; then
        source "$module_path"
        log "Модуль загружен: $module"
    else
        error "Модуль не найден: $module_path"
        exit 1
    fi
}

# Загружаем все модули
load_module "install-utils.sh"
load_module "install-config.sh"
load_module "install-system.sh"
load_module "install-telegram.sh"
load_module "install-core.sh"

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
            --redis-password)
                REDIS_PASSWORD="$2"
                shift 2
                ;;
            --redis-password=*)
                REDIS_PASSWORD="${1#*=}"
                shift
                ;;
            --notification-webhook)
                NOTIFICATION_WEBHOOK="$2"
                shift 2
                ;;
            --notification-webhook=*)
                NOTIFICATION_WEBHOOK="${1#*=}"
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
                show_version
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
    echo "║  📦 Модульная архитектура (v$SCRIPT_VERSION)                        ║"
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
    
    # Настраиваем систему
    setup_system
    
    # Устанавливаем приложение
    install_application
    
    # Завершаем установку
    finalize_installation
    
    # Показываем финальную информацию
    show_final_info
    
    # Очищаем временные файлы
    cleanup
}

# Запускаем главную функцию
main "$@"
