#!/bin/bash
# Скрипт управления мониторингом

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🔧 Управление мониторингом AntiSpam Bot${NC}"
    echo -e "${BLUE}======================================${NC}"
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

show_help() {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  start     - Запустить мониторинг"
    echo "  stop      - Остановить мониторинг"
    echo "  restart   - Перезапустить мониторинг"
    echo "  status    - Показать статус"
    echo "  logs      - Показать логи"
    echo "  update    - Обновить образы"
    echo "  check     - Проверить мониторинг"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

start_monitoring() {
    print_info "Запуск мониторинга..."
    sudo systemctl start monitoring
    sleep 3
    
    if systemctl is-active --quiet monitoring; then
        print_success "Мониторинг запущен"
    else
        print_error "Не удалось запустить мониторинг"
        return 1
    fi
}

stop_monitoring() {
    print_info "Остановка мониторинга..."
    sudo systemctl stop monitoring
    
    if ! systemctl is-active --quiet monitoring; then
        print_success "Мониторинг остановлен"
    else
        print_error "Не удалось остановить мониторинг"
        return 1
    fi
}

restart_monitoring() {
    print_info "Перезапуск мониторинга..."
    sudo systemctl restart monitoring
    sleep 3
    
    if systemctl is-active --quiet monitoring; then
        print_success "Мониторинг перезапущен"
    else
        print_error "Не удалось перезапустить мониторинг"
        return 1
    fi
}

show_status() {
    print_info "Статус сервисов:"
    echo ""
    
    # Статус мониторинга
    if systemctl is-active --quiet monitoring; then
        print_success "Monitoring: Запущен"
    else
        print_error "Monitoring: Остановлен"
    fi
    
    # Статус бота
    if systemctl is-active --quiet antispam-bot; then
        print_success "AntiSpam Bot: Запущен"
    else
        print_error "AntiSpam Bot: Остановлен"
    fi
    
    # Статус Docker
    if systemctl is-active --quiet docker; then
        print_success "Docker: Запущен"
    else
        print_error "Docker: Остановлен"
    fi
    
    echo ""
    
    # Проверка портов
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    if netstat -tlnp 2>/dev/null | grep -q ":19999"; then
        print_success "Netdata: http://${SERVER_IP}:19999"
    else
        print_error "Netdata: Недоступен"
    fi
    
    if netstat -tlnp 2>/dev/null | grep -q ":3001"; then
        print_success "Uptime Kuma: http://${SERVER_IP}:3001"
    else
        print_error "Uptime Kuma: Недоступен"
    fi
}

show_logs() {
    print_info "Логи мониторинга:"
    echo ""
    
    if [ -d "monitoring" ]; then
        cd monitoring
        docker-compose logs --tail=50
        cd ..
    else
        print_error "Директория monitoring не найдена"
    fi
}

update_monitoring() {
    print_info "Обновление образов мониторинга..."
    
    if [ -d "monitoring" ]; then
        cd monitoring
        docker-compose pull
        docker-compose up -d
        print_success "Образы обновлены"
        cd ..
    else
        print_error "Директория monitoring не найдена"
        return 1
    fi
}

check_monitoring() {
    print_info "Проверка мониторинга..."
    
    if [ -f "scripts/check-monitoring.sh" ]; then
        chmod +x scripts/check-monitoring.sh
        ./scripts/check-monitoring.sh
    else
        print_error "Скрипт проверки не найден"
        return 1
    fi
}

# Основная логика
print_header

case "${1:-help}" in
    start)
        start_monitoring
        ;;
    stop)
        stop_monitoring
        ;;
    restart)
        restart_monitoring
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    update)
        update_monitoring
        ;;
    check)
        check_monitoring
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Неизвестная команда: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
