#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# Скрипт для настройки Git репозитория
# Использование: ./scripts/setup-git.sh

set -e

echo "🔧 Настройка Git репозитория"

# Настраиваем Git для игнорирования прав доступа
echo "📝 Настройка Git для игнорирования прав доступа..."
git config core.filemode false
git config core.autocrlf true
git config core.ignorecase true

# Настраиваем пользователя (если не настроен)
if [ -z "$(git config user.name)" ]; then
    echo "👤 Настройка пользователя Git..."
    read -p "Введите ваше имя: " USER_NAME
    read -p "Введите ваш email: " USER_EMAIL
    git config user.name "$USER_NAME"
    git config user.email "$USER_EMAIL"
fi

# Создаем ветку main (если не существует)
if [ -z "$(git branch --list main)" ]; then
    echo "🌿 Создание ветки main..."
    git checkout -b main
fi

# Создаем ветку develop
if [ -z "$(git branch --list develop)" ]; then
    echo "🌿 Создание ветки develop..."
    git checkout -b develop
fi

# Возвращаемся на main
git checkout main

echo "✅ Git репозиторий настроен!"
echo ""
echo "📋 Настройки Git:"
echo "  filemode: $(git config core.filemode)"
echo "  autocrlf: $(git config core.autocrlf)"
echo "  ignorecase: $(git config core.ignorecase)"
echo "  user.name: $(git config user.name)"
echo "  user.email: $(git config user.email)"
echo ""
echo "🌿 Ветки:"
git branch -a
