#!/bin/bash

# Модуль установки безопасности
# Использование: source scripts/install/install-security.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
log_info() {
    echo -e "${BLUE}[SECURITY]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SECURITY]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[SECURITY]${NC} $1"
}

log_error() {
    echo -e "${RED}[SECURITY]${NC} $1"
}

# Установка зависимостей безопасности
install_security_dependencies() {
    log_info "Установка зависимостей безопасности..."
    
    # Проверяем Python пакеты
    local packages=("bandit" "safety" "cryptography")
    
    for package in "${packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            log_info "Устанавливаем $package..."
            pip3 install "$package" --quiet --disable-pip-version-check
        else
            log_info "$package уже установлен"
        fi
    done
    
    log_success "Зависимости безопасности установлены"
}

# Настройка структуры логов
setup_logs_structure() {
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

# Настройка переменных окружения
setup_environment() {
    log_info "Настройка переменных окружения для безопасности..."
    
    # Создаем или обновляем .env
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
        # Проверяем, есть ли уже настройки безопасности
        if ! grep -q "ENABLE_FULL_LOGGING" .env; then
            log_info "Добавляем настройки безопасности в .env..."
            echo "" >> .env
            echo "# Безопасность" >> .env
            echo "ENABLE_FULL_LOGGING=true" >> .env
            log_success "Настройки безопасности добавлены в .env"
        else
            log_info "Настройки безопасности уже присутствуют в .env"
        fi
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
setup_cron_tasks() {
    log_info "Настройка автоматических задач безопасности..."
    
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

# Проверка статуса безопасности
check_security_status() {
    log_info "Проверка статуса безопасности..."
    
    local status=0
    
    # Проверяем структуру логов
    if [[ -d "logs" ]]; then
        log_success "✓ Структура логов настроена"
    else
        log_warning "✗ Структура логов не настроена"
        status=1
    fi
    
    # Проверяем отчеты безопасности
    if [[ -d "reports/security" ]]; then
        log_success "✓ Директория отчетов безопасности создана"
    else
        log_warning "✗ Директория отчетов безопасности не найдена"
        status=1
    fi
    
    # Проверяем зависимости
    if python3 -c "import bandit, safety, cryptography" 2>/dev/null; then
        log_success "✓ Все зависимости безопасности установлены"
    else
        log_warning "✗ Некоторые зависимости безопасности отсутствуют"
        status=1
    fi
    
    # Проверяем скрипты
    if [[ -f "scripts/security-check.sh" && -f "scripts/setup-logs-structure.sh" ]]; then
        log_success "✓ Скрипты безопасности доступны"
    else
        log_warning "✗ Некоторые скрипты безопасности отсутствуют"
        status=1
    fi
    
    return $status
}

# Основная функция установки безопасности
install_security() {
    log_info "Установка модуля безопасности..."
    log_info "================================"
    
    install_security_dependencies
    setup_logs_structure
    run_security_checks
    setup_environment
    create_symlinks
    setup_cron_tasks
    
    if check_security_status; then
        log_success "Модуль безопасности установлен успешно!"
        return 0
    else
        log_warning "Модуль безопасности установлен с предупреждениями"
        return 1
    fi
}

# Если скрипт запущен напрямую
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    install_security
fi
