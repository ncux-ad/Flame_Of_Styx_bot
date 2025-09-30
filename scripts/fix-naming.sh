#!/bin/bash

# Скрипт для исправления названий сервисов
# Приводит все к единому стандарту: flame-of-styx-bot

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
log_info() {
    echo -e "${BLUE}[FIX]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[FIX]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[FIX]${NC} $1"
}

log_error() {
    echo -e "${RED}[FIX]${NC} $1"
}

# Проверка прав
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Скрипт запущен с правами root. Это может быть небезопасно."
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Остановка старого сервиса
stop_old_service() {
    log_info "Остановка старого сервиса antispam-bot..."
    
    if systemctl is-active --quiet antispam-bot 2>/dev/null; then
        sudo systemctl stop antispam-bot
        log_success "Сервис antispam-bot остановлен"
    else
        log_info "Сервис antispam-bot не запущен"
    fi
    
    if systemctl is-enabled --quiet antispam-bot 2>/dev/null; then
        sudo systemctl disable antispam-bot
        log_success "Сервис antispam-bot отключен"
    else
        log_info "Сервис antispam-bot не был включен"
    fi
}

# Создание нового сервиса
create_new_service() {
    log_info "Создание нового сервиса flame-of-styx-bot..."
    
    # Получаем текущую директорию
    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)
    
    # Создаем systemd сервис
    sudo tee /etc/systemd/system/flame-of-styx-bot.service > /dev/null <<EOF
[Unit]
Description=Flame of Styx AntiSpam Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10

# Ограничения ресурсов
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

    log_success "Сервис flame-of-styx-bot создан"
}

# Включение нового сервиса
enable_new_service() {
    log_info "Включение нового сервиса flame-of-styx-bot..."
    
    sudo systemctl daemon-reload
    sudo systemctl enable flame-of-styx-bot.service
    
    log_success "Сервис flame-of-styx-bot включен"
}

# Обновление пользователя
update_user() {
    log_info "Обновление пользователя системы..."
    
    # Проверяем, существует ли пользователь flame-bot
    if ! id flame-bot &>/dev/null; then
        log_info "Создаем пользователя flame-bot..."
        sudo useradd --system --shell /bin/false --home-dir /opt/flame-of-styx-bot --create-home flame-bot
        log_success "Пользователь flame-bot создан"
    else
        log_info "Пользователь flame-bot уже существует"
    fi
    
    # Обновляем права на директории
    if [[ -d "/var/log/flame-of-styx" ]]; then
        sudo chown -R flame-bot:flame-bot /var/log/flame-of-styx
        log_success "Права на /var/log/flame-of-styx обновлены"
    fi
    
    if [[ -d "/opt/flame-of-styx/logs" ]]; then
        sudo chown -R flame-bot:flame-bot /opt/flame-of-styx/logs
        log_success "Права на /opt/flame-of-styx/logs обновлены"
    fi
}

# Обновление crontab
update_crontab() {
    log_info "Обновление crontab задач..."
    
    # Получаем текущий crontab
    current_crontab=$(crontab -l 2>/dev/null || echo "")
    
    # Заменяем antispam-bot на flame-of-styx-bot
    new_crontab=$(echo "$current_crontab" | sed 's/antispam-bot/flame-of-styx-bot/g')
    
    # Устанавливаем новый crontab
    echo "$new_crontab" | crontab -
    
    log_success "Crontab обновлен"
}

# Обновление logrotate
update_logrotate() {
    log_info "Обновление logrotate конфигурации..."
    
    if [[ -f "/etc/logrotate.d/flame-of-styx" ]]; then
        # Обновляем пользователя в logrotate
        sudo sed -i 's/flame-bot flame-bot/antispam antispam/g' /etc/logrotate.d/flame-of-styx
        log_success "Logrotate конфигурация обновлена"
    else
        log_warning "Logrotate конфигурация не найдена"
    fi
}

# Удаление старого сервиса
remove_old_service() {
    log_info "Удаление старого сервиса antispam-bot..."
    
    if [[ -f "/etc/systemd/system/antispam-bot.service" ]]; then
        sudo rm /etc/systemd/system/antispam-bot.service
        sudo systemctl daemon-reload
        log_success "Старый сервис antispam-bot удален"
    else
        log_info "Старый сервис antispam-bot не найден"
    fi
}

# Проверка результата
check_result() {
    log_info "Проверка результата..."
    
    # Проверяем новый сервис
    if systemctl is-enabled --quiet flame-of-styx-bot 2>/dev/null; then
        log_success "✓ Сервис flame-of-styx-bot включен"
    else
        log_warning "✗ Сервис flame-of-styx-bot не включен"
    fi
    
    # Проверяем что старый сервис отключен
    if ! systemctl is-enabled --quiet antispam-bot 2>/dev/null; then
        log_success "✓ Старый сервис antispam-bot отключен"
    else
        log_warning "✗ Старый сервис antispam-bot все еще включен"
    fi
    
    # Проверяем пользователя
    if id flame-bot &>/dev/null; then
        log_success "✓ Пользователь flame-bot существует"
    else
        log_warning "✗ Пользователь flame-bot не найден"
    fi
}

# Основная функция
main() {
    log_info "Исправление названий сервисов"
    log_info "============================="
    
    check_permissions
    stop_old_service
    create_new_service
    enable_new_service
    update_user
    update_crontab
    update_logrotate
    remove_old_service
    check_result
    
    log_success "Исправление названий завершено!"
    log_info ""
    log_info "Теперь используйте:"
    log_info "  • Статус: sudo systemctl status flame-of-styx-bot"
    log_info "  • Логи: sudo journalctl -u flame-of-styx-bot -f"
    log_info "  • Перезапуск: sudo systemctl restart flame-of-styx-bot"
    log_info "  • Остановка: sudo systemctl stop flame-of-styx-bot"
    log_info ""
    log_info "Для запуска нового сервиса:"
    log_info "  sudo systemctl start flame-of-styx-bot"
}

# Запуск
main "$@"
