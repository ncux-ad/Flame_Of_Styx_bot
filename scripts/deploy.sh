#!/bin/bash

# Скрипт развертывания AntiSpam Bot
# Использование: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="antispam-bot"
INSTALL_DIR="/opt/antispam-bot"
SERVICE_USER="antispam"

echo "🚀 Развертывание $PROJECT_NAME в окружении $ENVIRONMENT"

# Проверяем права root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Проверяем Python
if ! command -v python3.11 &> /dev/null; then
    echo "🐍 Python 3.11 не найден, устанавливаем..."
    ./scripts/install-python.sh
fi

# Создаем пользователя
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

# Создаем виртуальное окружение
echo "🐍 Создание виртуального окружения"
cd $INSTALL_DIR
sudo -u $SERVICE_USER python3.11 -m venv venv

# Устанавливаем зависимости
echo "📦 Установка зависимостей"
sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install --upgrade pip
sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install -r requirements.txt

# Настраиваем конфигурацию
if [ ! -f $INSTALL_DIR/.env ]; then
    echo "⚙️  Настройка конфигурации"
    cp $INSTALL_DIR/env.example $INSTALL_DIR/.env
    echo "⚠️  Не забудьте настроить .env файл в $INSTALL_DIR!"
    echo "   nano $INSTALL_DIR/.env"
fi

# Устанавливаем systemd сервис
echo "🔧 Установка systemd сервиса"
cp systemd/antispam-bot.service /etc/systemd/system/
chmod 644 /etc/systemd/system/antispam-bot.service
systemctl daemon-reload

# Включаем автозапуск
echo "🚀 Включение автозапуска"
systemctl enable antispam-bot

# Запускаем сервис
echo "▶️  Запуск сервиса"
systemctl start antispam-bot

# Проверяем статус
echo "🔍 Проверка статуса"
sleep 5
systemctl status antispam-bot --no-pager

echo "✅ Развертывание завершено!"
echo ""
echo "📋 Команды управления:"
echo "  Статус:   sudo systemctl status antispam-bot"
echo "  Логи:     sudo journalctl -u antispam-bot -f"
echo "  Перезапуск: sudo systemctl restart antispam-bot"
echo "  Остановка: sudo systemctl stop antispam-bot"
