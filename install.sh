#!/bin/bash
# Главный установочный скрипт для AntiSpam Bot
# Main installation script for AntiSpam Bot

set -euo pipefail

# Load secure utilities
source "$(dirname "$0")/scripts/secure_shell_utils.sh"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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
echo "║  🛡️ Встроенная система безопасности                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

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

# Функция получения конфигурации
get_configuration() {
    echo ""
    info "Настройка конфигурации:"
    echo ""

    # Домен
    while true; do
        read -p "Введите домен (например: bot.example.com): " DOMAIN
        if [ -n "$DOMAIN" ] && [[ "$DOMAIN" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            success "Домен: $DOMAIN"
            break
        else
            error "Неверный формат домена. Попробуйте снова."
        fi
    done

    # Email
    while true; do
        read -p "Введите email для Let's Encrypt: " EMAIL
        if [ -n "$EMAIL" ] && [[ "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            success "Email: $EMAIL"
            break
        else
            error "Неверный формат email. Попробуйте снова."
        fi
    done

    # Bot Token
    while true; do
        read -p "Введите Telegram Bot Token: " BOT_TOKEN
        if [ -n "$BOT_TOKEN" ] && [[ "$BOT_TOKEN" =~ ^[0-9]+:[a-zA-Z0-9_-]+$ ]]; then
            success "Bot Token: ${BOT_TOKEN:0:10}..."
            break
        else
            error "Неверный формат Bot Token. Формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        fi
    done

    # Admin IDs
    read -p "Введите Admin IDs через запятую (например: 123456789,987654321): " ADMIN_IDS
    if [ -z "$ADMIN_IDS" ]; then
        ADMIN_IDS="123456789"
        warning "Используется Admin ID по умолчанию: $ADMIN_IDS"
    fi
    success "Admin IDs: $ADMIN_IDS"

    # Дополнительные настройки
    echo ""
    info "Дополнительные настройки:"

    read -p "Введите пароль для Redis (по умолчанию: random): " REDIS_PASSWORD
    if [ -z "$REDIS_PASSWORD" ]; then
        REDIS_PASSWORD=$(openssl rand -base64 32)
        success "Сгенерирован случайный пароль Redis"
    fi

    read -p "Введите webhook для уведомлений (опционально): " NOTIFICATION_WEBHOOK
    if [ -n "$NOTIFICATION_WEBHOOK" ]; then
        success "Webhook: $NOTIFICATION_WEBHOOK"
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
        libfreetype6-dev

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
EOF

    systemctl enable fail2ban
    systemctl start fail2ban

    # Настройка logrotate
    cat > /etc/logrotate.d/antispam-bot << EOF
/var/log/antispam-bot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 antispam antispam
    postrotate
        systemctl reload antispam-bot 2>/dev/null || true
    endscript
}
EOF

    # Создание пользователя
    if ! id "antispam" &>/dev/null; then
        useradd -r -s /bin/bash -d /opt/antispam-bot -m antispam
        success "Создан пользователь antispam"
    fi

    # Создание директорий
    mkdir -p /opt/antispam-bot
    mkdir -p /var/log/antispam-bot
    mkdir -p /etc/antispam-bot

    chown -R antispam:antispam /opt/antispam-bot
    chown -R antispam:antispam /var/log/antispam-bot
    chown -R antispam:antispam /etc/antispam-bot

    success "Система настроена"
}

# Функция установки через Docker
install_docker_version() {
    log "Установка через Docker..."

    # Создание конфигурации
    cat > /opt/antispam-bot/.env.prod << EOF
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
    cp docker-compose.prod.yml /opt/antispam-bot/

    # Создание systemd сервиса
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

    # Создание cron задачи для обновления
    echo "0 3 * * * /opt/antispam-bot/update.sh >> /var/log/antispam-bot/update.log 2>&1" | crontab -u antispam -

    success "Docker версия установлена"
}

# Функция установки через systemd
install_systemd_version() {
    log "Установка через systemd..."

    # Копирование файлов
    cp -r . /opt/antispam-bot/
    chown -R antispam:antispam /opt/antispam-bot

    # Создание виртуального окружения
    sudo -u antispam python3 -m venv /opt/antispam-bot/venv
    sudo -u antispam /opt/antispam-bot/venv/bin/pip install --upgrade pip
    sudo -u antispam /opt/antispam-bot/venv/bin/pip install -r /opt/antispam-bot/requirements.txt

    # Создание конфигурации
    cat > /etc/antispam-bot/.env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
DB_PATH=/opt/antispam-bot/db.sqlite3
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
User=antispam
Group=antispam
WorkingDirectory=/opt/antispam-bot
Environment=PATH=/opt/antispam-bot/venv/bin
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

    # Создание cron задачи для обновления
    echo "0 3 * * * /opt/antispam-bot/update.sh >> /var/log/antispam-bot/update.log 2>&1" | crontab -u antispam -

    success "systemd версия установлена"
}

# Функция настройки Let's Encrypt
setup_letsencrypt() {
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        log "Настройка Let's Encrypt для Docker..."

        # Запуск nginx для получения сертификатов
        cd /opt/antispam-bot
        docker-compose -f docker-compose.prod.yml up -d nginx

        # Ожидание запуска nginx
        sleep 10

        # Получение сертификатов
        docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-init.sh

        # Запуск всех сервисов
        docker-compose -f docker-compose.prod.yml up -d

    elif [ "$INSTALLATION_TYPE" = "systemd" ]; then
        log "Настройка Let's Encrypt для systemd..."

        # Установка certbot
        apt-get install -y certbot python3-certbot-nginx

        # Получение сертификатов
        certbot certonly --webroot -w /var/www/html -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

        # Настройка nginx
        apt-get install -y nginx
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

        ln -sf /etc/nginx/sites-available/antispam-bot /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        nginx -t && systemctl reload nginx

        # Настройка автообновления сертификатов
        echo "0 2 * * * certbot renew --quiet && systemctl reload nginx" | crontab -
    fi

    success "Let's Encrypt настроен"
}

# Функция финальной настройки
finalize_installation() {
    log "Финальная настройка..."

    # Включение сервисов
    if [ "$INSTALLATION_TYPE" = "docker" ]; then
        systemctl enable antispam-bot-docker
        systemctl start antispam-bot-docker
    elif [ "$INSTALLATION_TYPE" = "systemd" ]; then
        systemctl enable antispam-bot
        systemctl start antispam-bot
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
    choose_installation_type
    get_configuration
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
