#!/bin/bash
# Только Netdata - самый простой вариант для VPS

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
    echo -e "${BLUE}📊 Netdata Only - Simple VPS Setup${NC}"
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

# Настраиваем firewall
print_step "Настраиваем firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 19999/tcp comment "Netdata monitoring"
    print_success "UFW firewall настроен"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=19999/tcp
    sudo firewall-cmd --reload
    print_success "Firewalld настроен"
fi

# Запускаем Netdata
print_step "Запускаем Netdata..."
sudo systemctl enable netdata
sudo systemctl restart netdata

# Ждем запуска
sleep 3

# Проверяем статус
if systemctl is-active --quiet netdata; then
    print_success "Netdata запущен успешно"
    
    # Проверяем порт
    if netstat -tlnp 2>/dev/null | grep -q ":19999"; then
        SERVER_IP=$(hostname -I | awk '{print $1}')
        print_success "Netdata доступен: http://${SERVER_IP}:19999"
    else
        print_error "Порт 19999 не открыт"
    fi
else
    print_error "Netdata не запустился"
    print_info "Логи сервиса:"
    sudo journalctl -u netdata -n 10 --no-pager
    exit 1
fi

print_success "🎉 Netdata установлен и работает!"
print_info "Управление:"
print_info "  • Статус: sudo systemctl status netdata"
print_info "  • Логи: sudo journalctl -u netdata -f"
print_info "  • Перезапуск: sudo systemctl restart netdata"
print_info "  • Остановка: sudo systemctl stop netdata"
print_info ""
print_info "💡 Это самый легкий вариант мониторинга для VPS!"
