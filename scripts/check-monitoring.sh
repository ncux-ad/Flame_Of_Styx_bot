#!/bin/bash
# Скрипт проверки мониторинга

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🔍 Проверка мониторинга AntiSpam Bot${NC}"
    echo -e "${BLUE}====================================${NC}"
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

print_header

# Проверяем статус сервисов
echo -e "${PURPLE}📊 Статус сервисов:${NC}"
echo ""

# Проверяем бота
if systemctl is-active --quiet antispam-bot; then
    print_success "AntiSpam Bot: Запущен"
else
    print_error "AntiSpam Bot: Остановлен"
fi

# Проверяем мониторинг
if systemctl is-active --quiet monitoring; then
    print_success "Monitoring: Запущен"
else
    print_error "Monitoring: Остановлен"
fi

# Проверяем Docker
if systemctl is-active --quiet docker; then
    print_success "Docker: Запущен"
else
    print_error "Docker: Остановлен"
fi

echo ""

# Проверяем порты
echo -e "${PURPLE}🌐 Проверка портов:${NC}"
echo ""

SERVER_IP=$(hostname -I | awk '{print $1}')

# Проверяем Netdata
if netstat -tlnp 2>/dev/null | grep -q ":19999"; then
    print_success "Netdata: http://${SERVER_IP}:19999"
    
    # Проверяем доступность
    if curl -s http://localhost:19999 > /dev/null 2>&1; then
        print_success "Netdata: Доступен"
    else
        print_warning "Netdata: Порт открыт, но сервис недоступен"
    fi
else
    print_error "Netdata: Не запущен (порт 19999)"
fi

# Проверяем Uptime Kuma
if netstat -tlnp 2>/dev/null | grep -q ":3001"; then
    print_success "Uptime Kuma: http://${SERVER_IP}:3001"
    
    # Проверяем доступность
    if curl -s http://localhost:3001 > /dev/null 2>&1; then
        print_success "Uptime Kuma: Доступен"
    else
        print_warning "Uptime Kuma: Порт открыт, но сервис недоступен"
    fi
else
    print_error "Uptime Kuma: Не запущен (порт 3001)"
fi

echo ""

# Проверяем Docker контейнеры
echo -e "${PURPLE}🐳 Docker контейнеры:${NC}"
echo ""

if command -v docker &> /dev/null; then
    cd monitoring 2>/dev/null || {
        print_error "Директория monitoring не найдена"
        exit 1
    }
    
    if docker-compose ps | grep -q "Up"; then
        print_success "Контейнеры мониторинга запущены:"
        docker-compose ps
    else
        print_error "Контейнеры мониторинга не запущены"
        docker-compose ps
    fi
    
    cd ..
else
    print_error "Docker не установлен"
fi

echo ""

# Проверяем логи
echo -e "${PURPLE}📝 Последние логи:${NC}"
echo ""

# Логи бота
if systemctl is-active --quiet antispam-bot; then
    print_info "Логи AntiSpam Bot (последние 5 строк):"
    sudo journalctl -u antispam-bot -n 5 --no-pager
    echo ""
fi

# Логи мониторинга
if systemctl is-active --quiet monitoring; then
    print_info "Логи мониторинга (последние 5 строк):"
    sudo journalctl -u monitoring -n 5 --no-pager
    echo ""
fi

# Проверяем использование ресурсов
echo -e "${PURPLE}💻 Использование ресурсов:${NC}"
echo ""

# CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    print_warning "CPU: ${CPU_USAGE}% (высокая загрузка)"
else
    print_success "CPU: ${CPU_USAGE}%"
fi

# Memory
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
    print_warning "Memory: ${MEMORY_USAGE}% (высокое использование)"
else
    print_success "Memory: ${MEMORY_USAGE}%"
fi

# Disk
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
if (( DISK_USAGE > 90 )); then
    print_warning "Disk: ${DISK_USAGE}% (мало места)"
else
    print_success "Disk: ${DISK_USAGE}%"
fi

echo ""

# Рекомендации
echo -e "${PURPLE}💡 Рекомендации:${NC}"
echo ""

if ! systemctl is-active --quiet antispam-bot; then
    print_info "Запустите бота: sudo systemctl start antispam-bot"
fi

if ! systemctl is-active --quiet monitoring; then
    print_info "Запустите мониторинг: sudo systemctl start monitoring"
fi

if ! netstat -tlnp 2>/dev/null | grep -q ":19999"; then
    print_info "Netdata не запущен. Проверьте: cd monitoring && docker-compose logs netdata"
fi

if ! netstat -tlnp 2>/dev/null | grep -q ":3001"; then
    print_info "Uptime Kuma не запущен. Проверьте: cd monitoring && docker-compose logs uptime-kuma"
fi

echo ""
echo -e "${CYAN}🔧 Полезные команды:${NC}"
echo -e "  • ${YELLOW}Перезапустить мониторинг${NC}: sudo systemctl restart monitoring"
echo -e "  • ${YELLOW}Просмотр логов${NC}: cd monitoring && docker-compose logs -f"
echo -e "  • ${YELLOW}Статус всех сервисов${NC}: sudo systemctl status antispam-bot monitoring"
echo -e "  • ${YELLOW}SSH туннель${NC}: ssh -L 19999:localhost:19999 -L 3001:localhost:3001 ${USER}@${SERVER_IP}"
echo ""
