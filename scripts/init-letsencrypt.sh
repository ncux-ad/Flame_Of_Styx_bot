#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"
# Скрипт инициализации Let's Encrypt для AntiSpam Bot
# Let's Encrypt initialization script for AntiSpam Bot

set -e

echo "🔐 Инициализация Let's Encrypt для AntiSpam Bot"
echo "=============================================="

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

# Проверка переменных окружения
DOMAIN=${DOMAIN:-"antispam-bot.com"}
EMAIL=${EMAIL:-"admin@antispam-bot.com"}

# Проверка обязательных переменных
if [ "$DOMAIN" = "antispam-bot.com" ] || [ "$DOMAIN" = "your-domain.com" ]; then
    error "❌ Домен не настроен!"
    error "Установите переменную DOMAIN:"
    error "export DOMAIN=\"your-domain.com\""
    error "export EMAIL=\"your-email@example.com\""
    error ""
    error "Или создайте .env.prod файл:"
    error "cp env.prod.example .env.prod"
    error "nano .env.prod"
    exit 1
fi

if [ "$EMAIL" = "admin@antispam-bot.com" ] || [ "$EMAIL" = "your-email@example.com" ]; then
    error "❌ Email не настроен!"
    error "Установите переменную EMAIL:"
    error "export EMAIL=\"your-email@example.com\""
    exit 1
fi

log "Домен: $DOMAIN"
log "Email: $EMAIL"

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose не установлен!"
    exit 1
fi

# Создание директорий
log "Создание необходимых директорий..."
mkdir -p nginx/ssl
mkdir -p secrets

# Создание временных сертификатов для nginx
log "Создание временных сертификатов..."
openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=AntiSpam Bot/OU=IT/CN=$DOMAIN"

# Создание .env файла для продакшена
log "Создание .env файла для продакшена..."
cat > .env.prod << EOF
# Production environment variables
DOMAIN=$DOMAIN
EMAIL=$EMAIL
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=366490333,439304619
DB_PATH=db.sqlite3
REDIS_PASSWORD=your_redis_password_here
NOTIFICATION_WEBHOOK=
EOF

# Создание secrets
log "Создание Docker secrets..."
mkdir -p secrets
echo "your_telegram_bot_token_here" > secrets/bot_token.txt
echo "366490333,439304619" > secrets/admin_ids.txt
echo "db.sqlite3" > secrets/db_path.txt
echo "your_redis_password_here" > secrets/redis_password.txt

# Запуск nginx для получения сертификатов
log "Запуск nginx для получения сертификатов..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Ожидание запуска nginx
log "Ожидание запуска nginx..."
sleep 10

# Проверка доступности nginx
if ! curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN" | grep -q "200\|301\|302"; then
    warning "Nginx недоступен. Проверьте настройки DNS и порты."
    warning "Убедитесь, что домен $DOMAIN указывает на этот сервер."
fi

# Запуск certbot для получения сертификатов
log "Запуск certbot для получения сертификатов..."
docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-init.sh

# Проверка успешности получения сертификатов
if [ -f "nginx/ssl/cert.pem" ] && [ -f "nginx/ssl/key.pem" ]; then
    success "Сертификаты успешно получены!"

    # Перезапуск nginx с новыми сертификатами
    log "Перезапуск nginx с новыми сертификатами..."
    docker-compose -f docker-compose.prod.yml restart nginx

    # Проверка HTTPS
    sleep 5
    if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" | grep -q "200\|301\|302"; then
        success "HTTPS работает корректно!"
    else
        warning "HTTPS может быть недоступен. Проверьте настройки."
    fi

    # Настройка cron для автоматического обновления
    log "Настройка автоматического обновления сертификатов..."
    echo "0 2 * * * cd $(pwd) && docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-renew.sh >> /var/log/letsencrypt-renewal.log 2>&1" | sudo tee /etc/cron.d/letsencrypt-renewal

    success "Инициализация Let's Encrypt завершена успешно!"
    success "Сертификаты будут автоматически обновляться каждый день в 2:00"

else
    error "Не удалось получить сертификаты!"
    error "Проверьте настройки DNS и доступность домена."
    exit 1
fi

# Финальная проверка
log "Финальная проверка статуса..."
docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-status.sh

echo ""
success "🎉 Let's Encrypt успешно настроен для $DOMAIN!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Обновите переменные в .env.prod"
echo "2. Запустите: docker-compose -f docker-compose.prod.yml up -d"
echo "3. Проверьте: https://$DOMAIN"
echo ""
echo "🔧 Управление сертификатами:"
echo "- Статус: docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-status.sh"
echo "- Обновление: docker-compose -f docker-compose.prod.yml run --rm certbot /scripts/certbot-renew.sh"
echo "- Логи: docker-compose -f docker-compose.prod.yml logs certbot"
