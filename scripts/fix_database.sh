#!/bin/bash
# Скрипт для исправления ошибки базы данных

set -euo pipefail

# Цвета для вывода
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверяем, что скрипт запущен от root или с sudo
if [[ $EUID -ne 0 ]]; then
    error "Этот скрипт должен быть запущен с правами root или через sudo"
    exit 1
fi

log "🔧 Исправление ошибки базы данных..."

# Определяем пользователя бота
BOT_USER="ncux11"
BOT_DIR="/home/${BOT_USER}/bots/Flame_Of_Styx_bot"

# Проверяем существование директории
if [[ ! -d "$BOT_DIR" ]]; then
    error "Директория бота не найдена: $BOT_DIR"
    exit 1
fi

log "📁 Директория бота: $BOT_DIR"

# Переходим в директорию бота
cd "$BOT_DIR"

# Проверяем виртуальное окружение
if [[ ! -d "venv" ]]; then
    error "Виртуальное окружение не найдено в $BOT_DIR/venv"
    exit 1
fi

log "🐍 Активация виртуального окружения..."
source venv/bin/activate

# Проверяем alembic
if ! command -v alembic &> /dev/null; then
    warning "Alembic не найден в виртуальном окружении"
    log "📦 Установка alembic..."
    pip install alembic
    
    if [[ $? -eq 0 ]]; then
        success "Alembic установлен успешно!"
    else
        error "Ошибка при установке alembic"
        exit 1
    fi
fi

log "📊 Применение миграции базы данных..."
alembic upgrade head

if [[ $? -eq 0 ]]; then
    success "Миграция применена успешно!"
else
    error "Ошибка при применении миграции"
    exit 1
fi

log "🔄 Перезапуск сервиса бота..."
systemctl restart antispam-bot

if [[ $? -eq 0 ]]; then
    success "Сервис бота перезапущен успешно!"
else
    error "Ошибка при перезапуске сервиса"
    exit 1
fi

# Проверяем статус сервиса
log "📊 Проверка статуса сервиса..."
systemctl status antispam-bot --no-pager -l

success "✅ Исправление ошибки базы данных завершено!"
success "Теперь команды /status и /channels должны работать корректно"

log "💡 Для проверки работы бота используйте команды:"
log "   - /status - для просмотра статистики"
log "   - /channels - для просмотра каналов"
log "   - /help - для просмотра справки"
