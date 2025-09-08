#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"
# Скрипт настройки домена для Let's Encrypt
# Domain setup script for Let's Encrypt

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🌐 Настройка домена для AntiSpam Bot"
echo "=================================="

# Проверка существования .env.prod
if [ -f ".env.prod" ]; then
    log "Найден .env.prod файл. Загружаем переменные..."
    source .env.prod
else
    log "Создание .env.prod файла..."
    cp env.prod.example .env.prod
    warning "Отредактируйте .env.prod файл с вашими настройками:"
    echo ""
    echo "nano .env.prod"
    echo ""
    echo "Или установите переменные окружения:"
    echo "export DOMAIN=\"your-domain.com\""
    echo "export EMAIL=\"your-email@example.com\""
    echo ""
    read -p "Нажмите Enter после настройки..."
fi

# Загрузка переменных
if [ -f ".env.prod" ]; then
    source .env.prod
fi

# Проверка переменных
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "your-domain.com" ]; then
    error "❌ Домен не настроен!"
    echo ""
    echo "Установите домен одним из способов:"
    echo ""
    echo "1. Переменная окружения:"
    echo "   export DOMAIN=\"your-domain.com\""
    echo ""
    echo "2. Файл .env.prod:"
    echo "   nano .env.prod"
    echo "   DOMAIN=your-domain.com"
    echo ""
    exit 1
fi

if [ -z "$EMAIL" ] || [ "$EMAIL" = "your-email@example.com" ]; then
    error "❌ Email не настроен!"
    echo ""
    echo "Установите email одним из способов:"
    echo ""
    echo "1. Переменная окружения:"
    echo "   export EMAIL=\"your-email@example.com\""
    echo ""
    echo "2. Файл .env.prod:"
    echo "   nano .env.prod"
    echo "   EMAIL=your-email@example.com"
    echo ""
    exit 1
fi

log "Домен: $DOMAIN"
log "Email: $EMAIL"

# Проверка DNS
log "Проверка DNS настроек..."
echo ""

# Получение IP адреса домена
DOMAIN_IP=$(dig +short $DOMAIN | head -n1)
if [ -z "$DOMAIN_IP" ]; then
    error "❌ Не удалось получить IP адрес домена $DOMAIN"
    error "Проверьте DNS настройки!"
    exit 1
fi

log "IP адрес домена: $DOMAIN_IP"

# Получение внешнего IP сервера
SERVER_IP=$(curl -s ifconfig.me)
if [ -z "$SERVER_IP" ]; then
    warning "Не удалось получить внешний IP сервера"
    warning "Проверьте вручную: curl ifconfig.me"
else
    log "IP адрес сервера: $SERVER_IP"
fi

# Проверка соответствия IP
if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
    success "✅ DNS настроен корректно!"
else
    warning "⚠️ IP адреса не совпадают!"
    warning "Домен: $DOMAIN_IP"
    warning "Сервер: $SERVER_IP"
    warning "Убедитесь, что домен указывает на этот сервер"
fi

# Проверка доступности HTTP
log "Проверка доступности HTTP..."
if curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN" | grep -q "200\|301\|302"; then
    success "✅ HTTP доступен!"
else
    warning "⚠️ HTTP недоступен"
    warning "Убедитесь, что nginx запущен и порт 80 открыт"
fi

# Проверка портов
log "Проверка портов..."
if netstat -tuln | grep -q ":80 "; then
    success "✅ Порт 80 открыт"
else
    warning "⚠️ Порт 80 не открыт"
fi

if netstat -tuln | grep -q ":443 "; then
    success "✅ Порт 443 открыт"
else
    warning "⚠️ Порт 443 не открыт"
fi

# Рекомендации
echo ""
log "💡 Рекомендации:"
echo ""

if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo "1. Настройте DNS запись A:"
    echo "   $DOMAIN -> $SERVER_IP"
    echo ""
fi

echo "2. Убедитесь, что порты 80 и 443 открыты в файрволе:"
echo "   sudo ufw allow 80"
echo "   sudo ufw allow 443"
echo ""

echo "3. Проверьте настройки домена:"
echo "   nslookup $DOMAIN"
echo "   dig $DOMAIN"
echo ""

echo "4. После настройки DNS запустите:"
echo "   make letsencrypt-init"
echo ""

# Создание .env.prod с правильными настройками
if [ ! -f ".env.prod" ]; then
    log "Создание .env.prod файла..."
    cat > .env.prod << EOF
# Production Environment Variables
DOMAIN=$DOMAIN
EMAIL=$EMAIL
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=366490333,439304619
DB_PATH=db.sqlite3
REDIS_PASSWORD=your_redis_password_here
NOTIFICATION_WEBHOOK=
RENEWAL_THRESHOLD=30
EOF
    success "✅ .env.prod создан с настройками домена"
fi

success "🎉 Настройка домена завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Обновите BOT_TOKEN в .env.prod"
echo "2. Запустите: make letsencrypt-init"
echo "3. Проверьте: https://$DOMAIN"
