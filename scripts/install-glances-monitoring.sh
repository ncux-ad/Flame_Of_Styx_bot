#!/bin/bash
# Установка Glances - легкий мониторинг для VPS

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
    echo -e "${BLUE}👁️ Glances Monitoring Setup${NC}"
    echo -e "${BLUE}============================${NC}"
    echo -e "${YELLOW}💡 Легкий Python-мониторинг с веб-интерфейсом${NC}"
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

# Проверяем Python
print_step "Проверяем Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 не установлен"
    exit 1
fi

# Устанавливаем Glances в venv
print_step "Устанавливаем Glances в виртуальное окружение..."
pip install glances[web]

# Находим путь к glances в venv
GLANCES_PATH=$(which glances)
if [ -z "$GLANCES_PATH" ]; then
    # Ищем в venv
    GLANCES_PATH="./venv/bin/glances"
    if [ ! -f "$GLANCES_PATH" ]; then
        GLANCES_PATH="/usr/local/bin/glances"
    fi
fi

print_info "Glances установлен в: $GLANCES_PATH"

# Обновляем путь для systemd (будет в /home/glances/venv/bin/glances)
GLANCES_SYSTEMD_PATH="/home/glances/venv/bin/glances"

# Создаем пользователя для Glances
print_step "Создаем пользователя glances..."
sudo userdel glances 2>/dev/null || true
sudo useradd -r -s /bin/false -m glances 2>/dev/null || {
    print_warning "Пользователь glances уже существует, продолжаем..."
}

# Копируем venv для glances
print_step "Копируем виртуальное окружение для glances..."
sudo cp -r venv /home/glances/
sudo chown -R glances:glances /home/glances/venv

# Проверяем что пользователь glances существует
if ! id glances >/dev/null 2>&1; then
    print_error "Пользователь glances не создан!"
    exit 1
fi

# Создаем конфигурацию Glances
print_step "Создаем конфигурацию Glances..."
sudo mkdir -p /etc/glances
# Удаляем старый конфиг если есть
sudo rm -f /etc/glances/glances.conf
sudo tee /etc/glances/glances.conf > /dev/null <<EOF
[global]
# Основные настройки
refresh = 2
time = 10
one_shot = False
percpu = True
disable_plugin = docker,raid,ip,folders,ports,processcount,processlist,processlistfast,quicklook,system,uptime,load,mem,memswap,network,diskio,fs,now,alert,amps,cloud,gpu,containers,chart,psutilversion,smart,wifi

# Веб-интерфейс
web_server = True
web_server_port = 8080
web_server_host = 0.0.0.0

# REST API
rest_api = True
rest_api_port = 61208
rest_api_host = 0.0.0.0

# Логирование
log_file = /var/log/glances.log
log_level = INFO

# Ограничения для VPS
disable_plugin = docker,raid,ip,folders,ports,processcount,processlist,processlistfast,quicklook,system,uptime,load,mem,memswap,network,diskio,fs,now,alert,amps,cloud,gpu,containers,chart,psutilversion,raid,smart,wifi
EOF

# Создаем systemd сервис
print_step "Создаем systemd сервис..."
sudo tee /etc/systemd/system/glances.service > /dev/null <<EOF
[Unit]
Description=Glances - Real-time system monitoring
Documentation=https://github.com/nicolargo/glances
After=network.target

[Service]
Type=simple
User=glances
Group=glances
WorkingDirectory=/home/glances
ExecStart=$GLANCES_SYSTEMD_PATH -w --port 61208 --bind 0.0.0.0
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/home/glances/venv/bin:/usr/local/bin:/usr/bin:/bin

# Ограничения ресурсов для VPS
MemoryLimit=64M
CPUQuota=10%

[Install]
WantedBy=multi-user.target
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
    listen 8081;
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
    sudo ufw allow 8080/tcp comment "Glances web interface"
    sudo ufw allow 61208/tcp comment "Glances REST API"
    sudo ufw allow 8081/tcp comment "Healthcheck endpoint"
    print_success "UFW firewall настроен"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=8080/tcp
    sudo firewall-cmd --permanent --add-port=61208/tcp
    sudo firewall-cmd --permanent --add-port=8081/tcp
    sudo firewall-cmd --reload
    print_success "Firewalld настроен"
fi

# Запускаем сервисы
print_step "Запускаем сервисы..."
sudo systemctl daemon-reload
sudo systemctl enable glances
sudo systemctl start glances

sudo systemctl enable nginx
sudo systemctl restart nginx

# Ждем запуска
sleep 5

# Проверяем статус
if systemctl is-active --quiet glances; then
    print_success "Glances запущен успешно"
else
    print_error "Glances не запустился"
    print_info "Логи сервиса:"
    sudo journalctl -u glances -n 10 --no-pager
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

if netstat -tlnp 2>/dev/null | grep -q ":8080"; then
    print_success "Glances веб-интерфейс: http://${SERVER_IP}:8080"
else
    print_error "Порт 8080 не открыт"
fi

if netstat -tlnp 2>/dev/null | grep -q ":61208"; then
    print_success "Glances REST API: http://${SERVER_IP}:61208"
else
    print_error "Порт 61208 не открыт"
fi

if netstat -tlnp 2>/dev/null | grep -q ":8081"; then
    print_success "Healthcheck: http://${SERVER_IP}:8081/healthcheck.php"
else
    print_error "Порт 8081 не открыт"
fi

print_success "🎉 Glances мониторинг установлен и работает!"
print_info "Управление:"
print_info "  • Статус: sudo systemctl status glances"
print_info "  • Логи: sudo journalctl -u glances -f"
print_info "  • Перезапуск: sudo systemctl restart glances"
print_info "  • Остановка: sudo systemctl stop glances"
print_info ""
print_info "💡 Glances - самый легкий мониторинг для VPS!"
print_info "💡 Веб-интерфейс + REST API + Telegram-алерты!"
