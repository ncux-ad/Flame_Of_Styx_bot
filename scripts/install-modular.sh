#!/bin/bash

# Модульная установка бота
# Использование: ./scripts/install-modular.sh [modules...]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для красивого вывода
print_header() {
    echo -e "${BLUE}🚀 Flame of Styx Bot - Модульная установка${NC}"
    echo -e "${BLUE}===========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

print_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Доступные модули
declare -A MODULES=(
    ["core"]="Установка основного функционала бота"
    ["security"]="Настройка безопасности и логов"
    ["monitoring"]="Установка системы мониторинга"
    ["all"]="Установка всех модулей"
)

# Показать доступные модули
show_modules() {
    echo -e "${YELLOW}Доступные модули:${NC}"
    for module in "${!MODULES[@]}"; do
        echo "  • $module - ${MODULES[$module]}"
    done
}

# Установка модуля core
install_core() {
    print_step "Установка модуля core..."
    
    if [[ -f "scripts/install/install-core.sh" ]]; then
        source scripts/install/install-core.sh
        print_success "Модуль core установлен"
        return 0
    else
        print_error "Модуль core не найден"
        return 1
    fi
}

# Установка модуля security
install_security() {
    print_step "Установка модуля security..."
    
    if [[ -f "scripts/install/install-security.sh" ]]; then
        source scripts/install/install-security.sh
        if install_security; then
            print_success "Модуль security установлен"
            return 0
        else
            print_warning "Модуль security установлен с предупреждениями"
            return 1
        fi
    else
        print_error "Модуль security не найден"
        return 1
    fi
}

# Установка модуля monitoring
install_monitoring() {
    print_step "Установка модуля monitoring..."
    
    if [[ -f "scripts/install/install-monitoring-module.sh" ]]; then
        source scripts/install/install-monitoring-module.sh
        
        MONITORING_TYPE=$(install_monitoring "interactive")
        
        if [[ "$MONITORING_TYPE" != "None" ]]; then
            print_success "Модуль monitoring установлен: $MONITORING_TYPE"
            return 0
        else
            print_info "Модуль monitoring пропущен"
            return 1
        fi
    else
        print_error "Модуль monitoring не найден"
        return 1
    fi
}

# Интерактивный выбор модулей
interactive_mode() {
    print_info "Интерактивный режим установки"
    echo ""
    
    # Показываем доступные модули
    show_modules
    echo ""
    
    # Спрашиваем какие модули установить
    echo -e "${YELLOW}Выберите модули для установки (через пробел):${NC}"
    echo "Пример: core security monitoring"
    echo "Или 'all' для установки всех модулей"
    echo ""
    read -p "Введите модули: " -a selected_modules
    
    if [[ ${#selected_modules[@]} -eq 0 ]]; then
        print_error "Не выбрано ни одного модуля"
        exit 1
    fi
    
    # Проверяем наличие модуля all
    for module in "${selected_modules[@]}"; do
        if [[ "$module" == "all" ]]; then
            selected_modules=("core" "security" "monitoring")
            break
        fi
    done
    
    # Устанавливаем выбранные модули
    for module in "${selected_modules[@]}"; do
        if [[ -n "${MODULES[$module]}" ]]; then
            case $module in
                "core")
                    install_core
                    ;;
                "security")
                    install_security
                    ;;
                "monitoring")
                    install_monitoring
                    ;;
            esac
        else
            print_warning "Неизвестный модуль: $module"
        fi
    done
}

# Автоматический режим
auto_mode() {
    print_info "Автоматический режим установки"
    echo ""
    
    # Устанавливаем все модули по порядку
    install_core
    install_security
    install_monitoring
    
    print_success "Автоматическая установка завершена"
}

# Основная функция
main() {
    print_header
    
    # Проверяем аргументы
    if [[ $# -eq 0 ]]; then
        interactive_mode
    elif [[ "$1" == "all" ]]; then
        auto_mode
    else
        # Устанавливаем указанные модули
        for module in "$@"; do
            if [[ -n "${MODULES[$module]}" ]]; then
                case $module in
                    "core")
                        install_core
                        ;;
                    "security")
                        install_security
                        ;;
                    "monitoring")
                        install_monitoring
                        ;;
                esac
            else
                print_warning "Неизвестный модуль: $module"
            fi
        done
    fi
    
    echo ""
    print_success "Модульная установка завершена!"
    print_info "Для управления ботом используйте:"
    echo -e "  • ${YELLOW}Статус${NC}: sudo systemctl status antispam-bot"
    echo -e "  • ${YELLOW}Логи${NC}: sudo journalctl -u antispam-bot -f"
    echo -e "  • ${YELLOW}Перезапуск${NC}: sudo systemctl restart antispam-bot"
}

# Запуск
main "$@"
