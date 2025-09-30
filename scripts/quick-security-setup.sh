#!/bin/bash

# Быстрая настройка безопасности для существующих установок
# Использование: ./scripts/quick-security-setup.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Скрипт запущен с правами root. Это может быть небезопасно."
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей безопасности..."
    
    # Проверяем Python пакеты
    if ! python3 -c "import bandit" 2>/dev/null; then
        log_warning "bandit не установлен. Устанавливаем..."
        pip3 install bandit
    fi
    
    if ! python3 -c "import safety" 2>/dev/null; then
        log_warning "safety не установлен. Устанавливаем..."
        pip3 install safety
    fi
    
    if ! python3 -c "import cryptography" 2>/dev/null; then
        log_warning "cryptography не установлен. Устанавливаем..."
        pip3 install cryptography
    fi
    
    log_success "Все зависимости безопасности установлены"
}

# Настройка структуры логов
setup_logs() {
    log_info "Настройка структуры логов..."
    
    if [[ -f "scripts/setup-logs-structure.sh" ]]; then
        chmod +x scripts/setup-logs-structure.sh
        ./scripts/setup-logs-structure.sh
        log_success "Структура логов настроена"
    else
        log_warning "Скрипт настройки логов не найден, создаем базовую структуру..."
        mkdir -p logs/{general,encrypted,security,reports}
        log_success "Базовая структура логов создана"
    fi
}

# Запуск проверок безопасности
run_security_checks() {
    log_info "Запуск проверок безопасности..."
    
    if [[ -f "scripts/security-check.sh" ]]; then
        chmod +x scripts/security-check.sh
        ./scripts/security-check.sh
        log_success "Проверки безопасности завершены"
    else
        log_warning "Скрипт проверки безопасности не найден"
    fi
}

# Обновление конфигурации
update_config() {
    log_info "Обновление конфигурации..."
    
    # Проверяем, есть ли уже настройки безопасности в bot.py
    if ! grep -q "pii_protection" bot.py 2>/dev/null; then
        log_info "Добавляем импорт PII protection в bot.py..."
        # Здесь можно добавить автоматическое обновление bot.py
        log_warning "Необходимо вручную добавить импорт PII protection в bot.py"
    fi
    
    # Проверяем переменные окружения
    if [[ ! -f ".env" ]]; then
        log_info "Создаем файл .env..."
        cat > .env << EOF
# Окружение
ENVIRONMENT=production

# Безопасность
ENABLE_FULL_LOGGING=true

# PII Protection (генерируется автоматически)
# PII_ENCRYPTION_KEY=your_key_here
EOF
        log_success "Файл .env создан"
    else
        log_info "Файл .env уже существует"
    fi
}

# Создание символических ссылок
create_symlinks() {
    log_info "Создание символических ссылок..."
    
    # Создаем ссылку на логи в корне проекта
    if [[ ! -L "logs" && ! -d "logs" ]]; then
        if [[ -d "/var/log/flame-of-styx" ]]; then
            ln -sf /var/log/flame-of-styx logs
            log_success "Создана символическая ссылка logs -> /var/log/flame-of-styx"
        else
            log_warning "Директория /var/log/flame-of-styx не найдена"
        fi
    else
        log_info "Ссылка logs уже существует"
    fi
}

# Настройка cron задач
setup_cron() {
    log_info "Настройка автоматических задач..."
    
    # Проверяем, есть ли уже задачи безопасности в crontab
    if ! crontab -l 2>/dev/null | grep -q "security-check"; then
        log_info "Добавляем задачу проверки безопасности в crontab..."
        
        # Получаем текущий crontab
        current_crontab=$(crontab -l 2>/dev/null || echo "")
        
        # Добавляем новую задачу
        new_crontab="$current_crontab
# Проверка безопасности Flame of Styx Bot (еженедельно)
0 2 * * 0 cd $(pwd) && ./scripts/security-check.sh >> logs/security/cron.log 2>&1"
        
        # Устанавливаем новый crontab
        echo "$new_crontab" | crontab -
        log_success "Задача проверки безопасности добавлена в crontab"
    else
        log_info "Задача проверки безопасности уже существует в crontab"
    fi
}

# Проверка статуса
check_status() {
    log_info "Проверка статуса безопасности..."
    
    # Проверяем структуру логов
    if [[ -d "logs" ]]; then
        log_success "✓ Структура логов настроена"
    else
        log_warning "✗ Структура логов не настроена"
    fi
    
    # Проверяем отчеты безопасности
    if [[ -d "reports/security" ]]; then
        log_success "✓ Директория отчетов безопасности создана"
    else
        log_warning "✗ Директория отчетов безопасности не найдена"
    fi
    
    # Проверяем зависимости
    if python3 -c "import bandit, safety, cryptography" 2>/dev/null; then
        log_success "✓ Все зависимости безопасности установлены"
    else
        log_warning "✗ Некоторые зависимости безопасности отсутствуют"
    fi
    
    # Проверяем скрипты
    if [[ -f "scripts/security-check.sh" && -f "scripts/setup-logs-structure.sh" ]]; then
        log_success "✓ Скрипты безопасности доступны"
    else
        log_warning "✗ Некоторые скрипты безопасности отсутствуют"
    fi
}

# Основная функция
main() {
    log_info "Быстрая настройка безопасности Flame of Styx Bot"
    log_info "================================================"
    
    check_permissions
    check_dependencies
    setup_logs
    run_security_checks
    update_config
    create_symlinks
    setup_cron
    check_status
    
    log_success "Настройка безопасности завершена!"
    log_info ""
    log_info "Что было сделано:"
    log_info "  ✓ Установлены зависимости безопасности"
    log_info "  ✓ Настроена структура логов"
    log_info "  ✓ Запущены проверки безопасности"
    log_info "  ✓ Обновлена конфигурация"
    log_info "  ✓ Созданы символические ссылки"
    log_info "  ✓ Настроены автоматические задачи"
    log_info ""
    log_info "Полезные команды:"
    log_info "  • Проверка безопасности: ./scripts/security-check.sh"
    log_info "  • Анализ спама: /spam_analysis (в боте)"
    log_info "  • Логи безопасности: tail -f logs/security/security.log"
    log_info "  • Отчеты: reports/security/security-summary.md"
    log_info ""
    log_info "Для применения изменений перезапустите бота:"
    log_info "  sudo systemctl restart antispam-bot"
}

# Запуск
main "$@"
