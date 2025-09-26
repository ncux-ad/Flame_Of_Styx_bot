#!/bin/bash
# Простое исправление базы данных

set -euo pipefail

# Цвета для вывода
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log "🔧 Простое исправление базы данных..."

# Определяем пользователя бота
BOT_USER="ncux11"
BOT_DIR="/home/${BOT_USER}/bots/Flame_Of_Styx_bot"

# Переходим в директорию бота
cd "$BOT_DIR"

# Активируем виртуальное окружение
log "🐍 Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем alembic если не установлен
if ! command -v alembic &> /dev/null; then
    log "📦 Установка alembic..."
    pip install alembic
fi

# Проверяем наличие файла базы данных (правильное имя)
DB_FILE="db.sqlite3"
if [[ ! -f "$DB_FILE" ]]; then
    error "Файл базы данных не найден: $DB_FILE"
    log "🔍 Поиск файлов базы данных..."
    find . -name "*.db" -o -name "*.sqlite3" | head -5
    exit 1
fi

log "📊 Применение миграции базы данных..."

# Применяем миграцию
alembic upgrade head

if [[ $? -eq 0 ]]; then
    success "Миграция применена успешно!"
else
    error "Ошибка при применении миграции"
    exit 1
fi

# Перезапускаем сервис
log "🔄 Перезапуск сервиса бота..."
systemctl restart antispam-bot

if [[ $? -eq 0 ]]; then
    success "Сервис бота перезапущен успешно!"
else
    error "Ошибка при перезапуске сервиса"
    exit 1
fi

success "✅ Исправление базы данных завершено!"
