#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"
# Скрипт удаления AntiSpam Bot
# Uninstall script for AntiSpam Bot

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

echo -e "${RED}"
echo "🗑️  УДАЛЕНИЕ ANTI-SPAM BOT"
echo "========================="
echo -e "${NC}"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    error "Запустите с правами root: sudo bash uninstall.sh"
    exit 1
fi

# Функция подтверждения
confirm() {
    echo ""
    warning "⚠️  ВНИМАНИЕ! Это действие удалит AntiSpam Bot и все связанные данные!"
    echo ""
    echo "Будут удалены:"
    echo "  - Все файлы бота"
    echo "  - База данных"
    echo "  - Логи"
    echo "  - Конфигурация"
    echo "  - systemd сервисы"
    echo "  - Docker контейнеры (если используется Docker)"
    echo ""
    read -p "Вы уверены, что хотите продолжить? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        success "Удаление отменено"
        exit 0
    fi
}

# Функция определения типа установки
detect_installation_type() {
    if systemctl is-active --quiet antispam-bot-docker 2>/dev/null; then
        INSTALLATION_TYPE="docker"
        success "Обнаружена Docker установка"
    elif systemctl is-active --quiet antispam-bot 2>/dev/null; then
        INSTALLATION_TYPE="systemd"
        success "Обнаружена systemd установка"
    else
        warning "Не удалось определить тип установки"
        INSTALLATION_TYPE="unknown"
    fi
}

# Функция остановки сервисов
stop_services() {
    log "Остановка сервисов..."

    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        systemctl stop antispam-bot-docker 2>/dev/null || true
        systemctl disable antispam-bot-docker 2>/dev/null || true
    elif [ "$INSTALLATION_TYPE" = "systemd" ]; then
        systemctl stop antispam-bot 2>/dev/null || true
        systemctl disable antispam-bot 2>/dev/null || true
    fi

    success "Сервисы остановлены"
}

# Функция удаления Docker контейнеров
remove_docker_containers() {
    log "Удаление Docker контейнеров..."

    if [ -d "/opt/antispam-bot" ]; then
        cd /opt/antispam-bot
        docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
    fi

    # Удаление образов
    docker images | grep antispam | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

    success "Docker контейнеры удалены"
}

# Функция удаления systemd сервисов
remove_systemd_services() {
    log "Удаление systemd сервисов..."

    # Удаление сервисов
    rm -f /etc/systemd/system/antispam-bot.service
    rm -f /etc/systemd/system/antispam-bot-docker.service

    # Перезагрузка systemd
    systemctl daemon-reload

    success "systemd сервисы удалены"
}

# Функция удаления файлов
remove_files() {
    log "Удаление файлов..."

    # Удаление основных файлов
    rm -rf /opt/antispam-bot
    rm -rf /var/log/antispam-bot
    rm -rf /etc/antispam-bot

    # Удаление скрипта управления
    rm -f /usr/local/bin/antispam-bot

    # Удаление cron задач
    crontab -u antispam -r 2>/dev/null || true

    success "Файлы удалены"
}

# Функция удаления пользователя
remove_user() {
    log "Удаление пользователя antispam..."

    # Удаление пользователя
    userdel -r antispam 2>/dev/null || true

    success "Пользователь удален"
}

# Функция удаления nginx конфигурации
remove_nginx_config() {
    log "Удаление nginx конфигурации..."

    # Удаление конфигурации nginx
    rm -f /etc/nginx/sites-available/antispam-bot
    rm -f /etc/nginx/sites-enabled/antispam-bot

    # Перезапуск nginx
    systemctl reload nginx 2>/dev/null || true

    success "nginx конфигурация удалена"
}

# Функция удаления Let's Encrypt сертификатов
remove_letsencrypt() {
    log "Удаление Let's Encrypt сертификатов..."

    # Удаление сертификатов (только для нашего домена)
    if [ -n "$DOMAIN" ]; then
        certbot delete --cert-name "$DOMAIN" --non-interactive --agree-tos 2>/dev/null || true
    else
        log "⚠️  Домен не указан, пропускаем удаление сертификатов"
    fi

    success "Let's Encrypt сертификаты удалены"
}

# Функция удаления Docker (опционально)
remove_docker() {
    echo ""
    read -p "Удалить Docker? (yes/no): " remove_docker
    if [ "$remove_docker" = "yes" ]; then
        log "Удаление Docker..."

        # Остановка Docker
        systemctl stop docker 2>/dev/null || true

        # Удаление Docker
        apt-get remove -y docker-ce docker-ce-cli containerd.io docker-compose-plugin 2>/dev/null || true

        # Удаление репозитория
        rm -f /etc/apt/sources.list.d/docker.list
        rm -f /usr/share/keyrings/docker-archive-keyring.gpg

        success "Docker удален"
    fi
}

# Функция удаления зависимостей (опционально)
remove_dependencies() {
    echo ""
    read -p "Удалить зависимости (Python, Redis, nginx)? (yes/no): " remove_deps
    if [ "$remove_deps" = "yes" ]; then
        log "Удаление зависимостей..."

        # Остановка сервисов
        systemctl stop redis-server 2>/dev/null || true
        systemctl stop nginx 2>/dev/null || true

        # Удаление пакетов
        apt-get remove -y redis-server nginx python3 python3-pip python3-venv 2>/dev/null || true

        success "Зависимости удалены"
    fi
}

# Функция очистки логов
cleanup_logs() {
    log "Очистка логов..."

    # Очистка systemd логов
    journalctl --vacuum-time=1s 2>/dev/null || true

    # Очистка Docker логов
    docker system prune -f 2>/dev/null || true

    success "Логи очищены"
}

# Функция создания бэкапа перед удалением
create_backup() {
    echo ""
    read -p "Создать бэкап перед удалением? (yes/no): " create_backup
    if [ "$create_backup" = "yes" ]; then
        log "Создание бэкапа..."

        BACKUP_DIR="/opt/antispam-bot-backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"

        # Копирование файлов
        if [ -d "/opt/antispam-bot" ]; then
            cp -r /opt/antispam-bot "$BACKUP_DIR/"
        fi

        if [ -d "/etc/antispam-bot" ]; then
            cp -r /etc/antispam-bot "$BACKUP_DIR/"
        fi

        success "Бэкап создан в $BACKUP_DIR"
    fi
}

# Функция показа информации
show_info() {
    echo ""
    success "🎉 УДАЛЕНИЕ ЗАВЕРШЕЕНО!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ИНФОРМАЦИЯ ОБ УДАЛЕНИИ                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}🗑️  Удалено:${NC}"
    echo "  - Все файлы бота"
    echo "  - База данных"
    echo "  - Логи"
    echo "  - Конфигурация"
    echo "  - systemd сервисы"
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        echo "  - Docker контейнеры"
    fi
    echo ""
    echo -e "${YELLOW}📁 Остались:${NC}"
    echo "  - Бэкапы (если создавались)"
    echo "  - Системные зависимости (если не удалялись)"
    echo ""
    echo -e "${GREEN}✅ AntiSpam Bot полностью удален!${NC}"
    echo ""
}

# Главная функция
main() {
    confirm
    detect_installation_type
    create_backup
    stop_services

    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        remove_docker_containers
    fi

    remove_systemd_services
    remove_files
    remove_user
    remove_nginx_config
    remove_letsencrypt
    remove_docker
    remove_dependencies
    cleanup_logs
    show_info
}

# Запуск
main "$@"
