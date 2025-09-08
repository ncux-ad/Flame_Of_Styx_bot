#!/bin/bash

# Скрипт проверки здоровья AntiSpam Bot
# Использование: ./scripts/healthcheck.sh

set -e

PROJECT_NAME="antispam-bot"
HEALTH_STATUS=0

echo "🏥 Проверка здоровья $PROJECT_NAME"

# Проверяем статус контейнеров
echo "📦 Проверка контейнеров..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Контейнеры не запущены"
    HEALTH_STATUS=1
else
    echo "✅ Контейнеры запущены"
fi

# Проверяем доступность Redis
echo "🔴 Проверка Redis..."
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis доступен"
else
    echo "❌ Redis недоступен"
    HEALTH_STATUS=1
fi

# Проверяем логи на ошибки
echo "📝 Проверка логов на ошибки..."
ERROR_COUNT=$(docker-compose logs --tail=100 | grep -i "error\|exception\|traceback" | wc -l)
if [ $ERROR_COUNT -gt 0 ]; then
    echo "⚠️  Найдено $ERROR_COUNT ошибок в логах"
    HEALTH_STATUS=1
else
    echo "✅ Ошибок в логах не найдено"
fi

# Проверяем использование диска
echo "💾 Проверка использования диска..."
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "⚠️  Диск заполнен на $DISK_USAGE%"
    HEALTH_STATUS=1
else
    echo "✅ Использование диска: $DISK_USAGE%"
fi

# Проверяем использование памяти
echo "🧠 Проверка использования памяти..."
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "⚠️  Память заполнена на $MEMORY_USAGE%"
    HEALTH_STATUS=1
else
    echo "✅ Использование памяти: $MEMORY_USAGE%"
fi

# Итоговый статус
if [ $HEALTH_STATUS -eq 0 ]; then
    echo "✅ Все проверки пройдены успешно"
    exit 0
else
    echo "❌ Обнаружены проблемы"
    exit 1
fi
