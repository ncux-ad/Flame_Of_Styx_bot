#!/bin/bash
# Простая установка Uptime Kuma без сборки (используем готовую версию)

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
    echo -e "${BLUE}🚀 Simple Uptime Kuma Setup (No Build)${NC}"
    echo -e "${BLUE}=====================================${NC}"
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

# Останавливаем существующий сервис
print_step "Останавливаем существующий сервис..."
sudo systemctl stop uptime-kuma 2>/dev/null || true

# Удаляем старую установку
print_step "Удаляем старую установку..."
sudo rm -rf /opt/uptime-kuma
sudo rm -rf /home/uptime-kuma/uptime-kuma

# Создаем пользователя
print_step "Создаем пользователя uptime-kuma..."
sudo userdel uptime-kuma 2>/dev/null || true
sudo rm -rf /home/uptime-kuma
sudo useradd -m -s /bin/bash uptime-kuma

# Создаем директории
print_step "Создаем директории..."
sudo mkdir -p /opt/uptime-kuma
sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma

# Устанавливаем права на домашнюю директорию
sudo chown -R uptime-kuma:uptime-kuma /home/uptime-kuma
sudo chmod 755 /home/uptime-kuma

# Скачиваем готовую версию Uptime Kuma
print_step "Скачиваем готовую версию Uptime Kuma..."
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

# Устанавливаем только production зависимости
print_step "Устанавливаем production зависимости..."
cd /opt/uptime-kuma

# Увеличиваем лимит памяти
export NODE_OPTIONS="--max-old-space-size=512"

# Устанавливаем как root, потом меняем владельца
sudo npm install --production --no-optional --no-audit --no-fund
sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma

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
# Ограничения ресурсов для слабого VPS
MemoryLimit=256M
CPUQuota=25%

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
sudo systemctl daemon-reload

# Запускаем сервис
print_step "Запускаем сервис..."
sudo systemctl start uptime-kuma

# Ждем запуска
sleep 5

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

# Настраиваем firewall
print_step "Настраиваем firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 3001/tcp comment "Uptime Kuma monitoring" 2>/dev/null || true
    print_success "UFW firewall настроен"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=3001/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
    print_success "Firewalld настроен"
fi

print_success "🎉 Uptime Kuma установлен и работает!"
print_info "Управление:"
print_info "  • Статус: sudo systemctl status uptime-kuma"
print_info "  • Логи: sudo journalctl -u uptime-kuma -f"
print_info "  • Перезапуск: sudo systemctl restart uptime-kuma"
print_info "  • Остановка: sudo systemctl stop uptime-kuma"
