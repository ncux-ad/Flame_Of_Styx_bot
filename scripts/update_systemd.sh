#!/bin/bash

# Скрипт для обновления systemd конфигурации на сервере

set -e

echo "🔄 Обновление systemd конфигурации..."

# Останавливаем сервис
echo "⏹️ Остановка сервиса..."
sudo systemctl stop antispam-bot.service || true

# Копируем обновленный systemd файл
echo "📋 Копирование systemd файла..."
sudo cp systemd/antispam-bot.service /etc/systemd/system/

# Создаем директорию для override если не существует
sudo mkdir -p /etc/systemd/system/antispam-bot.service.d/

# Копируем override файл
echo "⚙️ Копирование override конфигурации..."
sudo cp systemd/antispam-bot.service.d/override.conf /etc/systemd/system/antispam-bot.service.d/ || true

# Перезагружаем systemd
echo "🔄 Перезагрузка systemd..."
sudo systemctl daemon-reload

# Включаем и запускаем сервис
echo "▶️ Запуск сервиса..."
sudo systemctl enable antispam-bot.service
sudo systemctl start antispam-bot.service

# Проверяем статус
echo "📊 Статус сервиса:"
sudo systemctl status antispam-bot.service --no-pager

echo "✅ Systemd конфигурация обновлена!"
echo ""
echo "🔍 Проверьте PATH в сервисе:"
echo "sudo systemctl show antispam-bot.service | grep PATH"
echo ""
echo "📋 Теперь команда /logs должна работать!"
