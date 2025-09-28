#!/bin/bash
# Установка только Netdata (системный мониторинг)

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
    echo -e "${BLUE}📊 Netdata Only Setup (VPS Optimized)${NC}"
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
sudo systemctl start netdata

# Проверяем статус
if systemctl is-active --quiet netdata; then
    print_success "Netdata запущен"
    SERVER_IP=$(hostname -I | awk '{print $1}')
    print_success "Netdata доступен: http://${SERVER_IP}:19999"
else
    print_error "Netdata не запустился"
    exit 1
fi

print_success "🎉 Netdata установлен и работает!"
