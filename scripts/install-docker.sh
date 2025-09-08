#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"
# Скрипт установки AntiSpam Bot через Docker
# Docker installation script for AntiSpam Bot

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
echo "🐳 УСТАНОВКА ANTI-SPAM BOT ЧЕРЕЗ DOCKER"
echo "======================================"
echo -e "${NC}"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    error "Запустите с правами root: sudo bash install-docker.sh"
    exit 1
fi

# Функция установки Docker
install_docker() {
    log "Установка Docker..."

    # Удаление старых версий
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Обновление пакетов
    apt-get update -y
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

    # Добавление GPG ключа Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Добавление репозитория Docker
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Установка Docker
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Запуск и включение Docker
    systemctl enable docker
    systemctl start docker

    # Добавление пользователя в группу docker
    usermod -aG docker $SUDO_USER

    success "Docker установлен"
}

# Функция настройки системы
setup_system() {
    log "Настройка системы..."

    # Установка базовых пакетов
    apt-get update -y
    apt-get install -y curl wget git unzip htop nano vim ufw fail2ban cron openssl dnsutils net-tools

    # Настройка файрвола
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable

    # Настройка fail2ban
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
EOF

    systemctl enable fail2ban
    systemctl start fail2ban

    # Создание пользователя
    if ! id "antispam" &>/dev/null; then
        useradd -r -s /bin/bash -d /opt/antispam-bot -m antispam
    fi

    # Создание директорий
    mkdir -p /opt/antispam-bot
    mkdir -p /var/log/antispam-bot
    chown -R antispam:antispam /opt/antispam-bot
    chown -R antispam:antispam /var/log/antispam-bot

    success "Система настроена"
}

# Функция получения конфигурации
get_config() {
    echo ""
    log "Настройка конфигурации:"

    # Домен
    read -p "Введите домен (например: bot.example.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        error "Домен обязателен!"
        exit 1
    fi

    # Email
    read -p "Введите email для Let's Encrypt: " EMAIL
    if [ -z "$EMAIL" ]; then
        error "Email обязателен!"
        exit 1
    fi

    # Bot Token
    read -p "Введите Telegram Bot Token: " BOT_TOKEN
    if [ -z "$BOT_TOKEN" ]; then
        error "Bot Token обязателен!"
        exit 1
    fi

    # Admin IDs
    read -p "Введите Admin IDs через запятую: " ADMIN_IDS
    if [ -z "$ADMIN_IDS" ]; then
        ADMIN_IDS="123456789"
    fi

    # Redis Password
    REDIS_PASSWORD=$(openssl rand -base64 32)

    success "Конфигурация получена"
}

# Функция копирования файлов
copy_files() {
    log "Копирование файлов проекта..."

    # Копирование всех файлов
    cp -r . /opt/antispam-bot/
    chown -R antispam:antispam /opt/antispam-bot

    # Создание .env.prod
    cat > /opt/antispam-bot/.env.prod << EOF
DOMAIN=$DOMAIN
EMAIL=$EMAIL
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
DB_PATH=db.sqlite3
REDIS_PASSWORD=$REDIS_PASSWORD
NOTIFICATION_WEBHOOK=
RENEWAL_THRESHOLD=30
EOF

    success "Файлы скопированы"
}

# Функция создания systemd сервиса
create_systemd_service() {
    log "Создание systemd сервиса..."

    cat > /etc/systemd/system/antispam-bot-docker.service << EOF
[Unit]
Description=AntiSpam Bot Docker Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/antispam-bot
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=antispam
Group=antispam

[Install]
WantedBy=multi-user.target
EOF

    # Создание скрипта обновления
    cat > /opt/antispam-bot/update.sh << 'EOF'
#!/bin/bash
cd /opt/antispam-bot
git pull origin main
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
EOF

    chmod +x /opt/antispam-bot/update.sh

    # Создание cron задачи
    echo "0 3 * * * /opt/antispam-bot/update.sh >> /var/log/antispam-bot/update.log 2>&1" | crontab -u antispam -

    success "systemd сервис создан"
}

# Функция настройки Let's Encrypt
setup_letsencrypt() {
    log "Настройка Let's Encrypt..."

    cd /opt/antispam-bot

    # Запуск nginx для получения сертификатов
    docker-compose -f docker-compose.prod.yml up -d nginx

    # Ожидание запуска nginx
    sleep 15

    # Получение сертификатов
    docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-init.sh

    # Запуск всех сервисов
    docker-compose -f docker-compose.prod.yml up -d

    success "Let's Encrypt настроен"
}

# Функция создания скрипта управления
create_management_script() {
    log "Создание скрипта управления..."

    cat > /usr/local/bin/antispam-bot << 'EOF'
#!/bin/bash
case "$1" in
    start)
        systemctl start antispam-bot-docker
        ;;
    stop)
        systemctl stop antispam-bot-docker
        ;;
    restart)
        systemctl restart antispam-bot-docker
        ;;
    status)
        systemctl status antispam-bot-docker
        ;;
    logs)
        journalctl -u antispam-bot-docker -f
        ;;
    update)
        /opt/antispam-bot/update.sh
        ;;
    docker-logs)
        cd /opt/antispam-bot && docker-compose -f docker-compose.prod.yml logs -f
        ;;
    docker-ps)
        cd /opt/antispam-bot && docker-compose -f docker-compose.prod.yml ps
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update|docker-logs|docker-ps}"
        exit 1
        ;;
esac
EOF

    chmod +x /usr/local/bin/antispam-bot

    success "Скрипт управления создан"
}

# Функция запуска сервисов
start_services() {
    log "Запуск сервисов..."

    # Включение и запуск сервиса
    systemctl enable antispam-bot-docker
    systemctl start antispam-bot-docker

    # Ожидание запуска
    sleep 10

    # Проверка статуса
    if systemctl is-active --quiet antispam-bot-docker; then
        success "Сервис запущен"
    else
        error "Ошибка запуска сервиса"
        systemctl status antispam-bot-docker
        exit 1
    fi
}

# Функция вывода информации
show_info() {
    echo ""
    success "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ИНФОРМАЦИЯ ОБ УСТАНОВКЕ                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}🌐 Домен:${NC} $DOMAIN"
    echo -e "${YELLOW}📧 Email:${NC} $EMAIL"
    echo -e "${YELLOW}🤖 Bot Token:${NC} ${BOT_TOKEN:0:10}..."
    echo -e "${YELLOW}👑 Admin IDs:${NC} $ADMIN_IDS"
    echo ""
    echo -e "${YELLOW}📋 Команды управления:${NC}"
    echo "  antispam-bot start       - Запуск бота"
    echo "  antispam-bot stop        - Остановка бота"
    echo "  antispam-bot restart     - Перезапуск бота"
    echo "  antispam-bot status      - Статус бота"
    echo "  antispam-bot logs        - Просмотр логов"
    echo "  antispam-bot update      - Обновление бота"
    echo "  antispam-bot docker-logs - Логи Docker контейнеров"
    echo "  antispam-bot docker-ps   - Статус Docker контейнеров"
    echo ""
    echo -e "${YELLOW}🔗 Полезные ссылки:${NC}"
    echo "  https://$DOMAIN - Веб-интерфейс"
    echo "  /opt/antispam-bot - Директория бота"
    echo "  /var/log/antispam-bot - Логи бота"
    echo ""
    echo -e "${GREEN}✅ Бот готов к работе!${NC}"
    echo ""
}

# Главная функция
main() {
    install_docker
    setup_system
    get_config
    copy_files
    create_systemd_service
    setup_letsencrypt
    create_management_script
    start_services
    show_info
}

# Запуск
main "$@"
