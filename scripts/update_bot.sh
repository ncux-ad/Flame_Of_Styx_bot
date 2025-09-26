#!/bin/bash
# =============================================================================
# СКРИПТ ОБНОВЛЕНИЯ ANTI-SPAM BOT
# =============================================================================

# Метаданные скрипта
SCRIPT_NAME="AntiSpam Bot Updater"
SCRIPT_VERSION="2.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Функции логирования
log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
info() { echo -e "${CYAN}[INFO]${NC} $1"; }

# Переменные
BOT_DIR=""
BACKUP_DIR=""
SERVICE_NAME="antispam-bot"
INSTALLATION_TYPE=""

# Функция показа заголовка
show_header() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ANTI-SPAM BOT UPDATER                     ║"
    echo "║                                                              ║"
    echo "║  🔄 Автоматическое обновление бота                          ║"
    echo "║  🛡️ Создание резервных копий                                ║"
    echo "║  🔧 Поддержка Docker и systemd                              ║"
    echo "║  📦 Модульная архитектура (v$SCRIPT_VERSION)                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Функция проверки прав root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "Этот скрипт должен запускаться с правами root (sudo)"
        exit 1
    fi
}

# Функция определения директории бота
detect_bot_directory() {
    info "Определение директории бота..."
    
    # Возможные пути установки
    local possible_paths=(
        "/opt/antispam-bot"
        "/opt/Flame_Of_Styx_bot"
        "$HOME/bots/Flame_Of_Styx_bot"
        "$HOME/bots/antispam-bot"
        "/home/$(whoami)/bots/Flame_Of_Styx_bot"
        "/home/$(whoami)/bots/antispam-bot"
    )
    
    # Добавляем текущую директорию если мы в ней
    if [ -f "bot.py" ] && [ -f "requirements.txt" ]; then
        possible_paths=("$(pwd)" "${possible_paths[@]}")
    fi
    
    for path in "${possible_paths[@]}"; do
        if [ -d "$path" ] && [ -f "$path/bot.py" ] && [ -f "$path/requirements.txt" ]; then
            BOT_DIR="$path"
            BACKUP_DIR="$(dirname "$path")/antispam-bot-backups"
            success "Директория бота найдена: $BOT_DIR"
            return 0
        fi
    done
    
    error "Не удалось найти директорию бота"
    error "Убедитесь, что бот установлен и файлы bot.py и requirements.txt существуют"
    exit 1
}

# Функция определения типа установки
detect_installation_type() {
    info "Определение типа установки..."
    
    if systemctl is-active --quiet "${SERVICE_NAME}-docker" 2>/dev/null; then
        INSTALLATION_TYPE="docker"
        success "Обнаружена Docker установка"
    elif systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        INSTALLATION_TYPE="systemd"
        success "Обнаружена systemd установка"
    else
        error "Не удалось определить тип установки"
        error "Убедитесь, что бот установлен и запущен"
        exit 1
    fi
}

# Функция проверки существования директории бота
check_bot_directory() {
    if [ ! -d "$BOT_DIR" ]; then
        error "Директория бота не найдена: $BOT_DIR"
        error "Убедитесь, что бот был установлен"
        exit 1
    fi
    
    if [ ! -f "$BOT_DIR/bot.py" ]; then
        error "Файл bot.py не найден в $BOT_DIR"
        error "Убедитесь, что это правильная директория бота"
        exit 1
    fi
    
    success "Директория бота найдена: $BOT_DIR"
}

# Функция создания резервной копии
create_backup() {
    info "Создание резервной копии..."
    
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_path="$BACKUP_DIR/backup-$timestamp"
    
    # Создаем директорию для бэкапов
    mkdir -p "$BACKUP_DIR"
    
    # Создаем бэкап
    cp -r "$BOT_DIR" "$backup_path"
    
    # Сохраняем конфигурацию
    if [ "$INSTALLATION_TYPE" = "systemd" ]; then
        cp "/etc/systemd/system/$SERVICE_NAME.service" "$backup_path/" 2>/dev/null || true
        cp "/etc/$SERVICE_NAME/.env" "$backup_path/" 2>/dev/null || true
    fi
    
    success "Резервная копия создана: $backup_path"
    echo "$backup_path"
}

# Функция проверки доступных обновлений
check_updates() {
    info "Проверка доступных обновлений..."
    
    cd "$BOT_DIR"
    
    # Получаем информацию о последнем коммите
    if ! git fetch origin 2>/dev/null; then
        error "Ошибка при получении обновлений из git"
        warning "Возможно, нужно настроить git safe.directory:"
        warning "git config --global --add safe.directory $BOT_DIR"
        return 1
    fi
    
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse origin/master)
    
    if [ "$local_commit" = "$remote_commit" ]; then
        success "У вас уже установлена последняя версия"
        return 1
    else
        warning "Доступно обновление"
        info "Локальная версия: $local_commit"
        info "Удаленная версия: $remote_commit"
        return 0
    fi
}

# Функция остановки сервиса
stop_service() {
    info "Остановка сервиса..."
    
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        systemctl stop "${SERVICE_NAME}-docker" || true
    else
        systemctl stop "$SERVICE_NAME" || true
    fi
    
    # Ждем остановки
    sleep 3
    
    success "Сервис остановлен"
}

# Функция исправления прав доступа
fix_permissions() {
    info "Исправление прав доступа..."
    
    if [ ! -d "$BOT_DIR" ]; then
        error "Директория бота не найдена: $BOT_DIR"
        return 1
    fi
    
    # Определяем правильного пользователя
    local bot_user=$(stat -c '%U' "$BOT_DIR" 2>/dev/null)
    local bot_group=$(stat -c '%G' "$BOT_DIR" 2>/dev/null)
    
    # Если не удалось определить, пробуем найти по systemd сервису
    if [ -z "$bot_user" ] || [ -z "$bot_group" ]; then
        if systemctl is-active --quiet antispam-bot.service 2>/dev/null; then
            bot_user=$(systemctl show -p User --value antispam-bot.service 2>/dev/null || echo "")
            bot_group=$(systemctl show -p Group --value antispam-bot.service 2>/dev/null || echo "")
        fi
    fi
    
    # Если все еще не определено, используем текущего пользователя
    if [ -z "$bot_user" ] || [ -z "$bot_group" ]; then
        bot_user=$(whoami)
        bot_group=$(id -gn)
    fi
    
    # Исправляем права на всю директорию
    chown -R "$bot_user:$bot_group" "$BOT_DIR" 2>/dev/null || true
    
    # Устанавливаем правильные права на файлы
    chmod -R 755 "$BOT_DIR" 2>/dev/null || true
    chmod 600 "$BOT_DIR/.env" 2>/dev/null || true
    
    success "Права доступа исправлены для пользователя: $bot_user"
}

# Функция обновления кода
update_code() {
    info "Обновление кода..."
    
    cd "$BOT_DIR"
    
    # Сохраняем локальные изменения
    git stash push -m "Auto-stash before update $(date)" || true
    
    # Получаем обновления
    if ! git fetch origin 2>/dev/null; then
        error "Ошибка при получении обновлений из git"
        warning "Возможно, нужно настроить git safe.directory:"
        warning "git config --global --add safe.directory $BOT_DIR"
        return 1
    fi
    
    if ! git reset --hard origin/master 2>/dev/null; then
        error "Ошибка при обновлении кода"
        return 1
    fi
    
    # Восстанавливаем права доступа
    info "Восстановление прав доступа..."
    
    # Определяем правильного пользователя
    local bot_user=$(stat -c '%U' "$BOT_DIR" 2>/dev/null)
    local bot_group=$(stat -c '%G' "$BOT_DIR" 2>/dev/null)
    
    # Если не удалось определить, пробуем найти по systemd сервису
    if [ -z "$bot_user" ] || [ -z "$bot_group" ]; then
        if systemctl is-active --quiet antispam-bot.service 2>/dev/null; then
            bot_user=$(systemctl show -p User --value antispam-bot.service 2>/dev/null || echo "")
            bot_group=$(systemctl show -p Group --value antispam-bot.service 2>/dev/null || echo "")
        fi
    fi
    
    # Если все еще не определено, используем текущего пользователя
    if [ -z "$bot_user" ] || [ -z "$bot_group" ]; then
        bot_user=$(whoami)
        bot_group=$(id -gn)
    fi
    
    # Исправляем права на всю директорию
    chown -R "$bot_user:$bot_group" "$BOT_DIR" 2>/dev/null || true
    
    # Устанавливаем правильные права на файлы
    chmod -R 755 "$BOT_DIR" 2>/dev/null || true
    chmod 600 "$BOT_DIR/.env" 2>/dev/null || true
    
    success "Права доступа восстановлены для пользователя: $bot_user"
    
    success "Код обновлен"
}

# Функция обновления зависимостей
update_dependencies() {
    info "Обновление зависимостей..."
    
    if [ "$INSTALLATION_TYPE" = "systemd" ]; then
        # Обновляем Python зависимости
        "$BOT_DIR/venv/bin/pip" install --upgrade pip
        "$BOT_DIR/venv/bin/pip" install -r "$BOT_DIR/requirements.txt"
        success "Python зависимости обновлены"
    elif [ "$INSTALLATION_TYPE" = "docker" ]; then
        # Обновляем Docker образы
        cd "$BOT_DIR"
        docker-compose -f docker-compose.prod.yml pull
        success "Docker образы обновлены"
    fi
}

# Функция запуска сервиса
start_service() {
    info "Запуск сервиса..."
    
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        cd "$BOT_DIR"
        docker-compose -f docker-compose.prod.yml up -d --build
        systemctl start "${SERVICE_NAME}-docker"
    else
        systemctl start "$SERVICE_NAME"
    fi
    
    success "Сервис запущен"
}

# Функция проверки статуса
check_status() {
    info "Проверка статуса сервиса..."
    
    sleep 5
    
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        if systemctl is-active --quiet "${SERVICE_NAME}-docker"; then
            success "Docker сервис работает"
        else
            error "Docker сервис не работает"
            systemctl status "${SERVICE_NAME}-docker" --no-pager
            return 1
        fi
    else
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            success "systemd сервис работает"
        else
            error "systemd сервис не работает"
            systemctl status "$SERVICE_NAME" --no-pager
            return 1
        fi
    fi
}

# Функция проверки логов
check_logs() {
    info "Проверка логов..."
    
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        echo "Последние логи Docker:"
        docker-compose -f "$BOT_DIR/docker-compose.prod.yml" logs --tail=20
    else
        echo "Последние логи systemd:"
        journalctl -u "$SERVICE_NAME" --tail=20 --no-pager
    fi
}

# Функция отката
rollback() {
    warning "Выполняется откат к предыдущей версии..."
    
    # Поиск последнего бэкапа
    local latest_backup=$(ls -t "$BACKUP_DIR"/backup-* 2>/dev/null | head -n1)
    
    if [ -z "$latest_backup" ]; then
        error "Резервная копия не найдена"
        exit 1
    fi
    
    info "Откат к $latest_backup"
    
    # Останавливаем сервис
    stop_service
    
    # Восстанавливаем из бэкапа
    rm -rf "$BOT_DIR"
    cp -r "$latest_backup" "$BOT_DIR"
    
    # Запускаем сервис
    start_service
    
    success "Откат выполнен"
}

# Функция очистки старых бэкапов
cleanup_backups() {
    info "Очистка старых резервных копий..."
    
    # Удаляем бэкапы старше 7 дней
    find "$BACKUP_DIR" -name "backup-*" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
    
    success "Старые резервные копии удалены"
}

# Функция показа информации
show_info() {
    echo ""
    success "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ИНФОРМАЦИЯ ОБ ОБНОВЛЕНИИ                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Тип установки:${NC} $INSTALLATION_TYPE"
    echo -e "${YELLOW}📅 Дата обновления:${NC} $(date)"
    echo -e "${YELLOW}📁 Директория:${NC} $BOT_DIR"
    echo -e "${YELLOW}💾 Резервные копии:${NC} $BACKUP_DIR"
    echo ""
    echo -e "${YELLOW}📋 Команды управления:${NC}"
    echo "  sudo systemctl status $SERVICE_NAME     - Статус бота"
    echo "  sudo journalctl -u $SERVICE_NAME -f     - Просмотр логов"
    echo "  sudo systemctl restart $SERVICE_NAME    - Перезапуск бота"
    echo "  sudo systemctl stop $SERVICE_NAME       - Остановка бота"
    echo ""
    echo -e "${GREEN}✅ Бот обновлен и готов к работе!${NC}"
    echo ""
}

# Функция показа справки
show_help() {
    cat << EOF
ИСПОЛЬЗОВАНИЕ:
    $0 [КОМАНДА]

КОМАНДЫ:
    update           - Обновить бота (по умолчанию)
    check            - Проверить доступные обновления
    rollback         - Откатиться к предыдущей версии
    logs             - Показать логи
    status           - Показать статус сервиса
    fix-permissions  - Исправить права доступа к файлам
    cleanup          - Очистить старые резервные копии
    help             - Показать эту справку

ПРИМЕРЫ:
    sudo $0                    # Обновить бота
    sudo $0 check             # Проверить обновления
    sudo $0 rollback          # Откатиться к предыдущей версии
    sudo $0 logs              # Показать логи
    sudo $0 status            # Показать статус
    sudo $0 fix-permissions   # Исправить права доступа

ОПИСАНИЕ:
    Скрипт автоматически определяет тип установки (Docker/systemd)
    и выполняет соответствующее обновление с созданием резервных копий.
EOF
}

# Главная функция
main() {
    show_header
    
    # Проверяем права root
    check_root
    
    # Определяем директорию бота
    detect_bot_directory
    
    # Настраиваем git для работы с директорией (исправляем ошибку dubious ownership)
    if [ -n "$BOT_DIR" ] && [ -d "$BOT_DIR" ]; then
        git config --global --add safe.directory "$BOT_DIR" 2>/dev/null || true
    fi
    
    # Определяем тип установки
    detect_installation_type
    
    # Проверяем директорию бота
    check_bot_directory
    
    # Обрабатываем команды
    case "${1:-update}" in
        "update")
            info "Начинаем обновление..."
            
            # Проверяем обновления
            if ! check_updates; then
                info "Обновления не требуются"
                exit 0
            fi
            
            # Создаем резервную копию
            create_backup
            
            # Останавливаем сервис
            stop_service
            
            # Обновляем код
            update_code
            
            # Обновляем зависимости
            update_dependencies
            
            # Запускаем сервис
            start_service
            
            # Проверяем статус
            check_status
            
            # Очищаем старые бэкапы
            cleanup_backups
            
            # Показываем информацию
            show_info
            ;;
        "check")
            check_updates
            ;;
        "rollback")
            rollback
            check_status
            ;;
        "logs")
            check_logs
            ;;
        "status")
            check_status
            ;;
        "cleanup")
            cleanup_backups
            ;;
        "fix-permissions")
            fix_permissions
            ;;
        "help")
            show_help
            ;;
        *)
            error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

# Запуск
main "$@"
