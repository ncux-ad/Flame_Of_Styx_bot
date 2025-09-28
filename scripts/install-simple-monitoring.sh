#!/bin/bash
# Простой мониторинг - только Netdata + встроенный healthcheck

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🚀 Simple Monitoring Setup${NC}"
    echo -e "${BLUE}=========================${NC}"
    echo -e "${YELLOW}💡 Только Netdata + встроенный healthcheck${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

print_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

print_header

# Устанавливаем Netdata
print_step "Устанавливаем Netdata..."
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y netdata
elif command -v yum &> /dev/null; then
    sudo yum install -y epel-release
    sudo yum install -y netdata
elif command -v dnf &> /dev/null; then
    sudo dnf install -y epel-release
    sudo dnf install -y netdata
else
    print_error "Не поддерживаемая система"
    exit 1
fi

# Настраиваем Netdata для VPS
print_step "Настраиваем Netdata для VPS..."
sudo tee /etc/netdata/netdata.conf > /dev/null <<EOF
[global]
    memory mode = ram
    history = 3600
    update every = 5
    web files owner = netdata
    web files group = netdata

[web]
    bind to = 0.0.0.0:19999

[plugins]
    python.d = yes
    node.d = no
    go.d = no

[plugin:python.d]
    # Отключаем тяжелые плагины для VPS
    nginx = no
    apache = no
    mysql = no
    postgres = no
    redis = no
    memcached = no
    elasticsearch = no
    mongodb = no
    rabbitmq = no
    disk_space = yes
    disk_io = yes
    netstat = yes
    systemd = yes
EOF

# Создаем простой healthcheck endpoint
print_step "Создаем healthcheck endpoint..."
sudo mkdir -p /var/www/html
sudo tee /var/www/html/healthcheck.php > /dev/null <<'EOF'
<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$status = [
    'status' => 'ok',
    'timestamp' => date('Y-m-d H:i:s'),
    'uptime' => shell_exec('uptime -p'),
    'memory' => shell_exec('free -h | grep Mem'),
    'disk' => shell_exec('df -h / | tail -1'),
    'bot_status' => 'running'
];

// Проверяем статус бота
$bot_pid = shell_exec('pgrep -f "python.*bot.py"');
if (empty(trim($bot_pid))) {
    $status['bot_status'] = 'stopped';
    $status['status'] = 'warning';
}

echo json_encode($status, JSON_PRETTY_PRINT);
?>
EOF

# Устанавливаем права
sudo chown www-data:www-data /var/www/html/healthcheck.php
sudo chmod 644 /var/www/html/healthcheck.php

# Устанавливаем nginx для healthcheck
print_step "Устанавливаем nginx для healthcheck..."
if command -v apt &> /dev/null; then
    sudo apt install -y nginx
elif command -v yum &> /dev/null; then
    sudo yum install -y nginx
elif command -v dnf &> /dev/null; then
    sudo dnf install -y nginx
fi

# Настраиваем nginx
sudo tee /etc/nginx/sites-available/healthcheck > /dev/null <<EOF
server {
    listen 8080;
    server_name _;
    
    root /var/www/html;
    index healthcheck.php;
    
    location / {
        try_files \$uri \$uri/ =404;
    }
    
    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
    }
}
EOF

# Активируем сайт
sudo ln -sf /etc/nginx/sites-available/healthcheck /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Настраиваем firewall
print_step "Настраиваем firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 19999/tcp comment "Netdata monitoring"
    sudo ufw allow 8080/tcp comment "Healthcheck endpoint"
    print_success "UFW firewall настроен"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=19999/tcp
    sudo firewall-cmd --permanent --add-port=8080/tcp
    sudo firewall-cmd --reload
    print_success "Firewalld настроен"
fi

# Запускаем сервисы
print_step "Запускаем сервисы..."
sudo systemctl enable netdata
sudo systemctl restart netdata

sudo systemctl enable nginx
sudo systemctl restart nginx

# Ждем запуска
sleep 3

# Проверяем статус
if systemctl is-active --quiet netdata; then
    print_success "Netdata запущен успешно"
else
    print_error "Netdata не запустился"
    exit 1
fi

if systemctl is-active --quiet nginx; then
    print_success "Nginx запущен успешно"
else
    print_error "Nginx не запустился"
    exit 1
fi

# Проверяем порты
SERVER_IP=$(hostname -I | awk '{print $1}')

if netstat -tlnp 2>/dev/null | grep -q ":19999"; then
    print_success "Netdata доступен: http://${SERVER_IP}:19999"
else
    print_error "Порт 19999 не открыт"
fi

if netstat -tlnp 2>/dev/null | grep -q ":8080"; then
    print_success "Healthcheck доступен: http://${SERVER_IP}:8080/healthcheck.php"
else
    print_error "Порт 8080 не открыт"
fi

print_success "🎉 Простой мониторинг установлен и работает!"
print_info "Управление:"
print_info "  • Netdata: sudo systemctl status netdata"
print_info "  • Nginx: sudo systemctl status nginx"
print_info "  • Healthcheck: curl http://localhost:8080/healthcheck.php"
print_info ""
print_info "💡 Это самый легкий вариант мониторинга!"
print_info "💡 Healthcheck показывает статус бота и системы!"
