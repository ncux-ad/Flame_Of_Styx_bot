#!/bin/bash
# Скрипт инициализации Let's Encrypt сертификатов
# Initialization script for Let's Encrypt certificates

set -e

echo "🔐 Инициализация Let's Encrypt сертификатов..."

# Переменные окружения
DOMAIN=${DOMAIN:-"antispam-bot.com"}
EMAIL=${EMAIL:-"admin@antispam-bot.com"}
WEBROOT_PATH="/var/www/certbot"

# Создание директорий
mkdir -p "$WEBROOT_PATH"
mkdir -p "/etc/letsencrypt/live/$DOMAIN"
mkdir -p "/etc/letsencrypt/archive/$DOMAIN"

# Проверка существования сертификатов
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "✅ Сертификаты уже существуют"
    exit 0
fi

# Получение сертификата
echo "📋 Получение сертификата для домена: $DOMAIN"
certbot certonly \
    --webroot \
    --webroot-path="$WEBROOT_PATH" \
    --email="$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains="$DOMAIN,www.$DOMAIN" \
    --non-interactive \
    --expand

# Проверка успешности
if [ $? -eq 0 ]; then
    echo "✅ Сертификат успешно получен!"

    # Копирование сертификатов в nginx
    cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "/etc/nginx/ssl/cert.pem"
    cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "/etc/nginx/ssl/key.pem"

    # Перезапуск nginx
    echo "🔄 Перезапуск nginx..."
    nginx -s reload

    echo "🎉 Инициализация завершена успешно!"
else
    echo "❌ Ошибка при получении сертификата"
    exit 1
fi
