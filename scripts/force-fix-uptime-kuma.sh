#!/bin/bash
# Принудительное исправление Uptime Kuma

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
    echo -e "${BLUE}🔨 Force Fix Uptime Kuma${NC}"
    echo -e "${BLUE}=======================${NC}"
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

# Останавливаем сервис
print_step "Останавливаем Uptime Kuma..."
sudo systemctl stop uptime-kuma 2>/dev/null || true

# Удаляем старую установку
print_step "Удаляем старую установку..."
sudo rm -rf /opt/uptime-kuma/*

# Создаем пользователя заново
print_step "Пересоздаем пользователя..."
sudo userdel uptime-kuma 2>/dev/null || true
sudo useradd -r -s /bin/false -m uptime-kuma
sudo chown -R uptime-kuma:uptime-kuma /home/uptime-kuma

# Создаем директорию
print_step "Создаем директорию..."
sudo mkdir -p /opt/uptime-kuma
sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma

# Скачиваем Uptime Kuma
print_step "Скачиваем Uptime Kuma..."
cd /tmp
rm -rf uptime-kuma-1.23.3 1.23.3.tar.gz 2>/dev/null || true

wget https://github.com/louislam/uptime-kuma/archive/refs/tags/1.23.3.tar.gz
tar -xzf 1.23.3.tar.gz

# Копируем файлы
print_step "Копируем файлы..."
sudo cp -r uptime-kuma-1.23.3/* /opt/uptime-kuma/
sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma

# Очищаем
rm -rf uptime-kuma-1.23.3 1.23.3.tar.gz

# Устанавливаем зависимости как root
print_step "Устанавливаем зависимости (root метод)..."
cd /opt/uptime-kuma

# Устанавливаем как root
sudo npm install --production --omit=dev --force

# Меняем владельца
sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma

# Проверяем установку
print_step "Проверяем установку..."
if [[ -f "package.json" ]] && [[ -d "node_modules" ]]; then
    print_success "Зависимости установлены"
else
    print_error "Зависимости не установлены"
    exit 1
fi

# Создаем systemd сервис
print_step "Создаем systemd сервис..."
sudo tee /etc/systemd/system/uptime-kuma.service > /dev/null <<EOF
[Unit]
Description=Uptime Kuma - A fancy self-hosted monitoring tool
Documentation=https://github.com/louislam/uptime-kuma
After=network.target

[Service]
Type=simple
User=uptime-kuma
Group=uptime-kuma
WorkingDirectory=/opt/uptime-kuma
ExecStart=/usr/bin/node server/server.js
Restart=on-failure
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=3001
Environment=HOST=0.0.0.0

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
sudo systemctl daemon-reload

# Тестируем запуск
print_step "Тестируем запуск..."
cd /opt/uptime-kuma

# Запускаем в фоне для теста
sudo -u uptime-kuma timeout 10s node server/server.js &
TEST_PID=$!

sleep 5

# Проверяем, запустился ли
if kill -0 $TEST_PID 2>/dev/null; then
    print_success "Uptime Kuma запускается корректно"
    kill $TEST_PID 2>/dev/null || true
else
    print_error "Uptime Kuma не запускается"
    print_info "Попробуем запустить вручную:"
    sudo -u uptime-kuma node server/server.js 2>&1 | head -20
    exit 1
fi

# Запускаем сервис
print_step "Запускаем сервис..."
sudo systemctl start uptime-kuma

sleep 3

# Проверяем статус
if systemctl is-active --quiet uptime-kuma; then
    print_success "Uptime Kuma запущен успешно"
    
    # Проверяем порт
    if netstat -tlnp 2>/dev/null | grep -q ":3001"; then
        SERVER_IP=$(hostname -I | awk '{print $1}')
        print_success "Uptime Kuma доступен: http://${SERVER_IP}:3001"
    else
        print_error "Порт 3001 не открыт"
    fi
else
    print_error "Uptime Kuma не запустился"
    print_info "Логи сервиса:"
    sudo journalctl -u uptime-kuma -n 20 --no-pager
    exit 1
fi

print_success "🎉 Uptime Kuma принудительно исправлен и работает!"
