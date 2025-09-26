#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# Скрипт для инициализации Git репозитория
# Использование: ./scripts/init-git.sh

set -e

echo "🚀 Инициализация Git репозитория для AntiSpam Bot"

# Проверяем наличие Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен"
    exit 1
fi

# Инициализируем Git репозиторий (если не инициализирован)
if [ ! -d ".git" ]; then
    echo "📁 Инициализация Git репозитория..."
    git init
fi

# Добавляем remote origin (если не добавлен)
if ! git remote | grep -q origin; then
    echo "🔗 Добавьте remote origin:"
    echo "   git remote add origin https://github.com/your-username/antispam-bot.git"
    echo "   git branch -M main"
fi

# Добавляем все файлы
echo "📝 Добавление файлов в Git..."
git add .

# Создаем первый коммит
echo "💾 Создание первого коммита..."
if git diff --cached --quiet; then
    echo "ℹ️  Нет изменений для коммита"
else
    git commit -m "🎉 Initial commit: AntiSpam Bot project setup

- ✅ Базовая архитектура aiogram 3.x
- ✅ Модели базы данных (SQLAlchemy)
- ✅ Сервисы для модерации и управления
- ✅ Обработчики и middleware
- ✅ DevOps инфраструктура (Docker, systemd)
- ✅ CI/CD с GitHub Actions
- ✅ Тестирование и линтеры
- ✅ Полная документация

Готово для разработки! 🚀"
    fi
fi

# Создаем ветку develop
echo "🌿 Создание ветки develop..."
git checkout -b develop

echo "✅ Git репозиторий инициализирован!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Добавьте remote origin:"
echo "   git remote add origin https://github.com/your-username/antispam-bot.git"
echo ""
echo "2. Отправьте код на GitHub:"
echo "   git push -u origin main"
echo "   git push -u origin develop"
echo ""
echo "3. Настройте .env файл:"
echo "   cp env.example .env"
echo "   # Отредактируйте .env файл"
echo ""
echo "4. Запустите локально:"
echo "   docker-compose up -d"
echo ""
echo "5. Или установите зависимости:"
echo "   pip install -e \".[dev]\""
echo "   python bot.py"
