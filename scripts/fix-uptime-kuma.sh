#!/bin/bash
# Исправление Uptime Kuma

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
    echo -e "${BLUE}🔧 Uptime Kuma Fix${NC}"
    echo -e "${BLUE}=================${NC}"
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

# Останавливаем сервис
print_step "Останавливаем Uptime Kuma..."
sudo systemctl stop uptime-kuma

# Проверяем права доступа
print_step "Проверяем права доступа..."
sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma
sudo chmod -R 755 /opt/uptime-kuma

# Проверяем Node.js
print_step "Проверяем Node.js..."
if ! command -v node &> /dev/null; then
    print_error "Node.js не найден!"
    exit 1
fi

node_version=$(node --version)
print_info "Node.js версия: $node_version"

# Проверяем зависимости
print_step "Проверяем зависимости..."
cd /opt/uptime-kuma

if [[ ! -d "node_modules" ]]; then
    print_info "Устанавливаем зависимости..."
    sudo -u uptime-kuma npm install --production
else
    print_info "Зависимости уже установлены"
fi

# Проверяем файлы
print_step "Проверяем файлы..."
if [[ ! -f "package.json" ]] || [[ ! -f "server/server.js" ]]; then
    print_error "Файлы Uptime Kuma не найдены!"
    print_info "Переустанавливаем Uptime Kuma..."
    
    # Очищаем директорию
    sudo rm -rf /opt/uptime-kuma/*
    
    cd /tmp
    # Скачиваем стабильную версию
    wget https://github.com/louislam/uptime-kuma/archive/refs/tags/1.23.3.tar.gz
    tar -xzf 1.23.3.tar.gz
    
    # Копируем файлы
    sudo cp -r uptime-kuma-1.23.3/* /opt/uptime-kuma/
    sudo chown -R uptime-kuma:uptime-kuma /opt/uptime-kuma
    
    # Очищаем временные файлы
    rm -rf uptime-kuma-1.23.3 1.23.3.tar.gz
    
    print_success "Uptime Kuma переустановлен"
    
    # Переходим в директорию и устанавливаем зависимости
    cd /opt/uptime-kuma
    print_info "Устанавливаем зависимости..."
    sudo -u uptime-kuma npm install --production --omit=dev
else
    print_info "Файлы Uptime Kuma найдены"
fi

# Тестируем запуск
print_step "Тестируем запуск..."
cd /opt/uptime-kuma

# Запускаем в фоне для теста
sudo -u uptime-kuma timeout 10s node server/server.js &
TEST_PID=$!

sleep 5

# Проверяем, запустился ли
if kill -0 $TEST_PID 2>/dev/null; then
    print_success "Uptime Kuma запускается корректно"
    kill $TEST_PID 2>/dev/null || true
else
    print_error "Uptime Kuma не запускается"
    print_info "Логи ошибок:"
    sudo -u uptime-kuma node server/server.js 2>&1 | head -20
    exit 1
fi

# Запускаем сервис
print_step "Запускаем сервис..."
sudo systemctl start uptime-kuma

sleep 3

# Проверяем статус
if systemctl is-active --quiet uptime-kuma; then
    print_success "Uptime Kuma запущен успешно"
else
    print_error "Uptime Kuma не запустился"
    print_info "Логи сервиса:"
    sudo journalctl -u uptime-kuma -n 20 --no-pager
    exit 1
fi

# Проверяем порт
print_step "Проверяем порт..."
if netstat -tlnp 2>/dev/null | grep -q ":3001"; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
    print_success "Uptime Kuma доступен: http://${SERVER_IP}:3001"
else
    print_error "Порт 3001 не открыт"
fi

print_success "🎉 Uptime Kuma исправлен и работает!"
