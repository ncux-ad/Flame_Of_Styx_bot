#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# Скрипт для настройки WSL для работы с AntiSpam Bot
# Использование: ./scripts/setup-wsl.sh

set -e

echo "🐧 Настройка WSL для AntiSpam Bot"

# Проверяем, что мы в WSL (более гибкая проверка)
if [ ! -f /proc/version ]; then
    echo "❌ Не удается определить окружение"
    exit 1
fi

# Проверяем WSL (Microsoft или WSL2)
if ! grep -q -E "(Microsoft|WSL)" /proc/version; then
    echo "⚠️  Предупреждение: скрипт предназначен для WSL, но может работать и в других Linux окружениях"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ WSL обнаружен"

# Обновляем систему
echo "🔄 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
echo "📦 Установка необходимых пакетов..."
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    sqlite3 \
    redis-server \
    htop \
    tree \
    nano \
    vim

# Устанавливаем Python 3.11 если не установлен
if ! command -v python3.11 &> /dev/null; then
    echo "🐍 Установка Python 3.11..."
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
fi

# Устанавливаем pip для Python 3.11
echo "📦 Установка pip для Python 3.11..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Создаем виртуальное окружение
echo "🐍 Создание виртуального окружения..."
python3.11 -m venv venv

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip install --upgrade pip

# Проверяем существование requirements.txt
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "❌ Файл requirements.txt не найден!"
    exit 1
fi

# Устанавливаем dev зависимости
echo "🛠️ Установка dev зависимостей..."
pip install -e ".[dev]"

# Устанавливаем pre-commit
echo "🔗 Установка pre-commit..."
pre-commit install

# Создаем директории
echo "📁 Создание директорий..."
mkdir -p data logs

# Настраиваем права доступа
echo "🔐 Настройка прав доступа..."
chmod +x scripts/*.sh

# Создаем .env файл если не существует
if [ ! -f .env ]; then
    echo "⚙️ Создание .env файла..."
    cp env.example .env
    echo "⚠️  Не забудьте настроить .env файл!"
fi

# Настраиваем Git
echo "🔧 Настройка Git..."
git config core.filemode false
git config core.autocrlf true
git config core.ignorecase true

# Проверяем настройки
echo "✅ Проверка настроек..."
echo "Python версия: $(python3.11 --version)"
echo "Pip версия: $(pip --version)"
echo "Git настройки:"
echo "  filemode: $(git config core.filemode)"
echo "  autocrlf: $(git config core.autocrlf)"
echo "  ignorecase: $(git config core.ignorecase)"

echo ""
echo "🎉 WSL настроен для работы с AntiSpam Bot!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте .env файл: nano .env"
echo "2. Запустите бота: python bot.py"
echo "3. Или используйте Docker: docker-compose up -d"
echo ""
echo "🛠️ Полезные команды:"
echo "  Активация venv: source venv/bin/activate"
echo "  Линтеры: black . && ruff check . && mypy app/"
echo "  Тесты: pytest -v"
echo "  Pre-commit: pre-commit run --all-files"
