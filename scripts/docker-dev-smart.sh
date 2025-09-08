#!/bin/bash

# Load secure utilities
source "$(dirname "$0")/secure_shell_utils.sh"

# 🐳 Умный Docker Development Script для AntiSpam Bot
# Пересобирает образ только при изменении зависимостей

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

# Проверка изменений в requirements.txt
check_requirements_changed() {
    if [ ! -f .docker-requirements-hash ]; then
        return 0  # Файл не существует, нужно пересобрать
    fi

    current_hash=$(md5sum requirements.txt | cut -d' ' -f1)
    stored_hash=$(cat .docker-requirements-hash)

    if [ "$current_hash" != "$stored_hash" ]; then
        return 0  # Хеш изменился, нужно пересобрать
    fi

    return 1  # Хеш не изменился, пересобирать не нужно
}

# Обновление хеша requirements.txt
update_requirements_hash() {
    md5sum requirements.txt | cut -d' ' -f1 > .docker-requirements-hash
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

# Умная сборка образа
smart_build() {
    if check_requirements_changed; then
        log "Обнаружены изменения в requirements.txt, пересобираю образ..."
        docker-compose build --no-cache
        update_requirements_hash
        log "Образ пересобран и хеш обновлен"
    else
        log "Зависимости не изменились, использую существующий образ"
    fi
}

# Запуск бота
start_bot() {
    log "Запуск AntiSpam Bot в Docker..."
    smart_build
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

# Принудительная пересборка
force_build() {
    log "Принудительная пересборка образа..."
    docker-compose build --no-cache
    update_requirements_hash
    log "Образ пересобран"
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
    rm -f .docker-requirements-hash
    log "Очистка завершена"
}

# Статус контейнеров
show_status() {
    log "Статус контейнеров:"
    docker-compose ps
}

# Функция помощи
show_help() {
    echo "🐳 Умный Docker Development Script для AntiSpam Bot"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  start     - Запустить бота (умная сборка)"
    echo "  stop      - Остановить бота"
    echo "  restart   - Перезапустить бота"
    echo "  build     - Принудительная пересборка"
    echo "  logs      - Показать логи бота"
    echo "  shell     - Войти в контейнер"
    echo "  clean     - Очистить Docker ресурсы"
    echo "  status    - Показать статус контейнеров"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Особенности:"
    echo "  - Образ пересобирается только при изменении requirements.txt"
    echo "  - Код монтируется как volume для hot reload"
    echo "  - Быстрый запуск при неизменных зависимостях"
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
            force_build
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
