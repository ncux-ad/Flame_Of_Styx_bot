#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# 🚀 Быстрый запуск AntiSpam Bot в Docker
# Простой скрипт для быстрого старта

echo "🐳 Быстрый запуск AntiSpam Bot в Docker..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    exit 1
fi

# Проверка .env
if [ ! -f .env ]; then
    echo "⚠️  .env файл не найден, создаю из примера..."
    cp env.example .env
    echo "📝 Отредактируйте .env файл с вашими настройками!"
    echo "   BOT_TOKEN=your_telegram_bot_token_here"
    echo "   ADMIN_IDS=123456789,987654321"
    exit 1
fi

# Сборка и запуск
echo "🔨 Сборка Docker образа..."
docker-compose build

echo "🚀 Запуск бота..."
docker-compose up -d antispam-bot

echo "✅ Бот запущен!"
echo "📋 Для просмотра логов: docker-compose logs -f antispam-bot"
echo "🛑 Для остановки: docker-compose down"
echo "🔧 Для входа в контейнер: docker-compose exec antispam-bot /bin/bash"
