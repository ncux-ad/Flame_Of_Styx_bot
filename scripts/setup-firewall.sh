#!/bin/bash
# Настройка firewall для мониторинга

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для красивого вывода
print_header() {
    echo -e "${BLUE}🛡️ Firewall Setup for Monitoring${NC}"
    echo -e "${BLUE}===============================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
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

# Проверяем, что мы на сервере
if [[ "$USER" == "root" ]]; then
    print_error "Не запускайте скрипт от root! Используйте обычного пользователя."
    exit 1
fi

print_step "Настраиваем firewall для мониторинга..."

# Проверяем, какой firewall используется
if command -v ufw &> /dev/null; then
    print_info "Настраиваем UFW firewall..."
    
    # Открываем порты для мониторинга
    sudo ufw allow 19999/tcp comment "Netdata monitoring"
    sudo ufw allow 3001/tcp comment "Uptime Kuma monitoring"
    
    # Включаем UFW если не включен
    if ! sudo ufw status | grep -q "Status: active"; then
        print_info "Включаем UFW firewall..."
        sudo ufw --force enable
    fi
    
    print_success "UFW firewall настроен"
    echo ""
    print_info "Статус UFW:"
    sudo ufw status
    
elif command -v firewall-cmd &> /dev/null; then
    print_info "Настраиваем firewalld..."
    
    # Открываем порты
    sudo firewall-cmd --permanent --add-port=19999/tcp
    sudo firewall-cmd --permanent --add-port=3001/tcp
    sudo firewall-cmd --reload
    
    print_success "Firewalld настроен"
    echo ""
    print_info "Открытые порты:"
    sudo firewall-cmd --list-ports
    
elif command -v iptables &> /dev/null; then
    print_info "Настраиваем iptables..."
    
    # Открываем порты
    sudo iptables -A INPUT -p tcp --dport 19999 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 3001 -j ACCEPT
    
    # Сохраняем правила
    if command -v iptables-save &> /dev/null; then
        sudo iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
    fi
    
    print_success "iptables настроен"
    echo ""
    print_info "Правила iptables:"
    sudo iptables -L | grep -E "(19999|3001)"
    
else
    print_warning "Firewall не найден. Настройте вручную:"
    echo "  • Откройте порты 19999 и 3001"
    echo "  • Настройте правила безопасности"
    echo ""
    print_info "Ручная настройка:"
    echo "  # UFW:"
    echo "  sudo ufw allow 19999/tcp"
    echo "  sudo ufw allow 3001/tcp"
    echo ""
    echo "  # Firewalld:"
    echo "  sudo firewall-cmd --permanent --add-port=19999/tcp"
    echo "  sudo firewall-cmd --permanent --add-port=3001/tcp"
    echo "  sudo firewall-cmd --reload"
    echo ""
    echo "  # iptables:"
    echo "  sudo iptables -A INPUT -p tcp --dport 19999 -j ACCEPT"
    echo "  sudo iptables -A INPUT -p tcp --dport 3001 -j ACCEPT"
    exit 1
fi

# Проверяем порты
print_step "Проверяем порты..."
SERVER_IP=$(hostname -I | awk '{print $1}')

if netstat -tlnp 2>/dev/null | grep -q ":19999"; then
    print_success "Netdata: http://${SERVER_IP}:19999"
else
    print_error "Netdata: Порт 19999 не открыт"
fi

if netstat -tlnp 2>/dev/null | grep -q ":3001"; then
    print_success "Uptime Kuma: http://${SERVER_IP}:3001"
else
    print_error "Uptime Kuma: Порт 3001 не открыт"
fi

echo ""
print_success "🎉 Firewall настроен!"
echo ""
print_info "📊 Доступ к мониторингу:"
echo -e "  • ${GREEN}Netdata${NC}: http://${SERVER_IP}:19999"
echo -e "  • ${GREEN}Uptime Kuma${NC}: http://${SERVER_IP}:3001"
echo ""
print_info "🔒 Безопасность:"
echo -e "  • ${YELLOW}Порты открыты только для мониторинга${NC}"
echo -e "  • ${YELLOW}Остальные порты заблокированы${NC}"
echo -e "  • ${YELLOW}Рекомендуется использовать SSH туннель${NC}"
echo ""
print_info "💡 SSH туннель (рекомендуется):"
echo -e "  ssh -L 19999:localhost:19999 -L 3001:localhost:3001 ${USER}@${SERVER_IP}"
echo -e "  Затем откройте http://localhost:19999 и http://localhost:3001"
echo ""
