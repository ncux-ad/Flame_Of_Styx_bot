#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"
# Скрипт для настройки Docker secrets для продакшена

set -e

echo "🔐 Настройка Docker secrets для AntiSpam Bot"

# Создание директории для secrets
mkdir -p secrets

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден. Создайте его на основе .env.example"
    exit 1
fi

# Загрузка переменных из .env
source .env

# Создание файлов secrets
echo "📝 Создание файлов secrets..."

# BOT_TOKEN
if [ -n "$BOT_TOKEN" ] && [ "$BOT_TOKEN" != "your_telegram_bot_token_here" ]; then
    echo "$BOT_TOKEN" > secrets/bot_token.txt
    chmod 600 secrets/bot_token.txt
    echo "✅ bot_token.txt создан"
else
    echo "❌ BOT_TOKEN не настроен в .env файле"
    exit 1
fi

# ADMIN_IDS
if [ -n "$ADMIN_IDS" ]; then
    echo "$ADMIN_IDS" > secrets/admin_ids.txt
    chmod 600 secrets/admin_ids.txt
    echo "✅ admin_ids.txt создан"
else
    echo "❌ ADMIN_IDS не настроен в .env файле"
    exit 1
fi

# DB_PATH
if [ -n "$DB_PATH" ]; then
    echo "$DB_PATH" > secrets/db_path.txt
    chmod 600 secrets/db_path.txt
    echo "✅ db_path.txt создан"
else
    echo "❌ DB_PATH не настроен в .env файле"
    exit 1
fi

# Создание .env.prod для продакшена
cat > .env.prod << EOF
# Production environment variables
# Эти переменные будут использоваться в docker-compose.prod.yml

# Redis password (генерируется автоматически)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Nginx configuration
NGINX_HOST=antispam-bot.com
NGINX_SSL_CERT=/etc/nginx/ssl/cert.pem
NGINX_SSL_KEY=/etc/nginx/ssl/key.pem

# Monitoring (опционально)
PROMETHEUS_ENABLED=false
GRAFANA_ENABLED=false
EOF

echo "✅ .env.prod создан"

# Создание директории для SSL сертификатов
mkdir -p nginx/ssl

echo ""
echo "🔒 Настройка SSL сертификатов..."
echo "Поместите ваши SSL сертификаты в директорию nginx/ssl/:"
echo "  - cert.pem (сертификат)"
echo "  - key.pem (приватный ключ)"
echo ""
echo "Или создайте самоподписанный сертификат для тестирования:"
echo "  openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes"

echo ""
echo "✅ Docker secrets настроены!"
echo ""
echo "🚀 Для запуска в продакшене используйте:"
echo "  docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "📋 Проверьте права доступа к secrets:"
ls -la secrets/
