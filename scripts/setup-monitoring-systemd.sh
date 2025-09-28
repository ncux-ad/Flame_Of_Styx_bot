#!/bin/bash
# Установка мониторинга через systemd (без Docker)

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
    echo -e "${BLUE}🔧 Systemd Monitoring Setup for AntiSpam Bot${NC}"
    echo -e "${BLUE}============================================${NC}"
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

# Проверяем, что мы в правильной директории
if [[ ! -f "bot.py" ]]; then
    print_error "Запустите скрипт из корневой директории проекта!"
    exit 1
fi

print_success "Проверки пройдены"

# Создаем директорию для мониторинга
print_step "Создаем директорию мониторинга..."
mkdir -p monitoring/systemd
cd monitoring/systemd

# Устанавливаем Netdata
print_step "Устанавливаем Netdata..."

# Проверяем, установлен ли Netdata
if ! command -v netdata &> /dev/null; then
    print_info "Устанавливаем Netdata..."
    
    # Установка Netdata через пакетный менеджер
    if command -v apt &> /dev/null; then
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y netdata
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y epel-release
        sudo yum install -y netdata
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y netdata
    else
        print_error "Неподдерживаемый дистрибутив Linux"
        exit 1
    fi
    
    if command -v netdata &> /dev/null; then
        print_success "Netdata установлен"
    else
        print_error "Не удалось установить Netdata"
        exit 1
    fi
else
    print_success "Netdata уже установлен"
fi

# Устанавливаем Uptime Kuma
print_step "Устанавливаем Uptime Kuma..."

# Создаем пользователя для Uptime Kuma
if ! id "uptime-kuma" &>/dev/null; then
    sudo useradd -r -s /bin/false uptime-kuma
    print_success "Пользователь uptime-kuma создан"
else
    print_info "Пользователь uptime-kuma уже существует"
fi

# Создаем директорию для Uptime Kuma
sudo mkdir -p /opt/uptime-kuma
sudo chown uptime-kuma:uptime-kuma /opt/uptime-kuma

# Устанавливаем Node.js (если не установлен)
if ! command -v node &> /dev/null; then
    print_info "Устанавливаем Node.js..."
    
    # Установка Node.js через NodeSource
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    if command -v node &> /dev/null; then
        print_success "Node.js установлен"
    else
        print_error "Не удалось установить Node.js"
        exit 1
    fi
else
    print_success "Node.js уже установлен"
fi

# Устанавливаем Uptime Kuma
if [[ ! -d "/opt/uptime-kuma" ]]; then
    print_info "Скачиваем Uptime Kuma..."
    
    cd /tmp
    # Скачиваем релиз вместо master ветки
    wget https://github.com/louislam/uptime-kuma/archive/refs/tags/1.23.3.tar.gz
    tar -xzf 1.23.3.tar.gz
    sudo mv uptime-kuma-1.23.3/* /opt/uptime-kuma/
    sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma
    rm -rf uptime-kuma-1.23.3 1.23.3.tar.gz
    
    # Устанавливаем зависимости
    cd /opt/uptime-kuma
    sudo -u uptime-kuma npm install --production
    
    print_success "Uptime Kuma установлен"
else
    print_success "Uptime Kuma уже установлен"
fi

# Создаем systemd сервисы
print_step "Создаем systemd сервисы..."

# Сервис для Netdata
sudo tee /etc/systemd/system/netdata.service > /dev/null <<EOF
[Unit]
Description=Netdata Real-time Performance Monitoring
Documentation=https://docs.netdata.cloud
Wants=network-online.target
After=network-online.target

[Service]
Type=notify
ExecStart=/usr/sbin/netdata -D
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
Restart=on-failure
RestartSec=10
TimeoutStopSec=5
KillSignal=SIGTERM
User=netdata
Group=netdata

[Install]
WantedBy=multi-user.target
EOF

# Сервис для Uptime Kuma
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

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем и запускаем сервисы
print_step "Запускаем сервисы..."

# Netdata
sudo systemctl enable netdata
sudo systemctl start netdata

# Uptime Kuma
sudo systemctl enable uptime-kuma
sudo systemctl start uptime-kuma

# Ждем запуска
sleep 5

# Проверяем статус
print_step "Проверяем статус сервисов..."

if systemctl is-active --quiet netdata; then
    print_success "Netdata: Запущен"
else
    print_error "Netdata: Не запущен"
fi

if systemctl is-active --quiet uptime-kuma; then
    print_success "Uptime Kuma: Запущен"
else
    print_error "Uptime Kuma: Не запущен"
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

# Создаем скрипт управления
print_step "Создаем скрипт управления..."

cat > ../../scripts/monitoring-systemd-control.sh << 'EOF'
#!/bin/bash
# Управление мониторингом через systemd

case "${1:-help}" in
    start)
        sudo systemctl start netdata uptime-kuma
        echo "✅ Мониторинг запущен"
        ;;
    stop)
        sudo systemctl stop netdata uptime-kuma
        echo "✅ Мониторинг остановлен"
        ;;
    restart)
        sudo systemctl restart netdata uptime-kuma
        echo "✅ Мониторинг перезапущен"
        ;;
    status)
        echo "=== Netdata ==="
        sudo systemctl status netdata --no-pager -l
        echo ""
        echo "=== Uptime Kuma ==="
        sudo systemctl status uptime-kuma --no-pager -l
        ;;
    logs)
        echo "=== Netdata Logs ==="
        sudo journalctl -u netdata -n 20 --no-pager
        echo ""
        echo "=== Uptime Kuma Logs ==="
        sudo journalctl -u uptime-kuma -n 20 --no-pager
        ;;
    enable)
        sudo systemctl enable netdata uptime-kuma
        echo "✅ Автозапуск включен"
        ;;
    disable)
        sudo systemctl disable netdata uptime-kuma
        echo "✅ Автозапуск отключен"
        ;;
    help|--help|-h)
        echo "Использование: $0 [команда]"
        echo ""
        echo "Команды:"
        echo "  start     - Запустить мониторинг"
        echo "  stop      - Остановить мониторинг"
        echo "  restart   - Перезапустить мониторинг"
        echo "  status    - Показать статус"
        echo "  logs      - Показать логи"
        echo "  enable    - Включить автозапуск"
        echo "  disable   - Отключить автозапуск"
        echo "  help      - Показать эту справку"
        ;;
    *)
        echo "❌ Неизвестная команда: $1"
        echo "Используйте: $0 help"
        exit 1
        ;;
esac
EOF

chmod +x ../../scripts/monitoring-systemd-control.sh

print_success "Скрипт управления создан: scripts/monitoring-systemd-control.sh"

# Возвращаемся в корневую директорию
cd ../..

echo ""
print_success "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo ""
print_info "📊 Доступ к мониторингу:"
echo -e "  • ${GREEN}Netdata${NC}: http://${SERVER_IP}:19999"
echo -e "  • ${GREEN}Uptime Kuma${NC}: http://${SERVER_IP}:3001"
echo ""
print_info "🔧 Управление:"
echo -e "  • ${YELLOW}Статус${NC}: ./scripts/monitoring-systemd-control.sh status"
echo -e "  • ${YELLOW}Логи${NC}: ./scripts/monitoring-systemd-control.sh logs"
echo -e "  • ${YELLOW}Остановить${NC}: ./scripts/monitoring-systemd-control.sh stop"
echo -e "  • ${YELLOW}Запустить${NC}: ./scripts/monitoring-systemd-control.sh start"
echo ""
print_info "💡 Преимущества systemd версии:"
echo -e "  • ${CYAN}Нет зависимости от Docker${NC}"
echo -e "  • ${CYAN}Лучшая производительность${NC}"
echo -e "  • ${CYAN}Интеграция с systemd${NC}"
echo -e "  • ${CYAN}Автозапуск при загрузке${NC}"
echo ""
