#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"
# Скрипт установки AntiSpam Bot через systemd
# systemd installation script for AntiSpam Bot

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
echo "⚙️  УСТАНОВКА ANTI-SPAM BOT ЧЕРЕЗ SYSTEMD"
echo "========================================"
echo -e "${NC}"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    error "Запустите с правами root: sudo bash install-systemd.sh"
    exit 1
fi

# Функция установки зависимостей
install_dependencies() {
    log "Установка зависимостей..."

    # Обновление пакетов
    apt-get update -y

    # Установка Python и зависимостей
    apt-get install -y python3 python3-pip python3-venv python3-dev

    # Установка системных зависимостей
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
        curl \
        wget \
        git \
        htop \
        nano \
        vim \
        ufw \
        fail2ban \
        cron \
        openssl \
        dnsutils \
        net-tools \
        nginx \
        certbot \
        python3-certbot-nginx \
        redis-server

    success "Зависимости установлены"
}

# Функция настройки системы
setup_system() {
    log "Настройка системы..."

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
    mkdir -p /etc/antispam-bot
    mkdir -p /var/www/html

    chown -R antispam:antispam /opt/antispam-bot
    chown -R antispam:antispam /var/log/antispam-bot
    chown -R antispam:antispam /etc/antispam-bot
    chown -R www-data:www-data /var/www/html

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
    read -p "Введите пароль для Redis (по умолчанию: random): " REDIS_PASSWORD
    if [ -z "$REDIS_PASSWORD" ]; then
        REDIS_PASSWORD=$(openssl rand -base64 32)
        success "Сгенерирован случайный пароль Redis"
    fi

    success "Конфигурация получена"
}

# Функция копирования файлов
copy_files() {
    log "Копирование файлов проекта..."

    # Копирование всех файлов
    cp -r . /opt/antispam-bot/
    chown -R antispam:antispam /opt/antispam-bot

    success "Файлы скопированы"
}

# Функция создания виртуального окружения
create_venv() {
    log "Создание виртуального окружения..."

    # Создание виртуального окружения
    sudo -u antispam python3 -m venv /opt/antispam-bot/venv

    # Установка зависимостей
    sudo -u antispam /opt/antispam-bot/venv/bin/pip install --upgrade pip
    sudo -u antispam /opt/antispam-bot/venv/bin/pip install -r /opt/antispam-bot/requirements.txt

    success "Виртуальное окружение создано"
}

# Функция настройки Redis
setup_redis() {
    log "Настройка Redis..."

    # Настройка Redis
    cat > /etc/redis/redis.conf << EOF
# Redis configuration for AntiSpam Bot
bind 127.0.0.1
port 6379
requirepass $REDIS_PASSWORD
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

    systemctl enable redis-server
    systemctl restart redis-server

    success "Redis настроен"
}

# Функция создания systemd сервиса
create_systemd_service() {
    log "Создание systemd сервиса..."

    # Создание конфигурации
    cat > /etc/antispam-bot/.env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
DB_PATH=/opt/antispam-bot/db.sqlite3
REDIS_PASSWORD=$REDIS_PASSWORD
NOTIFICATION_WEBHOOK=
EOF

    # Создание systemd сервиса
    cat > /etc/systemd/system/antispam-bot.service << EOF
[Unit]
Description=AntiSpam Bot Service
After=network.target redis.service

[Service]
Type=simple
User=antispam
Group=antispam
WorkingDirectory=/opt/antispam-bot
Environment=PATH=/opt/antispam-bot/venv/bin
EnvironmentFile=/etc/antispam-bot/.env
ExecStart=/opt/antispam-bot/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=antispam-bot

[Install]
WantedBy=multi-user.target
EOF

    # Создание скрипта обновления
    cat > /opt/antispam-bot/update.sh << 'EOF'
#!/bin/bash
cd /opt/antispam-bot
git pull origin main
/opt/antispam-bot/venv/bin/pip install -r requirements.txt
systemctl restart antispam-bot
EOF

    chmod +x /opt/antispam-bot/update.sh

    # Создание cron задачи
    echo "0 3 * * * /opt/antispam-bot/update.sh >> /var/log/antispam-bot/update.log 2>&1" | crontab -u antispam -

    success "systemd сервис создан"
}

# Функция настройки nginx
setup_nginx() {
    log "Настройка nginx..."

    # Создание конфигурации nginx
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

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Включение сайта
    ln -sf /etc/nginx/sites-available/antispam-bot /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # Проверка конфигурации
    nginx -t

    systemctl enable nginx
    systemctl restart nginx

    success "nginx настроен"
}

# Функция настройки Let's Encrypt
setup_letsencrypt() {
    log "Настройка Let's Encrypt..."

    # Получение сертификатов
    certbot certonly --webroot -w /var/www/html -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

    # Настройка автообновления
    echo "0 2 * * * certbot renew --quiet && systemctl reload nginx" | crontab -

    # Перезапуск nginx с SSL
    systemctl reload nginx

    success "Let's Encrypt настроен"
}

# Функция создания скрипта управления
create_management_script() {
    log "Создание скрипта управления..."

    cat > /usr/local/bin/antispam-bot << 'EOF'
#!/bin/bash
case "$1" in
    start)
        systemctl start antispam-bot
        ;;
    stop)
        systemctl stop antispam-bot
        ;;
    restart)
        systemctl restart antispam-bot
        ;;
    status)
        systemctl status antispam-bot
        ;;
    logs)
        journalctl -u antispam-bot -f
        ;;
    update)
        /opt/antispam-bot/update.sh
        ;;
    nginx-logs)
        journalctl -u nginx -f
        ;;
    redis-logs)
        journalctl -u redis-server -f
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update|nginx-logs|redis-logs}"
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

    # Включение и запуск сервисов
    systemctl enable antispam-bot
    systemctl start antispam-bot

    # Ожидание запуска
    sleep 5

    # Проверка статуса
    if systemctl is-active --quiet antispam-bot; then
        success "Сервис запущен"
    else
        error "Ошибка запуска сервиса"
        systemctl status antispam-bot
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
    echo "  antispam-bot nginx-logs  - Логи nginx"
    echo "  antispam-bot redis-logs  - Логи Redis"
    echo ""
    echo -e "${YELLOW}🔗 Полезные ссылки:${NC}"
    echo "  https://$DOMAIN - Веб-интерфейс"
    echo "  /opt/antispam-bot - Директория бота"
    echo "  /var/log/antispam-bot - Логи бота"
    echo "  /etc/antispam-bot - Конфигурация бота"
    echo ""
    echo -e "${GREEN}✅ Бот готов к работе!${NC}"
    echo ""
}

# Главная функция
main() {
    install_dependencies
    setup_system
    get_config
    copy_files
    create_venv
    setup_redis
    create_systemd_service
    setup_nginx
    setup_letsencrypt
    create_management_script
    start_services
    show_info
}

# Запуск
main "$@"
