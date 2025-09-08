#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# 🐳 Docker Development Script для AntiSpam Bot
# Быстрый запуск и управление Docker контейнерами

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен!"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен!"
        exit 1
    fi
}

# Проверка .env файла
check_env() {
    if [ ! -f .env ]; then
        warn ".env файл не найден, создаю из примера..."
        cp env.example .env
        warn "Отредактируйте .env файл с вашими настройками!"
        exit 1
    fi
}

# Функция помощи
show_help() {
    echo "🐳 Docker Development Script для AntiSpam Bot"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  start     - Запустить бота в Docker"
    echo "  stop      - Остановить бота"
    echo "  restart   - Перезапустить бота"
    echo "  build     - Собрать Docker образ"
    echo "  logs      - Показать логи бота"
    echo "  shell     - Войти в контейнер"
    echo "  clean     - Очистить Docker ресурсы"
    echo "  status    - Показать статус контейнеров"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start          # Запустить бота"
    echo "  $0 logs -f        # Смотреть логи в реальном времени"
    echo "  $0 shell          # Войти в контейнер для отладки"
}

# Запуск бота
start_bot() {
    log "Запуск AntiSpam Bot в Docker..."
    docker-compose up -d antispam-bot
    log "Бот запущен! Используйте '$0 logs' для просмотра логов"
}

# Остановка бота
stop_bot() {
    log "Остановка AntiSpam Bot..."
    docker-compose down
    log "Бот остановлен"
}

# Перезапуск бота
restart_bot() {
    log "Перезапуск AntiSpam Bot..."
    docker-compose restart antispam-bot
    log "Бот перезапущен"
}

# Сборка образа
build_image() {
    log "Сборка Docker образа..."
    docker-compose build --no-cache
    log "Образ собран"
}

# Просмотр логов
show_logs() {
    docker-compose logs "$@"
}

# Вход в контейнер
enter_shell() {
    log "Вход в контейнер AntiSpam Bot..."
    docker-compose exec antispam-bot /bin/bash
}

# Очистка Docker ресурсов
clean_docker() {
    log "Очистка Docker ресурсов..."
    docker-compose down -v
    docker system prune -f
    log "Очистка завершена"
}

# Статус контейнеров
show_status() {
    log "Статус контейнеров:"
    docker-compose ps
}

# Основная логика
main() {
    check_docker
    check_env

    case "${1:-help}" in
        start)
            start_bot
            ;;
        stop)
            stop_bot
            ;;
        restart)
            restart_bot
            ;;
        build)
            build_image
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        shell)
            enter_shell
            ;;
        clean)
            clean_docker
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

# Запуск
main "$@"
