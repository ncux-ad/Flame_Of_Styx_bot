#!/bin/bash
# Docker fallback для мониторинга (если systemd не работает)

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
    echo -e "${BLUE}🐳 Docker Fallback Monitoring${NC}"
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

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker не установлен. Установите Docker сначала:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    echo "   sudo usermod -aG docker $USER"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose не установлен. Установите Docker Compose сначала."
    exit 1
fi

print_success "Docker проверен"

# Создаем Docker Compose файл
print_step "Создаем Docker Compose файл..."
mkdir -p monitoring

cat > monitoring/docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Netdata - мониторинг сервера
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
    restart: unless-stopped

  # Uptime Kuma - мониторинг доступности
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    container_name: uptime-kuma
    ports:
      - "3001:3001"
    volumes:
      - uptime-kuma-data:/app/data
    restart: unless-stopped

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

# Создаем systemd сервис для Docker
print_step "Создаем systemd сервис для Docker..."
sudo tee /etc/systemd/system/monitoring-docker.service > /dev/null <<EOF
[Unit]
Description=Monitoring Services (Docker)
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
sudo systemctl enable monitoring-docker.service

print_success "Docker мониторинг настроен"

# Проверяем порты
print_step "Проверяем порты..."
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

print_success "🎉 Docker мониторинг установлен и работает!"
