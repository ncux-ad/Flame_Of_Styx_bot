#!/bin/bash
# Оптимизированная установка Uptime Kuma для слабого VPS

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
    echo -e "${BLUE}🚀 VPS Optimized Uptime Kuma Setup${NC}"
    echo -e "${BLUE}===================================${NC}"
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

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_header

# Проверяем права
if [[ $EUID -eq 0 ]]; then
    print_error "Не запускайте скрипт от root!"
    exit 1
fi

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

# Клонируем репозиторий
print_step "Клонируем Uptime Kuma..."
cd /home/uptime-kuma
sudo -u uptime-kuma git clone https://github.com/louislam/uptime-kuma.git

# Переходим в директорию
cd uptime-kuma

# Устанавливаем зависимости с оптимизацией для VPS
print_step "Устанавливаем зависимости (VPS оптимизация)..."
print_warning "Это может занять время на слабом VPS..."

# Увеличиваем лимит памяти для npm
export NODE_OPTIONS="--max-old-space-size=512"

# Устанавливаем только production зависимости
sudo -u uptime-kuma npm install --production --no-optional --no-audit --no-fund

# Собираем проект
print_step "Собираем проект..."
sudo -u uptime-kuma npm run build

# Копируем в /opt
print_step "Копируем в /opt..."
sudo cp -r /home/uptime-kuma/uptime-kuma/* /opt/uptime-kuma/
sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma

# Очищаем временные файлы
sudo rm -rf /home/uptime-kuma/uptime-kuma

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
ExecStart=/usr/bin/npm run start-server
Restart=on-failure
RestartSec=10
Environment=NODE_ENV=production
Environment=PORT=3001
Environment=HOST=0.0.0.0
# Ограничения ресурсов для слабого VPS
MemoryLimit=512M
CPUQuota=50%

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
