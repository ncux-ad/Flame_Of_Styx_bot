#!/bin/bash

# Скрипт для настройки среды разработки
# Использование: ./scripts/setup-dev.sh

set -e

echo "🛠️ Настройка среды разработки для AntiSpam Bot"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен"
    exit 1
fi

# Проверяем версию Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
    echo "❌ Требуется Python 3.11+, установлен $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION найден"

# Создаем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "🐍 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔌 Активация виртуального окружения..."
source venv/bin/activate

# Обновляем pip
echo "📦 Обновление pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "📚 Установка зависимостей..."
pip install -e ".[dev]"

# Устанавливаем pre-commit
echo "🔧 Настройка pre-commit..."
pre-commit install

# Создаем .env файл
if [ ! -f ".env" ]; then
    echo "⚙️ Создание .env файла..."
    cp env.example .env
    echo "⚠️  Не забудьте настроить .env файл!"
fi

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p data logs

echo "✅ Среда разработки настроена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте .env файл:"
echo "   nano .env"
echo ""
echo "2. Активируйте виртуальное окружение:"
echo "   source venv/bin/activate"
echo ""
echo "3. Запустите тесты:"
echo "   pytest"
echo ""
echo "4. Запустите линтеры:"
echo "   black ."
echo "   ruff check ."
echo "   mypy app/"
echo ""
echo "5. Запустите бота:"
echo "   python bot.py"
