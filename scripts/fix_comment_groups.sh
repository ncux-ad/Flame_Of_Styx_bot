#!/bin/bash
# Скрипт для исправления групп комментариев в базе данных

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

log "🔧 Исправление групп комментариев в базе данных..."

# Определяем пользователя бота
BOT_USER="ncux11"
BOT_DIR="/home/${BOT_USER}/bots/Flame_Of_Styx_bot"

# Переходим в директорию бота
cd "$BOT_DIR"

# Активируем виртуальное окружение
log "🐍 Активация виртуального окружения..."
source venv/bin/activate

# Запускаем скрипт исправления
log "📊 Запуск скрипта исправления..."
python scripts/fix_comment_groups.py

if [[ $? -eq 0 ]]; then
    success "Группы комментариев исправлены успешно!"
else
    error "Ошибка при исправлении групп комментариев"
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

success "✅ Исправление групп комментариев завершено!"
log "💡 Теперь команды /status и /channels должны показывать группы комментариев"
