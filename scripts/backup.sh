#!/bin/bash

# Скрипт резервного копирования AntiSpam Bot
# Использование: ./scripts/backup.sh

set -e

BACKUP_DIR="/backups/antispam-bot"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="antispam-backup-$DATE"

echo "💾 Создание резервной копии $BACKUP_NAME"

# Создаем директорию для бэкапов
mkdir -p $BACKUP_DIR

# Создаем временную директорию
TEMP_DIR="/tmp/$BACKUP_NAME"
mkdir -p $TEMP_DIR

# Копируем данные базы данных
echo "📊 Копирование базы данных..."
if [ -f "data/db.sqlite3" ]; then
    cp data/db.sqlite3 $TEMP_DIR/
fi

# Копируем конфигурацию
echo "⚙️  Копирование конфигурации..."
cp .env $TEMP_DIR/ 2>/dev/null || echo "⚠️  .env не найден"

# Копируем логи (последние 7 дней)
echo "📝 Копирование логов..."
if [ -d "logs" ]; then
    find logs -name "*.log" -mtime -7 -exec cp {} $TEMP_DIR/ \;
fi

# Создаем архив
echo "📦 Создание архива..."
cd /tmp
tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz $BACKUP_NAME
rm -rf $TEMP_DIR

# Удаляем старые бэкапы (старше 30 дней)
echo "🧹 Удаление старых бэкапов..."
find $BACKUP_DIR -name "antispam-backup-*.tar.gz" -mtime +30 -delete

echo "✅ Резервная копия создана: $BACKUP_DIR/$BACKUP_NAME.tar.gz"

# Отправляем в облачное хранилище (если настроено)
if [ ! -z "$S3_BUCKET" ]; then
    echo "☁️  Загрузка в S3..."
    aws s3 cp $BACKUP_DIR/$BACKUP_NAME.tar.gz s3://$S3_BUCKET/backups/
fi