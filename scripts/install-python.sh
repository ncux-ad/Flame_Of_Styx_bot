#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# Скрипт установки Python 3.11+ на Ubuntu 20.04
# Использование: sudo ./scripts/install-python.sh

set -e

PYTHON_VERSION="3.11"
PYTHON_FULL_VERSION="3.11.9"

echo "🐍 Установка Python $PYTHON_FULL_VERSION на Ubuntu 20.04"

# Проверяем права root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт с правами root (sudo)"
    exit 1
fi

# Обновляем систему
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Устанавливаем необходимые зависимости
echo "🔧 Установка зависимостей..."
apt install -y \
    software-properties-common \
    build-essential \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    wget \
    libbz2-dev

# Добавляем deadsnakes PPA для свежих версий Python
echo "➕ Добавление deadsnakes PPA..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update

# Устанавливаем Python 3.11
echo "🐍 Установка Python $PYTHON_VERSION..."
apt install -y \
    python$PYTHON_VERSION \
    python$PYTHON_VERSION-dev \
    python$PYTHON_VERSION-venv \
    python$PYTHON_VERSION-distutils

# Устанавливаем pip
echo "📦 Установка pip..."
wget https://bootstrap.pypa.io/get-pip.py
python$PYTHON_VERSION get-pip.py
rm get-pip.py

# Создаем символические ссылки
echo "🔗 Создание символических ссылок..."
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python$PYTHON_VERSION 1
update-alternatives --install /usr/bin/python python /usr/bin/python$PYTHON_VERSION 1

# Проверяем установку
echo "✅ Проверка установки..."
python3 --version
pip3 --version

echo "🎉 Python $PYTHON_FULL_VERSION успешно установлен!"
echo ""
echo "📋 Полезные команды:"
echo "  python3 --version"
echo "  pip3 --version"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
