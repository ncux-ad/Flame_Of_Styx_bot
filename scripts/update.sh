#!/bin/bash

# Скрипт обновления AntiSpam Bot
# Использование: ./scripts/update.sh

set -e

INSTALL_DIR="/opt/antispam-bot"
SERVICE_USER="antispam"

echo "🔄 Обновление AntiSpam Bot"

# Проверяем права root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Останавливаем сервис
echo "🛑 Остановка сервиса..."
systemctl stop antispam-bot

# Создаем бэкап
echo "💾 Создание бэкапа..."
BACKUP_DIR="/opt/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r $INSTALL_DIR $BACKUP_DIR/

# Обновляем код
echo "📋 Обновление кода..."
cp -r . $INSTALL_DIR/
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# Обновляем зависимости
echo "📦 Обновление зависимостей..."
cd $INSTALL_DIR
sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install --upgrade pip
sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install -r requirements.txt

# Перезагружаем systemd
echo "🔧 Перезагрузка systemd..."
systemctl daemon-reload

# Запускаем сервис
echo "▶️  Запуск сервиса..."
systemctl start antispam-bot

# Проверяем статус
echo "🔍 Проверка статуса..."
sleep 5
systemctl status antispam-bot --no-pager

echo "✅ Обновление завершено!"
echo "💾 Бэкап сохранен в: $BACKUP_DIR"
