#!/bin/bash
# =============================================================================
# СИСТЕМНЫЕ ФУНКЦИИ УСТАНОВКИ
# =============================================================================

# Функция установки системных зависимостей
install_system_dependencies() {
    info "Установка системных зависимостей..."
    
    # Обновляем пакеты
    apt update
    
    # Устанавливаем основные пакеты
    local packages=(
        "git"
        "curl"
        "wget"
        "python3"
        "python3-pip"
        "python3-venv"
        "python3-dev"
        "python3-cffi"
        "python3-cryptography"
        "nginx"
        "certbot"
        "python3-certbot-nginx"
        "fail2ban"
        "ufw"
        "htop"
        "nano"
        "unzip"
    )
    
    # Добавляем пакеты для Docker если нужен
    if [ "$SKIP_DOCKER" != "true" ] && [ "$INSTALLATION_TYPE" = "docker" ]; then
        packages+=("apt-transport-https" "ca-certificates" "gnupg" "lsb-release")
    fi
    
    # Устанавливаем пакеты
    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            info "Установка пакета: $package"
            apt install -y "$package"
        else
            info "Пакет уже установлен: $package"
        fi
    done
    
    success "Системные зависимости установлены"
}

# Функция установки Docker
install_docker() {
    # Пропускаем Docker если явно отключен или не нужен
    if [ "$SKIP_DOCKER" = "true" ]; then
        info "Docker пропущен (--skip-docker)"
        return 0
    fi
    
    if [ "$INSTALLATION_TYPE" != "docker" ]; then
        info "Docker не требуется для установки типа: $INSTALLATION_TYPE"
        return 0
    fi
    
    if command -v docker >/dev/null 2>&1; then
        info "Docker уже установлен"
        return 0
    fi
    
    info "Установка Docker..."
    
    # Добавляем официальный GPG ключ Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Добавляем репозиторий Docker
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Обновляем пакеты
    apt update
    
    # Устанавливаем Docker
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Запускаем Docker
    systemctl start docker
    systemctl enable docker
    
    success "Docker установлен"
}

# Функция настройки файрвола
setup_firewall() {
    info "Настройка файрвола UFW..."
    
    # Включаем UFW
    ufw --force enable
    
    # Разрешаем SSH
    ufw allow ssh
    
    # Разрешаем указанный SSH порт
    if [ "$SSH_PORT" != "22" ]; then
        ufw allow "$SSH_PORT/tcp"
        info "Разрешен SSH порт: $SSH_PORT"
    fi
    
    # Разрешаем HTTP и HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Показываем статус
    ufw status
    
    success "Файрвол настроен"
}

# Функция настройки fail2ban
setup_fail2ban() {
    info "Настройка fail2ban..."
    
    # Создаем конфигурацию jail.local
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh,$SSH_PORT
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[sshd-2022]
enabled = true
port = $SSH_PORT
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
EOF

    # Исправляем совместимость с Python 3.11+
    fix_fail2ban_python3_compatibility
    
    # Запускаем fail2ban
    systemctl enable fail2ban
    systemctl start fail2ban
    
    success "fail2ban настроен"
}

# Функция исправления совместимости fail2ban с Python 3.11+
fix_fail2ban_python3_compatibility() {
    log "Проверка совместимости fail2ban с Python..."
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log "Версия Python: $python_version"
    
    if [[ "$python_version" == "3.11" || "$python_version" == "3.12" || "$python_version" == "3.13" ]]; then
        log "Python $python_version обнаружен, создаем патч для fail2ban..."
        
        # Создаем wrapper для fail2ban-server
        cat > /usr/local/bin/fail2ban-server << 'EOF'
#!/usr/bin/env python3
# Wrapper для fail2ban с патчем для Python 3.11+
import sys
import os
sys.path.insert(0, '/usr/lib/python3/dist-packages')
try:
    from collections import MutableMapping
except ImportError:
    import collections
    import collections.abc
    collections.MutableMapping = collections.abc.MutableMapping
from fail2ban.server import main
if __name__ == '__main__':
    main()
EOF
        
        chmod +x /usr/local/bin/fail2ban-server
        
        # Создаем override для systemd
        mkdir -p /etc/systemd/system/fail2ban.service.d
        cat > /etc/systemd/system/fail2ban.service.d/override.conf << EOF
[Service]
ExecStart=
ExecStart=/usr/local/bin/fail2ban-server -xf start
EOF
        
        systemctl daemon-reload
        success "Патч для fail2ban создан для Python $python_version"
    else
        log "Python $python_version не требует патча для fail2ban"
    fi
}

# Функция установки Python зависимостей
install_python_dependencies() {
    info "Установка Python зависимостей..."
    
    # Создаем виртуальное окружение
    python3 -m venv --upgrade-deps "${BASE_DIR}/venv"
    
    # Устанавливаем права
    chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}/venv"
    
    # Активируем виртуальное окружение и устанавливаем зависимости
    sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install --upgrade pip setuptools
    sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install -r requirements.txt
    
    # Применяем миграции базы данных
    info "Применение миграций базы данных..."
    cd "${BASE_DIR}"
    sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/alembic" upgrade head
    
    success "Python зависимости установлены и миграции применены"
}

# Функция установки systemd версии
install_systemd_version() {
    info "Установка через systemd..."
    
    # Создаем пользователя если не существует
    if ! id "$RUN_USER" &>/dev/null; then
        useradd -r -s /bin/false "$RUN_USER"
        info "Создан пользователь: $RUN_USER"
    fi
    
    # Создаем директории
    create_directories
    
    # Копируем файлы если нужно
    if [ "$(pwd)" != "${BASE_DIR}" ]; then
        cp -r . "${BASE_DIR}/"
        chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}"
    else
        warning "Уже находимся в целевой директории ${BASE_DIR}, пропускаем копирование"
        chown -R ${RUN_USER}:${RUN_USER} "${BASE_DIR}"
    fi
    
    # Устанавливаем Python зависимости
    install_python_dependencies
    
    # Создаем systemd unit файл
    create_systemd_unit
    
    success "Установка через systemd завершена"
}

# Функция создания systemd unit файла
create_systemd_unit() {
    info "Создание systemd unit файла..."
    
    cat > "/etc/systemd/system/${APP_NAME}.service" << EOF
[Unit]
Description=AntiSpam Telegram Bot
After=network.target

[Service]
Type=simple
User=${RUN_USER}
Group=${RUN_USER}
WorkingDirectory=${BASE_DIR}
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${BASE_DIR}/venv/bin
Environment=PYTHONPATH=${BASE_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=${BASE_DIR}/venv/bin/python ${BASE_DIR}/bot.py
Restart=always
RestartSec=10
TimeoutStartSec=30

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=antispam-bot

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    success "Systemd unit файл создан"
}

# Функция настройки Nginx
setup_nginx() {
    info "Настройка Nginx..."
    
    # Создаем конфигурацию сайта
    cat > "/etc/nginx/sites-available/${APP_NAME}" << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Активируем сайт
    ln -sf "/etc/nginx/sites-available/${APP_NAME}" "/etc/nginx/sites-enabled/"
    
    # Удаляем дефолтный сайт
    rm -f /etc/nginx/sites-enabled/default
    
    # Проверяем конфигурацию
    nginx -t
    
    # Перезагружаем Nginx
    systemctl reload nginx
    
    success "Nginx настроен"
}

# Функция настройки Let's Encrypt
setup_letsencrypt() {
    info "Настройка Let's Encrypt SSL..."
    
    # Проверяем, что домен не localhost
    if [[ "$DOMAIN" == "localhost" || "$DOMAIN" == "127.0.0.1" ]]; then
        warning "Пропускаем SSL для localhost/127.0.0.1"
        return 0
    fi
    
    # Устанавливаем certbot в виртуальное окружение
    if [ -f "${BASE_DIR}/venv/bin/activate" ]; then
        sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install --upgrade pip
        sudo -u ${RUN_USER} "${BASE_DIR}/venv/bin/pip" install certbot certbot-nginx
        ln -sf "${BASE_DIR}/venv/bin/certbot" /usr/bin/certbot
    else
        error "Виртуальное окружение не найдено в ${BASE_DIR}/venv"
        return 1
    fi
    
    # Получаем SSL сертификат
    if certbot certonly --webroot -w /var/www/html -d $DOMAIN --email $EMAIL --agree-tos --non-interactive; then
        success "SSL сертификат получен для $DOMAIN"
        
        # Обновляем конфигурацию Nginx с SSL
        cat > "/etc/nginx/sites-available/${APP_NAME}" << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
        
        # Перезагружаем Nginx
        systemctl reload nginx
        
        # Настраиваем автообновление сертификатов
        echo "0 2 * * * certbot renew --quiet && systemctl reload nginx" | crontab -
        
    else
        warning "Не удалось получить SSL сертификат для $DOMAIN, продолжаем без SSL"
    fi
}

# Функция настройки ротации логов
setup_log_rotation() {
    info "Настройка ротации логов..."
    
    cat > "/etc/logrotate.d/${APP_NAME}" << EOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ${RUN_USER} ${RUN_USER}
    postrotate
        systemctl reload ${APP_NAME}.service > /dev/null 2>&1 || true
    endscript
}
EOF

    success "Ротация логов настроена"
}
