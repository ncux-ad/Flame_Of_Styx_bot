#!/bin/bash
# Быстрая установка мониторинга на сервере

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
    echo -e "${BLUE}🚀 Quick Monitoring Setup for AntiSpam Bot${NC}"
    echo -e "${BLUE}==========================================${NC}"
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

# Устанавливаем мониторинг
print_step "Устанавливаем мониторинг..."
chmod +x scripts/setup-monitoring.sh
./scripts/setup-monitoring.sh

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
sudo systemctl start monitoring.service

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
echo -e "${GREEN}🎉 УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo ""
echo -e "${CYAN}📊 Доступ к мониторингу:${NC}"
echo -e "  • ${GREEN}Netdata${NC}: http://${SERVER_IP}:19999"
echo -e "  • ${GREEN}Uptime Kuma${NC}: http://${SERVER_IP}:3001"
echo ""
echo -e "${CYAN}🔧 Управление:${NC}"
echo -e "  • ${YELLOW}Статус${NC}: sudo systemctl status monitoring"
echo -e "  • ${YELLOW}Логи${NC}: cd monitoring && docker-compose logs -f"
echo -e "  • ${YELLOW}Остановить${NC}: sudo systemctl stop monitoring"
echo -e "  • ${YELLOW}Запустить${NC}: sudo systemctl start monitoring"
echo ""
echo -e "${CYAN}📝 Следующие шаги:${NC}"
echo -e "  1. ${PURPLE}Откройте Netdata${NC} и настройте алерты"
echo -e "  2. ${PURPLE}Откройте Uptime Kuma${NC} и добавьте мониторинг бота"
echo -e "  3. ${PURPLE}Настройте уведомления${NC}"
echo ""
echo -e "${YELLOW}💡 Для SSH туннеля (рекомендуется):${NC}"
echo -e "  ssh -L 19999:localhost:19999 -L 3001:localhost:3001 ${USER}@${SERVER_IP}"
echo -e "  Затем откройте http://localhost:19999 и http://localhost:3001"
echo ""
