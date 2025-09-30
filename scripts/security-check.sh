#!/bin/bash

# Скрипт для проверки безопасности проекта
# Генерирует отчеты bandit и safety

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

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v bandit &> /dev/null; then
        log_error "bandit не установлен. Установите: pip install bandit"
        exit 1
    fi
    
    if ! command -v safety &> /dev/null; then
        log_error "safety не установлен. Установите: pip install safety"
        exit 1
    fi
    
    log_success "Все зависимости установлены"
}

# Создание директорий для отчетов
create_directories() {
    log_info "Создание директорий для отчетов..."
    
    local reports_dir="reports/security"
    mkdir -p "$reports_dir"
    
    log_success "Директории созданы: $reports_dir"
}

# Запуск bandit
run_bandit() {
    log_info "Запуск bandit для статического анализа безопасности..."
    
    local bandit_report="reports/security/bandit-report.json"
    local bandit_html="reports/security/bandit-report.html"
    
    # JSON отчет
    if bandit -r app/ -f json -o "$bandit_report"; then
        log_success "Bandit JSON отчет создан: $bandit_report"
    else
        log_warning "Bandit завершился с предупреждениями"
    fi
    
    # HTML отчет
    if bandit -r app/ -f html -o "$bandit_html"; then
        log_success "Bandit HTML отчет создан: $bandit_html"
    else
        log_warning "Bandit HTML отчет завершился с предупреждениями"
    fi
    
    # Показываем краткую статистику
    if [[ -f "$bandit_report" ]]; then
        local high_count=$(jq '.metrics._totals."SEVERITY.HIGH"' "$bandit_report" 2>/dev/null || echo "0")
        local medium_count=$(jq '.metrics._totals."SEVERITY.MEDIUM"' "$bandit_report" 2>/dev/null || echo "0")
        local low_count=$(jq '.metrics._totals."SEVERITY.LOW"' "$bandit_report" 2>/dev/null || echo "0")
        
        log_info "Статистика bandit:"
        log_info "  HIGH: $high_count"
        log_info "  MEDIUM: $medium_count"
        log_info "  LOW: $low_count"
    fi
}

# Запуск safety
run_safety() {
    log_info "Запуск safety для проверки уязвимостей в зависимостях..."
    
    local safety_report="reports/security/safety-report.json"
    
    # JSON отчет
    if safety check --json > "$safety_report" 2>/dev/null; then
        log_success "Safety JSON отчет создан: $safety_report"
    else
        log_warning "Safety завершился с предупреждениями"
    fi
    
    # Показываем краткую статистику
    if [[ -f "$safety_report" ]]; then
        local vuln_count=$(jq '.vulnerabilities | length' "$safety_report" 2>/dev/null || echo "0")
        log_info "Найдено уязвимостей: $vuln_count"
        
        if [[ $vuln_count -gt 0 ]]; then
            log_warning "Обнаружены уязвимости в зависимостях!"
            log_info "Проверьте отчет: $safety_report"
        else
            log_success "Уязвимости в зависимостях не найдены"
        fi
    fi
}

# Создание сводного отчета
create_summary_report() {
    log_info "Создание сводного отчета безопасности..."
    
    local summary_file="reports/security/security-summary.md"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > "$summary_file" << EOF
# Отчет безопасности Flame of Styx Bot

**Дата проверки:** $timestamp
**Версия:** $(git describe --tags --always 2>/dev/null || echo "unknown")

## Статистика Bandit

EOF

    # Добавляем статистику bandit
    if [[ -f "reports/security/bandit-report.json" ]]; then
        local high_count=$(jq '.metrics._totals."SEVERITY.HIGH"' "reports/security/bandit-report.json" 2>/dev/null || echo "0")
        local medium_count=$(jq '.metrics._totals."SEVERITY.MEDIUM"' "reports/security/bandit-report.json" 2>/dev/null || echo "0")
        local low_count=$(jq '.metrics._totals."SEVERITY.LOW"' "reports/security/bandit-report.json" 2>/dev/null || echo "0")
        
        cat >> "$summary_file" << EOF
- **HIGH severity:** $high_count
- **MEDIUM severity:** $medium_count  
- **LOW severity:** $low_count

EOF
    fi

    # Добавляем статистику safety
    cat >> "$summary_file" << EOF
## Статистика Safety

EOF

    if [[ -f "reports/security/safety-report.json" ]]; then
        local vuln_count=$(jq '.vulnerabilities | length' "reports/security/safety-report.json" 2>/dev/null || echo "0")
        cat >> "$summary_file" << EOF
- **Уязвимости в зависимостях:** $vuln_count

EOF
    fi

    cat >> "$summary_file" << EOF
## Файлы отчетов

- [Bandit JSON](bandit-report.json)
- [Bandit HTML](bandit-report.html)
- [Safety JSON](safety-report.json)

## Рекомендации

1. Регулярно запускайте проверки безопасности
2. Обновляйте зависимости при обнаружении уязвимостей
3. Исправляйте найденные проблемы с HIGH и MEDIUM severity
4. Мониторьте LOW severity проблемы

## Автоматизация

Для автоматизации проверок добавьте в CI/CD:

\`\`\`bash
./scripts/security-check.sh
\`\`\`

EOF

    log_success "Сводный отчет создан: $summary_file"
}

# Очистка старых отчетов
cleanup_old_reports() {
    log_info "Очистка старых отчетов..."
    
    local reports_dir="reports/security"
    local days_old=30
    
    if [[ -d "$reports_dir" ]]; then
        find "$reports_dir" -name "*.json" -mtime +$days_old -delete 2>/dev/null || true
        find "$reports_dir" -name "*.html" -mtime +$days_old -delete 2>/dev/null || true
        find "$reports_dir" -name "*.md" -mtime +$days_old -delete 2>/dev/null || true
        
        log_success "Старые отчеты (старше $days_old дней) удалены"
    fi
}

# Основная функция
main() {
    log_info "Проверка безопасности Flame of Styx Bot"
    log_info "======================================"
    
    check_dependencies
    create_directories
    run_bandit
    run_safety
    create_summary_report
    cleanup_old_reports
    
    log_success "Проверка безопасности завершена!"
    log_info ""
    log_info "Отчеты сохранены в: reports/security/"
    log_info "Откройте reports/security/security-summary.md для просмотра сводки"
}

# Запуск
main "$@"
