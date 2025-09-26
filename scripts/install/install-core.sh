#!/bin/bash
# =============================================================================
# ОСНОВНАЯ ЛОГИКА УСТАНОВКИ
# =============================================================================

# Функция завершения установки
finalize_installation() {
    info "Завершение установки..."
    
    # Создаем .env файл
    create_local_env
    
    # Настраиваем права
    set_permissions
    
    # Запускаем сервис
    if [ "$INSTALLATION_TYPE" = "systemd" ]; then
        systemctl enable "${APP_NAME}.service"
        systemctl start "${APP_NAME}.service"
        
        # Проверяем здоровье сервиса
        health_check
    fi
    
    # Отправляем тестовое уведомление
    send_test_notification
    
    success "Установка завершена"
}

# Функция проверки здоровья сервиса
health_check() {
    info "Проверка здоровья сервиса..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if systemctl is-active --quiet "${APP_NAME}.service"; then
            success "Сервис ${APP_NAME} запущен и работает"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Попытка $attempt/$max_attempts: ожидание запуска сервиса..."
        sleep 2
    done
    
    error "Сервис ${APP_NAME} не запустился за $max_attempts попыток"
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

# Функция показа финальной информации
show_final_info() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    УСТАНОВКА ЗАВЕРШЕНА                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    success "🎉 AntiSpam Bot успешно установлен!"
    echo ""
    
    echo "📋 Информация об установке:"
    echo "  • Профиль: $PROFILE"
    echo "  • Тип: $INSTALLATION_TYPE"
    echo "  • Домен: $DOMAIN"
    echo "  • Email: $EMAIL"
    echo "  • Директория: $BASE_DIR"
    echo "  • SSH порт: $SSH_PORT"
    echo ""
    
    if [ "$INSTALLATION_TYPE" = "systemd" ]; then
        echo "🔧 Управление сервисом:"
        echo "  • Статус: systemctl status ${APP_NAME}.service"
        echo "  • Запуск: systemctl start ${APP_NAME}.service"
        echo "  • Остановка: systemctl stop ${APP_NAME}.service"
        echo "  • Перезапуск: systemctl restart ${APP_NAME}.service"
        echo "  • Логи: journalctl -u ${APP_NAME}.service -f"
        echo ""
    fi
    
    echo "🌐 Веб-интерфейс:"
    if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != "127.0.0.1" ]]; then
        echo "  • HTTP: http://$DOMAIN"
        echo "  • HTTPS: https://$DOMAIN"
    else
        echo "  • HTTP: http://localhost"
    fi
    echo ""
    
    echo "🛡️ Безопасность:"
    echo "  • UFW: $(systemctl is-active ufw 2>/dev/null || echo 'неактивен')"
    echo "  • Fail2ban: $(systemctl is-active fail2ban 2>/dev/null || echo 'неактивен')"
    echo ""
    
    if [ "$INSTALLATION_TYPE" = "systemd" ]; then
        echo "📊 Статус сервисов:"
        echo "  • ${APP_NAME}: $(systemctl is-active ${APP_NAME}.service 2>/dev/null || echo 'неактивен')"
        echo "  • Nginx: $(systemctl is-active nginx 2>/dev/null || echo 'неактивен')"
        echo ""
    fi
    
    echo "📁 Файлы конфигурации:"
    echo "  • .env: $BASE_DIR/.env"
    echo "  • Логи: $LOG_DIR/"
    echo "  • Конфигурация: $CONFIG_DIR/"
    echo ""
    
    if [ -n "$NATIVE_CHANNEL_IDS" ] && [ "$NATIVE_CHANNEL_IDS" != "-10000000000" ]; then
        echo "📺 Нативные каналы:"
        echo "  • $NATIVE_CHANNEL_IDS"
        echo ""
    fi
    
    echo "🔧 Следующие шаги:"
    echo "  1. Добавьте бота в каналы как администратора"
    echo "  2. Настройте права бота (удаление сообщений, блокировка пользователей)"
    echo "  3. Проверьте работу командой /status в личке с ботом"
    echo "  4. Настройте каналы командой /channels"
    echo ""
    
    echo "📚 Документация:"
    echo "  • README.md - основная информация"
    echo "  • docs/ADMIN_GUIDE.md - руководство администратора"
    echo "  • docs/TROUBLESHOOTING.md - устранение неполадок"
    echo ""
    
    echo "🆘 Поддержка:"
    echo "  • GitHub: https://github.com/ncux-ad/Flame_Of_Styx_bot"
    echo "  • Разработчик: [@ncux-ad](https://github.com/ncux-ad)"
    echo ""
    
    success "Установка завершена успешно! 🚀"
}

# Функция установки приложения
install_application() {
    info "Установка приложения..."
    
    if [ "$INSTALLATION_TYPE" = "systemd" ]; then
        install_systemd_version
    elif [ "$INSTALLATION_TYPE" = "docker" ]; then
        install_docker_version
    else
        error "Неизвестный тип установки: $INSTALLATION_TYPE"
        exit 1
    fi
}

# Функция установки Docker версии
install_docker_version() {
    info "Установка через Docker..."
    
    # Создаем docker-compose.yml если не существует
    if [ ! -f "docker-compose.yml" ]; then
        cat > docker-compose.yml << EOF
version: '3.8'

services:
  antispam-bot:
    build: .
    container_name: antispam-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=\${BOT_TOKEN}
      - ADMIN_IDS=\${ADMIN_IDS}
      - NATIVE_CHANNEL_IDS=\${NATIVE_CHANNEL_IDS}
      - DB_PATH=\${DB_PATH}
      - LOG_LEVEL=\${LOG_LEVEL}
      - RATE_LIMIT=\${RATE_LIMIT}
      - RATE_INTERVAL=\${RATE_INTERVAL}
      - DOMAIN=\${DOMAIN}
      - EMAIL=\${EMAIL}
      - REDIS_PASSWORD=\${REDIS_PASSWORD}
      - NOTIFICATION_WEBHOOK=\${NOTIFICATION_WEBHOOK}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - antispam-network

networks:
  antispam-network:
    driver: bridge
EOF
    fi
    
    # Создаем .env файл для Docker
    create_local_env
    
    # Запускаем контейнер
    docker-compose up -d --build
    
    success "Установка через Docker завершена"
}

# Функция настройки системы
setup_system() {
    info "Настройка системы..."
    
    # Устанавливаем системные зависимости
    install_system_dependencies
    
    # Устанавливаем Docker если нужен
    install_docker
    
    # Настраиваем файрвол
    setup_firewall
    
    # Настраиваем fail2ban
    setup_fail2ban
    
    # Настраиваем Nginx
    setup_nginx
    
    # Настраиваем Let's Encrypt
    setup_letsencrypt
    
    # Настраиваем ротацию логов
    setup_log_rotation
    
    success "Система настроена"
}

# Функция очистки
cleanup() {
    info "Очистка временных файлов..."
    cleanup_temp_files
    success "Очистка завершена"
}

# Функция обработки ошибок
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    error "Ошибка в строке $line_number (код выхода: $exit_code)"
    error "Установка прервана"
    
    # Показываем информацию для отладки
    echo ""
    echo "🔍 Информация для отладки:"
    echo "  • Код ошибки: $exit_code"
    echo "  • Строка: $line_number"
    echo "  • Профиль: $PROFILE"
    echo "  • Тип: $INSTALLATION_TYPE"
    echo "  • Директория: $BASE_DIR"
    echo ""
    
    # Показываем последние логи
    if [ "$INSTALLATION_TYPE" = "systemd" ]; then
        echo "📋 Последние логи сервиса:"
        journalctl -u "${APP_NAME}.service" --no-pager -n 10 || true
    fi
    
    exit $exit_code
}

# Устанавливаем обработчик ошибок
trap 'handle_error $LINENO' ERR

# Функция показа версии
show_version() {
    echo "$SCRIPT_NAME v$SCRIPT_VERSION"
}

# Функция показа справки
show_help() {
    cat << EOF
ИСПОЛЬЗОВАНИЕ:
    $0 [ОПЦИИ]

ОПЦИИ:
    --profile PROFILE         Профиль установки (user|prod)
    --type TYPE              Тип установки (docker|systemd)
    --ssh-port PORT          SSH порт (по умолчанию: 22)
    --domain DOMAIN          Домен для Let's Encrypt
    --email EMAIL            Email для Let's Encrypt
    --bot-token TOKEN        Токен Telegram бота
    --admin-ids IDS          ID администраторов (через запятую)
    --channel-links LINKS    Ссылки на каналы (через запятую)
    --non-interactive        Неинтерактивный режим
    --dry-run                Режим проверки без изменений
    --skip-docker            Пропустить установку Docker (для слабых VPS)
    --base-dir DIR           Указать директорию установки
    --help                   Показать эту справку
    --version                Показать версию

ПРИМЕРЫ:
    sudo bash $0 --profile=user --type=systemd --domain=example.com --email=admin@example.com
    sudo bash $0 --non-interactive --bot-token=123:ABC --admin-ids=123456789
    sudo bash $0 --skip-docker --type=systemd --domain=example.com --email=admin@example.com
    sudo bash $0 --profile=user --base-dir=/home/user/my-bot --type=systemd
    sudo bash $0 --profile=prod --base-dir=/opt/my-custom-bot --type=systemd
EOF
}
