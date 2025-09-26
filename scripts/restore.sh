#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# Скрипт восстановления AntiSpam Bot
# Использование: ./scripts/restore.sh <backup_file>

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Укажите файл резервной копии"
    echo "Использование: $0 <backup_file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Файл $BACKUP_FILE не найден"
    exit 1
fi

echo "🔄 Восстановление из $BACKUP_FILE"

# Останавливаем сервисы
echo "🛑 Остановка сервисов..."
docker-compose down || true

# Создаем временную директорию
TEMP_DIR="/tmp/restore-$(date +%s)"
mkdir -p $TEMP_DIR

# Распаковываем архив
echo "📦 Распаковка архива..."
tar -xzf "$BACKUP_FILE" -C $TEMP_DIR

# Восстанавливаем данные
echo "📊 Восстановление данных..."
if [ -f "$TEMP_DIR/db.sqlite3" ]; then
    mkdir -p data
    cp "$TEMP_DIR/db.sqlite3" data/
    echo "✅ База данных восстановлена"
fi

# Восстанавливаем конфигурацию
if [ -f "$TEMP_DIR/.env" ]; then
    cp "$TEMP_DIR/.env" .
    echo "✅ Конфигурация восстановлена"
fi

# Восстанавливаем логи
if [ -d "$TEMP_DIR/logs" ]; then
    mkdir -p logs
    cp -r "$TEMP_DIR/logs"/* logs/ 2>/dev/null || true
    echo "✅ Логи восстановлены"
fi

# Очищаем временную директорию
rm -rf $TEMP_DIR

# Запускаем сервисы
echo "▶️  Запуск сервисов..."
docker-compose up -d

echo "✅ Восстановление завершено!"
