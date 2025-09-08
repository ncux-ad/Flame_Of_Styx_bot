#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# Скрипт для запуска разработки в WSL
# Использование: ./scripts/wsl-dev.sh

set -e

echo "🚀 Запуск разработки в WSL"

# Проверяем, что мы в WSL
if [ ! -f /proc/version ] || ! grep -q Microsoft /proc/version; then
    echo "❌ Этот скрипт должен запускаться в WSL"
    exit 1
fi

# Активируем виртуальное окружение
echo "🐍 Активация виртуального окружения..."
source venv/bin/activate

# Проверяем .env файл
if [ ! -f .env ]; then
    echo "⚠️  .env файл не найден! Создаю из примера..."
    cp env.example .env
    echo "📝 Отредактируйте .env файл перед запуском бота"
    echo "   nano .env"
    exit 1
fi

# Проверяем настройки
echo "🔍 Проверка настроек..."
if ! grep -q "BOT_TOKEN=" .env || grep -q "your_telegram_bot_token_here" .env; then
    echo "⚠️  BOT_TOKEN не настроен в .env файле"
    echo "   Отредактируйте .env файл: nano .env"
    exit 1
fi

if ! grep -q "ADMIN_IDS=" .env || grep -q "123456789,987654321" .env; then
    echo "⚠️  ADMIN_IDS не настроены в .env файле"
    echo "   Отредактируйте .env файл: nano .env"
    exit 1
fi

# Запускаем линтеры
echo "🔍 Запуск линтеров..."
black --check . || echo "⚠️  Black: найдены проблемы с форматированием"
ruff check . || echo "⚠️  Ruff: найдены проблемы с кодом"
mypy app/ || echo "⚠️  MyPy: найдены проблемы с типами"

# Запускаем тесты
echo "🧪 Запуск тестов..."
pytest -v || echo "⚠️  Тесты не прошли"

# Запускаем бота
echo "🤖 Запуск бота..."
python bot.py
