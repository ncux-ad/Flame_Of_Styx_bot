#!/bin/bash
# Упрощенная установка мониторинга (только Docker версия)

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
    echo -e "${BLUE}🚀 Simple Monitoring Setup for AntiSpam Bot${NC}"
    echo -e "${BLUE}===========================================${NC}"
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

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker не установлен. Установите Docker сначала:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    echo "   sudo usermod -aG docker $USER"
    echo "   newgrp docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose не установлен. Установите Docker Compose сначала."
    exit 1
fi

# Проверяем, что мы в правильной директории
if [[ ! -f "bot.py" ]]; then
    print_error "Запустите скрипт из корневой директории проекта!"
    exit 1
fi

# Проверяем права на Docker
if ! docker ps &> /dev/null; then
    print_error "Нет прав на Docker. Добавьте пользователя в группу docker:"
    echo "   sudo usermod -aG docker $USER"
    echo "   newgrp docker"
    exit 1
fi

print_success "Проверки пройдены"

# Останавливаем бота
print_step "Останавливаем бота..."
if systemctl is-active --quiet antispam-bot; then
    sudo systemctl stop antispam-bot
    print_success "Бот остановлен"
else
    print_info "Бот не был запущен"
fi

# Обновляем код
print_step "Обновляем код..."
git pull origin master
print_success "Код обновлен"

# Создаем Docker Compose файл
print_step "Создаем Docker Compose файл..."
mkdir -p monitoring

cat > monitoring/docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Netdata - мониторинг сервера (CPU, RAM, диск, сеть)
  netdata:
    image: netdata/netdata:latest
    container_name: netdata
    hostname: antispam-bot-monitor
    ports:
      - "19999:19999"
    volumes:
      - netdataconfig:/etc/netdata
      - netdatalib:/var/lib/netdata
      - netdatacache:/var/cache/netdata
      - /etc/passwd:/host/etc/passwd:ro
      - /etc/group:/host/etc/group:ro
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /etc/os-release:/host/etc/os-release:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    cap_add:
      - SYS_PTRACE
      - SYS_ADMIN
    security_opt:
      - apparmor:unconfined
    environment:
      - NETDATA_CLAIM_TOKEN=${NETDATA_CLAIM_TOKEN:-}
      - NETDATA_CLAIM_URL=${NETDATA_CLAIM_URL:-https://app.netdata.cloud}
      - NETDATA_CLAIM_ROOMS=${NETDATA_CLAIM_ROOMS:-}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:19999/api/v1/info"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Uptime Kuma - мониторинг доступности бота
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    container_name: uptime-kuma
    ports:
      - "3001:3001"
    volumes:
      - uptime-kuma-data:/app/data
    environment:
      - UPTIME_KUMA_DISABLE_FRAME_SAMEORIGIN=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3001"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  netdataconfig:
  netdatalib:
  netdatacache:
  uptime-kuma-data:
EOF

print_success "Docker Compose файл создан"

# Запускаем мониторинг
print_step "Запускаем мониторинг..."
cd monitoring
docker-compose up -d

# Ждем запуска
sleep 10

# Проверяем статус
print_step "Проверяем статус..."
if docker-compose ps | grep -q "Up"; then
    print_success "Мониторинг запущен"
else
    print_error "Не удалось запустить мониторинг"
    docker-compose logs
    exit 1
fi

cd ..

# Создаем systemd сервис
print_step "Настраиваем автозапуск..."
sudo tee /etc/systemd/system/monitoring.service > /dev/null <<EOF
[Unit]
Description=Monitoring Services (Netdata + Uptime Kuma)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)/monitoring
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
sudo systemctl daemon-reload
sudo systemctl enable monitoring.service

print_success "Мониторинг настроен и запущен"

# Запускаем бота
print_step "Запускаем бота..."
sudo systemctl start antispam-bot

# Ждем запуска
sleep 3

# Проверяем статус
print_step "Проверяем статус..."
echo ""
echo -e "${BLUE}=== СТАТУС СЕРВИСОВ ===${NC}"
sudo systemctl status antispam-bot --no-pager -l
echo ""
sudo systemctl status monitoring --no-pager -l
echo ""

# Настраиваем firewall
print_step "Настраиваем firewall..."

# Проверяем, какой firewall используется
if command -v ufw &> /dev/null; then
    print_info "Настраиваем UFW firewall..."
    sudo ufw allow 19999/tcp comment "Netdata monitoring"
    sudo ufw allow 3001/tcp comment "Uptime Kuma monitoring"
    print_success "UFW firewall настроен"
elif command -v firewall-cmd &> /dev/null; then
    print_info "Настраиваем firewalld..."
    sudo firewall-cmd --permanent --add-port=19999/tcp
    sudo firewall-cmd --permanent --add-port=3001/tcp
    sudo firewall-cmd --reload
    print_success "Firewalld настроен"
elif command -v iptables &> /dev/null; then
    print_info "Настраиваем iptables..."
    sudo iptables -A INPUT -p tcp --dport 19999 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 3001 -j ACCEPT
    print_success "iptables настроен"
else
    print_warning "Firewall не найден. Настройте вручную порты 19999 и 3001"
fi

# Проверяем порты
echo -e "${BLUE}=== ПРОВЕРКА ПОРТОВ ===${NC}"
SERVER_IP=$(hostname -I | awk '{print $1}')

if netstat -tlnp 2>/dev/null | grep -q ":19999"; then
    print_success "Netdata: http://${SERVER_IP}:19999"
else
    print_error "Netdata не запущен"
fi

if netstat -tlnp 2>/dev/null | grep -q ":3001"; then
    print_success "Uptime Kuma: http://${SERVER_IP}:3001"
else
    print_error "Uptime Kuma не запущен"
fi

echo ""
print_success "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo ""
print_info "📊 Доступ к мониторингу:"
echo -e "  • ${GREEN}Netdata${NC}: http://${SERVER_IP}:19999"
echo -e "  • ${GREEN}Uptime Kuma${NC}: http://${SERVER_IP}:3001"
echo ""
print_info "🔧 Управление:"
echo -e "  • ${YELLOW}Статус${NC}: sudo systemctl status monitoring"
echo -e "  • ${YELLOW}Логи${NC}: cd monitoring && docker-compose logs -f"
echo -e "  • ${YELLOW}Остановить${NC}: sudo systemctl stop monitoring"
echo -e "  • ${YELLOW}Запустить${NC}: sudo systemctl start monitoring"
echo ""
print_info "💡 Для SSH туннеля (рекомендуется):"
echo -e "  ssh -L 19999:localhost:19999 -L 3001:localhost:3001 ${USER}@${SERVER_IP}"
echo -e "  Затем откройте http://localhost:19999 и http://localhost:3001"
echo ""
