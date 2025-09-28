#!/bin/bash
# Простая установка Uptime Kuma

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
    echo -e "${BLUE}🔧 Uptime Kuma Installation${NC}"
    echo -e "${BLUE}============================${NC}"
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

# Останавливаем сервис если запущен
print_step "Останавливаем Uptime Kuma..."
sudo systemctl stop uptime-kuma 2>/dev/null || true

# Создаем пользователя
print_step "Создаем пользователя..."
if ! id "uptime-kuma" &>/dev/null; then
    sudo useradd -r -s /bin/false -m uptime-kuma
    print_success "Пользователь создан"
else
    print_info "Пользователь уже существует"
fi

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
sudo rm -rf /opt/uptime-kuma/*
sudo cp -r uptime-kuma-1.23.3/* /opt/uptime-kuma/
sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma

# Очищаем
rm -rf uptime-kuma-1.23.3 1.23.3.tar.gz

# Устанавливаем зависимости
print_step "Устанавливаем зависимости..."
cd /opt/uptime-kuma
sudo -u uptime-kuma npm install --production --omit=dev

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

# Запускаем сервис
print_step "Запускаем сервис..."
sudo systemctl enable uptime-kuma
sudo systemctl start uptime-kuma

# Ждем запуска
sleep 5

# Проверяем статус
print_step "Проверяем статус..."
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
    print_info "Логи:"
    sudo journalctl -u uptime-kuma -n 10 --no-pager
    exit 1
fi

print_success "🎉 Uptime Kuma установлен и работает!"
