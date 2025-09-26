#!/bin/bash

# Скрипт установки systemd сервиса для AntiSpam Bot
# Использование: sudo ./systemd/install.sh

set -e

SERVICE_NAME="antispam-bot"
SERVICE_FILE="antispam-bot.service"
INSTALL_DIR="/opt/antispam-bot"
SERVICE_USER="antispam"

echo "🔧 Установка systemd сервиса $SERVICE_NAME"

# Проверяем права root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Создаем пользователя для сервиса
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "👤 Создание пользователя $SERVICE_USER"
    useradd --system --shell /bin/false --home-dir $INSTALL_DIR --create-home $SERVICE_USER
else
    echo "✅ Пользователь $SERVICE_USER уже существует"
fi

# Создаем директорию установки
echo "📁 Создание директории $INSTALL_DIR"
mkdir -p $INSTALL_DIR
chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# Копируем файлы проекта
echo "📋 Копирование файлов проекта"
cp -r . $INSTALL_DIR/
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# Копируем systemd сервис
echo "⚙️  Установка systemd сервиса"
cp systemd/$SERVICE_FILE /etc/systemd/system/
chmod 644 /etc/systemd/system/$SERVICE_FILE

# Перезагружаем systemd
echo "🔄 Перезагрузка systemd"
systemctl daemon-reload

# Включаем автозапуск
echo "🚀 Включение автозапуска"
systemctl enable $SERVICE_NAME

echo "✅ Установка завершена!"
echo ""
echo "📋 Команды управления:"
echo "  Запуск:   sudo systemctl start $SERVICE_NAME"
echo "  Остановка: sudo systemctl stop $SERVICE_NAME"
echo "  Статус:   sudo systemctl status $SERVICE_NAME"
echo "  Логи:     sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "⚠️  Не забудьте настроить .env файл в $INSTALL_DIR"
