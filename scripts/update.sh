#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"
# Скрипт обновления AntiSpam Bot
# Update script for AntiSpam Bot

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

echo -e "${GREEN}"
echo "🔄 ОБНОВЛЕНИЕ ANTI-SPAM BOT"
echo "=========================="
echo -e "${NC}"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    error "Запустите с правами root: sudo bash update.sh"
    exit 1
fi

# Функция определения типа установки
detect_installation_type() {
    if systemctl is-active --quiet antispam-bot-docker 2>/dev/null; then
        INSTALLATION_TYPE="docker"
        success "Обнаружена Docker установка"
    elif systemctl is-active --quiet antispam-bot 2>/dev/null; then
        INSTALLATION_TYPE="systemd"
        success "Обнаружена systemd установка"
    else
        error "Не удалось определить тип установки"
        exit 1
    fi
}

# Функция создания бэкапа
create_backup() {
    log "Создание бэкапа..."

    BACKUP_DIR="/opt/antispam-bot-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        # Бэкап Docker конфигурации
        cp -r /opt/antispam-bot "$BACKUP_DIR/"
        success "Docker конфигурация сохранена в $BACKUP_DIR"
    else
        # Бэкап systemd конфигурации
        cp -r /opt/antispam-bot "$BACKUP_DIR/"
        cp /etc/systemd/system/antispam-bot.service "$BACKUP_DIR/"
        cp /etc/antispam-bot/.env "$BACKUP_DIR/"
        success "systemd конфигурация сохранена в $BACKUP_DIR"
    fi
}

# Функция обновления Docker версии
update_docker() {
    log "Обновление Docker версии..."

    cd /opt/antispam-bot

    # Остановка сервиса
    systemctl stop antispam-bot-docker

    # Обновление кода
    git fetch origin
    git reset --hard origin/main

    # Обновление образов
    docker-compose -f docker-compose.prod.yml pull

    # Пересборка и запуск
    docker-compose -f docker-compose.prod.yml up -d --build

    # Запуск сервиса
    systemctl start antispam-bot-docker

    success "Docker версия обновлена"
}

# Функция обновления systemd версии
update_systemd() {
    log "Обновление systemd версии..."

    cd /opt/antispam-bot

    # Остановка сервиса
    systemctl stop antispam-bot

    # Обновление кода
    git fetch origin
    git reset --hard origin/main

    # Обновление зависимостей
    /opt/antispam-bot/venv/bin/pip install --upgrade pip
    /opt/antispam-bot/venv/bin/pip install -r requirements.txt

    # Запуск сервиса
    systemctl start antispam-bot

    success "systemd версия обновлена"
}

# Функция проверки статуса
check_status() {
    log "Проверка статуса после обновления..."

    sleep 5

    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        if systemctl is-active --quiet antispam-bot-docker; then
            success "Docker сервис работает"
        else
            error "Docker сервис не работает"
            systemctl status antispam-bot-docker
            return 1
        fi
    else
        if systemctl is-active --quiet antispam-bot; then
            success "systemd сервис работает"
        else
            error "systemd сервис не работает"
            systemctl status antispam-bot
            return 1
        fi
    fi
}

# Функция проверки логов
check_logs() {
    log "Проверка логов..."

    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        echo "Последние логи Docker:"
        docker-compose -f /opt/antispam-bot/docker-compose.prod.yml logs --tail=20
    else
        echo "Последние логи systemd:"
        journalctl -u antispam-bot --tail=20
    fi
}

# Функция отката
rollback() {
    warning "Выполняется откат к предыдущей версии..."

    # Поиск последнего бэкапа
    LATEST_BACKUP=$(ls -t /opt/antispam-bot-backup-* | head -n1)

    if [ -z "$LATEST_BACKUP" ]; then
        error "Бэкап не найден"
        exit 1
    fi

    log "Откат к $LATEST_BACKUP"

    # Остановка сервиса
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        systemctl stop antispam-bot-docker
    else
        systemctl stop antispam-bot
    fi

    # Восстановление из бэкапа
    rm -rf /opt/antispam-bot
    cp -r "$LATEST_BACKUP" /opt/antispam-bot

    # Запуск сервиса
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        systemctl start antispam-bot-docker
    else
        systemctl start antispam-bot
    fi

    success "Откат выполнен"
}

# Функция очистки старых бэкапов
cleanup_backups() {
    log "Очистка старых бэкапов..."

    # Удаление бэкапов старше 7 дней
    find /opt -name "antispam-bot-backup-*" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true

    success "Старые бэкапы удалены"
}

# Функция проверки обновлений
check_updates() {
    log "Проверка доступных обновлений..."

    cd /opt/antispam-bot

    # Получение информации о последнем коммите
    git fetch origin
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)

    if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
        success "У вас уже установлена последняя версия"
        return 1
    else
        warning "Доступно обновление"
        echo "Локальная версия: $LOCAL_COMMIT"
        echo "Удаленная версия: $REMOTE_COMMIT"
        return 0
    fi
}

# Функция показа информации
show_info() {
    echo ""
    success "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ИНФОРМАЦИЯ ОБ ОБНОВЛЕНИИ                ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Тип установки:${NC} $INSTALLATION_TYPE"
    echo -e "${YELLOW}📅 Дата обновления:${NC} $(date)"
    echo -e "${YELLOW}📁 Директория:${NC} /opt/antispam-bot"
    echo ""
    echo -e "${YELLOW}📋 Команды управления:${NC}"
    echo "  antispam-bot status  - Статус бота"
    echo "  antispam-bot logs    - Просмотр логов"
    echo "  antispam-bot restart - Перезапуск бота"
    echo ""
    echo -e "${GREEN}✅ Бот обновлен и готов к работе!${NC}"
    echo ""
}

# Главная функция
main() {
    # Проверка аргументов
    case "${1:-update}" in
        "update")
            detect_installation_type
            create_backup
            if [ "$INSTALLATION_TYPE" = "docker" ]; then
                update_docker
            else
                update_systemd
            fi
            check_status
            cleanup_backups
            show_info
            ;;
        "check")
            detect_installation_type
            if check_updates; then
                echo "Доступно обновление. Запустите: sudo bash update.sh"
            fi
            ;;
        "rollback")
            detect_installation_type
            rollback
            check_status
            ;;
        "logs")
            detect_installation_type
            check_logs
            ;;
        *)
            echo "Использование: $0 {update|check|rollback|logs}"
            echo ""
            echo "  update   - Обновить бота"
            echo "  check    - Проверить доступные обновления"
            echo "  rollback - Откатиться к предыдущей версии"
            echo "  logs     - Показать логи"
            exit 1
            ;;
    esac
}

# Запуск
main "$@"
