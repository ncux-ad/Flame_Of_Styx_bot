#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# Скрипт для работы с Docker в WSL
# Использование: ./scripts/wsl-docker.sh [command]

set -e

COMMAND=${1:-help}

echo "🐳 Docker в WSL - $COMMAND"

# Проверяем, что мы в WSL
if [ ! -f /proc/version ] || ! grep -q Microsoft /proc/version; then
    echo "❌ Этот скрипт должен запускаться в WSL"
    exit 1
fi

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    echo "📝 Установите Docker Desktop для Windows и включите WSL2 интеграцию"
    exit 1
fi

case $COMMAND in
    "build")
        echo "🔨 Сборка Docker образа..."
        docker build -t antispam-bot .
        ;;
    "up")
        echo "🚀 Запуск контейнеров..."
        docker-compose up -d
        ;;
    "down")
        echo "🛑 Остановка контейнеров..."
        docker-compose down
        ;;
    "logs")
        echo "📋 Просмотр логов..."
        docker-compose logs -f antispam-bot
        ;;
    "shell")
        echo "🐚 Подключение к контейнеру..."
        docker-compose exec antispam-bot /bin/bash
        ;;
    "restart")
        echo "🔄 Перезапуск контейнеров..."
        docker-compose restart
        ;;
    "clean")
        echo "🧹 Очистка Docker..."
        docker-compose down
        docker system prune -f
        docker volume prune -f
        ;;
    "dev")
        echo "🛠️ Запуск в режиме разработки..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        ;;
    "help"|*)
        echo "📋 Доступные команды:"
        echo "  build    - Сборка Docker образа"
        echo "  up       - Запуск контейнеров"
        echo "  down     - Остановка контейнеров"
        echo "  logs     - Просмотр логов"
        echo "  shell    - Подключение к контейнеру"
        echo "  restart  - Перезапуск контейнеров"
        echo "  clean    - Очистка Docker"
        echo "  dev      - Запуск в режиме разработки"
        echo ""
        echo "Примеры:"
        echo "  ./scripts/wsl-docker.sh up"
        echo "  ./scripts/wsl-docker.sh logs"
        echo "  ./scripts/wsl-docker.sh shell"
        ;;
esac
